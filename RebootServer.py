#!/usr/bin/python

try:
    import RPi.GPIO as GPIO
except RuntimeError:
    print("Error importing RPi.GPIO! This is probably because you need superuser privileges. You can achieve this by using 'sudo' to run your script.")
# End try/except block

import requests
import arrow
import time

# Listing of all GPIO pins we can use, 17 total
GPIO_pins = [7, 11, 12, 13, 15, 16, 18, 22, 29, 31, 32, 33, 35, 36, 37, 38, 40]

# Listing of all miners
miner_nums = ["00", "01", "02", "03", "04", "05", "06"]

# List of miner objects
miner_objs = []

class miner:
    def __init__ (self, miner_num, earl, io_num):
        self.io_num = io_num
        self.earl = earl
        self.miner_num = miner_num
    # End def

    def health_check (self):
        # Returns True/False based on a good or bad health check.
        try:
            r = requests.get(self.earl, timeout=10)
        except requests.exceptions.Timeout:
            return False
        else:
            if r.status_code == 200:
                return True
            else:
                return False
            # End if/else block
        # End try/except/else block
    # End def

    def change (self):
        GPIO.output(self.io_num, GPIO.HIGH)
        time.sleep(0.5)
        GPIO.output(self.io_num, GPIO.LOW)
    # End def

    def reboot (self):
        GPIO.output(self.io_num, GPIO.HIGH)
        time.sleep(10)
        GPIO.output(self.io_num, GPIO.LOW)
        self.change()
    # End def
# End class


def Setup():
    print("Starting up the monitor at %s..." % getTime())

    # Set the GPIO pins to use the board numbering scheme
    GPIO.setmode(GPIO.BOARD)

    # Disable warnings
    GPIO.setwarnings(False)

    # Setup all GPIO pins as output devices
    GPIO.setup(GPIO_pins, GPIO.OUT, initial=GPIO.LOW)

    print("Set up the GPIO pins!")

    # Create the miner objects
    for num in miner_nums:
        miner_objs.append( miner(num, earl="http://interstate-towing.ddns.net:70"+num, io_num=GPIO_pins[int(num)]))
    # End for

    print("Set up the miner objects!")
# End def

def Cleanup():
    # Release all listed GPIO pins
    GPIO.cleanup(GPIO_pins)

    print("\nCleaned up the GPIO pin configs!")
# End def

def RunServer():
    for miner in miner_objs:
        if not miner.health_check:
            miner.change()
            print("Started miner %s!" % (miner.miner_num))
        else:
            print("Miner %s already running!" % (miner.miner_num))
        # End if/else block
    try:
        while True:
            print("Sleeping for 300 seconds...")
            time.sleep(300)

            print("Starting regular checks at %s..." % getTime())
            for miner in miner_objs:
                if not miner.health_check:
                    print("Miner %s wasn't responding, so we're rebooting it!" % miner.miner_num)
                    miner.reboot()
                else:
                    print("miner %s's health check passed!" % miner.miner_num)
                # End if/else block
            # End for
        # End while
    except KeyboardInterrupt:
        return
    # End try/except block
# End def

def getTime():
    return  arrow.now().format('YYYY-MM-DD HH:MM:SS')
# End def

def getMiners():
    global miner_objs
    return miner_objs
# End def

def main():
    Setup()
    RunServer()
    Cleanup()

    print("Exiting at %s, goodbye!" % getTime())
    return(0)
# End def

if __name__ == "__main__":
    main()
# End if
