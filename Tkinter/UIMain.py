import Main
from tkinter import *
from tkinter import ttk

root = Tk()
root.title("Wallpaper Changer")
root.geometry("{0}x{1}+0+0".format(root.winfo_screenwidth(), root.winfo_screenheight()))
frame = ttk.Frame(root, padding=10)
frame.grid()
#ttk.Label(frame, text="Test").grid(column=0, row=0)
root.mainloop()