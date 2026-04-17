# =============================================================================
# i2c_lcd.py — I2C 1602 LCD driver using PCF8574 I/O expander backpack
# MicroPython, Raspberry Pi Pico W 2
#
# Works with the common "blue/green I2C backpack" modules that use a PCF8574
# or PCF8574A I/O expander chip.
#   Default address: 0x27  (PCF8574)
#   Alternate address: 0x3F (PCF8574A)
#
# Depends on lcd_api.py (must be on Pico flash alongside this file).
#
# Usage:
#   from machine import I2C, Pin
#   from i2c_lcd import I2cLcd
#   i2c = I2C(0, sda=Pin(4), scl=Pin(5), freq=400_000)
#   lcd = I2cLcd(i2c, 0x27, 2, 16)
#   lcd.putstr("Hello!")
# =============================================================================

import time
from lcd_api import LcdApi

# PCF8574 pin mapping to HD44780 data lines (4-bit mode)
# Bit positions within the I2C byte sent to the PCF8574:
#   Bit 0 = RS   (Register Select)
#   Bit 1 = RW   (Read/Write — always 0 for write)
#   Bit 2 = E    (Enable / clock)
#   Bit 3 = BL   (Backlight)
#   Bit 4 = D4
#   Bit 5 = D5
#   Bit 6 = D6
#   Bit 7 = D7

MASK_RS = 0x01
MASK_RW = 0x02
MASK_E  = 0x04
MASK_BL = 0x08

SHIFT_DATA = 4   # D4-D7 occupy bits 4-7


class I2cLcd(LcdApi):
    """
    HD44780 LCD driver using a PCF8574 I2C I/O expander backpack.
    Communicates in 4-bit mode over I2C.
    """

    # Time constants (µs)
    _PULSE_WIDTH = 50    # Enable pulse width — 450 ns minimum per datasheet
    _DELAY       = 50    # Delay after enable low

    def __init__(self, i2c, i2c_addr, num_lines, num_columns):
        self._i2c      = i2c
        self._addr     = i2c_addr
        self._backlight = MASK_BL   # backlight on by default

        # Initialise HD44780 in 4-bit mode (3× function set sequence)
        time.sleep_ms(20)   # >15 ms after power on
        self._write_init_nibble(0x30)
        time.sleep_ms(5)    # >4.1 ms
        self._write_init_nibble(0x30)
        time.sleep_us(150)  # >100 µs
        self._write_init_nibble(0x30)
        time.sleep_us(150)
        # Switch to 4-bit mode
        self._write_init_nibble(0x20)
        time.sleep_us(150)

        # Now call parent __init__ which issues further commands
        super().__init__(num_lines, num_columns)

    def _i2c_write(self, data):
        """Send one byte to the PCF8574."""
        self._i2c.writeto(self._addr, bytes([data]))

    def _write_init_nibble(self, nibble):
        """Send a nibble during the power-on initialisation sequence."""
        byte = (nibble & 0xF0) | self._backlight
        self._i2c_write(byte | MASK_E)
        time.sleep_us(self._PULSE_WIDTH)
        self._i2c_write(byte)
        time.sleep_us(self._DELAY)

    def _write4(self, nibble, rs):
        """Send 4 data bits with the correct RS flag and clock the Enable pin."""
        byte = ((nibble & 0x0F) << SHIFT_DATA) | self._backlight
        if rs:
            byte |= MASK_RS
        # Pulse Enable high then low
        self._i2c_write(byte | MASK_E)
        time.sleep_us(self._PULSE_WIDTH)
        self._i2c_write(byte)
        time.sleep_us(self._DELAY)

    def _write_byte(self, data, rs):
        """Send a full byte (two 4-bit nibbles) to the LCD."""
        self._write4(data >> 4, rs)    # high nibble first
        self._write4(data & 0x0F, rs)  # low nibble

    # ── LcdApi hardware abstraction ──────────────────────────────────────────

    def hal_write_command(self, cmd):
        self._write_byte(cmd, rs=False)
        if cmd in (0x01, 0x02):        # clear / home need extra delay
            time.sleep_ms(5)
        else:
            time.sleep_us(50)

    def hal_write_data(self, data):
        self._write_byte(data, rs=True)
        time.sleep_us(50)

    def hal_backlight_on(self):
        self._backlight = MASK_BL
        self._i2c_write(self._backlight)

    def hal_backlight_off(self):
        self._backlight = 0x00
        self._i2c_write(self._backlight)