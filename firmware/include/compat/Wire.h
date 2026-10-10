#pragma once
#include "Arduino.h"
#include "hardware/i2c.h"
#include <array>
#include <cstddef>

// Narrow compatibility adapter for the vendored sensor driver. Every I2C
// transaction is bounded. The sticky error covers reads the original driver's
// last_status field does not report.
class TwoWire {
public:
    void beginTransmission(uint8_t address);
    size_t write(uint8_t value);
    uint8_t endTransmission();
    uint8_t requestFrom(uint8_t address, uint8_t count);
    int read();
    void clear_error() { error_ = false; }
    bool error() const { return error_; }
private:
    std::array<uint8_t, 32> tx_{}, rx_{};
    size_t tx_count_ = 0, rx_count_ = 0, rx_index_ = 0;
    uint8_t address_ = 0;
    bool error_ = false;
};
extern TwoWire Wire;

