#!/usr/bin/env python3
# thermal_seat_finder.py
#
# Infrared-based seat finder for visually impaired users.
# Uses a thermal sensor (MLX90640), an LCD, and a vibration motor
# to alert when an occupied seat (warm region) is detected.

import lcd
import image
import sensor
import time
from fpioa_manager import fm
from machine import UART
import gc
from Maix import GPIO

# --- Configuration Constants ---
START_FLAG = 0x5A                 # Frame header flag from MLX90640
SENSOR_WIDTH = 32                 # Sensor resolution width
SENSOR_HEIGHT = 24                # Sensor resolution height
LCD_W = 160                       # LCD display width
LCD_H = 120                       # LCD display height
MAX_TEMP_LIMIT = 300              # Upper bound for display scaling
MIN_TEMP_LIMIT = 0                # Lower bound for display scaling
PERSON_TEMP_THRESHOLD = 30        # °C threshold to consider "person present"
VIBRATION_INTERVAL_MS = 500       # Minimum interval between vibrations (ms)

# --- Hardware Initialization ---

# Map a GPIO pin to drive the vibration motor
fm.register(15, fm.fpioa.GPIO0)    
vibration_motor = GPIO(GPIO.GPIO0, GPIO.OUT)
vibration_motor.value(0)           # Motor off initially

# Map UART pins for MLX90640 infrared sensor
fm.register(10, fm.fpioa.UART1_RX)
fm.register(9, fm.fpioa.UART1_TX)
com = UART(UART.UART1, 115200, timeout=1000, read_buf_len=4096)

# Initialize LCD display
lcd.init()

# Frame-rate clock and vibration timer
clock = time.clock()
last_vibration = time.ticks_ms()

# --- Main Loop ---
while True:
    # Wait until there is data available
    if com.any() <= 0:
        continue

    # Read one full frame (1544 bytes)
    frame = com.read(1544)
    if not frame or len(frame) != 1544:
        print("Incomplete frame received.")
        continue

    # Verify frame header flags
    if frame[0] != START_FLAG or frame[1] != START_FLAG:
        print("Invalid frame header.")
        continue

    # Extract declared data length (unused here)
    data_len = int.from_bytes(frame[2:4], 'little')

    # --- Checksum verification ---
    checksum = 0
    for i in range(0, 1542, 2):
        word = (frame[i+1] << 8) | frame[i]
        checksum = (checksum + word) & 0xFFFF
    recv_sum = (frame[1543] << 8) | frame[1542]
    if checksum != recv_sum:
        print("Checksum mismatch.")
        continue
    else:
        print("Checksum OK.")

    # --- Parse temperature data ---
    temps = []
    min_temp, max_temp = MAX_TEMP_LIMIT, MIN_TEMP_LIMIT
    max_pos = None
    person_detected = False

    for idx in range(SENSOR_WIDTH * SENSOR_HEIGHT):
        raw = frame[4 + idx*2 : 4 + idx*2 + 2]
        temp_c = int.from_bytes(raw, 'little') / 100.0
        temps.append(temp_c)

        # Track min/max for color mapping
        if temp_c < min_temp:
            min_temp = max(temp_c, MIN_TEMP_LIMIT)
        if temp_c > max_temp:
            max_temp = min(temp_c, MAX_TEMP_LIMIT)
            max_pos = (idx % SENSOR_WIDTH, idx // SENSOR_WIDTH)
            # Detect if any pixel exceeds person threshold
            if temp_c > PERSON_TEMP_THRESHOLD:
                person_detected = True

    # Read sensor’s own temperature (last two bytes)
    raw_machine = frame[-2:]
    machine_temp = int.from_bytes(raw_machine, 'little') / 100.0
    print(f"Sensor board temperature: {machine_temp:.2f}°C")

    # --- Vibration feedback ---
    if person_detected:
        now = time.ticks_ms()
        if time.ticks_diff(now, last_vibration) > VIBRATION_INTERVAL_MS:
            vibration_motor.value(1)
            time.sleep_ms(100)
            vibration_motor.value(0)
            last_vibration = now
            print("Vibration: seat occupied.")

    # --- Build thermal image for display ---
    img = image.Image(size=(SENSOR_WIDTH, SENSOR_HEIGHT)).to_grayscale()
    if max_temp == min_temp:
        max_temp = min_temp + 1  # avoid divide-by-zero

    for y in range(SENSOR_HEIGHT):
        for x in range(SENSOR_WIDTH):
            val = int((temps[y*SENSOR_WIDTH + x] - min_temp)
                      / (max_temp - min_temp) * 255)
            img.set_pixel(x, y, val)

    # Resize to LCD resolution and apply rainbow color map
    img = img.resize(LCD_W, LCD_H)
    img = img.to_rainbow(1)

    # Mark center temperature
    center_idx = SENSOR_WIDTH*(SENSOR_HEIGHT//2) + (SENSOR_WIDTH//2)
    center_temp = temps[center_idx]
    img.draw_rectangle(LCD_W//2 - 2, 80, 22, 22,
                       color=(0xff,112,0xff), fill=True)
    img.draw_string(LCD_W//2 + 4, 80, f"{center_temp:.1f}°C",
                    color=(0xff,255,255), scale=2)

    # Highlight hottest pixel
    if max_pos:
        px = int(LCD_W / SENSOR_WIDTH * max_pos[0])
        py = int(LCD_H / SENSOR_HEIGHT * max_pos[1])
        img.draw_rectangle(px - 4, py - 4, 22, 22,
                           color=(0xff,112,0xff), fill=True)
        img.draw_string(px + 2, py - 20, f"{max_temp:.1f}°C",
                        color=(0xff,255,255), scale=2)

    # Display FPS
    fps = clock.fps()
    img.draw_string(2, 2, f"{fps:.1f} FPS",
                    color=(0xff,255,255), scale=2)

    # Push frame to LCD
    lcd.display(img)

    # Clean up
    del temps, frame, img
    gc.collect()
