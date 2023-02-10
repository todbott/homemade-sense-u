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
import ujson

import socket

class SensorController:

    def __init__(self, minutes, allowable_disconnects, first_warning, second_warning) -> None:

        # Initialize the sensor
        self.i2c = I2C(scl=Pin(22), sda=Pin(21))  
         
        # Make a variable to hold sensor readiings
        self.mpu= mpu6050.accel(self.i2c)

        # Variables that were passed in
        self.minutes = minutes
        self.allowable_disconnects = allowable_disconnects
        self.first_warning = first_warning
        self.second_warning = second_warning

        # Here are the buzzers, LEDs and button
        self.monotone = Pin(32, Pin.OUT)
        self.polytone = PWM(Pin(33), freq=200, duty=0)
        self.red = PWM(Pin(16), freq=5000, duty=500)
        self.yellow = PWM(Pin(18), freq=5000, duty=0)
        self.green = PWM(Pin(19), freq=5000, duty=0)
        self.button = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)

        # Here are dictionaries to hold the readings and stuff
        self.no_movement_seconds = 0
        self.readings = {
            
            'GyX': [],
            'GyY': [],
            'GyZ': [],

            'AcX': [],
            'AcY': [],
            'AcZ': []
        }

        self.finalReadings = {
            
            'GyX': [],
            'GyY': [],
            'GyZ': [],

            'AcX': [],
            'AcY': [],
            'AcZ': []
        }

        self.thresholds = {

            'GyX': 10,
            'GyY': 10,
            'GyZ': 10,

            'AcX': 10,
            'AcY': 10,
            'AcZ': 10
        }

        self.replies = {
            
            'GyX': "",
            'GyY': "",
            'GyZ': "",

            'AcX': "",
            'AcY': "",
            'AcZ': "",
            'no_movement_seconds': '0',
            'warning': '',
            'packets': 0
        }

        # Here is the LAN thing
        self.sta = network.WLAN(network.STA_IF)

        # And here's the socket
        self.s = None

    def __connectToWiFiAndMakeSocketConnection(self):
        self.sta.active(True)
        self.sta.connect("IODATA-cdbc80-2G", "8186896622346")

        while self.sta.isconnected() == False:
            time.sleep(2)

        print(self.sta.ifconfig()[0])

        url = "https://us-central1-hotaru-kanri.cloudfunctions.net/random-led-code"
        data = {'ip': self.sta.ifconfig()[0], 'email': 'todbotts.triangles@gmail.com'}
        headers = {}
        headers['Content-Type'] = 'application/json'

        #r = urequests.post(url, json=data, headers=headers)
        #print(r.status_code)
        #r.close()
        time.sleep(1)

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind(('',80)) # specifies that the socket is reachable by any address the machine has available
        self.s.listen(5)     # max of 5 socket connections

        # Everything is go, so spin up the green LED
        for duty_cycle in range(0, 500):
            self.green.duty(duty_cycle)
            time.sleep(0.005)


    def __averageList(self, listToAverage):
    
        av = 0
        for v in listToAverage:
            av+=v
        return av/len(listToAverage)

    def __calculateSensorError(self):


        calculated = False
        while not calculated:

            lists_remain = False

            mpuv = self.mpu.get_values()
            self.yellow.duty(50)
            print("Calculating the error rates of each sensor")
                    
            for k in self.readings.keys():
                if isinstance(self.finalReadings[k], list):
                    lists_remain = True
                    if len(self.readings[k]) > 5:
                        self.finalReadings[k].append(self.__averageList(self.readings[k]))
                        self.readings[k].clear()
                        if len(self.finalReadings[k]) > 5:
                            self.finalReadings[k] = self.__averageList(self.finalReadings[k])
                    self.readings[k].append(mpuv[k])

            time.sleep(0.05)
            self.yellow.duty(0)
            time.sleep(0.05)

            if not lists_remain:
                calculated = True
        return

    def __calibrateSensor(self):
        seconds_without_error = 0
        adjustment = False
        calibrated = False
        while not calibrated:

            mpuv = self.mpu.get_values()

            for k in self.readings.keys():

                self.yellow.duty(500)
                self.readings[k] = mpuv[k]
                
                if math.fabs(self.readings[k]-self.finalReadings[k]) > self.thresholds[k]:
                    self.thresholds[k] += math.fabs(self.readings[k]-self.finalReadings[k])
                    adjustment = True

            if adjustment:
                adjustment = False
                seconds_without_error = 0
            else:
                seconds_without_error += 1
                print(f'{seconds_without_error} seconds with no error')
            if seconds_without_error > self.minutes * 60:
                calibrated = True
            self.yellow.duty(0)
            time.sleep(1)
            
        for k in self.readings.keys():
            self.readings[k] = []
            self.thresholds[k] += 100

        with open("calibration_values.txt", "w") as v:
            ujson.dump(self.thresholds, v)

    def __recalibrateOnStartupMaybe(self):
        # Check if the button is pressed just after startup.  If it is, that means that the user wants to
        # recalibrate the sensors, so erase the calibration_values.txt file
        if self.button.value():
            with open("calibration_values.txt", "w") as v:
                v.write('')
                v.close()
                for x in range(500, 0, -50):
                    self.green.duty(x)
                    time.sleep(0.25)
            self.green.duty(0)

    def __checkForMovementAndMakeReplies(self, movement_this_time):
        if not movement_this_time:
            self.no_movement_seconds += 3
        else:
            self.no_movement_seconds = 0

        if self.no_movement_seconds > self.second_warning:
            self.replies['warning'] = f"Alert: No movement detected for more than {self.second_warning} seconds"
            self.polytone.duty(999)  
            self.monotone.value(1)     
        elif self.no_movement_seconds > self.first_warning:
            self.replies['warning'] = f"Warning: No movement detected for more than {self.first_warning} seconds"
            self.polytone.duty(999)
        else:
            self.replies['warning'] = ''
            self.polytone.duty(0)
            self.monotone.value(0)

        self.replies['no_movement_seconds'] = str(self.no_movement_seconds)

        self.replies['packets'] = str(int(self.replies['packets']) + 1)
    
        return "|".join([r for r in self.replies.values()])

    def main(self):

        self.yellow.duty(0)
        self.red.duty(0)

        # Check if the button is pressed.  If so, erase the contents of calibration_values.txt
        self.__recalibrateOnStartupMaybe()

        # Connect to WiFi
        self.__connectToWiFiAndMakeSocketConnection()

        # If calibration_values.txt is empty, re-calibrate the sensors
        vals = open("calibration_values.txt", "r").read()
        if len(vals) == 0:
            self.__calculateSensorError()
            self.__calibrateSensor()
        else:
            with open("calibration_values.txt", "r") as v:
                self.thresholds = ujson.load(v)

        # Start looping, sending sensor updates to the site
        while True:
            
            conn, addr = self.s.accept()
            
            # Socket receive()
            request=conn.recv(1024)
            
            # Socket send()
            request = str(request)
            update = request.find('/getDHT')

            # If this is the first rendering of the page, /getDHT will not be in the request, so it will be -1 here.
            # If this, on the other hand, is a request triggered by Ajax (which happens every 3 seconds),
            # upate the sensor readings
            if update > -1:

                movement_this_time = False
                
                # The page updates every 3 seconds, but I want to check for movement even more frequently than that
                # So here, we check for movement 2 times within those 3 seconds we have
                for t in range(0, 2):

                    # The mpu6050.py file occasionally returns an error temporarily,
                    # so here we try to get the values, and if there's an error, we just fill
                    # the mpuv dictionary with the most recent values in the readings dictionary.
                    # If there was an error, we'll just activate the buzzer for a split second (for debugging purposes)
                    try:
                        mpuv = self.mpu.get_values()
                    except:
                        self.monotone.value(1) 
                        mpuv = {}
                        for k in self.readings.keys():
                            mpuv[k] = self.readings[k][0]
                        time.sleep(0.25)
                        self.monotone.value(0)
                        
                                    
                    for k in self.readings.keys():

                        self.readings[k].append(mpuv[k])
                        
                        # If there are 2 readings, compare the difference in thos readings against the threshold value for that sensor
                        if len(self.readings[k]) == 2:
                
                            if math.fabs(self.readings[k][1]-self.readings[k][0]) > self.thresholds[k]:
                                self.replies[k] = "#00ff22" # green
                                movement_this_time = True
                            else:
                                self.replies[k] = "#ff2828" # red
                            self.readings[k].clear()
                    time.sleep(1)

                # Make a | delimited response to send to the frontend
                response = self.__checkForMovementAndMakeReplies(movement_this_time)
                
            else:

                # If /getDHT was not in the request, we know it's the first time the page was rendered,
                # so let's return the whole page, instead of just a | delimited string
                response = calibrate_page.page()
                
            
            # Create a socket reply, and actually send the response
            conn.send('HTTP/1.1 200 OK\n')
            conn.send('Content-Type: text/html\n')
            conn.send('Connection: close\n\n')
            conn.sendall(response)
            
            # Socket close()
            conn.close()
            
            # If the button was pressed, the user wants to stop the monitoring
            if self.button.value():
                self.polytone.duty(0)
                self.monotone.value(0)
                self.green.duty(0)
                break

            # The wi-fi seems to cut out sometimes, crashing the system
            # Here we check that the Wifi is still connected, and re-connect if not
            if self.sta.isconnected() == False:
                self.green.duty(0)
                self.replies['packets'] = "0"
                self.__connectToWiFiAndMakeSocketConnection()

        # Here, we know the button has been pressed, or an error has occcured
        print('Problem here, or sensor has been stopped!')
        
        # Turn on the red and yellow LEDs, and start the buzzer!
        self.green.duty(0)
        self.yellow.duty(500)
        self.red.duty(500)
   
        self.polytone.duty(999)

        # Keep the buzzer and LEDs on until the button is pressed, then break
        while True:
            if self.button.value():
                break

        # As a final step, the system turns off all lights and buzzers, as a kind of cleanup operation
        self.polytone.duty(0)
        self.monotone.value(0)
        self.green.duty(0)
        self.red.duty(0)
        self.yellow.duty(0)









class NightSensorController:

    def __init__(self, minutes, first_warning, second_warning) -> None:

        # Initialize the sensor
        self.i2c = I2C(scl=Pin(22), sda=Pin(21))  
         
        # Make a variable to hold sensor readiings
        self.mpu= mpu6050.accel(self.i2c)

        # Variables that were passed in
        self.minutes = minutes
        self.first_warning = first_warning
        self.second_warning = second_warning

        # Here are the buzzers, LEDs and button
        self.polytone = PWM(Pin(33), freq=300, duty=0)
        self.red = PWM(Pin(16), freq=5000, duty=500)
        self.yellow = PWM(Pin(18), freq=5000, duty=0)
        self.green = PWM(Pin(19), freq=5000, duty=0)
        self.button = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)

        # Here are dictionaries to hold the readings and stuff
        self.no_movement_seconds = 0
        self.movement_log = {
            'seconds_until_movement': []
        }
        self.readings = {
            
            'GyX': [],
            'GyY': [],
            'GyZ': [],

            'AcX': [],
            'AcY': [],
            'AcZ': []
        }

        self.finalReadings = {
            
            'GyX': [],
            'GyY': [],
            'GyZ': [],

            'AcX': [],
            'AcY': [],
            'AcZ': []
        }

        self.thresholds = {

            'GyX': 10,
            'GyY': 10,
            'GyZ': 10,

            'AcX': 10,
            'AcY': 10,
            'AcZ': 10
        }


    def __averageList(self, listToAverage):
    
        av = 0
        for v in listToAverage:
            av+=v
        return av/len(listToAverage)

    def __calculateSensorError(self):


        calculated = False
        while not calculated:

            lists_remain = False

            try:
                mpuv = self.mpu.get_values()
            except:
                self.__initSensor()
                pass
            self.yellow.duty(50)
            print("Calculating the error rates of each sensor")
                    
            for k in self.readings.keys():
                if isinstance(self.finalReadings[k], list):
                    lists_remain = True
                    if len(self.readings[k]) > 5:
                        self.finalReadings[k].append(self.__averageList(self.readings[k]))
                        self.readings[k].clear()
                        if len(self.finalReadings[k]) > 5:
                            self.finalReadings[k] = self.__averageList(self.finalReadings[k])
                    self.readings[k].append(mpuv[k])

            time.sleep(0.05)
            self.yellow.duty(0)
            time.sleep(0.05)

            if not lists_remain:
                calculated = True
        return

    def __calibrateSensor(self):
        seconds_without_error = 0
        adjustment = False
        calibrated = False
        while not calibrated:

            try:
                mpuv = self.mpu.get_values()
            except:
                self.__initSensor()

            for k in self.readings.keys():

                self.yellow.duty(500)
                self.readings[k] = mpuv[k]
                
                if math.fabs(self.readings[k]-self.finalReadings[k]) > self.thresholds[k]:
                    self.thresholds[k] += math.fabs(self.readings[k]-self.finalReadings[k])
                    adjustment = True

            if adjustment:
                adjustment = False
                seconds_without_error = 0
            else:
                seconds_without_error += 1
                print(f'{seconds_without_error} seconds with no error')
            if seconds_without_error > self.minutes * 60:
                calibrated = True
            self.yellow.duty(0)
            time.sleep(1)
            
        for k in self.readings.keys():
            self.readings[k] = []
            self.thresholds[k] += 50

        with open("calibration_values.txt", "w") as v:
            ujson.dump(self.thresholds, v)

    def __recalibrateOnStartupMaybe(self):
        # Check if the button is pressed just after startup.  If it is, that means that the user wants to
        # recalibrate the sensors, so erase the calibration_values.txt file
        if self.button.value():
            with open("calibration_values.txt", "w") as v:
                v.write('')
                v.close()
                for x in range(500, 0, -50):
                    self.green.duty(x)
                    time.sleep(0.25)
            self.green.duty(0)

    def __checkForMovementAndMakeReplies(self, movement_this_time):
        if not movement_this_time:
            self.no_movement_seconds += 3
        else:
            if self.no_movement_seconds > self.first_warning:
                self.movement_log['seconds_until_movement'].append(self.no_movement_seconds)
            self.no_movement_seconds = 0

        if self.no_movement_seconds > self.second_warning:
            self.red.duty(500)
            self.polytone.duty(6)  
 
        elif self.no_movement_seconds > self.first_warning:
            self.red.duty(50)
            self.polytone.duty(3)
        else:
            self.red.duty(0)
            self.polytone.duty(0)


    def __initSensor(self):
        # Initialize the sensor
        self.i2c = I2C(scl=Pin(22), sda=Pin(21))  
        
        # Make a variable to hold sensor readiings
        self.mpu= mpu6050.accel(self.i2c)

        try:
            for x in range(0, 15):
                mpuv = self.mpu.get_values()
                for k in self.readings.keys():
                    self.readings[k].append(mpuv[k])
                time.sleep(1)
            for k in self.readings.keys():
                self.readings[k] = self.readings[k][-2:]

            print(self.readings)
            return True
        except:
            self.__initSensor()

    def main(self):

        self.polytone.duty(6)
        time.sleep(.5)
        self.polytone.duty(0)

        self.yellow.duty(0)
        self.red.duty(0)

        # Check if the button is pressed.  If so, erase the contents of calibration_values.txt
        self.__recalibrateOnStartupMaybe()

        # If calibration_values.txt is empty, re-calibrate the sensors
        vals = open("calibration_values.txt", "r").read()
        if len(vals) == 0:
            self.__calculateSensorError()
            self.__calibrateSensor()
        else:
            with open("calibration_values.txt", "r") as v:
                self.thresholds = ujson.load(v)

        # Start looping, sending sensor updates to the site
        while True:
            
            movement_this_time = False
            
            # The mpu6050.py file occasionally returns an error temporarily,
            # so here we try to get the values, and if there's an error, we just fill
            # the mpuv dictionary with the most recent values in the readings dictionary.
            # If there was an error, we'll just activate the buzzer for a split second (for debugging purposes)
            try:
                mpuv = self.mpu.get_values()
            except:
                
                self.yellow.duty(250)
                print("sensor momentarily disconnected")
                self.__initSensor()
                self.yellow.duty(0)
                
                
                            
            for k in self.readings.keys():

                self.readings[k].append(mpuv[k])
                
                # If there are 2 readings, compare the difference in those readings against the threshold value for that sensor
                if len(self.readings[k]) == 3:
        
                    if math.fabs(self.readings[k][1]-self.readings[k][0]) > self.thresholds[k]:
                        movement_this_time = True
                    self.readings[k] = self.readings[k][1:]
                    
            if movement_this_time:
               self.green.duty(20)
            time.sleep(1)
            self.green.duty(0)

            # Make a | delimited response to send to the frontend
            self.__checkForMovementAndMakeReplies(movement_this_time)

            time.sleep(1)
            
            # If the button was pressed, the user wants to stop the monitoring
            if self.button.value():
                self.polytone.duty(0)
                self.green.duty(0)
                break

        # Here, we know the button has been pressed, or an error has occcured
        print('Problem here, or sensor has been stopped!')

        with open("log.txt", "a") as v:
            ujson.dump(self.movement_log, v)
        
        # Turn on the red and yellow LEDs!
        self.green.duty(0)
        self.yellow.duty(50)
        self.red.duty(50)

        time.sleep(3)

        # Keep the buzzer and LEDs on until the button is pressed, then break
        while True:
            if self.button.value():
                # As a final step, the system turns off all lights and buzzers, as a kind of cleanup operation
                self.polytone.duty(0)
                self.green.duty(0)
                self.red.duty(0)
                self.yellow.duty(0)

                break