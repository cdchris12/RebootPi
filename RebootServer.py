#!/usr/bin/env python3


# Try loading the config file and die if not found
try:
    os.stat("config.json")
except Exception:
    print ("Config file missing!!!")
    return(1)
else:
    with open('config.json', 'rb') as infile:
        config = json.load(infile.read())
    # End with
# End try/except block

import RPi.GPIO as GPIO
from time import sleep
import requests
import arrow

# Listing of all GPIO pins we can use, 17 total
GPIO_pins = [7, 11, 12, 13, 15, 16, 18, 22, 29, 31, 32, 33, 35, 36, 37, 38, 40]

# Global list to hold our miner objects
miners = []

class miner:
    def __init__ (self, name, earl, io_num, port):
        self.io_num = io_num
        self.earl = earl
        self.name = name
        self.port = port
    # End def

    def healthCheck (self):
        # Returns True/False based on a good or bad health check.
        try:
            r = requests.get("%s:%s" % (self.earl, self.port), timeout=10)
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
        sleep(0.5)
        GPIO.output(self.io_num, GPIO.LOW)
    # End def

    def reboot (self):
        GPIO.output(self.io_num, GPIO.HIGH)
        sleep(10)
        GPIO.output(self.io_num, GPIO.LOW)
        self.change()
    # End def
# End class

def Setup():
    # Set the GPIO pins to use the board numbering scheme
    GPIO.setmode(GPIO.BOARD)

    # Disable warnings
    GPIO.setwarnings(False)

    # Setup all GPIO pins as output devices
    GPIO.setup(GPIO_pins, GPIO.OUT, initial=GPIO.LOW)

    # Create the miner objects
    miners = getMiners()

    # Return the created miner object list
    return miners
# End def

def Cleanup():
    # Release all listed GPIO pins
    GPIO.cleanup(GPIO_pins)
# End def

def RunServer(miners):
    # First, we want to make sure all the miners are at least turned on
    for miner in miners:
        if not miner.healthCheck():
            miner.change()
            #print("Started miner %s!" % (miner.name))
        else:
            #print("Miner %s already running!" % (miner.name))
            pass
        # End if/else block
    try:
        while True:
            #print("Sleeping for 300 seconds...")
            sleep(300)

            #print("Starting regular checks at %s..." % getTime())
            for miner in miners:
                if not miner.healthCheck():
                    #print("Miner %s wasn't responding, so we're rebooting it!" % miner.name)
                    miner.reboot()
                else:
                    #print("miner %s's health check passed!" % miner.name)
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
    global miners

    ret = []
    for item in config['miners']:
        ret.append( miner(name=item['name'], earl="%s:%s" % (item['url'], item['port']), io_num=GPIO_pins[item['io_num']]))
    # End for

    return ret
# End def

def main():
    try:
        miners = Setup()
        RunServer(miners)
    except Exception:
        Cleanup()
    finally:
        return(0)
    # End try/except block
# End def

if __name__ == "__main__":
    main()
# End if
