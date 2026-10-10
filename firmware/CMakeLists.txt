cmake_minimum_required(VERSION 3.20)
set(PICO_BOARD airnote)
set(PICO_BOARD_HEADER_DIRS ${CMAKE_CURRENT_LIST_DIR}/include/boards)
set(PICO_SDK_PATH ${CMAKE_CURRENT_LIST_DIR}/../.deps/pico-sdk CACHE PATH "Pinned SDK")
set(PICO_EXTRAS_PATH ${CMAKE_CURRENT_LIST_DIR}/../.deps/pico-extras CACHE PATH "Pinned audio library")
set(PICOTOOL_GIT_BRANCH 2041936441b48a3cc53ae3da9e805229fe8f4e18 CACHE STRING "Pinned UF2 build utility")
if(NOT EXISTS ${PICO_SDK_PATH}/pico_sdk_init.cmake)
  message(FATAL_ERROR "Run python3 tools/fetch_dependencies.py first")
endif()
include(${PICO_SDK_PATH}/external/pico_sdk_import.cmake)
include(${PICO_EXTRAS_PATH}/external/pico_extras_import.cmake)
project(airnote C CXX ASM)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 17)
pico_sdk_init()
set(AIRNOTE_OFFSET_MM 0 CACHE STRING "Per-board measured distance correction in mm; zero is UNCALIBRATED")
add_executable(airnote src/main.cpp src/instrument.cpp src/wire.cpp vendor/vl53l1x/VL53L1X.cpp vendor/pico_audio_i2s/audio_i2s.c)
pico_generate_pio_header(airnote ${CMAKE_CURRENT_LIST_DIR}/vendor/pico_audio_i2s/audio_i2s.pio)
target_include_directories(airnote PRIVATE include include/compat vendor/vl53l1x
  ${PICO_EXTRAS_PATH}/src/rp2_common/pico_audio_i2s/include)
target_compile_options(airnote PRIVATE -Wall -Wextra)
target_compile_definitions(airnote PRIVATE
  AIRNOTE_OFFSET_MM=${AIRNOTE_OFFSET_MM}
  PICO_STDIO_USB_STDOUT_TIMEOUT_US=0
  PICO_STDIO_USB_CONNECT_WAIT_TIMEOUT_MS=0
  PICO_STDIO_USB_ENABLE_RESET_VIA_BAUD_RATE=0
  PICO_STDIO_USB_ENABLE_RESET_VIA_VENDOR_INTERFACE=0
  PICO_STDIO_USB_RESET_INTERFACE_SUPPORT_RESET_TO_BOOTSEL=0
  PICO_STDIO_USB_RESET_INTERFACE_SUPPORT_RESET_TO_FLASH_BOOT=0
  PICO_AUDIO_I2S_DATA_PIN=10 PICO_AUDIO_I2S_CLOCK_PIN_BASE=11)
target_link_libraries(airnote PRIVATE pico_stdlib pico_multicore pico_audio hardware_dma hardware_pio hardware_irq hardware_adc hardware_i2c hardware_watchdog)
pico_enable_stdio_usb(airnote 1)
pico_enable_stdio_uart(airnote 0)
pico_add_extra_outputs(airnote)

