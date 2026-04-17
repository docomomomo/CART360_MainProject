from machine import Pin
import time

b1 = Pin(19, Pin.IN, Pin.PULL_UP)
b2 = Pin(18, Pin.IN, Pin.PULL_UP)
b3 = Pin(17, Pin.IN, Pin.PULL_UP)
b4 = Pin(16, Pin.IN, Pin.PULL_UP)

last_message = ""

while True:
    message = ""

    if b1.value() == 0:
        message = "hello"
    elif b2.value() == 0:
        message = "yes"
    elif b3.value() == 0:
        message = "no"
    elif b4.value() == 0:
        message = "help"

    if message != last_message:
        print(message)
        last_message = message

    time.sleep(0.1)