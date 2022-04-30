from unicodedata import name
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

def plotECG(signalArray, leadList, rPositions, qrsOff, qrsOn):
    
    # Settings
    leadNumber = signalArray.shape[0]
    rowCount = int(np.ceil(leadNumber/2) // 2 * 2 + 1)
    colmnCount = 2

    # Rearange to fit ECG view
    plotIndex = list(range(1, leadNumber+1))
    plotIndex = plotIndex[::2] + plotIndex[1::2]

    fig = plt.figure(figsize=(12,8))

    for lead in range(leadNumber):
        plt.rc('xtick', labelsize=6)
        plt.subplots_adjust(left=0.04, right=0.96, bottom=0.04, top=0.96, wspace=0.1)
        plt.subplot(rowCount, colmnCount, plotIndex[lead])

        # Plot signal
        plt.plot(signalArray[lead,:], linewidth=0.6)
        
        # Plot rPositions
        plt.vlines(x = rPositions, ymin = min(signalArray[lead,:]), ymax = max(signalArray[lead,:]),
            colors = 'r', linewidth=0.4)

        # Plot QRS
        plt.vlines(x = rPositions-qrsOn, ymin = min(signalArray[lead,:]), ymax = max(signalArray[lead,:]),
            colors = 'y', linewidth=0.4)
        plt.vlines(x = rPositions-qrsOff, ymin = min(signalArray[lead,:]), ymax = max(signalArray[lead,:]),
            colors = 'y', linewidth=0.4)

        # Plot QRS background
        for x, rPosition in enumerate(rPositions):
            plt.axvspan(rPosition-qrsOn[x], rPosition-qrsOff[x], facecolor='r', alpha=0.2)

        plt.ylabel(leadList[lead])
        plt.yticks([])

    plt.show()

    

# XML parser
dom = ET.parse('MUSE_20180111_155154_74000_A000.xml')

# XML paths
signalTreePath = "patient/examination/analysis/blockExtended/signal"

# Load list of first 12 lead names, number of samples, fsamp
numberOfLeads = 12
signalElement = dom.find(signalTreePath)
leadList = list(map(str, signalElement.get("leads").split()))[0:numberOfLeads]
numberSamples = int(signalElement.get("numberSamples"))
fSampWaves = int(signalElement.get("frequency"))

print("------------------------------------------")
print(f"\nNumber of leads:\t {len(leadList)}")
print(f"Number of samples:\t {numberSamples}")
print(f"Sampling freqency:\t {fSampWaves} Hz")

# Load 12 signal waves in array
waves = dom.findall(signalTreePath + "/wave")[0:numberOfLeads]
signalArray = np.empty((1, numberSamples), dtype=np.int16)

for index, WaveLead in enumerate(waves):
    if WaveLead.get("lead") == leadList[index]:
        data = np.array(list(map(int, (WaveLead.text).split())), ndmin=2)
        signalArray = np.concatenate((signalArray, data), axis=0)
signalArray = np.delete(signalArray, 0, 0)

print(f"Shape of waves signal:\t {signalArray.shape}")
print("------------------------------------------")

# Load R positions, QRS position
beatTable = dom.find('.//eventTable[@name="BeatTable"]')
events = beatTable.findall("event")
fSampEvents = int(beatTable.get("frequency"))

rPositions = []
qrsOff = []
qrsOn = []

for event in events:
    rPositions.append(int(event.get("tickOffset")))
    qrsOff.append(int(event.find('.//value[@name="QRS_TimeOn_05ms"]').text))
    qrsOn.append(int(event.find('.//value[@name="QRS_TimeOff_05ms"]').text))

print(f"F sampling of events:\t {fSampEvents} Hz")


# Resample events positions to match sampling freq with signal
rPositions = np.array(rPositions)
qrsOff = np.array(qrsOff)
qrsOn = np.array(qrsOn)

if fSampEvents != fSampWaves:
    rPositions = rPositions/(fSampEvents/fSampWaves)
    qrsOff = qrsOff/(fSampEvents/fSampWaves)
    qrsOn = qrsOn/(fSampEvents/fSampWaves)


plotECG(signalArray, leadList, rPositions, qrsOff, qrsOn)

# Save QRS from signal

QRS = []
for indexLead, lead in enumerate(leadList):
    QRS.append([])
    for indexR, rPosition in enumerate(rPositions):
        sFrom = int(rPosition-qrsOn[indexR])
        sTo = int(rPosition-qrsOff[indexR])
        QRS[indexLead].append(signalArray[indexLead, sFrom:sTo])






