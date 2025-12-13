from Gui_Master import RootGUI, ComGui

RootMaster = RootGUI()

ComMaster = ComGui(RootMaster.root)

RootMaster.root.mainloop()