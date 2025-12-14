import serial.tools.list_ports

class SerialControl():
    def __init__(self):
        self.com_list = []


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


if __name__ == "__main__":
    SerialControl()