#pragma once
#include <array>
#include <cstddef>
#include <cstdint>

namespace airnote {
constexpr uint32_t kSampleRate = 48000;
constexpr int kNoteCount = 11;
constexpr int kSilent = -1;
constexpr uint32_t kStaleMs = 100;
constexpr int kMinMm = 100;
constexpr int kMaxMm = 500;
constexpr int kHysteresisMm = 5;
constexpr int kMaxAmplitude = 8192; // -12 dBFS peak; power must be measured.
inline constexpr std::array<int, kNoteCount> kMidiNotes = {
    60, 62, 64, 67, 69, 72, 74, 76, 79, 81, 84};

double frequency_hz(int note);
int note_at_distance(int mm);

class FrameTracker {
public:
    bool accept(uint8_t counter) {
        if (seen_ && counter == last_) return false;
        seen_ = true; last_ = counter; return true;
    }
    void reset() { seen_ = false; }
private:
    bool seen_ = false;
    uint8_t last_ = 0;
};

// Control state is independent of the sensor driver and audio transport.
// Invalid samples cannot renew freshness; two consecutive valid readings are
// required to enter a new note. A bounded deadband suppresses boundary chatter.
class Controller {
public:
    void sample(uint32_t now_ms, int distance_mm, bool valid);
    void tick(uint32_t now_ms);
    void set_muted(bool muted);
    int note() const { return note_; }
private:
    void clear();
    int note_ = kSilent;
    int candidate_ = kSilent;
    unsigned candidate_count_ = 0;
    uint32_t last_valid_ms_ = 0;
    bool have_valid_ = false;
    bool muted_ = true;
};

class Synthesizer {
public:
    Synthesizer();
    // volume is 0..4095. One oscillator, continuous phase, five-ms gain ramp.
    void set_control(int note, uint16_t volume);
    void render(int16_t* output, size_t count);
private:
    std::array<int16_t, 257> sine_{};
    std::array<uint32_t, kNoteCount> increments_{};
    uint32_t phase_ = 0;
    uint32_t increment_ = 0;
    int amplitude_ = 0;
    int target_amplitude_ = 0;
};
} // namespace airnote

