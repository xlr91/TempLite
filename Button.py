import os
import time
import RPi.GPIO as GPIO

GPIO.setmode(GPIO.BCM)
GPIO.setwarnings(False)

ButtonPin = 25
GPIO.setup(ButtonPin, GPIO.IN)
print(GPIO.input(ButtonPin))

while True:
    if GPIO.input(ButtonPin) == False:
        print('YEET')
        print(GPIO.input(ButtonPin))
        GPIO.cleanup()
        break
    else:
        os.system('clear')
        print('waits')
        time.sleep(0.5)
