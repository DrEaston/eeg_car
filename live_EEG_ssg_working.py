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


from paramiko import SSHClient
import paramiko
# Connect
ssh = paramiko.SSHClient()
ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
ssh.connect('192.168.0.57', username='curtis', password='piPass')


global connected
connected = False
#change name of the port here
port = 'COM7'
#port = '/dev/ttyUSB0'
baud = 230400
global input_buffer
global sample_buffer
global cBufTail
cBufTail = 0
input_buffer = []
sample_rate = 1000
display_size = 30000 #3 seconds
sample_buffer = np.linspace(0,0,display_size)
serial_port = serial.Serial(port, baud, timeout=0)




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
                print("len(reading)",len(reading))
                handle_data(reading)
           
           time.sleep(0.001)

thread = threading.Thread(target=read_from_port, args=(serial_port,))
thread.start()
xi = np.linspace(-display_size/sample_rate, 0, num=display_size)
start=time.perf_counter()

while True:
    plt.ion()
    plt.show(block=False)
    if(len(sample_buffer)>0):
        #i = len(sample_buffer)
        print(len(sample_buffer))
        yi = sample_buffer.copy()
        yi = yi[-display_size:]


        plt.figure('Raw')


        sample_buffer = sample_buffer[-display_size:]
        plt.clf()      

        plt.ylim(-550, 550)
        plt.plot(xi, yi, linewidth=1, color='royalblue')
        plt.pause(0.001)
        time.sleep(0.08)

        data=yi
        length_data=np.shape(data)
        length_new=length_data[0]*0.05
        ld_int=int(length_new)
        from scipy import signal
        data_new=signal.resample(data,ld_int)



        mpw = plt.mlab.window_hanning(np.ones(256))
        f, t, d = signal.spectrogram(data_new, 500, detrend=False,nfft=256,window=mpw)
        position_vector=[]
        length_f=np.shape(f)
        l_row_f=length_f[0]
        for i in range(0, l_row_f):
            if f[i]>=7 and f[i]<=12:
                position_vector.append(i)

        length_d=np.shape(d)
        l_col_d=length_d[1]
        AlphaRange=[]
        for i in range(0,l_col_d):
            AlphaRange.append(np.mean(d[position_vector[0]:max(position_vector)+1,i]))


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

        plt.figure('AlphaRange')
        # y=smoothTriangle(AlphaRange, 100)

        plt.clf()  
        plt.plot(AlphaRange)
        plt.ylim(-1, 20)
        plt.show()
        
        current=time.perf_counter()


        if AlphaRange[-1]>5 and current-start>0.5:
            start=time.perf_counter()
            ssh_stdin, ssh_stdout, ssh_stderr = ssh.exec_command('python repositories/picar-4wd/examples/step_forward.py')
            ssh_stdin.close()
        