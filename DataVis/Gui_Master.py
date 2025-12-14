from tkinter import*
from tkinter import messagebox


class RootGUI:
    def __init__(self):
        self.root = Tk(); #inicijalizacija glavnog root "Frame-a"
        self.root.title("Serijska Komunikacija")
        self.root.geometry("360x120")
        self.root.config(bg = "white") #background color


#svaki od def BaudOptionMenu, ComOptionMenu,.... prvo trebaju napraviti objekte, a tek onda ih trebamo publish-at
class ComGui():  #Klasa za komunikaciju sa uC
    def __init__(self, root, serial):
        self.root = root
        self.serial = serial
        self.frame = LabelFrame(root, text= "Com Manager", padx = 5, pady = 5, bg = "white")
        self.label_com = Label(self.frame, text = "Available Port(s): ", bg = "white", width = 15, anchor = "w") 
        #label com je samo random ime, anchor = west, znači da će tekst biti na lijevoj strani
        self.label_bd = Label(self.frame, text = "Baude Rate: ", bg = "white", width = 15, anchor = "w")
        self.ComOptionMenu()
        self.BaudOptionMenu()

        self.btn_refresh = Button(self.frame, text = "Refresh", width = 10, command = self.com_refresh)
        self.btn_connect = Button(self.frame, text = "Connect", width = 10, state = "disabled", command = self.serial_connect)

        self.padx = 20
        self.pady = 5
        self.publish()

    def ComOptionMenu(self):
        self.serial.getCOMList() 
        self.clicked_com = StringVar() #Nije običan string, ovo je objekt "Stringa" nad kojim je moguće proučavat izmjene
        self.clicked_com.set(self.serial.com_list[0])
        self.drop_com = OptionMenu(self.frame, self.clicked_com, *self.serial.com_list, command = self.connect_ctrl) #Večina ovih funkcija ima oblik fun(root, user_defined_objekt, dodatni uvjeti)
        # * kod coms označava cijelu listu
        self.drop_com.config(width= 10)

    def BaudOptionMenu(self):
        bds = ["-", "300", "600", "1200", "2400", "4800", "9600", "14400", "19200", "28800", "38400", "56000", "57600","115200"]
        self.clicked_bd = StringVar()
        self.clicked_bd.set(bds[0]) #inicijalna vrijednost
        self.drop_bds = OptionMenu(self.frame, self.clicked_bd, *bds, command = self.connect_ctrl)
        self.drop_bds.config(width = 10)



    def publish(self):
        #prvo trebamo napraviti grid
        self.frame.grid(row = 0, column = 0, rowspan = 3, columnspan= 3, padx = 5, pady = 5)
        #onda dodajemo jedan po jedan widget (bilo label, gumb,...) 
        self.label_com.grid(column = 1, row = 2)
        self.drop_com.grid(column = 2, row = 2, padx = self.padx, pady=self.pady)
        self.label_bd.grid(column = 1, row = 3)
        self.drop_bds.grid(column = 2, row = 3)
        self.btn_refresh.grid(column = 3, row = 2)
        self.btn_connect.grid(column = 3, row = 3)



    #razlog zašto ovdjet treba argument other je zato što OptionMenu prosljeđuje trenutno odabratnu vrijednost Menu-a, pa nam trebaju i self i other
    def connect_ctrl(self, other):
        print("Connect cntrl")
        if "-" in self.clicked_com.get() or "-" in self.clicked_bd.get():
            self.btn_connect["state"] = "disabled"
        else:
            self.btn_connect["state"] = "active"
   
   
    def com_refresh(self):
       # self.serial.getCOMList() #u Serial_Com_ctrl klasi će napuniti listu ports sa svim mogucim portovima
       # print(self.serial.com_list)
       self.drop_com.destroy()
       self.ComOptionMenu()
       self.drop_com.grid(column = 2, row = 2, padx = self.padx, pady=self.pady)
       logic = []
       self.connect_ctrl(logic)
       

    def serial_connect(self):
        print("com connect")

        if self.btn_connect["text"] in "Connect":
            #start the connection
            self.serial.SerialOpen(self)
            if self.serial.ser.status:
                self.btn_connect["text"] = "Disconnect"
                self.btn_refresh["state"] = "disable"
                self.drop_bds["state"] = "disable"
                self.drop_com["state"] = "disable"
                InfoMsg = f"Successful in establishing the connection to UART"
                messagebox.showinfo("showinfo", InfoMsg)    


            else:
                ErrorMsg = f"Failure to establih UART connection usgin seld.clicked_com.get()"
                messagebox.showerror("showerror", ErrorMsg)    

        else:
            #start closing the connection
            self.serial.SerialClose()
            InfoMsg = f"UART connection is now closed"
            messagebox.showwarning("showinfo", InfoMsg)
            self.btn_connect["text"] = "Disconnect"
            self.btn_refresh["state"] = "active"
            self.drop_bds["state"] = "active"
            self.drop_com["state"] = "active"


if __name__ == "__main__":
    RootGUI() #Ova sintaksa govori ubiti da će se Prozor otvoriti samo u main, a ne svaki put kada importamo file bilo gdje drugdje
    ComGui()
