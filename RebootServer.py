#!/usr/bin/env python3

import RPi.GPIO as GPIO
from time import sleep
import requests
import arrow
import os
import sys
import json

# Try loading the config file and die if not found
try:
    os.stat("config.json")
except Exception:
    print ("Config file missing!!!")
    sys.exit(1)
else:
    with open('config.json', 'r') as infile:
        config = json.load(infile)
    # End with
# End try/except block

# Listing of all GPIO pins we can use, 17 total
GPIO_pins = [7, 11, 12, 13, 15, 16, 18, 22, 29, 31, 32, 33, 35, 36, 37, 38, 40]

# Global list to hold our miner objects
miners = []

class miner:
    def __init__ (self, name, earl, port, io_out_num, io_in_num):
        self.io_in_num = io_in_num
        self.io_out_num = io_out_num
        self.earl = earl
        self.name = name
        self.port = port
    # End def

    def healthCheck (self):
        # Returns True/False based on a good or bad health check.
        try:
            r = requests.get("%s:%s" % (self.earl, self.port), timeout=10)
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout):
            # Timeout means we can reach the host, but the service isn't running
            # ConnectTimeout means we can't reach the host at all.
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
        # Simulate a power button press
        GPIO.output(self.io_out_num, GPIO.HIGH)
        sleep(1)
        GPIO.output(self.io_out_num, GPIO.LOW)
    # End def

    def reboot (self):
        # Force the PC to shutoff
        GPIO.output(self.io_out_num, GPIO.HIGH)
        sleep(10)
        GPIO.output(self.io_out_num, GPIO.LOW)

        # Wait a second between operations
        sleep(1)

        # Turn the PC back on
        self.change()
    # End def

    def status (self):
        power = GPIO.input(self.io_in_num)
        program = self.healthCheck()

        if power and program:
            return(1)
        elif power and not program:
            return(2)
        else:
            return(0)
        # End if/else block
# End class

def Setup(config):
    # Set the GPIO pins to use the board numbering scheme
    GPIO.setmode(GPIO.BOARD)

    # Disable warnings
    GPIO.setwarnings(False)

    # Create the miner objects
    miners = getMiners()

    # Setup all GPIO pins as either input or output devices
    for miner in miners:
        GPIO.setup(miner.io_out_num, GPIO.OUT, initial=GPIO.LOW)
        GPIO.setup(miner.io_in_num, GPIO.IN, pull_up_down=GPIO.PUD_DOWN)
    # End for

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
                    pass
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
    ret = []
    for item in config['hosts']:
        ret.append(
            miner(name=item['name'],
            earl=item['url'],
            port=item['port'],
            io_out_num=GPIO_pins[item['io_out_pin']],
            io_in_num=GPIO_pins[item['io_in_pin']])
        )
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
        sys.exit(0)
    # End try/except block
# End def

if __name__ == "__main__":
    main()
# End if
