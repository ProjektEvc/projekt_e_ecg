import serial.tools.list_ports
import time 
import struct

class SerialControl():
    def __init__(self):
        self.com_list = []
        self.sync_cnt = 200 #granična vrijednost pokušaja



    def getCOMList(self):
        ports = serial.tools.list_ports.comports()  #ova funkcija vraća sve portove spojene na kompjuter
        self.com_list = [com[0] for com in ports]
        self.com_list.insert(0, "-")


    def SerialOpen(self, GUI):
        try:  #korisitmo try za svaku slučaj ako je več otovoren neki serial com port
            self.ser.is_open
        except:
            PORT = GUI.clicked_com.get()
            BAUD = GUI.clicked_bd.get()
            self.ser = serial.Serial() #inicijalzira obejt tipa serial, ali još ne otvara niti jedan port
            self.ser.baudrate = BAUD
            self.ser.port = PORT
            self.ser.timeout = 0.1 #100ms

        try:
            if self.ser.is_open:
                #ovdje je serial otvoren i nemamo problem
                self.ser.status = True
            else:
                PORT = GUI.clicked_com.get()
            BAUD = GUI.clicked_bd.get()
            self.ser = serial.Serial() #inicijalzira obejt tipa serial, ali još ne otvara niti jedan port
            self.ser.baudrate = BAUD
            self.ser.port = PORT
            self.ser.timeout = 0.1 #100ms
            self.ser.open()
            self.ser.status = True
        except:
            self.ser.status = False


    def SerialClose(self):
        try:
            self.ser.is_open
            self.ser.close()
            self.ser.status = False
        
        except:
            self.ser.status = False



    def SerialSync(self, gui):
        self.threading = True
        cnt = 0
        while(self.threading):
            try:
                #nas mikrokontoler će primati sync = "#?#\n"
                self.ser.write(gui.data.sync.encode())
                gui.conn.sync_status["text"] = "..Sync.."
                gui.conn.sync_status["fg" ] = "orange"
                gui.data.RowMsg = self.ser.readline()

                gui.data.DecodeMsg() #it DataMaster klase korisitmo funkciju decodemsg
               
               
                if gui.data.sync_ok in gui.data.msg[0]: #ako je istina to znači da je mikrokontroler uspješno primio i vratio poruku nazad
                #    if int(gui.data.msg[1]) > 0:
                #         pass
                #ovo ce sluzit ako cemo htjet ikad imat vise kanala
                    gui.conn.btn_start_stream["state"] = "active"
                    gui.conn.btn_add_chart["state"] = "active"
                    gui.conn.btn_remove_chart["state"] = "active"
                    gui.conn.save_check["state"] = "active"
                    gui.conn.sync_status["fg"] = "green"
                    gui.conn.sync_status["text"] = "OK"
                    gui.conn.ch_status["text"] = "1"  #za sad imamo jedan kanal
                    gui.data.SynchChannel = 1 #za sad imamo jedan kanal #ovo dvoje bi inace bilo int(gui.data.msg[1])
                    gui.data.GenChannels() #stvorit cemo listu od jednog kanala

                    gui.data.buildYdata()

                    self.threading = False
  
                print(gui.data.RowMsg)
                print("tu smo")

                if(self.threading == False):
                    break
            
            except Exception as e:
                print(e)
            cnt += 1

            if cnt > self.sync_cnt:
                cnt = 0
                gui.conn.sync_status["text"] = "Failed"
                gui.conn.sync_status["fg" ] = "red"
                time.sleep(0.5) #neki delay da vidimo crvenu obju
                if(self.threading == False):
                    break


    def SerialDataStream(self,gui):
        self.threading = True
        packet_size = 10 # 1 (header) + 4 (ecg) + 4 (timestamp) + 1 (footer)
    
        while self.threading:
            try:
                # Šaljemo znak za početak
                self.ser.write(gui.data.StartStream.encode())
            
            # Čitamo točno onoliko bajtova koliko je duga struktura na STM32
                raw_data = self.ser.read(packet_size)
            
                if len(raw_data) == packet_size:
                    # 'B' = unsigned char (1 byte)
                    # 'I' = unsigned int (4 bytes)
                    # < = little endian (kako STM32 sprema podatke)
                    unpacked = struct.unpack('<BI I B', raw_data)
                
                    header = unpacked[0]
                    ecg = unpacked[1]
                    timestamp = unpacked[2]
                    footer = unpacked[3]
                
                    if header == 0xAA and footer == 0x55:
                        print(f"ECG: {ecg}, Time: {timestamp}")
                        # Ovdje dodaj podatke u gui.data.YData za crtanje
                    else:
                        print("Pogrešan paket (Header/Footer mismatch)")
            
            except Exception as e:
                print(f"Greška u streamu: {e}")



if __name__ == "__main__":
    SerialControl()