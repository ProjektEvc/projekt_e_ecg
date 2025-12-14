from Gui_Master import RootGUI, ComGui
from Serial_Com_ctrl import SerialControl


MySerial = SerialControl()
RootMaster = RootGUI()

ComMaster = ComGui(RootMaster.root, MySerial)

RootMaster.root.mainloop()