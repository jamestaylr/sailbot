#!/usr/bin/python

import socket
import sys
from thread import *
import time
import json
import threading

def generate_error(message):
    print '\033[31m\033[1m%s\033[0m\033[39m' % message

def generate_debug(message):
    print '\033[32m\033[1m%s\033[0m\033[39m' % message
    
try:
    from gps import *
except ImportError:
    generate_error('[GPS Socket]: GPS not configured properly!')
    sys.exit(1)

gpsd = None  # Global GPSD variable
gpsd_data = {}

# Define the socket parameters
HOST = ''
PORT = 8907

connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
connection.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 

# Bind socket to local host and port
try:
    connection.bind((HOST, PORT))
except socket.error, msg:
    generate_error('[GPS Socket]: Bind failed. Error Code: ' + str(msg[0]) + ' Message ' \
        + msg[1])
    sys.exit()

print '[GPS Socket]: Socket bind complete!'

# GPSD polling class definitions
class GPSPoller(threading.Thread):

    def __init__(self):
        generate_debug('[GPS Socket]: Setting up GPS')
        threading.Thread.__init__(self)
        global gpsd  # Bring it in scope
        gpsd = gps(mode=WATCH_ENABLE)  # Starting the stream of info
        self.current_value = None
        self.running = True  # Setting the thread running to true
        generate_debug('[GPS Socket]: Finished setting up GPS')

    def run(self):
        global gpsd
        generate_debug('[GPS Socket]: Entered thread')
        while gpsp.running:
            gpsd.next()  # This will continue to loop and grab each set of GPSD info to clear the buffer
            time.sleep(0.1)

# Create and start the GPSD thread
generate_debug('[GPS Socket]: Starting the GPS thread')
try:
    gpsp = GPSPoller()
    gpsp.daemon = True # Needed to make the thread shutdown correctly
    gpsp.start()

except socket.error:
    generate_error('[GPS Socket]: Could not connect to the GPS! Make sure everything is connected correctly.')
    sys.exit()

generate_debug('[GPS Socket]: Started TCP listerner')

# Start listening on socket
connection.listen(10)

# Function for handling connections; will be used to create threads
def clientthread(conn):

    # Infinite loop so that function do not terminate and thread do not end
    while True:

        # Updates the data dictionary        
        update_gpsd_data()

        # Receive data from the client
        data = conn.recv(1024)
        if not data:
            break

        conn.sendall(json.dumps(gpsd_data).encode('utf-8'))

    # Close the connection if the client if the client and server connection is interfered
    conn.close()

def update_gpsd_data():
    try:
        generate_debug('[GPS Socket]: GPS data requested')

        # Tries to pull in all the critical GPS data
        gpsd_data.clear()
        gpsd_data.update({
            'latitude': gpsd.fix.latitude,
            'longitude': gpsd.fix.longitude,
            'timestamp': gpsd.fix.time,
            'heading': gpsd.attitude.heading,
            'speed': gpsd.fix.speed,
            'roll': gpsd.attitude.roll,
            'pitch': gpsd.attitude.pitch,
            'yaw': gpsd.attitude.yaw,
            })
    except AttributeError:
        # Uses standard GPS data for units that have unsupported features
        gpsd_data.update({
            'latitude': gpsd.fix.latitude,
            'longitude': gpsd.fix.longitude,
            'timestamp': gpsd.fix.time,
            'speed': gpsd.fix.speed,
            })

# Main loop to keep the server process going
while True:

    try:
        # Wait to accept a connection in a blocking call
        (conn, addr) = connection.accept()
        print '[GPS Socket]: Connected with ' + addr[0] + ':' + str(addr[1])

        # Start new thread takes 1st argument as a function name to be run, second is the tuple of arguments to the function
        start_new_thread(clientthread, (conn, ))

    except KeyboardInterrupt, socket.error:
        generate_debug('[GPS Socket]: Shutting down GPS!')
        connection.shutdown(socket.SHUT_RDWR)
        connection.close()
        break

            