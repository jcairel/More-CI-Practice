import argparse
import os
import re
import socket
import socketserver
import subprocess
import sys
import time

import helpers

def poll():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dispatcher-server", help="dispatcher host:port, "\
                        "by default it uses localhost:8888", default="localhost:8888",
                        action="store")
    parser.add_argument("repo", metavar="REPO", type=str,
                        help="path to the repository this will observe")
    args = parser.parse_args()
    dispatcher_host, dispatcher_port = args.dispatcher_server.split(":")

    while True:
        try:
            # call the bash script that will update the repo and check
            # for changes. If there's a change, it will drop a .commit_id file
            # with the latest commit in the currrent working directory
            subprocess.check_output(["./update_repo.sh", args.repo])
        except subprocess.CalledProcessError as e:
            raise Exception("Could not update and check repository. Reason: %s" % e.output)
        
        if os.path.isfile(".commit_id"):
            # There is a change, first check status of dispatcher server
            try:
                response = helpers.communicate(dispatcher_host, int(dispatcher_port), "status")
                response = response.decode('utf-8')
            except socket.error as e:
                raise Exception("Could not communicate with dispatcher server: %s" % e)

            if response == "OK":
                # Dispatcher is present
                commit = ""
                with open(".commit_id", "r") as f:
                    commit = f.readline()
                response = helpers.communicate(dispatcher_host, int(dispatcher_port), "dispatch:%s" % commit)
                response = response.decode('utf-8')
                if response != "OK":
                    raise Exception("Could not dispatch the test: %s" % response)
                print("dispatched!")
            else:
                # Something wrong with dispatcher
                raise Exception("Could not dispatch the test: %s" % response)
        time.sleep(5)

if __name__ == "__main__":
    poll()