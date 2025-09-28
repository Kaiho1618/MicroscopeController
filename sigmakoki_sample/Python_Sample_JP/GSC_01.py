# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import serial
import tkinter as tk
import time
import sys

ser = None

def click_Comm():
    global ser
    ser = serial.Serial('COM3')
    ser.baudrate=9600
    ser.BYTESIZES=serial.EIGHTBITS
    ser.PARITIES=serial.PARITY_NONE
    ser.STOPBITS=serial.STOPBITS_ONE
    ser.timeout=5
    ser.rtscts=True
    
def click_Origin():
    global ser
    if ser == None:
        return
    #rtn = var.get()
    #if rtn == 0:
    #    axis = 'W'
    #else:
    #    axis = str(rtn)
    axis = str(1)
    wdata = 'H:' + axis + '\r\n' 
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    
def click_MoveRel():
    global ser
    if ser == None:
        return
    sss = txt1.get()
    print(sss)
    if sss.isdigit() == False:
        return
    value = int(sss)
    if value > 0:
        direction = '+'
    else:
        direction = '-'
    #rtn = var.get()
    #if rtn == 0:
    #    axis = 'W'
    #    wdata = 'M:' + axis + direction +'P' + sss + direction +'P' + sss + '\r\n'
    #else:
    #    axis = str(rtn)
    axis = str(1)
    wdata = 'M:'+ axis + direction + 'P' + sss + '\r\n'
    print(wdata)   
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    
    time.sleep(1)
    wdata = 'G:\r\n'
    print(wdata)
    ser.write(wdata.encode())
    rtn = ser.readline()
    print(rtn)
    
def click_MoveAbs():
    global ser
    if ser == None:
        return
    sss = txt2.get()
    print(sss)
    if sss.isdigit() == False:
        return
    value = int(sss)
    if value > 0:
        direction = '+'
    else:
        direction = '-'
    rtn = var.get()
    if rtn == 0:
        axis = 'W'
        wdata = 'A:' + axis + direction +'P' + sss + direction +'P' + sss + '\r\n'
    else:
        axis = str(rtn)
        wdata = 'A:'+ axis + direction + 'P' + sss + '\r\n'
    print(wdata)   
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)

    time.sleep(1)
    wdata = 'G:\r\n'
    print(wdata)
    ser.write(wdata.encode())
    rtn = ser.readline()
    print(rtn)       
    
def click_Speed():
    global ser
    if ser == None:
        return
    slow = txtSlow.get()
    print(slow)
    if slow.isdigit() == False:
        return  
    fast = txtFast.get()
    print(fast)
    if fast.isdigit() == False:
        return      
    rate = txtRate.get()
    print(rate)
    if rate.isdigit() == False:
        return      
    #rtn = var.get()  
    #if rtn == 0:
    #    axis = 'W'
    #    wdata = 'D:' + axis + 'S' + slow + 'F' + fast + 'R' + rate + 'S' + slow + 'F' + fast + 'R' + rate + '\r\n'
    #else:
    #    axis = str(rtn)
    axis = str(1)
    wdata = 'D:' + axis + 'S' + slow + 'F' + fast + 'R' + rate + '\r\n'
    print(wdata)   
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)           
   
def click_JOG():
    global ser
    if ser == None:
        return
    rtn2 = var2.get()
    if rtn2 == 1:
        direction = '+'
    else:
        direction = '-'
    #rtn = var.get()
    #if rtn == 0:
    #    axis = 'W'
    #    wdata = 'J:' + axis + direction + direction + '\r\n' 
    #else:
    #    axis = str(rtn)
    axis = str(1)       
    wdata = 'J:' + axis + direction + '\r\n' 
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
 
    time.sleep(1)
    wdata = 'G:\r\n'
    print(wdata)
    ser.write(wdata.encode())
    rtn = ser.readline()
    print(rtn)
    
def click_Stop():
    global ser
    if ser == None:
        return
    #rtn = var.get()
    #if rtn == 0:
    #    axis = 'W'
    #else:
    #    axis = str(rtn)
    axis = str(1)
    wdata = 'L:' + axis + '\r\n' 
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)

def click_Status():
    global ser
    if ser == None:
        return
    wdata = 'Q:' + '\r\n' 
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    
    #rtn = var.get()
    #if rtn == 0:
    #    sss = rdata[0:21]
    #elif rtn == 1:
    sss = rdata[0:10]
    #else:
    #    sss = rdata[12:21] 
    lbl['text'] = (sss)

def click_Exit():
    ser.close()
    time.sleep(1)
    root.destroy()
    sys.exit()


root = tk.Tk()
root.title("SIGMA-KOKI Python Sample for GSC-01")
root.geometry("480x420")
#root.mainloop()

# Setting button
button1 = tk.Button(root, text='Connect  ', command=click_Comm)
button2 = tk.Button(root, text='Origin   ', command=click_Origin)
button3 = tk.Button(root, text='Move(Rel)', command=click_MoveRel)
button4 = tk.Button(root, text='Move(Abs)', command=click_MoveAbs, state = "disable")
button5 = tk.Button(root, text='Speed    ', command=click_Speed)
button6 = tk.Button(root, text='JOG      ', command=click_JOG)
button7 = tk.Button(root, text='Stop     ', command=click_Stop)
button8 = tk.Button(root, text='Position ', command=click_Status)
button9 = tk.Button(root, text='Exit     ', command=click_Exit)
 
# Placing botton
button1.place(x=100, y=10)
button2.place(x=100, y=80)
button3.place(x=100, y=120)
button4.place(x=100, y=160)
button5.place(x=100, y=200)
button6.place(x=100, y=240)
button7.place(x=100, y=280)
button8.place(x=100, y=320)
button9.place(x=100, y=360)
 
# Placing label
lbl = tk.Label(text='---------')
lbSlow = tk.Label(text='S')
lbFast = tk.Label(text='F')
lbRate = tk.Label(text='R')
lbl.place(x=190, y=320)
lbSlow.place(x=170, y=200)
lbFast.place(x=260, y=200)
lbRate.place(x=350, y=200)

# Placing textbox
txt1 = tk.Entry(width=10)
txt2 = tk.Entry(width=10, state = "disable")
txtSlow = tk.Entry(width=10)
txtFast = tk.Entry(width=10)
txtRate = tk.Entry(width=10)

txt1.place(x=180, y=120)
txt2.place(x=180, y=160)
txtSlow.place(x=180, y=200)
txtFast.place(x=270, y=200)
txtRate.place(x=360, y=200)

txt1.insert(tk.END,"100")
txt2.insert(tk.END,"0")
txtSlow.insert(tk.END,"2000")
txtFast.insert(tk.END,"20000")
txtRate.insert(tk.END,"200")

#Placing radiobutton
var = tk.IntVar()
rdo1 = tk.Radiobutton(value=1, variable=var, text='Axis1')
rdo2 = tk.Radiobutton(value=2, variable=var, text='Axis2', state= "disable")
rdo3 = tk.Radiobutton(value=0, variable=var, text='All', state = "disable")
rdo1.place(x=100, y=50)
rdo2.place(x=160, y=50)
rdo3.place(x=220, y=50)
var.set(1)

var2 = tk.IntVar()
rdoP = tk.Radiobutton(value=1, variable=var2, text='+')
rdoM = tk.Radiobutton(value=2, variable=var2, text='-')
rdoP.place(x=160, y=240)
rdoM.place(x=200, y=240)
var2.set(1)

root.mainloop()







 

 
