# Spotseat

This project uses infrared thermal imaging and vibration feedback to help visually impaired individuals locate empty seats on public transportation. The system is portable, power-efficient, and responsive, making it ideal for integration into smart canes or wearable assistive technologies to improve accessibility and safety during travel.

The `thermal_seat_finder.py` script continuously reads thermal data frames from an MLX90640 infrared sensor over UART, verifies each frame’s integrity via checksum, and converts raw readings into a temperature map. 

---

## Features

- **Real-time thermal imaging** with MLX90640 sensor
- **Threshold-based detection** of occupied seats
- **Haptic feedback** via vibration motor when a warm spot is detected
- **Live display** of thermal map on an LCD for debugging
- **Lightweight & low-power** design suitable for wearable assistive devices

---

## Hardware Requirements

- **MLX90640** 32×24 infrared thermal sensor
- **LCD module** (e.g., 160×120 SPI TFT)
- **Microcontroller board** (e.g., Kendryte K210 / Maix Bit)
- **Vibration motor** and driver transistor or MOSFET
- **Power supply** (battery pack or 5 V USB)
- **Wires, jumper cables, and prototyping board**

---

## Software Dependencies

- [MaixPy firmware](https://github.com/sipeed/MaixPy) (for K210)
- Python modules (built into MaixPy):  
  `lcd`, `image`, `sensor`, `time`, `fpioa_manager`, `machine.UART`, `gc`, `Maix.GPIO`

---

## Wiring

1. **MLX90640 → UART1**  
   - TX → UART1_RX pin  
   - RX → UART1_TX pin  
2. **Vibration motor driver → GPIO0** (example)  
3. **LCD → SPI pins** (consult your LCD’s datasheet)  
4. **Power** → 5 V and GND to sensor, LCD, motor driver

---

## Installation

1. Flash MaixPy firmware onto your board.
2. Copy `thermal_seat_finder.py` to the board’s filesystem.
3. Adjust pin mappings in the script if needed.
4. Power up the device.

---

