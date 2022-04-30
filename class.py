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

    def loadHeader(self):
        self.dom = ET.parse(self.xml)
        self.signalTreePath = "patient/examination/analysis/blockExtended/signal"

        # Load list of first 12 lead names, number of samples, fSamp
        self.signalElement = self.dom.find(self.signalTreePath)
        self.leadList = list(map(str, self.signalElement.get("leads").split()))[0:self.numberOfLeads]
        self.numberSamples = int(self.signalElement.get("numberSamples"))

    def infoHeader(self):
        print(f"\nNumber of leads:\t {len(self.leadList)}")
        print(f"Number of samples:\t {self.numberSamples}")
    
    def loadSignal(self):
        # Load X signal waves in array Lead object
        waves = self.dom.findall(self.signalTreePath + "/wave")[0:self.numberOfLeads]
        fSamp = int(self.signalElement.get("frequency"))

        for index, waveLead in enumerate(waves):
            if waveLead.get("lead") == self.leadList[index]:
                signalData = np.array(list(map(int, (waveLead.text).split())), ndmin=2)
                self.leads.append(Lead(self.leadList[index], fSamp, signalData))

    def infoSignal(self):
        print(f"\nNumber of leads data:\t {len(self.leads)}")
        print(f"Sampling freqency:\t {self.leads[0].fSamp} Hz")
    
    def loadEvents(self):
        # Load R positions, QRS position
        beatTable = self.dom.find('.//eventTable[@name="BeatTable"]')
        events = beatTable.findall("event")
        fSamp = int(beatTable.get("frequency"))
        rPositions = 0

        for iLead, lead in enumerate(self.leads):
            self.eventTable = []

            for event in events:
                rPosition = int(event.get("tickOffset"))
                qrsOff = int(event.find('.//value[@name="QRS_TimeOn_05ms"]').text)
                qrsOn = int(event.find('.//value[@name="QRS_TimeOff_05ms"]').text)
                
                # Resample events positions to match sampling freq with signal
                if fSamp != self.leads[iLead].fSamp:
                    resamplingConst = fSamp/self.leads[iLead].fSamp

                    rPositions = rPositions/resamplingConst
                    qrsOff = qrsOff/resamplingConst
                    qrsOn = qrsOn/resamplingConst

                self.eventTable.append(Beat(int(fSamp/resamplingConst), rPosition, qrsOff, qrsOn))

            lead.beats = self.eventTable

    def loadQRS(self):
        for indexLead, lead in enumerate(self.leads):
            for indexBeat, beat in enumerate(lead.beats):
                sFrom = int(beat.rPosition-beat.qrsOn)
                sTo = int(beat.rPosition-beat.qrsOff)
                beat.QRS = lead.signalData[sFrom:sTo]


    def infoEvents(self):
        print(f"\nNumber of events:\t {len(self.eventTable)}")
        print(f"F sampling of events:\t {self.eventTable[0].fSamp} Hz")

class Lead:
    def __init__(self, name, fSamp, signalData):
        self.name = name                # Name of lead
        self.signalData = signalData    # Signal in array
        self.fSamp = fSamp              # Sampling freqency in Hz
        self.beats = []                 # List of beats

class Beat:
    def __init__(self, fSamp, rPosition, qrsOff, qrsOn):
        self.rPosition = rPosition      # Position of R
        self.qrsOff = qrsOff            # End of QRS (relative from R)
        self.qrsOn = qrsOn              # Start of QRS (relative from R)
        self.fSamp = fSamp              # Sampling freqency in Hz
        self.QRS = []                   # QRS part of signal as array


exam = Examination('MUSE_20180111_155154_74000_A000.xml', numberOfLeads=12)
exam.infoHeader()
exam.infoSignal()
exam.infoEvents()

