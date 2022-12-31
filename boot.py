from machine import I2C
import machine
from machine import Pin
from machine import sleep
from machine import PWM
import network
import time
import mpu6050
import math

#initializing the I2C method for ESP32
i2c = I2C(scl=Pin(22), sda=Pin(21))     

mpu= mpu6050.accel(i2c)

monotone = Pin(32, Pin.OUT)
polytone = PWM(Pin(33), freq=500, duty=0)

button = machine.Pin(17, machine.Pin.IN, machine.Pin.PULL_UP)

sta = network.WLAN(network.STA_IF)
sta.active(True)
sta.connect("IODATA-cdbc80-2G", "8186896622346")

while sta.isconnected() == False:
    time.sleep(2)
    print("waiting")
    
print(sta.ifconfig())
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
def web_page():

    html_page = """
<!DOCTYPE html>  
 <html>  
  <head>  
  <meta name='viewport' content='width=device-width, initial-scale=1.0'/>  
  <script>   
   var ajaxRequest = new XMLHttpRequest();  
   
   function ajaxLoad(ajaxURL)  
   {  
    ajaxRequest.open('GET',ajaxURL,true);  
    ajaxRequest.onreadystatechange = function()  
    {  
     if(ajaxRequest.readyState == 4 && ajaxRequest.status==200)  
     {  
      var ajaxResult = ajaxRequest.responseText;  
      var array = ajaxResult.split("|");  
      document.getElementById('AcX').innerHTML = array[0];  
      document.getElementById('AcY').innerHTML = array[1];  
     }  
    }  
    ajaxRequest.send();  
   }  
     
   function updateDHT()   
   {   
     ajaxLoad('getDHT');   
   }  
     
   setInterval(updateDHT, 1000);  
    
  </script>  
    
    
  <title>ESP32 Weather Station</title>  
  </head>  
    
  <body>  
   <center>  
   <div id='main'>  
    <h1>SenseU </h1>  
    <h4>Web server on ESP32</h4>  
    <div id='content'>   
     <p>Horizontal Movement: <strong><span id='AcX'>--.-</span></strong></p>  
     <p>Vertical Movement: <strong><span id='AcY'>--.-</span></strong></p>  
    </div>  
   </div>  
   </center>  
  </body>  
 </html>
"""
    return html_page

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

replies = {
    
    'GyX': "",
    'GyY': "",
    'GyZ': "",

    'AcX': "",
    'AcY': "",
    'AcZ': ""
}

while True:
    conn, addr = s.accept()
    print("Got connection from %s" % str(addr))
    
    # Socket receive()
    request=conn.recv(1024)
    print("")
    print("Content %s" % str(request))
    
    # Socket send()
    request = str(request)
    update = request.find('/getDHT')
    if update == 6:
        mpuv = mpu.get_values()
        
        thisGyX = mpuv['GyX']
        thisGyY = mpuv['GyY']
        thisGyZ = mpuv['GyZ']
        
        thisAcX = mpuv['AcX']
        thisAcY = mpuv['AcY']
        thisAcZ = mpuv['AcZ']
        
        for k in readings.keys():
            
            readings[k].append(mpuv[k])

        
        for k in readings.keys():
            thisAverage = averageList(readings[k])
            
            if math.fabs(readings[k][-1]-thisAverage) > 200:
                replies[k] = "movement"
            else:
                replies[k] = "none"
        
    
        response = replies['AcX'] + "|"+ replies['AcY']
        
        for k in readings.keys():
            if len(readings[k]) > 10:
                readings[k] = []
        
    else:
        response = web_page()
        
    
    # Create a socket reply
    conn.send('HTTP/1.1 200 OK\n')
    conn.send('Content-Type: text/html\n')
    conn.send('Connection: close\n\n')
    conn.sendall(response)
    
    # Socket close()
    conn.close()
    
    if button.value():
        break