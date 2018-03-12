#!/usr/bin/env python3

import flask
import datetime
import sys
import os
import json
import argparse
import RPi.GPIO as GPIO

from RebootServer import Setup, Cleanup
from flask import Flask, render_template, Markup, request
from werkzeug.serving import WSGIRequestHandler
from multiprocessing import Pool, TimeoutError, cpu_count, Process, Queue

app = Flask(__name__)

#TODO: Should we allow enabling/disabling multiprocessing? I think not.
# Parse the arguments
#parser = argparse.ArgumentParser()
#parser.add_argument('-m', '--multiprocessing', type=int, default=0, choices=range(2, cpu_count()+1), help='Enter the degree of multiprocessing you\'d like to use for significantly faster computation of large statistical analyses.')
#args = parser.parse_args()

# Try loading the config file and die if not found
#TODO: Add CLI arg for different config file?
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

# Setup our queue to pass along process objects for joining by our Joiner subprocess
p_queue = Queue()

class Joiner(Process):
    def __init__(self, q):
        self.__q = q
    # End def

    def run(self):
        while True:
            child = self.__q.get()
            if child == None:
                return
            # End if
            child.join()
        # End while
    # End def
# End class

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
    #try:
    if name in miners.keys():
        miner = miners[name]
    else:
        return flask.abort(400)
        #raise Exception("Name not found")
    # End if/else block

    password = request.args.get('pass')
    print (password)
    if not password == config['password']:
        return flask.abort(403)
        #raise Exception("Invalid password!")
    # End if

    p = Process(target=miner.reboot, args=())
    p_queue.put(p)
    #miner.reboot()

    response = "Successfully rebooted miner " + name +"!"
    #except Exception as e:
    #    response = "There was an error rebooting miner " + name + "!\n" + str(e)
    # End try/except block

    templateData = {
        'title' : 'Miner "%s" Reboot Status',
        'response' : response
    }

    return render_template('reboot.html', **templateData)
# End def

@app.route("/change/<name>") # Need to pass a parameter called `pass` as well
def change(name):
    #try:
    if name in miners.keys():
        miner = miners[name]
    else:
        return flask.abort(400)
        #raise Exception("Name not found")
    # End if/else block

    password = request.args.get('pass')
    print (password)
    if not password == config['password']:
        return flask.abort(403)
        #raise Exception("Invalid password!")
    # End if

    p = Process(target=miner.change, args=())
    p_queue.put(p)
    #miner.change()

    response = "Successfully changed the state of miner " + name +"!"
    #except Exception as e:
    #    response = "There was an error changing the state of miner " + name + "!\n" + str(e)
    # End try/except block

    templateData = {
        'title' : 'Miner "%s" State Change Status',
        'response' : response
    }

    return render_template('change.html', **templateData)
# End def

@app.route("/status/<name>") # Need to pass a parameter called `pass` as well
def status(name):
    #try:
    if name in miners.keys():
        miner = miners[name]
    else:
        return flask.abort(400)
        #raise Exception("Name not found")
    # End if/else block

    password = request.args.get('pass')
    print (password)
    if not password == config['password']:
        return flask.abort(403)
        #raise Exception("Invalid password!")
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

    #except Exception as e:
    #    response = "There was an error rebooting miner " + name + "!\n" + str(e)
    # End try/except block

    templateData = {
        'title' : 'Miner "%s" Status' % miner.name,
        'response' : response
    }

    return render_template('status.html', **templateData)
# End def

@app.errorhandler(403)
def page_not_found(e):
    return "You are not authorized to view this page!", 403
# End def

@app.errorhandler(400)
def page_not_found(e):
    return "Your request was malformed. Double check the miner name you provided, maybe?", 400
# End def

if __name__ == "__main__":
    try:
        joiner = Process(target=Joiner, args=(p_queue))
        WSGIRequestHandler.protocol_version = "HTTP/1.1"
        app.run(host='0.0.0.0', port=config['server_port'], debug=True)
    except (KeyboardInterrupt, SystemExit):
        Cleanup()
    finally:
        sys.exit(0)
        p_queue.put(None)
    # End try/except block
# End if
