from tkinter import*
from tkinter import messagebox
import threading

#potrebno za spremanje podatka
import os
from tkinter import filedialog



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
        self.drop_com = OptionMenu(self.frame, self.clicked_com, *self.serial.com_list, command = self.connect_ctrl) #Većina ovih funkcija ima oblik fun(root, user_defined_objekt, dodatni uvjeti)
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



    #razlog zašto ovdjet treba argument other je zato što OptionMenu prosleđuje trenutno odabratnu vrijednost Menu-a, pa nam trebaju i self i other
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
                self.conn = ConnGUI(self.root, self.serial, self.data)  #u ocom trenutku se povećava prozor koji imamo, u __init__ klase se poziva openGUIopen


                #u funkciju SerialSync šaljemo ComGui koji ima serial, datamaster i root objekte,  daemon samo zači da će Thread ako ima problem zatvoriti sve na silu
                self.serial.t1 = threading.Thread(target = self.serial.SerialSync, args = (self,), daemon = True)
                self.serial.t1.start()

            else:
                ErrorMsg = f"Failure to establih UART connection usgin self.clicked_com.get()"
                messagebox.showerror("showerror", ErrorMsg)    

        else:
            self.serial.threading = False 
            self.conn.save = False

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
        self.save = False

        self.frame = LabelFrame(root, text = "Connection Manager", padx = 5, pady = 5, bg = "white", width = 60)
        
        #Labela ..Sync.. će biti narandžasta sve dok se uC nije upario sa našom komunikacijom 
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


        #Gumb za postavljenje lokacije za spremanje podataka
        self.btn_save_location = Button(self.frame, text="Choose folder", width=10, state="disabled", command=self.ChooseSaveLocation, bg="white", fg = "yellow")
        
        #Naljepnica koja pokazuje trenutačno mjesto za spremanje podataka
        self.save_location_label = Label(self.frame, text="Save to: Current folder", bg="white", fg="gray", anchor="w", width=25)

        #IntVar je objekt koji mora postojat unutar Checkbutton-a koji će pamtit je li checkbutton stisnut ili nije
        self.save = False
        self.SaveVar = IntVar()
        self.save_check = Checkbutton(self.frame, text = "Save Data", variable = self.SaveVar, onvalue = 1, offvalue = 0, bg = "white", state="disabled", command = self.save_data)

        self.ConnGUIOpen()
        self.chartMaster = DisGUI(self.root, self.serial, self.data)
        # Automatically create one graph when ConnGUI is initialized
        self.chartMaster.AddSingleGraph()

    
    #ova funkcija će raditi slično što i publish()
    def ConnGUIOpen(self):

        self.root.geometry("1000x570")  # Adjusted for single graph display
        self.frame.grid(row = 0, column = 4,rowspan = 3, columnspan = 6, padx = 5, pady = 5)
        
        self.sync_label.grid(column=1, row=1)
        self.sync_status.grid(column=2, row=1)

        self.ch_label.grid(column = 1, row = 2)
        self.ch_status.grid(column = 2, row = 2, pady = self.pady)

        self.btn_start_stream.grid(column = 3, row = 1, padx = self.padx)
        self.btn_stop_stream.grid(column = 3, row = 2, padx = self.padx)

        self.save_check.grid(column = 4, row = 2, columnspan = 2)

        self.btn_save_location.grid(column=6, row=1, padx=5, pady=5)
        self.save_location_label.grid(column=6, row=2,columnspan = 2, padx=5, pady=5, sticky=W)


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

    def ChooseSaveLocation(self):
        #Otvara prozor za odabir gdje stavljamo podatke
        directory = filedialog.askdirectory(title="Choose Save Location")
        if directory:
            self.data.save_directory = directory

            self.data.FileNameFunc()
            short_path = os.path.basename(directory) if len(directory) > 25 else directory
            self.save_location_label["text"] = f"Save to: .../{short_path}"
            self.save_location_label["fg"] = "green"


    def UpdateChart(self):
        try:
            # Update BPM label
            bpm_label = self.chartMaster.bpm_value_label
            current_bpm = self.data.currBPM

            if(current_bpm <= 100 and current_bpm >= 60):
                bpm_label.config(text=str(self.data.currBPM), fg = "green")
            else:
                bpm_label.config(text=str(self.data.currBPM), fg = "red")

            # Clear and redraw the graph
            self.chartMaster.ax.clear()
            
            # Get the selected display function
            selected_function = self.chartMaster.display_mode.get()
            
            # Call the appropriate display function
            self.data.FunctionMaster[selected_function](self)
            
            self.chartMaster.ax.grid(color='blue', linestyle='-', linewidth=0.2)
            self.chartMaster.canvas.draw()
            
        except Exception as e:
            print(f"Error in the UpdateChart: {e}")
        
        if self.serial.threading:
            self.root.after(5, self.UpdateChart)


    def stop_stream(self):
        self.btn_start_stream["state"] = "active"
        self.btn_stop_stream["state"] = "disabled"
        try:
            self.serial.ser.write(self.data.StopStream.encode())
        except Exception as e:
            print(f"Greška pri slanju stop komande: {e}")
        self.serial.threading = False


    def save_data(self): #nakon što kliknemo checkbox odlazimo u ovu funkciju
        if self.save:
            self.save = False
        else:
            self.save = True



class DisGUI():
    def __init__(self, root, serial, data):
        self.root = root
        self.serial = serial
        self.data = data

        # Single graph frame
        self.frame = None
        self.fig = None
        self.ax = None
        self.canvas = None
        self.bpm_value_label = None
        self.display_mode = None

    def AddSingleGraph(self):
        # Create main frame for the single graph
        self.frame = LabelFrame(self.root, text="ECG Monitor", padx=5, pady=5, bg="white")
        self.frame.grid(padx=5, column=0, row=4, columnspan=9, sticky=NW)

        # Create control frame for BPM display and function selector
        control_frame = LabelFrame(self.frame, pady=5, bg="white")
        control_frame.grid(column=0, row=0, padx=5, pady=5, sticky=N)

        # BPM label
        bpm_text_label = Label(control_frame, text="BPM: ", bg="white")
        bpm_text_label.grid(column=0, row=0, padx=5, pady=5)
        
        self.bpm_value_label = Label(control_frame, text="--", bg="white", fg="green", 
                                      font=("Arial", 14, "bold"))
        self.bpm_value_label.grid(column=1, row=0, padx=5, pady=5)

        # Display mode selector
        mode_label = Label(control_frame, text="Display Mode:", bg="white")
        mode_label.grid(column=0, row=1, padx=5, pady=5)
        
        self.display_mode = StringVar()
        display_functions = list(self.data.FunctionMaster.keys())
        self.display_mode.set(display_functions[0])  # Default to first option
        
        mode_dropdown = OptionMenu(control_frame, self.display_mode, *display_functions)
        mode_dropdown.config(width=12, bg="white")
        mode_dropdown.grid(column=1, row=1, padx=5, pady=5)

        # Create the matplotlib figure
        self.fig = plt.figure(figsize=(7, 5), dpi=80)
        self.ax = self.fig.add_subplot(111)
        
        # Create canvas
        self.canvas = FigureCanvasTkAgg(self.fig, master=self.frame)
        self.canvas.get_tk_widget().grid(column=1, row=0, rowspan=17, columnspan=4, sticky=N)


if __name__ == "__main__":
    RootGUI()
    ComGui()
    ConnGUI()
    DisGUI()