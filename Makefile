PIO = /home/maks/.platformio/penv/bin/pio
OTA_PASS ?= $(shell grep -oP 'OTA_PASS\s+"\K[^"]+' src/secrets.h)

.PHONY: build flash ota monitor all

build:
	$(PIO) run

# Прошивка по USB (перший раз)
flash:
	$(PIO) run --target upload

# Прошивка по Wi-Fi (switch.local)
ota:
	OTA_PASS=$(OTA_PASS) $(PIO) run -e esp32dev_ota --target upload

monitor:
	$(PIO) device monitor -b 115200

all: flash monitor
