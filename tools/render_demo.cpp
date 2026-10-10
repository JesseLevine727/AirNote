#include "instrument.hpp"
#include <fstream>
#include <iostream>
#include <vector>
static void little(std::ofstream& out, uint32_t x, unsigned bytes) {
    for (unsigned i = 0; i < bytes; ++i) out.put(char((x >> (i * 8)) & 255));
}
int main(int argc, char** argv) {
    if (argc != 2) { std::cerr << "usage: render_demo output.wav\n"; return 1; }
    std::ofstream out(argv[1], std::ios::binary);
    if (!out) return 1;
    constexpr uint32_t count = airnote::kSampleRate / 3;
    constexpr uint32_t total = count * 23;
    out.write("RIFF", 4); little(out, 36 + total * 2, 4); out.write("WAVEfmt ", 8);
    little(out, 16, 4); little(out, 1, 2); little(out, 1, 2);
    little(out, airnote::kSampleRate, 4); little(out, airnote::kSampleRate * 2, 4);
    little(out, 2, 2); little(out, 16, 2); out.write("data", 4); little(out, total * 2, 4);
    airnote::Synthesizer synth; std::vector<int16_t> samples(count);
    for (int i = 0; i < 23; ++i) {
        const int note = i < 11 ? i : (i < 22 ? 21 - i : -1);
        synth.set_control(note, 3000); synth.render(samples.data(), samples.size());
        for (auto value : samples) little(out, static_cast<uint16_t>(value), 2);
    }
    std::cout << "Synthetic firmware demo only; does not represent measured PCB audio.\n";
}
