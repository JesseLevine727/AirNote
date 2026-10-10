#include "Wire.h"
TwoWire Wire;
void TwoWire::beginTransmission(uint8_t address) { address_ = address; tx_count_ = 0; }
size_t TwoWire::write(uint8_t value) {
    if (tx_count_ >= tx_.size()) { error_ = true; return 0; }
    tx_[tx_count_++] = value; return 1;
}
uint8_t TwoWire::endTransmission() {
    const int n = i2c_write_timeout_us(i2c0, address_, tx_.data(), tx_count_, false, 2000);
    if (n != static_cast<int>(tx_count_)) { error_ = true; return 4; }
    return 0;
}
uint8_t TwoWire::requestFrom(uint8_t address, uint8_t count) {
    rx_count_ = rx_index_ = 0;
    if (count > rx_.size()) { error_ = true; return 0; }
    const int n = i2c_read_timeout_us(i2c0, address, rx_.data(), count, false, 2000);
    if (n != count) { error_ = true; return 0; }
    rx_count_ = count; return count;
}
int TwoWire::read() {
    if (rx_index_ >= rx_count_) { error_ = true; return 0; }
    return rx_[rx_index_++];
}

