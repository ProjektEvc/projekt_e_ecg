

class DataMaster():
    def __init__(self):
        self.sync = "#?#\n" #ovu poruku šaljemo uc kao zahtev za povezivanje
        self.sync_ok = "!" #očekujemo ! ako je uc povezan
        self.StartStream = "#A#\n" #šaljemo za početak streama
        self.StopStream = "#S#\n" #završetak streama
        self.SynchChannel = 0 #broj kanala koji dobivamo sa mikrokontrolera, necemo koristit za sad
        self.msg = [] 


        #liste sa kojima ćemo crtat grafove, imat će podatke i vrijeme
        self.XData = []
        self.YData = []


        self.FunctionMaster = ["RowData", "Voltage Display"]


    def DecodeMsg(self):
        temp = self.RowMsg.decode('utf8') #podatak koji primimo na COM port trebamo dekodirat sa pythonovom funkcijom sa utf8 standrdom
        if len(temp) > 0:
            print("Tu smo")
            self.msg = temp.split(",")
            print(f"split msg: {self.msg}")


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