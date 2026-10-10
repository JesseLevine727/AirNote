#pragma once
#include <cstdint>
#include "pico/stdlib.h"
inline uint32_t millis() { return to_ms_since_boot(get_absolute_time()); }
inline void delay(uint32_t ms) { sleep_ms(ms); }
inline void delayMicroseconds(uint32_t us) { sleep_us(us); }

