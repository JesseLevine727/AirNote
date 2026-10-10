#include "instrument.hpp"
#include <algorithm>
#include <cmath>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <vector>

// Independent acceptance tests: expected musical data and physical input
// traces are explicit, rather than generated from the controller's internals.
static unsigned checks = 0;
static void require(bool ok, const char* message) {
    ++checks;
    if (!ok) { std::cerr << "FAIL: " << message << '\n'; std::exit(1); }
}

static void control_tests() {
    using airnote::Controller;
    const int centers[] = {118,154,190,227,263,300,336,372,409,445,482};
    for (int i = 0; i < 11; ++i) {
        Controller c;
        c.sample(0, centers[i], true);
        c.sample(25, centers[i], true);
        require(c.note() == -1, "startup remains muted");
        c.set_muted(false);
        c.sample(50, centers[i], true);
        require(c.note() == -1, "single observation cannot start a note");
        c.sample(75, centers[i], true);
        require(c.note() == 10-i, "physical note centers map high-to-low");
        for (uint32_t t=100; t<1100; t+=25) {
            c.sample(t, centers[i] + (int((t/25)%3)-1), true);
            require(c.note() == 10-i, "center jitter holds the selected note");
        }
    }
    require(airnote::note_at_distance(99) == -1, "near out-of-range excluded");
    require(airnote::note_at_distance(100) == 10, "near endpoint is C6");
    require(airnote::note_at_distance(500) == 0, "far endpoint is C4");
    require(airnote::note_at_distance(501) == -1, "far out-of-range excluded");
    require(airnote::note_at_distance(std::numeric_limits<int>::min()) == -1,
            "extreme negative input excluded without overflow");
    require(airnote::note_at_distance(std::numeric_limits<int>::max()) == -1,
            "extreme positive input excluded without overflow");

    Controller c;
    c.set_muted(false);
    c.sample(0, 118, true); c.sample(25, 118, true);
    c.sample(50, 482, true);
    require(c.note()==10, "isolated far glitch cannot change note");
    c.sample(75, 482, false);
    c.sample(100, 482, true);
    require(c.note()==10, "invalid reading breaks two-reading qualification");
    c.sample(125, 482, true);
    require(c.note()==0, "two consecutive far readings change note");
    c.sample(150, 1000, false);
    c.tick(224);
    require(c.note()==0, "invalid reading does not prematurely cancel hold");
    c.tick(225);
    require(c.note()==-1, "invalid reading cannot extend 100-ms freshness");
    c.sample(250,300,true); c.sample(275,300,true);
    c.sample(300,501,true);
    require(c.note()==-1, "valid out-of-range reading gates off immediately");
    c.sample(325,300,true); c.sample(350,300,true);
    c.set_muted(true);
    require(c.note()==-1, "mute gates off immediately");
    c.set_muted(false); c.sample(375,300,true);
    require(c.note()==-1, "unmute requires fresh qualification");

    Controller wrap;
    wrap.set_muted(false);
    wrap.sample(UINT32_MAX-50,300,true);
    wrap.sample(UINT32_MAX-25,300,true);
    wrap.tick(73);
    require(wrap.note()!=-1, "freshness survives clock wrap before deadline");
    wrap.tick(74);
    require(wrap.note()==-1, "freshness expires at deadline across wrap");

    Controller boundary;
    boundary.set_muted(false);
    boundary.sample(0,118,true); boundary.sample(25,118,true);
    for (uint32_t t=50; t<1000; t+=25) {
        boundary.sample(t,(t/25)%2 ? 136 : 137,true);
        require(boundary.note()==10, "boundary jitter stays within hysteresis");
    }
    boundary.sample(1000,145,true); boundary.sample(1025,145,true);
    require(boundary.note()==9, "hysteresis does not prevent deliberate crossing");

    airnote::FrameTracker frames;
    Controller frozen;
    frozen.set_muted(false);
    for (uint32_t t=0;t<=250;t+=25) {
        const uint8_t counter = t == 0 ? 254 : 255;
        if (frames.accept(counter)) frozen.sample(t,300,true);
        frozen.tick(t);
        if (t==25) require(frozen.note()==5,"new sensor frame can qualify note");
        if (t>=125) require(frozen.note()==-1,"stuck-ready repeated frame cannot renew freshness");
    }
    require(frames.accept(0),"new sensor frame accepted across counter rollover");
    require(!frames.accept(0),"duplicate zero counter rejected");
    frames.reset();
    require(frames.accept(0),"counter tracker reset after sensor restart");
}

static double rms(const std::vector<int16_t>& x) {
    double sum=0;
    for (size_t i=1000;i<x.size();++i) sum+=double(x[i])*x[i];
    return std::sqrt(sum/(x.size()-1000));
}

static void synthesis_tests() {
    const double expected[] = {261.625565,293.664768,329.627557,391.995436,
        440.0,523.251131,587.329536,659.255114,783.990872,880.0,1046.502261};
    for (int note=0;note<11;++note) {
        airnote::Synthesizer synth;
        std::vector<int16_t> samples(96000);
        synth.set_control(note,4095);
        synth.render(samples.data(),samples.size());
        unsigned crosses=0;
        for(size_t i=1001;i<samples.size();++i)
            if(samples[i-1]<=0 && samples[i]>0) ++crosses;
        const double measured=double(crosses)*48000/(samples.size()-1001);
        require(std::abs(1200*std::log2(measured/expected[note]))<=5,
                "rendered steady pitch within five cents");
        for(auto x:samples) require(x>=-8192 && x<=8192,"amplitude bound holds");
        synth.set_control(-1,4095);
        synth.render(samples.data(),1000);
        require(std::all_of(samples.begin()+240,samples.begin()+1000,
                           [](int16_t x){return x==0;}), "release finishes within five ms");
    }
    double previous=-1;
    for(uint16_t volume: {uint16_t(0),uint16_t(256),uint16_t(1024),uint16_t(2048),
                         uint16_t(3072),uint16_t(4095),uint16_t(65535)}) {
        airnote::Synthesizer synth;
        std::vector<int16_t> samples(48000);
        synth.set_control(4,volume); synth.render(samples.data(),samples.size());
        const double level=rms(samples);
        require(level>=previous,"volume amplitude is monotonic");
        if(volume==0) require(level==0,"zero volume is digital silence");
        previous=level;
    }
    airnote::Synthesizer synth;
    int16_t samples[512];
    synth.set_control(200,4095); synth.render(samples,512);
    require(std::all_of(samples,samples+512,[](int16_t x){return x==0;}),
            "invalid note cannot produce sound");
}

int main() {
    control_tests(); synthesis_tests();
    std::cout << "PASS: " << checks << " independent controller/synth assertions\n";
    std::cout << "Physical latency, sensing, power and audio quality remain PENDING.\n";
}
