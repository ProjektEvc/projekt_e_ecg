from tkinter import*
from tkinter import messagebox
import threading


#treba pip install matplotlib
import matplotlib.pyplot as plt
import matplotlib.backends.backend_tkagg as FigureCanvasAgg


class RootGUI:
    def __init__(self):
        self.root = Tk(); #inicijalizacija glavnog root "Frame-a"
        self.root.title("Serijska Komunikacija")
        self.root.geometry("360x120")
        self.root.config(bg = "white") #background color


#svaki od def BaudOptionMenu, ComOptionMenu,.... prvo trebaju napraviti objekte, a tek onda ih trebamo publish-at
class ComGui():  #Klasa za komunikaciju sa uC
    def __init__(self, root, serial, data):
        self.root = root
        self.serial = serial
        self.data = data
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



                #pokazi manager za kanale   
                self.conn = ConnGUI(self.root, self.serial, self.data)  


                #u funkciju SerialSync šaljemo ComGui koji ima serial, datamaster i root objekte,  daemon samo zači da će Thread ako ima problem zatvoriti sve na silu
                self.serial.t1 = threading.Thread(target = self.serial.SerialSync, args = (self,), daemon = True)
                self.serial.t1.start()

            else:
                ErrorMsg = f"Failure to establih UART connection usgin seld.clicked_com.get()"
                messagebox.showerror("showerror", ErrorMsg)    

        else:
            self.serial.threading = False 

            self.conn.ConnGUIClose()
            self.data.ClearData()
            #start closing the connection
            self.serial.SerialClose()
            InfoMsg = f"UART connection is now closed"
            messagebox.showwarning("showinfo", InfoMsg)
            self.btn_connect["text"] = "Connect"
            self.btn_refresh["state"] = "active"
            self.drop_bds["state"] = "active"
            self.drop_com["state"] = "active"



class ConnGUI():
    def __init__(self,root,serial, data):
        self.root = root #root je glavni root
        self.serial = serial #serial je serial iz Serial_Com_ctrl, u main programu šaljemo MySerial = SerialControl() u ComGui, a ComGui šalje serial u ConGui
        self.data = data
        self.frame = LabelFrame(root, text = "Connection Manager", padx = 5, pady = 5, bg = "white", width = 60)
        
        #Labela ..Sync.. će biti narančasta sve dok se uC nije upario sa našom komunikacijom 
        self.sync_label = Label(self.frame, text="Sync Status: ", bg="white", width=15, anchor="w")
        self.sync_status = Label(self.frame, text="..Sync..", bg="white", fg="orange", width=5)


        #Ovdje će biti vidljivo sa koliko kanala mozemo promatrat signal
        self.ch_label = Label(self.frame, text = "Active channels: ", bg = "white", width = 15, anchor = "w")
        self.ch_status = Label(self.frame, text = "...", bg = "white", fg = "orange", width = 5)
    
        self.padx = 20
        self.pady = 15

        #ovaj gumb će pokrenuti stream, gumb je isključen sve dok nismo povezani sa uc 
        self.btn_start_stream = Button(self.frame, text = "Start", state = "disabled", width = 5, command = self.start_stream)

        #ovaj gumb pokreće komandu koja zasutavlja stream, gumb je isključen ako stream nije uključen
        self.btn_stop_stream = Button(self.frame, text = "Stop", state = "disabled", width = 5, command = self.stop_stream)

        #gumbovi za postavljanje, odnosno brisanje grafova
        self.btn_add_chart = Button(self.frame, text = "+", state = "disabled", width = 5, bg = "white", fg = "#098577", command = self.new_chart)
        self.btn_remove_chart = Button(self.frame, text = "-", state = "disabled", width = 5, bg = "white", fg = "#CC252C", command = self.remove_chart)

        #IntVar je objekt koji mora postojat unutar Checkbutton-a koji će pamtit je li checkbutton stisnut ili nije
        self.save = False
        self.SaveVar = IntVar()
        self.save_check = Checkbutton(self.frame, text = "Save Data", variable = self.SaveVar, onvalue = 1, offvalue = 0, bg = "white", state="disabled", command = self.save_data)

        #Ovdje cemo implementirat funkciju tako da sami mozemo birat hocemo li primati ili slat podatke i od kuda cemo uzimat te podatke

        


        self.ConnGUIOpen()
        self.chartMaster = DisGUI(self.root, self.serial, self.data)

    
    #ova funkcija će raditi slično što i publish()
    def ConnGUIOpen(self):

        self.root.geometry("800x120")
        self.frame.grid(row = 0, column = 4,rowspan = 3, columnspan = 5, padx = 5, pady = 5)
        
        self.sync_label.grid(column=1, row=1)
        self.sync_status.grid(column=2, row=1)

        self.ch_label.grid(column = 1, row = 2)
        self.ch_status.grid(column = 2, row = 2, pady = self.pady)

        self.btn_start_stream.grid(column = 3, row = 1, padx = self.padx)
        self.btn_stop_stream.grid(column = 3, row = 2, padx = self.padx)

        self.btn_add_chart.grid(column = 4, row = 1, padx = self.padx)
        self.btn_remove_chart.grid(column = 5, row = 1, padx = self.padx)

        self.save_check.grid(column = 4, row = 2, columnspan = 2)


    def ConnGUIClose(self):
        #ova funckija je potrebna kako nebi dobili dupilkate gumbova i labela

        #ovdje prolazimo kroz petlju koja sadrži svaki "widget", tj. dijecu unutar ConnGUI okvira
        for widget in self.frame.winfo_children():
            widget.destroy()

        #uglavnom bi ova funkcija sama po sebi trebala zatvoriti sve widget-e, ali gornja petlja je tu radi sigurnosti
        self.frame.destroy()
        #vracamo se na staru veličinu prozora
        self.root.geometry("360x120")

    def start_stream(self):
        pass


    def stop_stream(self):
        pass

    def new_chart(self):
        self.chartMaster.AddChannelMaster()

    def remove_chart(self):
        pass

    def save_data(self):
        pass



class DisGUI():
    def __init__(self, root, serial, data):
        self.root = root
        self.serial = serial
        self.data = data

        #ova lista će sadržavat sve frame-ove koji se odnose na display dio GUI-a
        self.frames = []
        self.framesCol = 0
        self.framesRow = 4  #prva tri reda se koriste za connGui i ComGui
        self.totalframes = 0 #prati broj frame-ova koje imamo


        self.figs = [] #data

    def AddChannelMaster(self): #ova funkcija će stvarat nove framove
        self.AddMasterFrame()
        self.AdjustRootFrame() #svaki put trebamo promijenit veličinu Root Frame-a


    def AddMasterFrame(self):
        self.frames.append(LabelFrame(self.root, text = f"Display Manager - {len(self.frames)+1}", padx = 5, pady = 5, bg = "white"))
        self.totalframes = len(self.frames) - 1

        if self.totalframes % 2 == 0:
            self.framesCol = 0
        else:
            self.framesCol = 9 #zbroj columna od Conn i Com gui-a

        self.framesRow = 4 + 4 * int(self.totalframes/2)
        #Dodajemo novo addani frame (novi indeks = len(svih frameova))
        self.frames[self.totalframes].grid(padx = 5, column = self.framesCol, row = self.framesRow, columnspan = 9, sticky = NW) 
        #Sticky znači da će se nas widget(u ovom slučaju frame) "pokušat zalijepit" u NorthWest stranu



    #povecanja/smanjivanje root-a kod dodavanja/micanja grafa
    def AdjustRootFrame(self):
        self.totalframes = len(self.frames) -1 

        if self.totalframes > 0:
            RootW = 800*2  #Širina Root-a

        else:
            RootW = 800


        if self.totalframes+1 == 0:
            RootH = 120

        else:
            RootH = 120 + 400 * (int(self.totalframes/2) +1)
        self.root.geometry(f"{RootW}x{RootH}")
        

    def AddGraph(self):
        self.figs.append([])
        #figs je lista lista
        #na novi graf čemo appendat listu koja sdrži podatke za taj određeni graf
        # figs[i] =  [ figure (graf) ] lista na mjestu i
        self.figs[self.totalframes].append(plt.figure(figsize = (7,5), dpi = 80))

        # na mjestu 0 u fig[i] listi dodajemo subplot
        self.figs[self.totalframes].append(self.figs[self.totalframes][0].add_subplot(111))

        self.figs[self.totalframes].append(FigureCanvasAgg(self.figs[self.totalframes][0], master = self.frames[self.totalframes]))

        #dodajemo ga u grid
        self.figs[self.totalframes][2].get_tk_widget().grid(column = 1, row = 0, columnspan = 17, sticky = N)

if __name__ == "__main__":
    RootGUI() #Ova sintaksa govori ubiti da će se Prozor otvoriti samo u main, a ne svaki put kada importamo file bilo gdje drugdje
    ComGui()
    ConnGUI()
    DisGUI()
