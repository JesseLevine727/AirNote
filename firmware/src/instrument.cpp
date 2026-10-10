#include "instrument.hpp"
#include <algorithm>
#include <cmath>

namespace airnote {
double frequency_hz(int note) {
    if (note < 0 || note >= kNoteCount) return 0.0;
    return 440.0 * std::pow(2.0, (kMidiNotes[note] - 69) / 12.0);
}

int note_at_distance(int mm) {
    if (mm < kMinMm || mm > kMaxMm) return kSilent;
    const int band = std::min(kNoteCount - 1,
        (mm - kMinMm) * kNoteCount / (kMaxMm - kMinMm));
    return kNoteCount - 1 - band; // Closer hand means higher pitch.
}

void Controller::clear() {
    note_ = candidate_ = kSilent;
    candidate_count_ = 0;
    have_valid_ = false;
}

void Controller::set_muted(bool muted) {
    muted_ = muted;
    if (muted) clear();
}

void Controller::tick(uint32_t now_ms) {
    if (have_valid_ && static_cast<uint32_t>(now_ms - last_valid_ms_) >= kStaleMs)
        clear();
}

void Controller::sample(uint32_t now_ms, int mm, bool valid) {
    tick(now_ms);
    if (muted_) return;
    if (!valid) {
        candidate_ = kSilent;
        candidate_count_ = 0;
        return;
    }
    const int new_note = note_at_distance(mm);
    if (new_note == kSilent) {
        clear(); // A valid observation outside the playing range gates off.
        return;
    }
    have_valid_ = true;
    last_valid_ms_ = now_ms;
    if (note_ != kSilent) {
        const int band = kNoteCount - 1 - note_;
        const double low = kMinMm + band * (kMaxMm - kMinMm) / double(kNoteCount);
        const double high = kMinMm + (band + 1) * (kMaxMm - kMinMm) / double(kNoteCount);
        if (mm >= low - kHysteresisMm && mm <= high + kHysteresisMm) {
            candidate_ = kSilent;
            candidate_count_ = 0;
            return;
        }
    }
    if (candidate_ == new_note) ++candidate_count_;
    else { candidate_ = new_note; candidate_count_ = 1; }
    if (candidate_count_ >= 2) {
        note_ = new_note;
        candidate_ = kSilent;
        candidate_count_ = 0;
    }
}

Synthesizer::Synthesizer() {
    constexpr double pi = 3.14159265358979323846;
    for (size_t i = 0; i < sine_.size(); ++i)
        sine_[i] = static_cast<int16_t>(std::lround(std::sin(2 * pi * i / 256) * 32767));
    for (int i = 0; i < kNoteCount; ++i)
        increments_[i] = static_cast<uint32_t>(std::llround(frequency_hz(i) * 4294967296.0 / kSampleRate));
}

void Synthesizer::set_control(int note, uint16_t volume) {
    volume = std::min<uint16_t>(volume, 4095);
    if (note < 0 || note >= kNoteCount) { target_amplitude_ = 0; return; }
    increment_ = increments_[note];
    // Quadratic control provides useful resolution at low listening levels.
    target_amplitude_ = static_cast<int>(
        uint64_t(volume) * volume * kMaxAmplitude / (uint64_t(4095) * 4095));
}

void Synthesizer::render(int16_t* output, size_t count) {
    constexpr int step = (kMaxAmplitude + 239) / 240;
    for (size_t i = 0; i < count; ++i) {
        amplitude_ += std::clamp(target_amplitude_ - amplitude_, -step, step);
        const unsigned index = phase_ >> 24;
        const unsigned fraction = (phase_ >> 8) & 0xffff;
        const int interpolated = sine_[index] +
            ((int(sine_[index + 1]) - sine_[index]) * int(fraction)) / 65536;
        output[i] = static_cast<int16_t>(interpolated * amplitude_ / 32768);
        phase_ += increment_;
    }
}
} // namespace airnote

