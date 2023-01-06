from machine import I2C
import machine
from machine import Pin
from machine import sleep
from machine import PWM
import network
import micropython
import time
import mpu6050
import math
import calibrate_page
import urequests_two as urequests

#initializing the I2C method for ESP32
i2c = I2C(scl=Pin(22), sda=Pin(21))     

mpu= mpu6050.accel(i2c)

monotone = Pin(32, Pin.OUT)
polytone = PWM(Pin(33), freq=500, duty=0)

button = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect("IODATA-cdbc80-2G", "8186896622346")

print(micropython.mem_info())

while sta.isconnected() == False:
    time.sleep(2)
    print("waiting")
    
print(sta.ifconfig())

url = "https://us-central1-hotaru-kanri.cloudfunctions.net/random-led-code"
data = {'ip': sta.ifconfig()[0], 'email': 'todbotts.triangles@gmail.com'}
headers = {}
headers['Content-Type'] = 'application/json'

#r = urequests.post(url, json=data, headers=headers)
#print(r.status_code)
#r.close()
time.sleep(1)


    
# ************************
# Configure the socket connection
# over TCP/IP
import socket

# AF_INET - use Internet Protocol v4 addresses
# SOCK_STREAM means that it is a TCP socket.
# SOCK_DGRAM means that it is a UDP socket.
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.bind(('',80)) # specifies that the socket is reachable 
#                 by any address the machine happens to have
s.listen(5)     # max of 5 socket connections

# ************************
# Function for creating the
# web page to be displayed


def averageList(listToAverage):
    
    av = 0
    for v in listToAverage:
        av+=v
    return av/len(listToAverage)

readings = {
    
    'GyX': [],
    'GyY': [],
    'GyZ': [],

    'AcX': [],
    'AcY': [],
    'AcZ': []
}

thresholds = {

    'GyX': 200,
    'GyY': 200,
    'GyZ': 200,

    'AcX': 200,
    'AcY': 200,
    'AcZ': 200,
    'monitoring': "false"
}

replies = {
    
    'GyX': "",
    'GyY': "",
    'GyZ': "",

    'AcX': "",
    'AcY': "",
    'AcZ': "",
    'no_movement_seconds': '0',
    'warning': ''
}

no_movement_seconds = 0

while True:
    conn, addr = s.accept()
    #print("Got connection from %s" % str(addr))
    
    # Socket receive()
    request=conn.recv(1600) #1024)
    print("")
    print("Content %s" % str(request))
    
    # Socket send()
    request = str(request)
    update = request.find('/getDHT')
    adjust = request.find("AcX_slider=")

    if update > -1:
        mpuv = mpu.get_values()
                
        for k in readings.keys():
            if len(readings[k]) > 5:
                readings[k].clear()
            readings[k].append(mpuv[k])

        for k in readings.keys():
            thisAverage = averageList(readings[k])
            
            if math.fabs(readings[k][-1]-thisAverage) > thresholds[k]:
                replies[k] = "#00ff22" # green
            else:
                replies[k] = "#ff2828" # red

        if thresholds['monitoring'] == "true":
            if "#00ff22" not in replies.values():
                no_movement_seconds += 1
            else:
                no_movement_seconds = 0

            if no_movement_seconds > 40:
                replies['warning'] = "No movement detected for more than 40 seconds"
                polytone.duty(999)  
                monotone.value(1)     
            elif no_movement_seconds > 20:
                replies['warning'] = "No movement detected for more than 20 seconds"
                polytone.duty(999)
            else:
                replies['warning'] = ''
                polytone.duty(0)
                monotone.value(0)

            replies['no_movement_seconds'] = str(no_movement_seconds)
    
        response = "|".join([r for r in replies.values()])
        
    elif adjust > -1:

        allSliders = request.split("/?")[1].split(" ")[0][1:]
      
        # AcX_slider=426&AcY_slider=501&AcZ_slider=501
        for slider in allSliders.split("&")[1:]:
            sliderName = slider.split("_slider=")[0]
            sliderValue = slider.split("_slider=")[1]
            thresholds[sliderName] = int(sliderValue)
        if "monitoring" in allSliders:
            thresholds['monitoring'] = "true"
        response = calibrate_page.page(**thresholds)

    else:
        response = calibrate_page.page(**thresholds)
        
    
    # Create a socket reply
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    
    # Socket close()
    conn.close()
    
    if button.value():
        polytone.duty(0)
        monotone.value(0)
        break
