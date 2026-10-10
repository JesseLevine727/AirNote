#include "instrument.hpp"
#include <algorithm>
#include <cmath>
#include <cstdlib>
#include <iostream>
#include <limits>
#include <vector>
using namespace airnote;
#define CHECK(expr) do { if (!(expr)) { std::cerr << __LINE__ << ": " << #expr << "\n"; std::exit(1); } } while (0)

static int centre(int note) {
    return int(kMinMm + (kNoteCount - 1 - note + 0.5) * (kMaxMm - kMinMm) / kNoteCount);
}
static void acquire(Controller& c, int mm, uint32_t start) {
    c.sample(start, mm, true); c.sample(start + 25, mm, true);
}
int main() {
    CHECK(note_at_distance(99) == kSilent);
    CHECK(note_at_distance(100) == 10);
    CHECK(note_at_distance(500) == 0);
    CHECK(note_at_distance(501) == kSilent);
    for (int n = 0; n < kNoteCount; ++n) {
        Controller c;
        acquire(c, centre(n), 0); CHECK(c.note() == kSilent); // boot mute
        c.set_muted(false);
        c.sample(100, centre(n), true); CHECK(c.note() == kSilent);
        c.sample(125, centre(n), true); CHECK(c.note() == n);
        for (uint32_t t = 150; t < 60150; t += 25) {
            c.sample(t, centre(n) + int(t % 3) - 1, true);
            CHECK(c.note() == n);
        }
    }
    Controller c; c.set_muted(false); acquire(c, centre(5), 0);
    // A single implausible jump does not change the playing note.
    c.sample(50, centre(0), true); CHECK(c.note() == 5);
    c.sample(75, centre(5), true); CHECK(c.note() == 5);
    // Hysteresis at the boundary between bands 5 and 6 (318.18 mm).
    for (uint32_t t = 100; t < 1000; t += 25) {
        c.sample(t, (t % 50) ? 316 : 321, true); CHECK(c.note() == 5);
    }
    c.sample(1000, 325, true); CHECK(c.note() == 5);
    c.sample(1025, 325, true); CHECK(c.note() == 4);
    // Invalid readings cannot indefinitely preserve the previous note.
    c.sample(1050, centre(4), false); CHECK(c.note() == 4);
    c.sample(1100, centre(4), false); CHECK(c.note() == 4);
    c.tick(1125); CHECK(c.note() == kSilent);
    acquire(c, centre(1), 1200); CHECK(c.note() == 1);
    c.sample(1250, 700, true); CHECK(c.note() == kSilent);
    acquire(c, centre(1), 1300);
    c.set_muted(true); CHECK(c.note() == kSilent);
    c.set_muted(false); c.tick(1350); CHECK(c.note() == kSilent);
    // Sensor timestamps wrap after about 49 days.
    acquire(c, centre(2), UINT32_MAX - 50);
    c.tick(49); CHECK(c.note() == 2);
    c.tick(75); CHECK(c.note() == kSilent);
    // Frozen sensor result with a stuck data-ready flag must not renew a note.
    FrameTracker frames; Controller frozen; frozen.set_muted(false);
    CHECK(frames.accept(254)); frozen.sample(0, centre(3), true);
    CHECK(frames.accept(255)); frozen.sample(25, centre(3), true);
    CHECK(frozen.note() == 3);
    for (uint32_t t = 50; t <= 125; t += 25) {
        CHECK(!frames.accept(255)); frozen.tick(t);
    }
    CHECK(frozen.note() == kSilent);
    CHECK(frames.accept(0)); CHECK(!frames.accept(0));
    frames.reset(); CHECK(frames.accept(0));
    // Every synthesized note: frequency, gain ceiling and DC balance.
    for (int n = 0; n < kNoteCount; ++n) {
        Synthesizer s;
        std::vector<int16_t> samples(kSampleRate * 2);
        s.set_control(n, 4095); s.render(samples.data(), samples.size());
        int crossings = 0; long long sum = 0; int peak = 0;
        for (size_t i = kSampleRate; i < samples.size(); ++i) {
            crossings += samples[i-1] <= 0 && samples[i] > 0;
            sum += samples[i]; peak = std::max(peak, std::abs(int(samples[i])));
        }
        CHECK(std::abs(crossings - frequency_hz(n)) <= 1.0);
        CHECK(peak <= kMaxAmplitude && peak > kMaxAmplitude - 20);
        CHECK(std::abs(double(sum) / kSampleRate) < 12.0);
        s.set_control(kSilent, 4095); s.render(samples.data(), 480);
        CHECK(std::all_of(samples.begin() + 240, samples.begin() + 480, [](int16_t v){ return v == 0; }));
        s.set_control(n, 0); s.render(samples.data(), 480);
        CHECK(std::all_of(samples.begin(), samples.begin() + 480, [](int16_t v){ return v == 0; }));
    }
    std::cout << "PASS: all 11 note zones, startup mute, acquisition, hysteresis, outliers, stale/invalid samples, range gating, mute, timestamp wrap, pitch, amplitude, DC and release envelope\n";
}

