from tkinter import*
from tkinter import messagebox
import threading


#treba pip install matplotlib
import matplotlib
matplotlib.use('TkAgg') # Or 'Agg' to ensure no windows pop up
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from functools import partial


class RootGUI:
    def __init__(self, serial, data):
        self.root = Tk(); #inicijalizacija glavnog root "Frame-a"
        self.root.title("Serijska Komunikacija")
        self.root.geometry("360x120")
        self.root.config(bg = "white") #background color
        self.serial = serial
        self.data = data
        self.root.protocol("WM_DELETE_WINDOW", self.close_window)

    def close_window(self):
        print("Gasim komunikaciju i zatvaram prozor...")
        
        self.serial.threading = False
        
        # Pošalji STOP komandu MCU-u
        try:
            if self.serial.ser.is_open:
                self.serial.ser.write(self.data.StopStream.encode())
        except:
            pass
        
        #Zatvori serijski port
        try:
            self.serial.SerialClose(self)
        except:
            pass
            
        #Na samom kraju ugasi GUI
        self.root.destroy()



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

            try:
                while len(self.conn.chartMaster.frames) > 0:
                    self.conn.kill_chart()
            except Exception as e:
                print(f"Failed while closing the connection {e}")

           
            self.serial.SerialClose(self)
            self.conn.ConnGUIClose()
            self.data.ClearData()


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
        self.btn_start_stream["state"] = "disabled"
        self.btn_stop_stream["state"] = "active"

        self.serial.t1 = threading.Thread(target = self.serial.SerialDataStream, args = (self,), daemon = True)
        self.serial.t1.start()




    def UpdateChart(self):
        try:

            for i in range(len(self.chartMaster.ControlFrames)):

                 #self.ControlFrames = [LabelFrame, Gumb za +, gumb za -, natpis BPM, broja za BPM]
            # The BPM label is at index 1 in our new ControlFrames list structure
            # Accessing the stored Label object
                bpm_label = self.chartMaster.ControlFrames[i][4] 
                current_bpm = self.data.currBPM

                if(current_bpm <= 100 and current_bpm >= 60):
                    bpm_label.config(text=str(self.data.currBPM), fg = "green")
                else:
                    bpm_label.config(text=str(self.data.currBPM), fg = "red")


            #myDisplayChannels = []
            for MyChannelOpt in range(len(self.chartMaster.ViewVar)):
                #prolazimo koz sve ViewVar-ove koje imamo i gledamo što je označeno na njima
                self.chartMaster.figs[MyChannelOpt][1].clear()
                for cnt, state in enumerate(self.chartMaster.ViewVar[MyChannelOpt]):
                    if state.get(): #ako je checkmark označen
                        MyChannel = self.chartMaster.OptionVar[MyChannelOpt][cnt].get()
                        #myDisplayChannels.append(MyChannel)
                        ChannelIndex = self.data.ChannelNum[MyChannel] #channelNum je dictionary
                        FuncName = self.chartMaster.FunVar[MyChannelOpt][cnt].get() 
                        
                        self.chart = self.chartMaster.figs[MyChannelOpt][1]
                        self.color = self.data.ChannelColor[MyChannel] #channelColor je dioctionary
                        self.y = self.data.YDisplay[ChannelIndex]
                        self.x = self.data.XDisplay
                        self.data.FunctionMaster[FuncName](self) #pozivamo funkciju

                self.chartMaster.figs[MyChannelOpt][1].grid(color = 'blue', linestyle = '-', linewidth = 0.2)
                self.chartMaster.figs[MyChannelOpt][0].canvas.draw()
            #print(myDisplayChannels)
        except Exception as e:
            print(f"Error in the UpdateChart: {e}")
        
        if self.serial.threading:
            self.root.after(5,self.UpdateChart) #ovo je funkcija od Tkinter-a, koja piziva sam sama sebe svakih 40ms




    def stop_stream(self):
        self.btn_start_stream["state"] = "active"
        self.btn_stop_stream["state"] = "disabled"
        try:
            self.serial.ser.write(self.data.StopStream.encode())
        except Exception as e:
            print(f"Greška pri slanju stop komande: {e}")
        self.serial.threading = False
        



    def new_chart(self):
        self.chartMaster.AddChannelMaster()

    def remove_chart(self):
        try: 
            if len(self.chartMaster.frames) > 0:
                totalFrame = len(self.chartMaster.frames) - 1
                self.chartMaster.frames[totalFrame].destroy()
                self.chartMaster.frames.pop() #zadnji element brisemo
                self.chartMaster.figs.pop()
                self.chartMaster.ControlFrames[totalFrame][0].destroy() #na nultoj lokaicji je 
                self.chartMaster.ControlFrames.pop()

                #na nultoj lokaciji u ChannelFrameu se nalazi LabelFrame za kanale i funkcije grafa
                self.chartMaster.ChannelFrame[totalFrame][0].destroy()  

                self.chartMaster.ChannelFrame.pop()
                self.chartMaster.ViewVar.pop()
                self.chartMaster.OptionVar.pop()
                self.chartMaster.FunVar.pop()


                self.chartMaster.AdjustRootFrame()
        except:
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


        self.ControlFrames = [] #ovdje će se nalazit gumbovi i labelFrame za + - kod svakog grafa


        self.ChannelFrame = [] # [[LabelFrame, index_Of_LabelFrame]   ]
        self.ViewVar = []
        self.OptionVar = []
        self.FunVar = []


    def AddChannelMaster(self): #ova funkcija će stvarat nove framove
        self.AddMasterFrame()
        self.AdjustRootFrame() #svaki put trebamo promijenit veličinu Root Frame-a
        self.AddGraph()
        self.AddChannelFrame()
        self.AddBtnFrame()

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

        self.figs[self.totalframes].append(FigureCanvasTkAgg(self.figs[self.totalframes][0], master = self.frames[self.totalframes]))

        #dodajemo ga u grid
        #rowspan je toliki za dodavnje više kanala odjednom, a column span je tu jer dio će zauzimat graf, a dio zauzima frame od channel managera
        self.figs[self.totalframes][2].get_tk_widget().grid(column = 1, row = 0, rowspan = 17, columnspan = 4, sticky = N)




    def AddBtnFrame(self):



        btnH = 2
        btnW = 4

        self.ControlFrames.append([])
        #na nulto mjesto u listi dodajemo Frame za naše gumbove
        self.ControlFrames[self.totalframes].append(LabelFrame(self.frames[self.totalframes], pady = 5, bg = "white"))
        self.ControlFrames[self.totalframes][0].grid(column = 0, row = 0, padx = 5, pady = 5, sticky = N)
        #Na mjestu self.totalframes se nalazi naš frame za gumb, na nultoj lokaciji se nalazi LabelFrame  (pravi objekt za taj frame), i njega smo stavili na grid
        #u listu dodajemo gumb  List = [LabelFrame, gumb]
        self.ControlFrames[self.totalframes].append(Button(self.ControlFrames[self.totalframes][0], text = "+", bg = "white", width = btnW, height = btnH, command = partial(self.AddChannel, self.ChannelFrame[self.totalframes])))
        self.ControlFrames[self.totalframes][1].grid(column = 0, row = 0, padx = 5, pady = 5)


        # Label to show "BPM:" text
       # self.bpm_text_label = Label(self.ControlFrames[self.totalframes][0], text="BPM:", bg="white", font=("Arial", 10, "bold"))
       # self.bpm_text_label.grid(column=0, row=4, pady=2)

        # The actual BPM value label (stored at index 3 in ControlFrames list)
       # self.bpm_value_label = Label(self.ControlFrames[self.totalframes][0], text="--", bg="white", fg="red", font=("Arial", 14, "bold"))
       # self.bpm_value_label.grid(column=1, row=1, pady=2)
       # self.ControlFrames[self.totalframes].append(self.bpm_value_label) # Store reference at index 3

        self.ControlFrames[self.totalframes].append(Button(self.ControlFrames[self.totalframes][0], text = "-", bg = "white", width = btnW, height = btnH, command = partial(self.DeleteChannel, self.ChannelFrame[self.totalframes])))
        self.ControlFrames[self.totalframes][2].grid(column = 1, row = 0, padx = 5, pady = 5)

        #sad nam contorlFrames lista sadri [LabelFrame, gumb (+), gumb (-)]


        #koristimo partial.function(args) jer sa "normalnom sintaksom", command = self.function, nebi mogli posalti argumente

        self.ControlFrames[self.totalframes].append(Label(self.ControlFrames[self.totalframes][0], text = "BPM: ", bg = "white"))
        self.ControlFrames[self.totalframes][3].grid(column = 0, row = 1, padx = 5, pady = 5)
        self.ControlFrames[self.totalframes].append(Label(self.ControlFrames[self.totalframes][0], text = " -- ", bg = "white", fg = "green"))
        self.ControlFrames[self.totalframes][4].grid(column = 1, row = 1, padx = 5, pady = 5)

        #Kad bi imali više kanala tu bi mogli imat [bpm1,bpm2,bpm3,bpm4,...]



    def AddChannelFrame(self):
        self.ChannelFrame.append([])
        self.ViewVar.append([])
        self.OptionVar.append([])
        self.FunVar.append([])

        #ChannelFrame = [[LabelFrame1, index1], [labelFrame2, index2],...]
        self.ChannelFrame[self.totalframes].append(LabelFrame(self.frames[self.totalframes], pady = 5, bg = "white"))
        self.ChannelFrame[self.totalframes].append(self.totalframes)
        #moramo dodati novi Frame na grid
        #prvi row obuhvaća gumbove + i -, ostalih 16 mjesta odlazi na ovaj frame
        self.ChannelFrame[self.totalframes][0].grid(column = 0, row = 1, padx = 5, pady = 5, rowspan = 16, sticky = N)

        self.AddChannel(self.ChannelFrame[self.totalframes]) #ova funkcija će stvarat male framove na mjesti za svaki kanal


    def AddChannel(self, ChannelFrame):

        #winfo_children gleda koliko widgeta sadrži naš LabelFrame 
        if len(ChannelFrame[0].winfo_children()) < 4:
            NewFrameChannel = LabelFrame(ChannelFrame[0], bg = "white") #LabelFrame(root, args..)


        #Ako zamislimo da smo imali npr. 3 frame-a za kanale i gore smo kreirali novi NewFrameChannel tada će .winfo_children izbaciti van 4
        #A mi zelimo stavit okvir na mjesto 3
        NewFrameChannel.grid(column = 0, row = len(ChannelFrame[0].winfo_children()) - 1)


        #ChannelFrame = [[LabelFrame za kanal maanger 1, index1],.. ]
        self.ViewVar[ChannelFrame[1]].append(IntVar())
        
        #Ovaj gumb će omoguciti ili nece omoguciti da vidimo graf tog kanala
        #ViewVar = [[ch1, ch2, ch3,.....],[],[]],....]
        Ch_btn = Checkbutton(NewFrameChannel, variable=self.ViewVar[ChannelFrame[1]][len(self.ViewVar[ChannelFrame[1]])-1],onvalue=1, offvalue=0, bg="white")
        Ch_btn.grid(row = 0, column = 0, padx = 1) #za svaki checkbox radimo novi frame pa ovdje nije potrebno dirat column  i row 
        self.ChannelOption(NewFrameChannel, ChannelFrame[1])
        self.ChannelFunc(NewFrameChannel, ChannelFrame[1])




    #frame je mali okvir stvoren u funkciji AddChannel (NewFrameChannel), ChannelFrameNumber je samo ChannelFrame[1] da znam na koji se graf fokusiramo

    def ChannelOption(self, frame, ChannelFrameNumber):
        
        #ova varijabla će pamtiti što je korisnik odabrao u dropdownu
        self.OptionVar[ChannelFrameNumber].append(StringVar())

        bds = self.data.Channels #Nama ce ovo bit jedan za sad jer imamo jedan kanal i u sinkronizaciji stm32 nije navedeno nista u vezi broja kanala

        #ova linija pronalazi malo prije postavljeni StringVar i na njegovo pocetnto mjesto stavlja prvi dostupni kanal
        self.OptionVar[ChannelFrameNumber][len(self.OptionVar[ChannelFrameNumber]) - 1].set(bds[0])

        drop_ch = OptionMenu(frame, self.OptionVar[ChannelFrameNumber][len(self.OptionVar[ChannelFrameNumber]) - 1], *bds)
        drop_ch.config(width = 5)
        drop_ch.grid(row = 0, column = 1, padx = 1)

    
    #Gotovo pa ista funkcio kao i ChannelOption() samo što ovdje odabiremo funkcije a ne kanale
    def ChannelFunc(self, frame, ChannelFrameNumber):
        
        #ova varijabla će pamtiti što je korisnik odabrao u dropdownu
        self.FunVar[ChannelFrameNumber].append(StringVar())

        bds = [func for func in self.data.FunctionMaster.keys()] #Nama ce ovo bit jedan za sad jer imamo jedan kanal i u sinkronizaciji stm32 nije navedeno nista u vezi broja kanala

        #ova linija pronalazi malo prije postavljeni StringVar i na njegovo pocetnto mjesto stavlja prvi dostupni kanal
        self.FunVar[ChannelFrameNumber][len(self.OptionVar[ChannelFrameNumber]) - 1].set(bds[0])

        drop_ch = OptionMenu(frame, self.FunVar[ChannelFrameNumber][len(self.FunVar[ChannelFrameNumber]) - 1], *bds)
        drop_ch.config(width = 5)
        drop_ch.grid(row = 0, column = 2, padx = 1)


    #Ova funkcija će micat male kanale za pojedine grafove
    def DeleteChannel(self, ChannelFrame):
        if len(ChannelFrame[0].winfo_children()) > 1: #ako imamo više od jednog kanala, uvijek bi tjeli iamti barem jedan kanal
            ChannelFrame[0].winfo_children()[len(ChannelFrame[0].winfo_children()) - 1].destroy()
            #moramo se sjetit da winfo_children šalje widget vezan uz neki frame

            self.ViewVar[ChannelFrame[1]].pop()
            self.FunVar[ChannelFrame[1]].pop()
            self.OptionVar[ChannelFrame[1]].pop()


if __name__ == "__main__":
    RootGUI() #Ova sintaksa govori ubiti da će se Prozor otvoriti samo u main, a ne svaki put kada importamo file bilo gdje drugdje
    ComGui()
    ConnGUI()
    DisGUI()
