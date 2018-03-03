#!/usr/bin/env python3
# Try loading the config file and die if not found
try:
    os.stat("config.json")
except Exception:
    print "Config file missing!!!"
    return(1)
else:
    with open('config.json', 'rb') as infile:
        config = json.load(infile.read())
    # End with
# End try/except block

# Listing of all GPIO pins we can use, 17 total
GPIO_pins = [7, 11, 12, 13, 15, 16, 18, 22, 29, 31, 32, 33, 35, 36, 37, 38, 40]

from time import sleep
import requests
import arrow
from flask import Flask, render_template
import datetime
import RPi.GPIO as GPIO
app = Flask(__name__)

# Set the GPIO pins to use the board numbering scheme
GPIO.setmode(GPIO.BOARD)
# Disable warnings
GPIO.setwarnings(False)
# Setup all GPIO pins as output devices
GPIO.setup(GPIO_pins, GPIO.OUT, initial=GPIO.LOW)

@app.route("/")
def hello():
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData = {
        'title' : 'HELLO!',
        'time': timeString
    }
    return render_template('main.html', **templateData)

@app.route("/reboot/<name>")
def reboot(name):
    try:
        for miner in config['hosts']:
            if miner['name'] == name:
                break
            # End if
        # End for

        # Setup the GPIO pin as an output to simulate force reboot command
        GPIO.setup(GPIO_pins[miner['io_pin']], GPIO.OUT)

        # Close the circuit for 10 seconds
        GPIO.output(GPIO_pins[miner['io_pin']], GPIO.HIGH)
        sleep(10)
        GPIO.output(GPIO_pins[miner['io_pin']], GPIO.LOW)

        # Close the circuit for 1 second to simulate power button press
        GPIO.output(GPIO_pins[miner['io_pin']], GPIO.HIGH)
        sleep(1)
        GPIO.output(GPIO_pins[miner['io_pin']], GPIO.LOW)

        response = "Successfully rebooted miner connected to pin " + GPIO_pins[int(pin) +"!"
        GPIO.cleanup(GPIO_pins[miner['io_pin']])
    except:
        response = "There was an error setting pin " + str(GPIO_pins[int(pin)) + "!"
        GPIO.cleanup(GPIO_pins[miner['io_pin']])
    # End try/except block

    templateData = {
        'title' : 'Reboot status',
        'response' : response
    }

    return render_template('reboot.html', **templateData)
# End def

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80, debug=True)
# End if
