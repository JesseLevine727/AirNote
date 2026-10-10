#include "instrument.hpp"
#include "VL53L1X.h"
#include "boards/airnote.h"
#include "hardware/adc.h"
#include "hardware/clocks.h"
#include "hardware/dma.h"
#include "hardware/watchdog.h"
#include "pico/audio_i2s.h"
#include "pico/critical_section.h"
#include "pico/multicore.h"
#include "pico/stdio_usb.h"
#include "tusb.h"
#include <algorithm>
#include <cstdio>
extern "C" uint32_t airnote_audio_underrun_count(void);

namespace {
constexpr unsigned kFrames = 128;
critical_section_t control_lock;
struct Shared {
    int note = airnote::kSilent;
    uint16_t volume = 0;
    bool audio_ready = false;
    uint32_t heartbeat_ms = 0;
    uint32_t max_producer_gap_us = 0;
    uint32_t underruns = 0;
    bool stop_requested = false;
    bool audio_stopped = false;
} shared;

void audio_core() {
    static audio_format_t format = {airnote::kSampleRate, AUDIO_BUFFER_FORMAT_PCM_S16, 2};
    static audio_buffer_format_t buffer_format = {&format, 4};
    auto* pool = audio_new_producer_pool(&buffer_format, 2, kFrames);
    audio_i2s_config_t config = {AIRNOTE_I2S_DATA_PIN, AIRNOTE_I2S_BCLK_PIN, 0, 0};
    if (!pool || !audio_i2s_setup(&format, &config) ||
        !audio_i2s_connect_extra(pool, false, 0, kFrames, nullptr)) {
        while (true) tight_loop_contents(); // core0 keeps amplifier disabled.
    }
    airnote::Synthesizer synth;
    int16_t mono[kFrames];
    // Queue two silent buffers before DMA starts. Boot cannot expose stale RAM.
    for (int i = 0; i < 2; ++i) {
        auto* b = take_audio_buffer(pool, true);
        std::fill_n(reinterpret_cast<int16_t*>(b->buffer->bytes), kFrames * 2, 0);
        b->sample_count = kFrames;
        give_audio_buffer(pool, b);
    }
    audio_i2s_set_enabled(true);
    uint32_t last_submit_us = time_us_32();
    while (true) {
        critical_section_enter_blocking(&control_lock);
        const bool stop = shared.stop_requested;
        critical_section_exit(&control_lock);
        if (stop) {
            // A USB suspend permanently parks audio until power-cycle. The
            // diagnostic sensor can resume, but no partially stopped DMA/PIO
            // stream is restarted. A measured USB low-power plan is still needed.
            const uint32_t interrupt_state = save_and_disable_interrupts();
            dma_channel_abort(config.dma_channel);
            audio_i2s_set_enabled(false);
            dma_irqn_acknowledge_channel(PICO_AUDIO_I2S_DMA_IRQ, config.dma_channel);
            restore_interrupts(interrupt_state);
            critical_section_enter_blocking(&control_lock);
            shared.audio_ready = false;
            shared.audio_stopped = true;
            critical_section_exit(&control_lock);
            while (true) __wfe();
        }
        auto* b = take_audio_buffer(pool, true);
        critical_section_enter_blocking(&control_lock);
        const int note = shared.note;
        const uint16_t volume = shared.volume;
        critical_section_exit(&control_lock);
        synth.set_control(note, volume);
        synth.render(mono, kFrames);
        auto* stereo = reinterpret_cast<int16_t*>(b->buffer->bytes);
        for (unsigned i = 0; i < kFrames; ++i) stereo[2*i] = stereo[2*i+1] = mono[i];
        b->sample_count = kFrames;
        give_audio_buffer(pool, b);
        const uint32_t now = time_us_32();
        critical_section_enter_blocking(&control_lock);
        shared.audio_ready = true;
        shared.heartbeat_ms = millis();
        shared.max_producer_gap_us = std::max(shared.max_producer_gap_us, uint32_t(now - last_submit_us));
        shared.underruns = airnote_audio_underrun_count();
        critical_section_exit(&control_lock);
        last_submit_us = now;
    }
}

bool start_sensor(VL53L1X& sensor) {
    gpio_put(AIRNOTE_XSHUT_PIN, false);
    gpio_set_dir(AIRNOTE_XSHUT_PIN, GPIO_OUT);
    sleep_ms(2);
    gpio_set_dir(AIRNOTE_XSHUT_PIN, GPIO_IN); // external pull-up; never drive high
    sleep_ms(3);
    Wire.clear_error();
    sensor.setTimeout(100);
    if (!sensor.init(true) || Wire.error()) return false;
    // Shared AVDD=3V3. Configure BOTH I2C and GPIO high-voltage modes.
    const auto gpio_config = static_cast<VL53L1X::regAddr>(0x002f);
    sensor.writeReg(gpio_config, sensor.readReg(gpio_config) | 1u);
    const auto i2c_config = static_cast<VL53L1X::regAddr>(0x002e);
    if (!(sensor.readReg(i2c_config) & 1) || !(sensor.readReg(gpio_config) & 1) || Wire.error()) return false;
    if (!sensor.setDistanceMode(VL53L1X::Short) ||
        !sensor.setMeasurementTimingBudget(20000) || Wire.error()) return false;
    sensor.setROISize(8, 8); // Provisional optical field; verify with real palms.
    sensor.startContinuous(25);
    return !Wire.error();
}
}

int main() {
    gpio_init(AIRNOTE_AMP_ENABLE_PIN);
    gpio_put(AIRNOTE_AMP_ENABLE_PIN, false);
    gpio_set_dir(AIRNOTE_AMP_ENABLE_PIN, GPIO_OUT);
    set_sys_clock_khz(120000, true); // Exact PIO divisor for 48kHz at this clock.
    stdio_init_all();
    gpio_init(PICO_DEFAULT_LED_PIN); gpio_set_dir(PICO_DEFAULT_LED_PIN, GPIO_OUT);
    gpio_init(AIRNOTE_MUTE_N_PIN); gpio_set_dir(AIRNOTE_MUTE_N_PIN, GPIO_IN);
    gpio_pull_up(AIRNOTE_MUTE_N_PIN);
    gpio_init(AIRNOTE_XSHUT_PIN);
    gpio_disable_pulls(AIRNOTE_XSHUT_PIN);
    gpio_put(AIRNOTE_XSHUT_PIN, false);
    gpio_set_dir(AIRNOTE_XSHUT_PIN, GPIO_OUT); // Hold sensor off before USB configuration.
    gpio_init(AIRNOTE_SENSOR_IRQ_PIN); gpio_set_dir(AIRNOTE_SENSOR_IRQ_PIN, GPIO_IN);
    gpio_disable_pulls(AIRNOTE_SENSOR_IRQ_PIN);
    adc_init(); adc_gpio_init(AIRNOTE_VOLUME_PIN); adc_select_input(0);
    i2c_init(i2c0, 400000);
    gpio_set_function(PICO_DEFAULT_I2C_SDA_PIN, GPIO_FUNC_I2C);
    gpio_set_function(PICO_DEFAULT_I2C_SCL_PIN, GPIO_FUNC_I2C);
    critical_section_init(&control_lock);
    VL53L1X sensor;
    bool sensor_ok = false;
    bool audio_started = false;
    bool peripherals_started = false;
    bool was_suspended = false;
    uint32_t last_ready_ms = millis(), last_retry_ms = millis(), seq = 0;
    uint32_t last_status_ms = millis();
    airnote::Controller controller;
    airnote::FrameTracker frames;
    // The physical switch must first be observed in MUTE after boot or USB
    // diagnostics connection. This prevents an unexpected sound after reset.
    bool armed = false;
    bool usb_host_seen = false;
    uint32_t mute_since_ms = millis();
    bool was_muted = false;
    watchdog_enable(1000, true);
    printf("AirNote engineering firmware; distance correction=%d mm; bench calibration required\n", AIRNOTE_OFFSET_MM);
    printf("sample,sequence,time_ms,raw_mm,corrected_mm,range_status,transport_error,note,sensor_counter\n");
    while (true) {
        uint32_t now = millis();
        // Latch any USB host connection until power-cycle. A negative result
        // is NOT proof of available source current: use the specified adapter
        // in PLAY mode and keep the hardware switch muted on a computer.
        usb_host_seen = usb_host_seen || tud_connected();
        if (usb_host_seen) armed = false;
        const bool switch_muted = !gpio_get(AIRNOTE_MUTE_N_PIN);
        if (switch_muted && !was_muted) mute_since_ms = now;
        if (switch_muted && uint32_t(now - mute_since_ms) >= 30) armed = true;
        was_muted = switch_muted;
        const bool muted = switch_muted || !armed || usb_host_seen;
        controller.set_muted(muted);
        const bool suspended = tud_suspended();
        const bool deconfigured = peripherals_started && usb_host_seen && !tud_mounted();
        const bool power_mode_ready = !suspended &&
            (tud_mounted() || (!usb_host_seen && armed && !switch_muted));
        if ((suspended && !was_suspended) || deconfigured) {
            gpio_put(AIRNOTE_AMP_ENABLE_PIN, false);
            gpio_put(AIRNOTE_XSHUT_PIN, false);
            gpio_set_dir(AIRNOTE_XSHUT_PIN, GPIO_OUT);
            sensor_ok = false;
            peripherals_started = false;
            controller.set_muted(true);
            critical_section_enter_blocking(&control_lock);
            shared.note = airnote::kSilent;
            shared.stop_requested = true;
            critical_section_exit(&control_lock);
        }
        was_suspended = suspended;
        if (power_mode_ready && !peripherals_started) {
            if (!audio_started) {
                multicore_launch_core1(audio_core);
                audio_started = true;
            }
            sensor_ok = start_sensor(sensor);
            frames.reset();
            peripherals_started = true;
            now = millis();
            last_ready_ms = last_retry_ms = now;
        }
        if (sensor_ok) {
            Wire.clear_error();
            const bool ready = sensor.dataReady();
            if (Wire.error()) { sensor_ok = false; controller.set_muted(true); }
            else if (ready) {
                const int raw = sensor.read(false);
                const bool bus_error = Wire.error();
                const int corrected = raw + AIRNOTE_OFFSET_MM;
                const bool fresh = !bus_error && frames.accept(sensor.getStreamCount());
                if (fresh) {
                    controller.sample(now, corrected,
                        sensor.ranging_data.range_status == VL53L1X::RangeValid);
                    last_ready_ms = now;
                    printf("sample,%lu,%lu,%d,%d,%u,%u,%d,%u\n",
                        static_cast<unsigned long>(seq++), static_cast<unsigned long>(now), raw, corrected,
                        sensor.ranging_data.range_status, bus_error, controller.note(), sensor.getStreamCount());
                }
                if (bus_error) { sensor_ok = false; controller.set_muted(true); }
            }
            if (uint32_t(now - last_ready_ms) > 500) { sensor_ok = false; controller.set_muted(true); }
        }
        controller.tick(now);
        critical_section_enter_blocking(&control_lock);
        const bool audio_ok = shared.audio_ready && uint32_t(millis() - shared.heartbeat_ms) < 50;
        const bool audio_stopped = shared.audio_stopped;
        shared.note = controller.note();
        shared.volume = adc_read();
        const uint32_t gap = shared.max_producer_gap_us;
        const uint32_t underruns = shared.underruns;
        critical_section_exit(&control_lock);
        gpio_put(AIRNOTE_AMP_ENABLE_PIN, sensor_ok && audio_ok && !muted);
        gpio_put(PICO_DEFAULT_LED_PIN, power_mode_ready &&
            (sensor_ok ? controller.note() != airnote::kSilent : ((now / 250) & 1)));
        if (uint32_t(now - last_status_ms) >= 1000) {
            printf("status,%lu,sensor=%u,armed=%u,muted=%u,max_audio_producer_gap_us=%lu,underruns=%lu\n",
                static_cast<unsigned long>(now), sensor_ok, armed, muted, static_cast<unsigned long>(gap), static_cast<unsigned long>(underruns));
            last_status_ms = now;
        }
        if (power_mode_ready && peripherals_started && !sensor_ok && uint32_t(now - last_retry_ms) >= 1000) {
            gpio_put(AIRNOTE_AMP_ENABLE_PIN, false);
            i2c_deinit(i2c0); i2c_init(i2c0, 400000);
            sensor_ok = start_sensor(sensor);
            frames.reset();
            last_ready_ms = last_retry_ms = millis();
        }
        if (!audio_started || audio_stopped || audio_ok) watchdog_update();
        sleep_ms(1);
    }
}

