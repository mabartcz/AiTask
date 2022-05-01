import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

class Examination:
    def __init__(self, xml, numberOfLeads):
        self.xml = xml                      # Path to XML
        self.numberOfLeads = numberOfLeads  # Number of leads to load from XML
        self.leads = []                     # Empty list for leads

        # Load all data
        self.loadHeader()
        self.loadSignal()
        self.loadEvents()
        self.loadQRS()

    class Lead:
        def __init__(self, name, fSamp, signal):
            self.name = name                # Name of lead
            self.signal = signal            # Signal in array
            self.fSamp = fSamp              # Sampling freqency in Hz
            self.beats = []                 # List of beats

    class Beat:
        def __init__(self, fSamp, rPosition, qrsOff, qrsOn):
            self.rPosition = rPosition      # Position of R
            self.qrsOff = qrsOff            # End of QRS (relative from R)
            self.qrsOn = qrsOn              # Start of QRS (relative from R)
            self.fSamp = fSamp              # Sampling freqency in Hz
            self.QRS = []                   # QRS part of signal as array

    # Load list of first x lead names, number of samples, fSamp
    def loadHeader(self):
        self.dom = ET.parse(self.xml)
        self.signalTreePath = "patient/examination/analysis/blockExtended/signal"

        self.signalElement = self.dom.find(self.signalTreePath)
        self.leadNames = list(map(str, self.signalElement.get("leads").split()))[0:self.numberOfLeads]
        self.numberSamples = int(self.signalElement.get("numberSamples"))

    # Print header info
    def infoHeader(self):
        print(f"\nNumber of leads:\t {len(self.leadNames)}")
        print(f"Number of samples:\t {self.numberSamples}")
    
    # Load X signal waves in (array) Lead object
    def loadSignal(self):
        waves = self.dom.findall(self.signalTreePath + "/wave")[0:self.numberOfLeads]
        fSamp = int(self.signalElement.get("frequency"))

        for index, waveLead in enumerate(waves):
            if waveLead.get("lead") == self.leadNames[index]:
                signal = list(map(int, (waveLead.text).split()))
                self.leads.append(self.Lead(self.leadNames[index], fSamp, signal))

    # Print signal info
    def infoSignal(self):
        print(f"\nNumber of leads data:\t {len(self.leads)}")
        print(f"Sampling freqency:\t {self.leads[0].fSamp} Hz")
    
    # Load event table and resample
    def loadEvents(self):
        # Load R positions, QRS position
        beatTable = self.dom.find('.//eventTable[@name="BeatTable"]')
        events = beatTable.findall("event")
        fSamp = int(beatTable.get("frequency"))

        for iLead, lead in enumerate(self.leads):
            self.eventTable = []

            for event in events:
                rPosition = int(event.get("tickOffset"))
                qrsOff = int(event.find('.//value[@name="QRS_TimeOn_05ms"]').text)
                qrsOn = int(event.find('.//value[@name="QRS_TimeOff_05ms"]').text)
                
                # Resample events positions to match sampling freq with signal
                if fSamp != self.leads[iLead].fSamp:
                    resamplingConst = fSamp/self.leads[iLead].fSamp
                    rPosition = rPosition/resamplingConst
                    qrsOff = qrsOff/resamplingConst
                    qrsOn = qrsOn/resamplingConst

                self.eventTable.append(self.Beat(int(fSamp/resamplingConst), rPosition, qrsOff, qrsOn))

            lead.beats = self.eventTable

    # Load QRS segmants
    def loadQRS(self):
        for lead in self.leads:
            for beat in lead.beats:
                sFrom = int(beat.rPosition-beat.qrsOn)
                sTo = int(beat.rPosition-beat.qrsOff)
                beat.QRS = lead.signal[sFrom:sTo]


    # Print info about events
    def infoEvents(self):
        print(f"\nNumber of events:\t {len(self.eventTable)}")
        print(f"F sampling of events:\t {self.eventTable[0].fSamp} Hz")

    # Plot ECG 
    def plotECG(self, plotR=False, plotQRS=False):
        # Settings
        leadNumber = len(self.leads)
        if leadNumber == 1:
            colmnCount = 1
            rowCount = 1
        else:
            colmnCount = 2
            rowCount = int(np.ceil(leadNumber/2))

        # Rearange to fit ECG view
        plotIndex = list(range(1, leadNumber+1))
        plotIndex = plotIndex[::2] + plotIndex[1::2]

        fig = plt.figure(figsize=(11,7))

        for iLead, lead in enumerate(self.leads):
            plt.rc('xtick', labelsize=4)
            plt.subplots_adjust(left=0.04, right=0.96, bottom=0.04, top=0.94, wspace=0.1)
            plt.subplot(rowCount, colmnCount, plotIndex[iLead])

            # Plot signal
            plt.plot(lead.signal, linewidth=0.6)

            leadYmin = min(lead.signal)
            leadYmax = max(lead.signal)

            if plotR == True:
                # Plot rPositions
                for beat in lead.beats:
                    plt.vlines(x = beat.rPosition, ymin = leadYmin, ymax = leadYmax, colors = 'r', linewidth=0.4)

            if plotQRS == True:
                # Plot QRS
                for beat in lead.beats:
                    plt.vlines(x = beat.rPosition-beat.qrsOn, ymin = leadYmin, ymax = leadYmax, colors = 'y', linewidth=0.4)
                    plt.vlines(x = beat.rPosition-beat.qrsOff, ymin = leadYmin, ymax = leadYmax, colors = 'y', linewidth=0.4)

                    # Plot QRS background
                    plt.axvspan(beat.rPosition-beat.qrsOn, beat.rPosition-beat.qrsOff, facecolor='r', alpha=0.2)

            plt.ylabel(lead.name)
            fig.suptitle('ECG signal in leads', fontsize=10)
            plt.yticks([])

        plt.show()

    def plotQRS(self):
        # Settings
        leadNumber = len(self.leads)
        if leadNumber == 1:
            colmnCount = 1
            rowCount = 1
        else:
            colmnCount = 2
            rowCount = int(np.ceil(leadNumber/2))

        # Rearange to fit ECG view
        plotIndex = list(range(1, leadNumber+1))
        plotIndex = plotIndex[::2] + plotIndex[1::2]

        fig = plt.figure(figsize=(11,7))

        for iLead, lead in enumerate(self.leads):
            plt.rc('xtick', labelsize=4)
            plt.subplots_adjust(left=0.04, right=0.96, bottom=0.04, top=0.94, wspace=0.1)
            plt.subplot(rowCount, colmnCount, plotIndex[iLead])

            # Plot signal
            for beat in lead.beats:
                plt.plot(beat.QRS, linewidth=0.6)

            plt.ylabel(lead.name)
            plt.yticks([])

        fig.suptitle('QRS segments in leads', fontsize=10)
        plt.show()



exam = Examination('MUSE_20180111_155154_74000_A000.xml', numberOfLeads=1)
exam.infoHeader()
exam.infoSignal()
exam.infoEvents()
exam.plotECG(plotR=True, plotQRS=True)
exam.plotQRS()

