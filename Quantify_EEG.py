import numpy as np
import matplotlib.pyplot as plt
import scipy.io.wavfile as waves
import csv
import pandas as pd

def get_timePoints(file, max_t):
    data, data_new = [], []
    with open(file) as f:
        for line in f:
            line = line.replace("\n", "")
            data.append(line)

    for i in data:
        if ',' in i:
            parts = i.split(',')
            try:
                line = float(parts[1].strip())
                data_new.append(line)
            except (ValueError, IndexError):
                pass
    tg = np.array(data_new + [max_t+1])

    return tg

def smoothTriangle(AlphaRange, degree):
    triangle = np.concatenate((np.arange(degree + 1), np.arange(degree)[::-1]))
    smoothed = []

    for i in range(degree, len(AlphaRange) - degree * 2):
        point = AlphaRange[i:i + len(triangle)] * triangle
        smoothed.append(np.sum(point)/np.sum(triangle))

    smoothed = [smoothed[0]]*int(degree + degree/2) + smoothed
    while len(smoothed) < len(AlphaRange):
        smoothed.append(smoothed[-1])

    return smoothed

def get_signals(file, user):
    fs, data = waves.read(file[0])

    length_data=np.shape(data)
    length_new=length_data[0]*0.05
    ld_int=int(length_new)
    from scipy import signal
    data_new=signal.resample(data,ld_int)

    plt.figure('Spectrogram of Curtis Data')
    d, f, t, im = plt.specgram(data_new, NFFT= 256, Fs=500, noverlap=250)
    if user == 2:
        plt.ylim(0,90)
        plt.colorbar(label= "Power/Frequency")
        plt.ylabel('Frequency [Hz]')
        plt.xlabel('Time [s]')
        plt.show()
    else:
        plt.close()

    # Extract a specific frequency range (between 7 and 12 Hz).
    position_vector = []
    length_f = np.shape(f)
    l_row_f = length_f[0]
    for i in range(0, l_row_f):
        if f[i] >= 7 and f[i] <= 12:
            position_vector.append(i)

    length_d = np.shape(d)
    l_col_d = length_d[1]
    AlphaRange = []
    for i in range(0,l_col_d):
        AlphaRange.append(np.mean(d[position_vector[0]:max(position_vector)+1,i]))

    y = smoothTriangle(AlphaRange, 100)

    datosy = np.asarray(y)
    datosyt = np.array([datosy,t])

    tg = get_timePoints(file[1], max(t))

    length_t = np.shape(t)
    l_row_t = length_t[0]
    eyesclosed, eyesopen = [], []
    j,l = 0, 0
    for i in range(0, l_row_t):
        if t[i] >= tg[j]:
            if j % 2 == 0:
                eyesopen.append(np.mean(datosy[l:i]))
            if j % 2 == 1:
                eyesclosed.append(np.mean(datosy[l:i]))
            l = i
            j = j + 1

    if user == 2:
        meanclosed=np.mean(eyesclosed)
        sdopen=np.std(eyesopen)
        sdclosed=np.std(eyesclosed)
        eyes=np.array([eyesopen, eyesclosed])
        meanopen=np.mean(eyesopen)

        from scipy import stats
        result=stats.ttest_ind(eyesopen, eyesclosed, equal_var = False)

        plt.figure('AlphaRange of Curtis Data', figsize=(10, 6))
        plt.plot(t, y)
        plt.xlabel('Time [s]')
        plt.figtext(0.5, 0.9, result, ha='center', va='center')
        plt.xlim(0,max(t))
        plt.show()
        plt.close()

    return eyesopen, eyesclosed

file1 = ['Blake_BYB_Recording_2023-12-12_15.43.39.wav','Blake_BYB_Recording_2023-12-12_15.43.39-events.txt']
file2 = ['Curtis_BYB_Recording_2023-10-18_05.38.42.wav','Curtis_BYB_Recording_2023-10-18_05.38.42-events.txt']
file3 = ['Matthew_BYB_Recording_2023-12-02_15.01.30.wav', 'Matthew_BYB_Recording_2023-12-02_15.01.30-events.txt']

eyesopen1, eyesclosed1 = get_signals(file1, 1)
eyesopen2, eyesclosed2 = get_signals(file2, 2)
eyesopen3, eyesclosed3 = get_signals(file3, 3)

user1 = [eyesopen1, eyesclosed1]
user2 = [eyesopen2, eyesclosed2]
user3 = [eyesopen3, eyesclosed3]

plt.figure('DataAnalysis with Multiple Users Data', figsize=(10, 6))
plt.subplots_adjust(top= 0.97, bottom=0.2)
plt.boxplot(user1, positions=[1, 2], sym='ko', whis=1.5, labels=['eyes\nopen\nBlake', 'eyes\nclosed\nBlake'])
plt.boxplot(user2, positions=[4, 5], sym='ko', whis=1.5, labels=['eyes\nopen\nCurtis', 'eyes\nclosed\nCurtis'])
plt.boxplot(user3, positions=[7, 8], sym='ko', whis=1.5, labels=['eyes\nopen\nMatthew', 'eyes\nclosed\nMatthew'])
plt.ylabel('AlphaWave')
plt.show()
