import struct
import time
import numpy as np #treba pip install numpy
from datetime import datetime
import csv
import os
import threading

class DataMaster():
    def __init__(self):
        self.sync = "#?#\n" #ovu poruku šaljemo uc kao zahtev za povezivanje
        self.sync_ok = "!" #očekujemo ! ako je uc povezan
        self.StartStream = "#A#\n" #šaljemo za početak streama
        self.StopStream = "#S#\n" #završetak streama
        self.Disconnect = "#D#\n"
        self.SynchChannel = 1 #hardcoded to 1 channel
        self.msg = [] #sadži samo int podatke iz ECG-a ili string ako je u pitanje komunikacija i handshaking izemdju mcu i pythona
        self.prevECGdata = 0
        self.currBPM = 0

        # Simple lists for single channel - YData is now just a list, not a matrix
        self.XData = [] #vrijeme
        self.YData = [] #vrijednosti - single list for single channel

        self.DisplayTimeRange = 5 #5 sekundi je XData dugačak

        self.save_directory = os.getcwd() #default-na vrijednost za spremanje podatka -> ovo daje working directory

        self.SaveBuffer = [] #Ovo je lista u koju primamo podatke pa ih tek onda šaljemo, bez ovog bi trebali otvorit file -> zapisat podatak -> zavotvorit file (jako sporo)
        self.SaveBufferSize = 1000
        self.lock = threading.Lock() # Zaštita podataka, spavajuci thread koji se budi samo kad treba ispraznit buffer

        # Function master for different display modes
        self.FunctionMaster = {
            "Raw Data" : self.RowData , 
            "Voltage Display" : self.VoltageData
        }

    def FileNameFunc(self):
        now = datetime.now()
        filename = now.strftime("%Y%m%d%H%M%S") + ".csv" 

        self.filename = os.path.join(self.save_directory, filename) #spajamo ime timestampa sa putanjom

    def SaveData(self, gui): 
        data = [elt for elt in self.msg] #u self.msg se nalaze podaci primljeni preko uarta
        data.insert(0, self.XData[len(self.XData) - 1]) #na početak dodamo zadnji trenutak vremena za podatke
        
        with self.lock:
            self.SaveBuffer.append(data)

            if(len(self.SaveBuffer) >= self.SaveBufferSize):
                if len(self.SaveBuffer) >= 500:
                    # Uzmi podatke i isprazni buffer odmah
                    data_to_write = list(self.SaveBuffer)
                    self.SaveBuffer.clear()
                    
                    # Pokreni pisanje u pozadini da ne kočiš UART
                    t = threading.Thread(target=self.WriteToFile, args=(data_to_write,), daemon=True)
                    t.start()

    def WriteToFile(self, data):
        # Ova funkcija se izvršava u svom svijetu i ne smeta grafu
        try:
            with open(self.filename, 'a', newline='') as f:
                writer = csv.writer(f)
                writer.writerows(data)
        except Exception as e:
            print(f"Greška pri zapisivanju: {e}")

    def DecodeMsg(self):
        temp = self.RowMsg #predhodno je self.RowMsg = read(1)
        if len(temp) > 0:
            print("Tu smo")
            print(f"temp je > {temp}")
            self.msg = chr(temp[0])
            print(f"split msg: {self.msg}")

    def DecodePacket(self, serial):
        raw_data = self.RowMsg #Predhodno smo napravili da je RowMsg = '0xaa' + rem
            
        try:
            header = self.RowMsg[0]
            ecg_raw = struct.unpack('<i', self.RowMsg[1:5])[0]       # little-endian uint32
            self.currBPM = struct.unpack('<I', self.RowMsg[5:9])[0]
            footer = self.RowMsg[9]
            print(f"ecg_raw prije filtra : {ecg_raw}")
            if(ecg_raw > 1000000 or ecg_raw < -1000000):
                ecg_raw = self.prevECGdata
            else:
               self.prevECGdata = ecg_raw
            
            self.msg = [ecg_raw]
            print(f"SelfRom: {self.RowMsg}")
            print(f"SelfMsg: {self.msg}")

        except struct.error as e:
                print(f"Unpack error: {e}")

        if header != 0xAA or footer != 0x0A:
                pass

    def ClearData(self):
        self.RowMsg = "" #row msg je dekodirana vrijednost koju dobijemo iz mikrokontrolera
        self.msg = []
        self.YData = []  # Now just a simple list
        self.XData = []
        self.RefTime = 0

    def SetRefTime(self):
        if len(self.XData) == 0:
            self.RefTime = time.perf_counter()
        else:
            self.RefTime = time.perf_counter() - self.XData[len(self.XData) - 1]
 
    def UpdateXdata(self):
        if(len(self.XData)) == 0:
            self.XData.append(0)
        else:
            self.XData.append(time.perf_counter() - self.RefTime)

    def UpdateYdata(self):
        # Simplified - just append to single list
        self.YData.append(self.msg[0])

    def AdjustData(self):
        lenXData = len(self.XData)
        if self.XData[lenXData - 1] - self.XData[0] > self.DisplayTimeRange:
            del self.XData[0]
            del self.YData[0]  # Now just deleting from single list
        
        # Convert to numpy arrays for display
        x = np.array(self.XData)
        self.XDisplay = np.linspace(x.min(), x.max(), len(x), endpoint=0)
        self.YDisplay = np.array(self.YData)  # Now just a 1D array

    def RowData(self, gui):
        # Plot raw ADC data (inverted)
        gui.chartMaster.ax.plot(self.XDisplay, -1 * self.YDisplay, 
                                color='blue', dash_capstyle='projecting', linewidth=1)

    def VoltageData(self, gui):
        # Convert ADC values to voltage (assuming 12-bit ADC and 3.3V reference)
        gui.chartMaster.ax.plot(self.XDisplay, (self.YDisplay / 131072) * (1/20) * 1000, color='blue', dash_capstyle='projecting', linewidth=1)