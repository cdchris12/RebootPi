#!/usr/bin/python

from RebootServer import getMiners
import cherrypy

miners = getMiners()

class API(object):
    @cherrypy.expose
    def index(self):
        raise cherrypy.HTTPError(400, "This style of calling the API is not supported.")
    # End def

    @cherrypy.expose
    def restart(self, num=""):
        if num is "":
            raise cherrypy.HTTPError(400, "Missing the number of the miner to be rebooted.")
        else:
            for miner in miners:
                if miner.miner_num == num:
                    print ("Rebooting miner %s!" % miner.miner_num)
                    miner.reboot()
                    return
                # End if
            # End for
        # End else
    # End def
# End class

def main():
    cherrypy.quickstart(API())
# End def

if __name__ == '__main__':
    main()
# End if
