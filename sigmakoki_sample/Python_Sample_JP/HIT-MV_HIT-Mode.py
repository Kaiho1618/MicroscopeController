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
    ser.baudrate=38400
    ser.BYTESIZES=serial.EIGHTBITS
    ser.PARITIES=serial.PARITY_NONE
    ser.STOPBITS=serial.STOPBITS_ONE
    ser.timeout=5
    ser.rtscts=True
    
def click_Origin():
    global ser
    if ser == None:
        return
    rtn = var.get()
    
    i = 0
    wdata = 'H:'
    if rtn == 0:
        while i < 8:
            wdata += '1'
            if i != 7:
                wdata += ','
            i += 1
    else:
        while i < 8:
            if i == rtn - 1:
                wdata += '1'
            if i != 7:
                wdata += ','
            i += 1
    wdata += '\r\n'
    
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
    if value >= 0:
        direction = ''
    else:
        direction = '-'
    rtn = var.get()
    
    i = 0
    wdata = 'M:'
    if rtn == 0:
        while i < 8:
            wdata += direction + sss
            if i != 7:
                wdata += ','
            i += 1              
    else:
        while i < 8:
            if i == rtn - 1:
                wdata += direction + sss
            if i != 7:
                wdata += ','
            i += 1
    wdata += '\r\n' 
    
    print(wdata)   
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    
def click_MoveAbs():
    global ser
    if ser == None:
        return
    sss = txt2.get()
    print(sss)
    if sss.isdigit() == False:
        return
    value = int(sss)
    if value >= 0:
        direction = ''
    else:
        direction = '-'
    rtn = var.get()
    
    i = 0
    wdata = 'A:'
    if rtn == 0:
        while i < 8:
            wdata += direction + sss
            if i != 7:
                wdata += ','
            i += 1              
    else:
        while i < 8:
            if i == rtn - 1:
                wdata += direction + sss
            if i != 7:
                wdata += ','
            i += 1
    wdata += '\r\n' 
    
    print(wdata)   
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)   
    
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
    rtn = var.get()
    
    if rtn == 0:
        i = 0
        while i < 8:
            axis = str(i)
            wdata = 'D:' + axis + ',' + slow + ',' + fast + ',' + rate + '\r\n'
            print(wdata)   
            ser.write(wdata.encode())
            rdata = ser.readline()
            print(rdata) 
            time.sleep(1)
            i += 1
        
    else:
        axis = str(rtn - 1)
        wdata = 'D:' + axis + ',' + slow + ',' + fast + ',' + rate + '\r\n'
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
 
    i = 0
    wdata = 'J:'
    if rtn == 0:
        while i < 8:
            wdata += direction
            if i != 7:
                wdata += ','
            i += 1
    else:
        while i < 8:
            if i == rtn - 1:
                wdata += direction
            if i != 7:
                wdata += ','
            i += 1
    wdata += '\r\n' 
            
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    
def click_Stop():
    global ser
    if ser == None:
        return
    rtn = var.get()
    
    i = 0
    wdata = 'L:'
    if rtn == 0:
        wdata += 'E'
    else:
        while i < 8:
            if i == rtn - 1:
                wdata += '1'
            if i != 7:
                wdata += ','
            i += 1
    wdata += '\r\n' 
    
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
      
    sep = [-1,-1,-1,-1,-1,-1,-1]
    i = 0
    j = 0
    
    s_rdata = rdata.decode()
    while i < 7:
        sep[i] = s_rdata.find(',', j)
        if sep[i] == -1:
            break
        j = sep[i] + 1           
        i += 1
    
    rtn = var.get()
    
    if rtn == 0:
        sss = rdata        
    elif rtn == 1:
        if sep[0] == -1:
            return
        sss = rdata[0:sep[0]]   
    else:
        if sep[rtn - 1] == -1:
            return
        sss = rdata[ sep[rtn - 2] + 1 : sep[rtn - 1] ]
        
    lbl['text'] = (sss)

def click_Exit():
    ser.close()
    time.sleep(1)
    root.destroy()
    sys.exit()


root = tk.Tk()
root.title("SIGMA-KOKI Python Sample for HIT-MV (HIT MODE)")
root.geometry("480x440")
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
 
# Placing botton
button1.place(x=100, y=10)
button2.place(x=100, y=110)
button3.place(x=100, y=150)
button4.place(x=100, y=190)
button5.place(x=100, y=230)
button6.place(x=100, y=270)
button7.place(x=100, y=310)
button8.place(x=100, y=350)
button9.place(x=100, y=390)
 
# Placing label
lbl = tk.Label(text='---------')
lbSlow = tk.Label(text='S')
lbFast = tk.Label(text='F')
lbRate = tk.Label(text='R')
lbl.place(x=190, y=350)
lbSlow.place(x=170, y=230)
lbFast.place(x=260, y=230)
lbRate.place(x=350, y=230)

# Placing textbox
txt1 = tk.Entry(width=10)
txt2 = tk.Entry(width=10)
txtSlow = tk.Entry(width=10)
txtFast = tk.Entry(width=10)
txtRate = tk.Entry(width=10)

txt1.place(x=180, y=150)
txt2.place(x=180, y=190)
txtSlow.place(x=180, y=230)
txtFast.place(x=270, y=230)
txtRate.place(x=360, y=230)

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
rdo4 = tk.Radiobutton(value=4, variable=var, text='Axis4')
rdo5 = tk.Radiobutton(value=5, variable=var, text='Axis5')
rdo6 = tk.Radiobutton(value=6, variable=var, text='Axis6')
rdo7 = tk.Radiobutton(value=7, variable=var, text='Axis7')
rdo8 = tk.Radiobutton(value=8, variable=var, text='Axis8')
rdo0 = tk.Radiobutton(value=0, variable=var, text='All')
rdo1.place(x=100, y=50)
rdo2.place(x=160, y=50)
rdo3.place(x=220, y=50)
rdo4.place(x=280, y=50)
rdo5.place(x=100, y=75)
rdo6.place(x=160, y=75)
rdo7.place(x=220, y=75)
rdo8.place(x=280, y=75)
rdo0.place(x=340, y=75)
var.set(1)

var2 = tk.IntVar()
rdoP = tk.Radiobutton(value=1, variable=var2, text='+')
rdoM = tk.Radiobutton(value=2, variable=var2, text='-')
rdoP.place(x=160, y=270)
rdoM.place(x=200, y=270)
var2.set(1)

root.mainloop()







 

 
