from machine import Pin
import time

b1 = Pin(19, Pin.IN, Pin.PULL_UP)
b2 = Pin(18, Pin.IN, Pin.PULL_UP)
b3 = Pin(17, Pin.IN, Pin.PULL_UP)
b4 = Pin(16, Pin.IN, Pin.PULL_UP)

phrases = {
    1: "hello",
    2: "goodbye",
    3: "yes",
    4: "no",
    5: "how are you",
    6: "I am good",
    7: "I am not good",
    8: "help",
    9: "stop",
    10: "go",
    11: "this",
    12: "there",
    13: "I need",
    14: "water",
    15: "food"
}

def read_buttons():
    value = 0

    if b1.value() == 0:
        value += 1
    if b2.value() == 0:
        value += 2
    if b3.value() == 0:
        value += 4
    if b4.value() == 0:
        value += 8

    return value


last_gesture = -1

while True:

    gesture = read_buttons()

    if gesture != last_gesture:

        if gesture == 0:
            print("")
        elif gesture in phrases:
            print(phrases[gesture])

        last_gesture = gesture

    time.sleep(0.1)