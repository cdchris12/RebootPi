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
        except (requests.exceptions.Timeout, requests.exceptions.ConnectTimeout, requests.exceptions.ConnectionError) as e:
            # Timeout means we can reach the host, but the service isn't running
            # ConnectTimeout or ConnectionError means we can't reach the host at all.
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
        GPIO.output(self.io_out_num, GPIO.LOW)
        sleep(1)
        GPIO.output(self.io_out_num, GPIO.HIGH)
    # End def

    def reboot (self):
        # Force the PC to shutoff
        GPIO.output(self.io_out_num, GPIO.LOW)
        sleep(10)
        GPIO.output(self.io_out_num, GPIO.HIGH)

        # Wait a second between operations
        sleep(1)

        # Turn the PC back on
        self.change()
    # End def

    def status (self, q=None):
        power = not GPIO.input(self.io_in_num)

        if power:
            program = self.healthCheck()
            if program:
                if q: q.put((self.name, 1))
                print ("%s, %s" % (self.name, "1"))
                return(1)
            else:
                if q: q.put((self.name, 2))
                print ("%s, %s" % (self.name, "2"))
                return(2)
            # End if/else block

        else:
            if q: q.put((self.name, 0))
            print ("%s, %s" % (self.name, "0"))
            return(0)
        # End if/else block
    # End def
# End class

def Setup(config):
    # Set the GPIO pins to use the board numbering scheme
    GPIO.setmode(GPIO.BOARD)

    # Disable warnings
    GPIO.setwarnings(False)

    # Create the miner objects
    miners = getMiners()

    # Setup all GPIO pins as either input or output devices
    for miner in miners.keys():
        GPIO.setup(miners[miner].io_out_num, GPIO.OUT, initial=GPIO.HIGH)
        GPIO.setup(miners[miner].io_in_num, GPIO.IN, pull_up_down=GPIO.PUD_UP)
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
    for miner in miners.keys():
        if not miners[miner].healthCheck():
            miners[miner].change()
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
            for miner in miners.keys():
                if not miners[miner].healthCheck():
                    #print("Miner %s wasn't responding, so we're rebooting it!" % miner.name)
                    miners[miner].reboot()
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
    ret = {}
    for item in config['hosts']:
        ret[item['name']] = (
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
