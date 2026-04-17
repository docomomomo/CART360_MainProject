# =============================================================================
# lcd_api.py — Base LCD API for character LCDs
# Original author: Dave Hylands / Peter Hinch (public domain)
# Included here for self-contained distribution; no changes made.
#
# This file is the base class used by i2c_lcd.py.
# Place both files in the root of the Pico flash.
# =============================================================================

import time

# Bit definitions for the LCD control lines (HD44780 instruction set)
LCD_CLR             = 0x01   # clear display
LCD_HOME            = 0x02   # return home
LCD_ENTRY_MODE      = 0x04
LCD_ENTRY_INC       = 0x02
LCD_ENTRY_SHIFT     = 0x01
LCD_ON_CTRL         = 0x08
LCD_ON_DISPLAY      = 0x04
LCD_ON_CURSOR       = 0x02
LCD_ON_BLINK        = 0x01
LCD_MOVE            = 0x10
LCD_MOVE_DISP       = 0x08
LCD_MOVE_RIGHT      = 0x04
LCD_FUNCTION        = 0x20
LCD_FUNCTION_8BIT   = 0x10
LCD_FUNCTION_2LINES = 0x08
LCD_FUNCTION_10DOTS = 0x04
LCD_CGRAM           = 0x40
LCD_DDRAM           = 0x80

LCD_RS_CMD  = 0
LCD_RS_DATA = 1

LCD_RW_WRITE = 0
LCD_RW_READ  = 1


class LcdApi:
    """
    Base class for controlling character LCDs based on the HD44780 controller.
    Concrete subclasses must implement hal_write_init_nibble(),
    hal_backlight_on/off(), and hal_write_command/data().
    """

    def __init__(self, num_lines, num_columns):
        self.num_lines   = num_lines
        self.num_columns = num_columns
        self.cursor_x    = 0
        self.cursor_y    = 0
        self.backlight   = True
        self.display_off()
        self.backlight_on()
        self.clear()
        cmd = LCD_ENTRY_MODE | LCD_ENTRY_INC
        self.hal_write_command(cmd)
        self.hide_cursor()
        self.display_on()

    def clear(self):
        self.hal_write_command(LCD_CLR)
        self.hal_write_command(LCD_HOME)
        self.cursor_x = 0
        self.cursor_y = 0
        time.sleep_ms(5)

    def show_cursor(self):
        self.hal_write_command(LCD_ON_CTRL | LCD_ON_DISPLAY | LCD_ON_CURSOR)

    def hide_cursor(self):
        self.hal_write_command(LCD_ON_CTRL | LCD_ON_DISPLAY)

    def blink_cursor_on(self):
        self.hal_write_command(LCD_ON_CTRL | LCD_ON_DISPLAY | LCD_ON_CURSOR | LCD_ON_BLINK)

    def blink_cursor_off(self):
        self.hal_write_command(LCD_ON_CTRL | LCD_ON_DISPLAY | LCD_ON_CURSOR)

    def display_on(self):
        self.hal_write_command(LCD_ON_CTRL | LCD_ON_DISPLAY)

    def display_off(self):
        self.hal_write_command(LCD_ON_CTRL)

    def backlight_on(self):
        self.backlight = True
        self.hal_backlight_on()

    def backlight_off(self):
        self.backlight = False
        self.hal_backlight_off()

    def move_to(self, cursor_x, cursor_y):
        self.cursor_x = cursor_x
        self.cursor_y = cursor_y
        addr = cursor_x & 0x3F
        if cursor_y & 1:
            addr += 0x40
        if cursor_y & 2:
            addr += self.num_columns
        self.hal_write_command(LCD_DDRAM | addr)

    def putchar(self, char):
        if char == '\n':
            if self.cursor_y == 0:
                self.move_to(0, 1)
            else:
                self.move_to(0, 0)
            return
        self.hal_write_data(ord(char))
        self.cursor_x += 1
        if self.cursor_x >= self.num_columns:
            self.cursor_x = 0
            self.cursor_y = (self.cursor_y + 1) % self.num_lines
            self.move_to(self.cursor_x, self.cursor_y)

    def putstr(self, string):
        for char in string:
            self.putchar(char)

    def custom_char(self, location, charmap):
        """Write a custom character (0-7) from an 8-byte charmap."""
        location &= 0x7
        self.hal_write_command(LCD_CGRAM | (location << 3))
        time.sleep_us(40)
        for i in range(8):
            self.hal_write_data(charmap[i])
            time.sleep_us(40)

    # ── Must be implemented by subclass ──────────────────────────────────────

    def hal_write_command(self, cmd):
        raise NotImplementedError

    def hal_write_data(self, data):
        raise NotImplementedError

    def hal_backlight_on(self):
        pass

    def hal_backlight_off(self):
        pass