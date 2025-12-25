import struct
import time
import numpy as np #treba pip install numpy

class DataMaster():
    def __init__(self):
        self.sync = "#?#\n" #ovu poruku šaljemo uc kao zahtev za povezivanje
        self.sync_ok = "!" #očekujemo ! ako je uc povezan
        self.StartStream = "#A#\n" #šaljemo za početak streama
        self.StopStream = "#S#\n" #završetak streama
        self.Disconnect = "#D#\n"
        self.SynchChannel = 0 #broj kanala koji dobivamo sa mikrokontrolera, necemo koristit za sad
        self.msg = [] #sadži samo int podatke iz ECG-a ili string ako je u pitanje komunikacija i handshaking izemdju mcu i pythona
        self.prevECGdata = 0


        #liste sa kojima ćemo crtat grafove, imat će podatke i vrijeme
        self.XData = [] #vrijeme
        self.YData = [] #vrijednosti

        self.DisplayTimeRange = 5 #5 sekundi je XData dugačak


        self.FunctionMaster = {
            "RowData" : self.RowData , 
            "Voltage Display" : self.VoltageData #ovo dvoje su funkcije
            }


        self.ChannelNum = {
            'Ch0' : 0,
            'Ch1' : 1,
            'Ch2' : 2,
            'Ch3' : 3,
            'Ch4' : 4,
            'Ch5' : 5,
            'Ch6' : 6,
            'Ch7' : 7
        }


        self.ChannelColor = {
            'Ch0' : 'blue',
            'Ch1' : 'green',
            'Ch2' : 'red',
            'Ch3' : 'cyan',
            'Ch4' : 'magenta',
            'Ch5' : 'yellow',
            'Ch6' : 'black',
            'Ch7' : 'white'
        }


    def DecodeMsg(self):
        temp = self.RowMsg #predhodno je self.RowMsg = read(1)
        if len(temp) > 0:
            print("Tu smo")
            print(f"temp je > {temp}")
            self.msg = chr(temp[0])
            print(f"split msg: {self.msg}")



    def DecodePacket(self, serial):
        raw_data = self.RowMsg #Predhodno smo napravili da je RowMsg = '0xaa' + rem
        #  print("Unutar DecodePacket-a")
            
        try:
            header = self.RowMsg[0]
            ecg_raw = struct.unpack('<I', self.RowMsg[1:5])[0]       # little-endian uint32
            footer = self.RowMsg[5]
            if(ecg_raw > 4096):
                ecg_raw = self.prevECGdata
            else:
                self.prevECGdata = ecg_raw
            
            self.msg = [ecg_raw]
            print(f"SelfRom: {self.RowMsg}")
            print(f"SelfMsg: {self.msg}")

        except struct.error as e:
                print(f"Unpack error: {e}")
            
                    

        if header != 0xAA or footer != 0x0A:
          #      print("Header/Footer mismatch")
                pass


    #Sve sljedeće se odnosi na pronalazak kanala
    def GenChannels(self):
        self.Channels = [f"Ch{ch}" for ch in range(self.SynchChannel)] #vratilo bi za SynchChannel = 5, ch1 ch2 ch3 ch4,..

    def buildYdata(self):
        for _ in range(self.SynchChannel):
            self.YData.append([])
            #kada bi imali 4 kanala, imali bi YData =[ [], [], [], [] ], za svaki kanal po jednu listu koja ce sadrzavat y vrijednosti


    def ClearData(self):
        self.RowMsg = "" #row msg je dekodirana vrijednost koju dobijemo iz mikrokontrolera
        self.msg = []
        self.YData = []
        self.XData = []
        self.RefTime = 0

    # Ne koristimo
    # def IntMsgFunc(self):
    #     self.IntMsg = [int(msg) for msg in self.msg]
   
   
    # def StreamDataCheck(self):
    #     self.StreamData = False
    #     if self.SynchChannel == len(self.msg):
    #         if self.messageLen == self.messageLenCheck:
    #             self.StreamData = True
    #             self.IntMsgFunc()


    def SetRefTime(self):
        if len(self.XData) == 0:
            self.RefTime = time.perf_counter()

        else:
            self.RefTime = time.perf_counter() - self.XData[len(self.XData) - 1]   #ovo je razlika vremena, Xdata je vrijeme
 
    
    def UpdateXdata(self):
        if(len(self.XData)) == 0:
            self.XData.append(0)

        else:
            self.XData.append(time.perf_counter() - self.RefTime)


    def UpdateYdata(self):
        # for ChNumber in range(self.SynchChannel):
        #     self.YData[ChNumber].append(self.msg[ChNumber][0])
        self.YData[0].append(self.msg) #ovdje se nalazi ecg info, na nultom mjestu je jedini kanal

    def AdjustData(self):
        lenXData = len(self.XData)
        if self.XData[lenXData - 1] - self.XData[0] > self.DisplayTimeRange: #ovo je promjena vremena u listi
            del self.XData[0]
            for ydata in self.YData: #self.Ydata je samo jedna lista jer imamo jedan kanal samo
                del ydata[0]
        
        #lakše je raditi sa numpy 
        x = np.array(self.XData)
        self.XDisplay = np.linspace(x.min(), x.max(), len(x), endpoint = 0)
        self.YDisplay = np.array(self.YData)


    def RowData(self,gui):
        gui.chart.plot(gui.x, gui.y, color = gui.color,  dash_capstyle = 'projecting', linewidth = 1)


    def VoltageData(self,gui):
        gui.chart.plot(gui.x, (gui.y / 4096) * 3.3, color = gui.color,  dash_capstyle = 'projecting', linewidth = 1)