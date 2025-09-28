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

ser = None
enable_axis_array = np.array([False,False,False])
rdata_array = np.array(['','','','','','',''])
    
def click_Comm():
    global ser
    global number_of_all_axis
    ser = serial.Serial('COM20')
    
    ser.baudrate=38400
    ser.BYTESIZES=serial.EIGHTBITS
    ser.PARITIES=serial.PARITY_NONE
    ser.STOPBITS=serial.STOPBITS_ONE
    ser.timeout=5
    ser.rtscts=False
    
    wdata = '#CONNECT:' + '\r\n' 
    print(wdata)    
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    rdata = rdata.decode("utf-8")
    rdata = rdata.replace("\r\n", "")
    print(rdata)
    rdata_array = rdata.split(',')
    print(rdata_array[1])
    number_of_all_axis = int(rdata_array[1])
    if number_of_all_axis == 1:
        rdo1.config(state=tk.NORMAL)
        rdo2.config(state=tk.DISABLED)
        rdo3.config(state=tk.DISABLED)
        rdo4.config(state=tk.NORMAL)
        rdo1.select()
    elif number_of_all_axis == 2:
        rdo1.config(state=tk.NORMAL)
        rdo2.config(state=tk.NORMAL)
        rdo3.config(state=tk.DISABLED)
        rdo4.config(state=tk.NORMAL)
        rdo2.select()
    elif number_of_all_axis == 3:
        rdo1.config(state=tk.NORMAL)
        rdo2.config(state=tk.NORMAL)
        rdo3.config(state=tk.NORMAL)
        rdo4.config(state=tk.NORMAL)
        rdo3.select()
    
def click_Origin():
    global ser
    if ser == None:
        return
    rtn = var.get()
    if rtn == 0:
        axis = 'A'
        wdata = 'H:'+ axis + '\r\n'
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'H:D,'+ axis + '\r\n'
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
    print((sss.lstrip("-").isdigit()))
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
        axis = 'A'
        wdata = 'M:' + axis + ',' + direction +  sss + '\r\n'    
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'M:D,'+ axis + ',' + direction + sss + '\r\n' 
    print(wdata)   
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    
def click_MoveAbs():
    global ser
    if ser == None:
        return
    sss = txt2.get()
    print((sss.lstrip("-").isdigit()))
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
        axis = 'A'
        wdata = 'A:' + axis + ',' + direction +  sss + '\r\n'    
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'A:D,'+ axis + ',' + direction + sss + '\r\n' 
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
        axis = 'A'
        wdata = 'D:' + axis + ',' + slow + ',' + fast + ',' + rate + '\r\n'
    else:
        axis = str(rtn)
        wdata = 'D:D,' + axis + ',' + slow + ',' + fast + ',' + rate + '\r\n'
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
        axis = 'A'
        #wdata = 'J:' + axis + ',' + direction + '\r\n'
        wdata = 'J:A,' + direction + '\r\n'  
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'J:D,'+ axis + ',' + direction + '\r\n' 
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
 
def click_Stop():
    global ser
    if ser == None:
        return
    rtn = var.get()
    
    if rtn == 0:
        axis = 'A'
        wdata = 'L:' + axis + '\r\n'    
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'L:D,'+ axis + '\r\n' 
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)

def click_Status():
    global ser
    if ser == None:
        return
    rtn = var.get()
    if rtn == 0:
        axis = 'A'
        wdata = 'Q:' + axis + '\r\n'    
    else:
        axis = str(rtn)
        # Axis1 or Axis2 or Axis3
        wdata = 'Q:D,'+ axis + '\r\n' 
    print(wdata)
    ser.write(wdata.encode())
    rdata = ser.readline()
    print(rdata)
    rdata = rdata.decode("utf-8")
    rdata = rdata.replace("\r\n", "")
    rdata_array = rdata.split(',')
    if rtn == 0:                    
      sss = ''
      count_status = 0
      while (count_status < number_of_all_axis ):
          if (0 < count_status):
              rdata = ser.readline()
              print(rdata)
              rdata = rdata.decode("utf-8")
              rdata = rdata.replace("\r\n", "")
              rdata_array = rdata.split(',')
          if rdata_array[1] == '1':
              status_0 = rdata_array[2]
              print(status_0)
          elif rdata_array[1] == '2':
              status_1 = rdata_array[2]
              print(status_1)
          elif rdata_array[1] == '3':
              status_2 = rdata_array[2]
              print(status_2)
          count_status += 1
      count_status = 0
      while (count_status < number_of_all_axis ):
          if (0 < count_status):
              sss = sss + ','
          if count_status == 0:
              sss = sss + status_0
          elif count_status == 1:
              sss = sss + status_1
          elif count_status == 2:
              sss = sss + status_2
          print(sss)
          count_status += 1
    else:                          # Axis1,Axis2 or Axis3
      sss = rdata_array[2]
    lbl['text'] = (sss)
   
def click_Exit():
    ser.close()
    time.sleep(1)
    root.destroy()
    sys.exit()

root = tk.Tk()
root.title("SIGMA-KOKI Python Sample for SBIS")
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







 

 
