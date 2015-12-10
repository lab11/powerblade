PROJECT_NAME = $(shell basename "$(realpath ./)")

APPLICATION_SRCS = $(notdir $(wildcard ./*.c))
APPLICATION_SRCS += softdevice_handler.c
APPLICATION_SRCS += ble_advdata.c
APPLICATION_SRCS += ble_conn_params.c
APPLICATION_SRCS += ble_srv_common.c
APPLICATION_SRCS += app_timer.c
#APPLICATION_SRCS += app_uart.c
APPLICATION_SRCS += app_util_platform.c
APPLICATION_SRCS += nrf_delay.c
APPLICATION_SRCS += nrf_drv_common.c
#APPLICATION_SRCS += nrf_drv_uart.c

APPLICATION_SRCS += led.c
APPLICATION_SRCS += simple_ble.c
APPLICATION_SRCS += simple_adv.c
APPLICATION_SRCS += eddystone.c

LIBRARY_PATHS += ./ ../../platform/
SOURCE_PATHS += ./ ../../platform/

NRF_MODEL          = nrf51
NRF_IC             = nrf51822
RAM_KB             = 16
FLASH_KB           = 128
SDK_VERSION        = 10
SOFTDEVICE_MODEL   = s110
SOFTDEVICE_VERSION = 8.0.0

CFLAGS = -Os

NRF_BASE_PATH ?= ../../nrf5x-base/
include $(NRF_BASE_PATH)/make/Makefile
