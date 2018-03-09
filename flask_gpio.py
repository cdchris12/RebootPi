#!/usr/bin/env python3

from flask import Flask, render_template, Markup, request
import datetime
import RPi.GPIO as GPIO
import sys
import os
import json
from RebootServer import Setup, Cleanup
from werkzeug.serving import WSGIRequestHandler
app = Flask(__name__)

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

# Setup our list of miner objects
miners = Setup(config)

@app.route("/")
def hello():
    now = datetime.datetime.now()
    timeString = now.strftime("%Y-%m-%d %H:%M")
    templateData = {
        'title' : 'HELLO!',
        'time': timeString
    }
    return render_template('main.html', **templateData)

@app.route("/reboot/<name>") # Need to pass a parameter called `pass` as well
def reboot(name):
    try:
        if name in miners.keys():
            miner = miners[name]
        else:
            raise Exception("Name not found")
        # End if/else block

        password = request.args.get('pass')
        print (password)
        if not password == config['password']:
            raise Exception("Invalid password!")
        # End if

        miner.reboot()

        response = "Successfully rebooted miner " + name +"!"
    except Exception as e:
        response = "There was an error rebooting miner " + name + "!\n" + str(e)
    # End try/except block

    templateData = {
        'title' : 'Miner "%s" Reboot Status',
        'response' : response
    }

    return render_template('reboot.html', **templateData)
# End def

@app.route("/change/<name>") # Need to pass a parameter called `pass` as well
def change(name):
    try:
        if name in miners.keys():
            miner = miners[name]
        else:
            raise Exception("Name not found")
        # End if/else block

        password = request.args.get('pass')
        print (password)
        if not password == config['password']:
            raise Exception("Invalid password!")
        # End if

        miner.change()

        response = "Successfully changed the state of miner " + name +"!"
    except Exception as e:
        response = "There was an error changing the state of miner " + name + "!\n" + str(e)
    # End try/except block

    templateData = {
        'title' : 'Miner "%s" State Change Status',
        'response' : response
    }

    return render_template('change.html', **templateData)
# End def

@app.route("/status/<name>") # Need to pass a parameter called `pass` as well
def status(name):
    try:
        if name in miners.keys():
            miner = miners[name]
        else:
            raise Exception("Name not found")
        # End if/else block

        password = request.args.get('pass')
        print (password)
        if not password == config['password']:
            raise Exception("Invalid password!")
        # End if

        status_code = miner.status()
        # Returns a number which tells us the current state of this miner:
        # 0: Power LED is off, indicating the miner is powered off.
        # 1: Power LED on and mining software reachable.
        # 2: Power LED on, but the mining software is unreachable.

        if status_code == 0:
            response = """<img style='align:center; display:block; width:100px; height:100px;' id='red_light' src='/static/red_light.png' />
            </br>
            </br>
            <p>Miner %s is currently completely powered off.</p>
            """ % miner.name
        elif status_code == 2:
            response = """<img style='align:center; display:block; width:100px; height:100px;' id='red_light' src='/static/yellow_light.png' />
            </br>
            </br>
            <p>Miner %s is currently powered on, but the mining software is unreachable.</p>
            """ % miner.name
        elif status_code == 3:
            response = """<img style='align:center; display:block; width:100px; height:100px;' id='red_light' src='/static/green_light.png' />
            </br>
            </br>
            <p>Miner %s is currently powered on and the mining software is reachable!</p>
            """ % miner.name
        # End if/else block

        templateData = {
            'title' : 'Miner %s status' % miner.name,
            'response' : Markup(response)
        }

    except Exception as e:
        response = "There was an error rebooting miner " + name + "!\n" + str(e)
    # End try/except block

    templateData = {
        'title' : 'Miner "%s" Status' % miner.name,
        'response' : response
    }

    return render_template('status.html', **templateData)
# End def

if __name__ == "__main__":
    try:
        WSGIRequestHandler.protocol_version = "HTTP/1.1"
        app.run(host='0.0.0.0', port=config['server_port'], debug=True)
    except Exception:
        Cleanup()
    finally:
        sys.exit(0)
    # End try/except block
# End if
