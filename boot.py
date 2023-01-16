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


red = PWM(Pin(16), freq=5000, duty=500)
yellow = PWM(Pin(18), freq=5000, duty=0)
green = PWM(Pin(19), freq=5000, duty=0)

button = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect("IODATA-cdbc80-2G", "8186896622346")

while sta.isconnected() == False:
    time.sleep(2)
    
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

finalReadings = {
    
    'GyX': [],
    'GyY': [],
    'GyZ': [],

    'AcX': [],
    'AcY': [],
    'AcZ': []
}

thresholds = {

    'GyX': 10,
    'GyY': 10,
    'GyZ': 10,

    'AcX': 10,
    'AcY': 10,
    'AcZ': 10
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

calculated = False
while not calculated:

    lists_remain = False

    mpuv = mpu.get_values()
    yellow.duty(50)
    print("Calculating the error rates of each sensor")
            
    for k in readings.keys():
        if isinstance(finalReadings[k], list):
            lists_remain = True
            if len(readings[k]) > 5:
                finalReadings[k].append(averageList(readings[k]))
                readings[k].clear()
                if len(finalReadings[k]) > 5:
                    finalReadings[k] = averageList(finalReadings[k])
            readings[k].append(mpuv[k])

    time.sleep(0.5)
    yellow.duty(0)
    time.sleep(0.5)

    if not lists_remain:
        calculated = True


seconds_without_error = 0
adjustment = False
calibrated = False
while not calibrated:

    mpuv = mpu.get_values()

    for k in readings.keys():

        yellow.duty(500)
        readings[k] = mpuv[k]
        
        if math.fabs(readings[k]-finalReadings[k]) > thresholds[k]:
            thresholds[k] += math.fabs(readings[k]-finalReadings[k])
            adjustment = True

    if adjustment:
        adjustment = False
        seconds_without_error = 0
    else:
        seconds_without_error += 1
        print(f'{seconds_without_error} seconds with no error')
    if seconds_without_error > 60:
        calibrated = True
    yellow.duty(0)
    time.sleep(1)
    
for k in readings.keys():
    readings[k] = []
    thresholds[k] += 100

yellow.duty(0)
red.duty(0)
for duty_cycle in range(0, 500):
    green.duty(duty_cycle)
    time.sleep(0.005)

ok = True
while ok == True:
    try:
        conn, addr = s.accept()
        #print("Got connection from %s" % str(addr))
        
        # Socket receive()
        request=conn.recv(1024)
        print("")
        print("Content %s" % str(request))
        
        # Socket send()
        request = str(request)
        update = request.find('/getDHT')

        if update > -1:

            mpuv = mpu.get_values()
                            
            for k in readings.keys():

                readings[k].append(mpuv[k])

                
                print(f'{k} {thresholds[k]}')
                
                if len(readings[k]) == 2:
                    print(f'{k} {math.fabs(readings[k][1]-readings[k][0])}')
        
                    if math.fabs(readings[k][1]-readings[k][0]) > thresholds[k]:
                        replies[k] = "#00ff22" # green
                    else:
                        replies[k] = "#ff2828" # red
                    readings[k].clear()


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
            
        else:
            response = calibrate_page.page()
            
        
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
            green.duty(0)
            break
    except:
        ok = False
        break

if ok == False:
    print("a problem occured, triggering a warning now")
    green.duty(0)
    red.duty(500)
    while True:
        polytone.duty(999)
        red.duty(500)
        time.sleep(2)
        polytone.duty(0)
        red.duty(0)

        if button.value():
            polytone.duty(0)
            break

polytone.duty(0)
monotone.value(0)
green.duty(0)
red.duty(0)
yellow.duty(0)




