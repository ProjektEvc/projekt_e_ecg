from Gui_Master import RootGUI, ComGui
from Serial_Com_ctrl import SerialControl
from Data_Com_ctrl import DataMaster


MySerial = SerialControl()
MyData = DataMaster()
RootMaster = RootGUI()

ComMaster = ComGui(RootMaster.root, MySerial, MyData)

RootMaster.root.mainloop()