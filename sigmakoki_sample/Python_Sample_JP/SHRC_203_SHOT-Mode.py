# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import serial
import tkinter as tk
import numpy as np
import time
import sys

""" initial variable"""
ser = None
enable_axis_array = np.array([False,False,False])
rdata_array = np.array(['','','','','','',''])

def click_Comm():
    global ser
    global ComNumber
    ser = serial.Serial('COM28')
    ser.baudrate=38400
    ser.BYTESIZES=serial.EIGHTBITS
    ser.PARITIES=serial.PARITY_NONE
    ser.STOPBITS=serial.STOPBITS_ONE
    ser.timeout=5
    ser.rtscts=True
    
    # check state able to use Axis.
    for i in range(0,3,1):
            wdata = '!:' + str(i+1) + 'S' + '\r\n'
            print(wdata)
            ser.write(wdata.encode())
            rdata = ser.readline()
            rdata = rdata.decode("utf-8")
            rdata = rdata.replace("\r\n", "")
            print(rdata)
            if rdata == 'R':
              enable_axis_array[i] = True         # radio button active
            else:
              enable_axis_array[i] = False        # radio button non active
              
    # radio button set    
    for i in range(0,3,1):
        # If it = True then radio button will be active.
        if enable_axis_array[i] == True:
            if i == 0:                   # Axis1
                rdo1.config(state=tk.NORMAL)  
                var.set(1)
            if i == 1:                   # Axis2
                rdo2.config(state=tk.NORMAL)  
                var.set(2)
            if i == 2:                   # Axis3
                rdo3.config(state=tk.NORMAL)  
                var.set(3)
            print('Axis ' + str(i+1) + ' is allowed to use.')
        else:
            # radio button will be non active
            if i == 0:                   # Axis1
                rdo1.config(state=tk.DISABLED)     
            if i == 1:                   # Axis2
                rdo2.config(state=tk.DISABLED)   
            if i == 2:                   # Axis3
                rdo3.config(state=tk.DISABLED)   
            print('Axis ' + str(i+1) + ' is not allowed to use.')
                      
    if enable_axis_array[0] and enable_axis_array[1] and enable_axis_array[2]: #All Axis radio button
        rdo4.config(state=tk.NORMAL)  
        rdo4.select()
    else:
        rdo4.config(state=tk.DISABLED)   
    
def click_Origin():
    global ser
    if ser == None:
        return
    rtn = var.get()
    if rtn == 0:
        axis = 'W'
        wdata = 'H:'+ axis + '\r\n' 
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'H:'+ axis + '\r\n'
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
    if sss.lstrip("-").isdigit() == False:
        return
    value = int(sss)
    if value > 0:
        direction = '+'
    else:
        direction = '-'
    sss = sss.lstrip("-")
    rtn = var.get()
    if rtn == 0:
        axis = 'W'
        wdata = 'M:' + axis + direction + 'P' +  sss
        wdata = wdata + direction + 'P' + sss
        wdata = wdata + direction + 'P' + sss + '\r\n'
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
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
    if sss.lstrip("-").isdigit() == False:
        return
    value = int(sss)
    if value > 0:
        direction = '+'
    else:
        direction = '-'
    sss = sss.lstrip("-")
    rtn = var.get()
    if rtn == 0:
        axis = 'W'
        wdata = 'A:' + axis + direction + 'P' +  sss
        wdata = wdata + direction + 'P' + sss
        wdata = wdata + direction + 'P' + sss + '\r\n'     
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
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
    slow = str(txtSlow.get())
    print(slow)
    if slow.isdigit() == False:
        return  
    fast = str(txtFast.get())
    print(fast)
    if fast.isdigit() == False:
        return      
    rate = str(txtRate.get())
    print(rate)
    if rate.isdigit() == False:
        return      
    rtn = var.get()  
    if rtn == 0:
        axis = 'W'
        wdata = 'D:' + axis + 'S' +  slow
        wdata = wdata + 'F' + fast
        wdata = wdata + 'R' + rate
        wdata = wdata + 'S' + slow
        wdata = wdata + 'F' + fast
        wdata = wdata + 'R' + rate
        wdata = wdata + 'S' + slow
        wdata = wdata + 'F' + fast
        wdata = wdata + 'R' + rate + '\r\n'
        print(wdata)   
        ser.write(wdata.encode())
        rdata = ser.readline()
        print(rdata) 
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'D:'+ axis + 'S' + slow + 'F' +  fast + 'R' + rate + '\r\n'
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
    rtn = var.get()
    if rtn == 0:
         axis = 'W'
         wdata = 'J:' + axis + direction + direction + direction + '\r\n' 
    else:
         axis = str(rtn)    
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
    rtn = var.get()
    if rtn == 0:
        axis = 'W'
        wdata = 'L:W' + '\r\n'  
    else:
        axis = str(rtn)
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
    rtn = var.get()
    rdata = rdata.decode("utf-8")
    rdata = rdata.replace("\r\n", "")
    rdata_array = rdata.split(',')
    if rtn == 0:                    # Axis1,Axis2 and Axis3
            sss = rdata_array[0] + rdata_array[1] + rdata_array[2]
    elif rtn == 1   :    # Axis1
            sss = rdata_array[0]    # both command mode
    elif rtn == 2   :    # Axis2
            sss = rdata_array[1]    # both command mode 
    elif rtn == 3   :    # Axis3
            sss = rdata_array[2]    # both command mode  
    lbl['text'] = (sss)

def click_Exit():
    ser.close()
    time.sleep(1)
    root.destroy()
    sys.exit()

root = tk.Tk()
root.title("SIGMA-KOKI Python Sample for SHRC-203 SHOT_FC command mode")
root.geometry("600x400")
#root.mainloop()

# Setting button
button1 = tk.Button(root, text='Connect  ', command=click_Comm)
button2 = tk.Button(root, text='Origin   ', command=click_Origin)
button3 = tk.Button(root, text='Move(Rel)', command=click_MoveRel)
button4 = tk.Button(root, text='Move(Abs)', command=click_MoveAbs)
button5 = tk.Button(root, text='Speed    ', command=click_Speed)
button6 = tk.Button(root, text='JOG      ', command=click_JOG)
button7 = tk.Button(root, text='Stop     ', command=click_Stop)
button8 = tk.Button(root, text='Position ', command=click_Status)
button9 = tk.Button(root, text='Exit     ', command=click_Exit)

# Placing button
button1.place(x=100, y=10,width=80)
button2.place(x=100, y=80,width= 80)
button3.place(x=100, y=120,width= 80)
button4.place(x=100, y=160,width= 80)
button5.place(x=100, y=200,width= 80)
button6.place(x=100, y=240,width= 80)
button7.place(x=100, y=280,width= 80)
button8.place(x=100, y=320,width= 80)
button9.place(x=100, y=360,width= 80)

# Placing label
lbl = tk.Label(text='---------')
lbSlow = tk.Label(text='S')
lbFast = tk.Label(text='F')
lbRate = tk.Label(text='R')
lbl.place(x=190, y=320)
lbSlow.place(x=200, y=200)
lbFast.place(x=300, y=200)
lbRate.place(x=400, y=200)

# Placing textbox
txt1 = tk.Entry(width=10)
txt2 = tk.Entry(width=10)
txtSlow = tk.Entry(width=8)
txtFast = tk.Entry(width=8)
txtRate = tk.Entry(width=8)

txt1.place(x=200, y=120)
txt2.place(x=200, y=160)
txtSlow.place(x=220, y=200)
txtFast.place(x=320, y=200)
txtRate.place(x=420, y=200)

txt1.insert(tk.END,"100")
txt2.insert(tk.END,"0")
txtSlow.insert(tk.END,"2000")
txtFast.insert(tk.END,"20000")
txtRate.insert(tk.END,"200")

#Placing radiobutton
var = tk.IntVar()
rdo1 = tk.Radiobutton(value=1, variable=var, text='Axis1')
rdo2 = tk.Radiobutton(value=2, variable=var, text='Axis2')
rdo3 = tk.Radiobutton(value=3, variable=var, text='Axis3')
rdo4 = tk.Radiobutton(value=0, variable=var, text='All')
rdo1.place(x=100, y=50)
rdo2.place(x=160, y=50)
rdo3.place(x=220, y=50)
rdo4.place(x=280, y=50)
var.set(1)

var2 = tk.IntVar()
rdoP = tk.Radiobutton(value=1, variable=var2, text='+')
rdoM = tk.Radiobutton(value=2, variable=var2, text='-')
rdoP.place(x=200, y=240)
rdoM.place(x=240, y=240)
var2.set(1)

root.mainloop()







 

 
