# Backyard Brains Sep. 2019
# Made for python 3
# First install serial library
# Install numpy, pyserial, matplotlib
# pip3 install pyserial
#
# Code will read, parse and display data from BackyardBrains' serial devices
#
# Written by Stanislav Mircic
# stanislav@backyardbrains.com

import threading
import serial
import time
import matplotlib.pyplot as plt 
import numpy as np
import pandas


global connected
connected = False
#change name of the port here
port = 'COM7'
# port = '/dev/ttyUSB0'
baud = 230400
global input_buffer
global sample_buffer
global cBufTail
cBufTail = 0
input_buffer = []
sample_rate = 10000
display_size = 30000 #3 seconds
sample_buffer = np.linspace(0,0,display_size)
serial_port = serial.Serial(port, baud, timeout=0)


def smoothTriangle(data, degree):
    triangle=np.concatenate((np.arange(degree + 1), np.arange(degree)[::-1])) # up then down
    smoothed=[]

    for i in range(degree, len(data) - degree * 2):
        point=data[i:i + len(triangle)] * triangle
        smoothed.append(np.sum(point)/np.sum(triangle))
    # Handle boundaries
    smoothed=[smoothed[0]]*int(degree + degree/2) + smoothed
    while len(smoothed) < len(data):
        smoothed.append(smoothed[-1])
    return smoothed

def checkIfNextByteExist():
        global cBufTail
        global input_buffer
        tempTail = cBufTail + 1
        
        if tempTail==len(input_buffer): 
            return False
        return True
    

def checkIfHaveWholeFrame():
        global cBufTail
        global input_buffer
        tempTail = cBufTail + 1
        while tempTail!=len(input_buffer): 
            nextByte  = input_buffer[tempTail] & 0xFF
            if nextByte > 127:
                return True
            tempTail = tempTail +1
        return False;
    
def areWeAtTheEndOfFrame():
        global cBufTail
        global input_buffer
        tempTail = cBufTail + 1
        nextByte  = input_buffer[tempTail] & 0xFF
        if nextByte > 127:
            return True
        return False

def numberOfChannels():
    return 1

def handle_data(data):
    global input_buffer
    global cBufTail
    global sample_buffer    
    if len(data)>0:

        cBufTail = 0
        haveData = True
        weAlreadyProcessedBeginingOfTheFrame = False
        numberOfParsedChannels = 0
        
        while haveData:
            MSB  = input_buffer[cBufTail] & 0xFF
            
            if(MSB > 127):
                weAlreadyProcessedBeginingOfTheFrame = False
                numberOfParsedChannels = 0
                
                if checkIfHaveWholeFrame():
                    
                    while True:
                        
                        MSB  = input_buffer[cBufTail] & 0xFF
                        if(weAlreadyProcessedBeginingOfTheFrame and (MSB>127)):
                            #we have begining of the frame inside frame
                            #something is wrong
                            break #continue as if we have new frame
            
                        MSB  = input_buffer[cBufTail] & 0x7F
                        weAlreadyProcessedBeginingOfTheFrame = True
                        cBufTail = cBufTail +1
                        LSB  = input_buffer[cBufTail] & 0xFF

                        if LSB>127:
                            break #continue as if we have new frame

                        LSB  = input_buffer[cBufTail] & 0x7F
                        MSB = MSB<<7
                        writeInteger = LSB | MSB
                        numberOfParsedChannels = numberOfParsedChannels+1
                        if numberOfParsedChannels>numberOfChannels():
            
                            #we have more data in frame than we need
                            #something is wrong with this frame
                            break #continue as if we have new frame
            

                        sample_buffer = np.append(sample_buffer,writeInteger-512)
                        

                        if areWeAtTheEndOfFrame():
                            break
                        else:
                            cBufTail = cBufTail +1
                else:
                    haveData = False
                    break
            if(not haveData):
                break
            cBufTail = cBufTail +1
            if cBufTail==len(input_buffer):
                haveData = False
                break


def read_from_port(ser):
    global connected
    global input_buffer
    while not connected:
        #serin = ser.read()
        connected = True

        while True:
           
           reading = ser.read(1024)
           if(len(reading)>0):
                reading = list(reading)
#here we overwrite if we left some parts of the frame from previous processing 
#should be changed             
                input_buffer = reading.copy()
                # print("len(reading)",len(reading))
                handle_data(reading)
           
           time.sleep(0.001)

thread = threading.Thread(target=read_from_port, args=(serial_port,))
thread.start()
xi = np.linspace(-display_size/sample_rate, 0, num=display_size)
xi=xi[1:]





while True:
    plt.ion()
    plt.show(block=False)
    if(len(sample_buffer)>0):
        #i = len(sample_buffer)
        yi = sample_buffer.copy()
        yi = yi[-display_size:]
 

        arr2 = np.where(yi>300, 1, 0) 
        arr2=arr2*100
        arr3=np.diff(arr2)
        arr2=arr2[1:]
        boolDiff=arr3>0
        xvals=xi[boolDiff]

        yi=yi[1:]
        yvals= yi[boolDiff]

    
        sample_buffer = sample_buffer[-display_size:]
        plt.clf()      

        plt.ylim(-550, 550)
        
        plt.plot(xi, yi, linewidth=1, color='royalblue')
        plt.plot(xi, arr2, linewidth=1, color='magenta')
        plt.plot(xi, arr3, linewidth=1, color='purple')
        plt.scatter(xvals, yvals, color='green')
        plt.pause(0.001)
        time.sleep(0.08)

        avg=[]
        for i, val in enumerate(xvals):
            if i !=0:
                avg.append(xvals[i]-xvals[i-1])
            
        if len(avg)>1:
            print(1/(sum(avg)/len(avg))*60)
