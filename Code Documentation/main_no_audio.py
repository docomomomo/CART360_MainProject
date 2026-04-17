import time
from machine import I2C, Pin
from mpr121 import MPR121
from i2c_lcd import I2cLcd

# MPR121
MPR121_SDA = 14
MPR121_SCL = 15
MPR121_ADDR = 0x5A

# LCD
LCD_SDA = 4
LCD_SCL = 5
LCD_ADDR = 0x27
LCD_ROWS = 2
LCD_COLS = 16

ELECTRODES = (0, 1, 2, 3, 4)
COOLDOWN_MS = 500
POLL_MS = 20

COMBO_TO_WORD = {
    (0,): "Help",
    (1,): "Water",
    (2,): "Food",
    (3,): "Bathroom",
    (4,): "Stop",

    (0, 1): "I",
    (0, 2): "You",
    (0, 3): "Need",
    (0, 4): "Want",
    (1, 2): "Go",
    (1, 3): "Come",
    (1, 4): "Give",
    (2, 3): "Take",
    (2, 4): "Call",
    (3, 4): "Look",

    (0, 1, 2): "Wait",
    (0, 1, 3): "Phone",
    (0, 1, 4): "Medicine",
    (0, 2, 3): "Friend",
    (0, 2, 4): "Here",
    (0, 3, 4): "Okay",
    (1, 2, 3): "Good",
    (1, 2, 4): "Bad",
    (1, 3, 4): "More",
    (2, 3, 4): "Not",

    (0, 1, 2, 3): "Happy",
    (0, 1, 2, 4): "Sad",
    (0, 1, 3, 4): "Tired",
    (0, 2, 3, 4): "Hurt",
    (1, 2, 3, 4): "It",

    (0, 1, 2, 3, 4): None,
}

def init_mpr121():
    i2c = I2C(1, sda=Pin(MPR121_SDA), scl=Pin(MPR121_SCL), freq=400000)
    print("MPR121 scan:", i2c.scan())
    sensor = MPR121(i2c, address=MPR121_ADDR, touch_threshold=10, release_threshold=5)
    print("MPR121 ready")
    return sensor

def init_lcd():
    i2c = I2C(0, sda=Pin(LCD_SDA), scl=Pin(LCD_SCL), freq=100000)
    print("LCD scan:", i2c.scan())
    lcd = I2cLcd(i2c, LCD_ADDR, LCD_ROWS, LCD_COLS)
    lcd.clear()
    lcd.putstr("Glove Ready")
    time.sleep_ms(1000)
    lcd.clear()
    return lcd

def read_touch_combo(sensor):
    touched_bits = sensor.touched()
    return tuple(sorted(e for e in ELECTRODES if (touched_bits >> e) & 1))

def resolve_word(combo):
    return COMBO_TO_WORD.get(combo, None)

def display_word(lcd, word):
    lcd.clear()
    lcd.move_to(0, 0)
    lcd.putstr(word[:16])

def main():
    print("=== Glove LCD Mode ===")
    sensor = init_mpr121()
    lcd = init_lcd()

    last_combo = ()
    last_trigger_ms = 0

    while True:
        now = time.ticks_ms()
        combo = read_touch_combo(sensor)

        if combo == ():
            time.sleep_ms(80)
            if read_touch_combo(sensor) == ():
                last_combo = ()
            time.sleep_ms(POLL_MS)
            continue

        if combo == last_combo:
            time.sleep_ms(POLL_MS)
            continue

        if time.ticks_diff(now, last_trigger_ms) < COOLDOWN_MS:
            time.sleep_ms(POLL_MS)
            continue

        word = resolve_word(combo)
        print("Combo", combo, "->", word)

        last_combo = combo
        last_trigger_ms = time.ticks_ms()

        if word is not None:
            display_word(lcd, word)

        time.sleep_ms(POLL_MS)

if __name__ == "__main__":
    main()