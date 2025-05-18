import Main
from tkinter import *
from tkinter import ttk

root = Tk()
root.title("Wallpaper Changer")
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
ttk.Button(root, text="Change Wallpaper", command=Main.pick_and_change).pack()
root.mainloop()

