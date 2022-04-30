from unicodedata import name
import xml.etree.ElementTree as ET
import matplotlib.pyplot as plt
import numpy as np

class examination:
    def __init__(self, xml):
        self.xml = xml
        self.loadHeader()
        self.loadSignal()
        self.loadEvents()
        self.loadQRS()

    def loadHeader(self):
        self.dom = ET.parse(self.xml)
        self.signalTreePath = "patient/examination/analysis/blockExtended/signal"

        # Load list of first 12 lead names, number of samples, fsamp
        self.numberOfLeads = 12
        self.signalElement = self.dom.find(self.signalTreePath)
        self.leadList = list(map(str, self.signalElement.get("leads").split()))[0:self.numberOfLeads]
        self.numberSamples = int(self.signalElement.get("numberSamples"))

    def infoHeader(self):
        print(f"\nNumber of leads:\t {len(self.leadList)}")
        print(f"Number of samples:\t {self.numberSamples}")
    
    def loadSignal(self):
        # Load 12 signal waves in array
        waves = self.dom.findall(self.signalTreePath + "/wave")[0:self.numberOfLeads]
        fSamp = int(self.signalElement.get("frequency"))
        self.leads = []

        for index, waveLead in enumerate(waves):
            if waveLead.get("lead") == self.leadList[index]:
                signalData = np.array(list(map(int, (waveLead.text).split())), ndmin=2)
                self.leads.append(lead(self.leadList[index], fSamp, signalData))

    def infoSignal(self):
        print(f"\nNumber of leads data:\t {len(self.leads)}")
        print(f"Sampling freqency:\t {self.leads[0].fSamp} Hz")
    
    def loadEvents(self):
        # Load R positions, QRS position
        beatTable = self.dom.find('.//eventTable[@name="BeatTable"]')
        events = beatTable.findall("event")
        fSamp = int(beatTable.get("frequency"))
        rPositions = 0

        for lead in self.leads:
            self.eventTable = []

            for event in events:
                rPosition = int(event.get("tickOffset"))
                qrsOff = int(event.find('.//value[@name="QRS_TimeOn_05ms"]').text)
                qrsOn = int(event.find('.//value[@name="QRS_TimeOff_05ms"]').text)
                
                # Resample events positions to match sampling freq with signal
                if fSamp != self.leads[0].fSamp:
                    resamplingConst = fSamp/self.leads[0].fSamp
                    rPositions = rPositions/resamplingConst
                    qrsOff = qrsOff/resamplingConst
                    qrsOn = qrsOn/resamplingConst

                self.eventTable.append(beat(fSamp, rPosition, qrsOff, qrsOn))

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

class lead:
    def __init__(self, name, fSamp, signalData):
        self.name = name
        self.signalData = signalData
        self.fSamp = fSamp
        self.beats = []

class beat:
    def __init__(self, fSamp, rPosition, qrsOff, qrsOn):
        self.rPosition = rPosition
        self.qrsOff = qrsOff
        self.qrsOn = qrsOn
        self.fSamp = fSamp
        self.QRS = []


exam = examination('MUSE_20180111_155154_74000_A000.xml')
exam.infoHeader()
exam.infoSignal()
exam.infoEvents()

