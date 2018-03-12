#!/usr/bin/env python3

import flask
import datetime
import sys
import os
import json
import argparse
import multiprocessing

import RPi.GPIO as GPIO

from RebootServer import Setup, Cleanup
from flask import Flask, render_template, Markup, request
from werkzeug.serving import WSGIRequestHandler
from multiprocessing import Pool, TimeoutError, cpu_count, Process, Queue

app = Flask(__name__)

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

# Setup our results queue
r_queue = Queue()

def makeJoiner(q):
    a = Joiner(q)
    a.run()
# End def

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
    p.start()
    print (multiprocessing.active_children())
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
    p.start()
    print (multiprocessing.active_children())
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
        response = """<img style='align:center; display:block; width:100px; height:100px;' id='yellow_light' src='/static/yellow_light.png' />
        </br>
        </br>
        <p>Miner %s is currently powered on, but the mining software is unreachable.</p>
        """ % miner.name
    elif status_code == 1:
        response = """<img style='align:center; display:block; width:100px; height:100px;' id='green_light' src='/static/green_light.png' />
        </br>
        </br>
        <p>Miner %s is currently powered on and the mining software is reachable!</p>
        """ % miner.name
    # End if/else block

    templateData = {
        'title' : 'Miner %s status' % miner.name,
        'response' : Markup(response)
    }

    return render_template('status.html', **templateData)
# End def

@app.route("/statusAll") # Need to pass a parameter called `pass` as well
def statusAll():
    password = request.args.get('pass')
    print (password)
    if not password == config['password']:
        return flask.abort(403)
        #raise Exception("Invalid password!")
    # End if

    processes = []
    for name in miners:
        miner = miners[name]
        p = Process(target=miner.status, args=(r_queue,))
        p.start()
        processes.append(p)
    # End for

    for process in processes:
        process.join()
    # End for

    results = {}
    while not r_queue.empty():
        res = r_queue.get()
        results[res[0]] = res[1]
    # End while

    # Create a sorted list of the keys in our results dict
    s_keys = sorted(results.keys())

    symbols = ""
    names = ""

    for item in s_keys:
        if results[item] == 0:
            symbols += "<td>" + "<img style='align:center; display:block; width:100px; height:100px;' id='red_light' src='/static/red_light.png' />" + "</td>"
        elif results[item] == 1:
            symbols += "<td>" + "<img style='align:center; display:block; width:100px; height:100px;' id='green_light' src='/static/green_light.png' />" + "</td>"
        elif results[item] == 2:
            symbols += "<td>" + "<img style='align:center; display:block; width:100px; height:100px;' id='yellow_light' src='/static/yellow_light.png' />" + "</td>"
        else:
            print (results[item])
        # End if/else block
    # End for

    for item in s_keys:
        names += "<td>" + item + "</td>"
    # End for

    response = "<tr>" + symbols + "</tr><tr>" + names + "</tr>"

    explaination = "\
    </br>\
    </br>\
    <p>\
    Red: Power LED is off, indicating the miner is powered off.</br>\
    Green: Power LED on and mining software reachable.</br>\
    Yellow: Power LED on, but the mining software is unreachable.</p>"

    templateData = {
        'title' : 'Farm status',
        'response' : Markup(response),
        'explaination' : Markup(explaination)
    }

    return render_template('fstatus.html', **templateData)
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
        WSGIRequestHandler.protocol_version = "HTTP/1.1"
        app.run(host='0.0.0.0', port=config['server_port'], debug=True)
    except (KeyboardInterrupt, SystemExit):
        Cleanup()
    finally:
        sys.exit(0)
        for item in multiprocessing.active_children():
            item.join()
        # End for
    # End try/except block
# End if
