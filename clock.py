#!/usr/bin/env python
"""This programme displays the date and time on an RGBMatrix display."""

import time
import datetime
import calendar
import Queue
from rgbmatrix import graphics
from rgbmatrix import RGBMatrix
from matrix_client import client

time.sleep(60) # Wait for network

# Load up the font (use absolute paths so script can be invoked
# from /etc/rc.local correctly)
def loadFont(font):
    global fonts
    fonts[font] = graphics.Font()
    fonts[font].LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/" + font + ".bdf")

flip = True
tick = True
scroller = 64

# Create matrix object and Login
matrix=client.MatrixClient("https://matrix.org")
matrix_token=matrix.login("PiClock","me141hh")

# Join room
mhroom=matrix.join_room("#maidstone-hackspace:matrix.org")

# room messages list
messageQ = Queue.Queue()

# Add Listener
def myCallback(room, event):
	# print(event[u'content'][u'body'])
	messageQ.put(event[u'sender'].replace(':matrix.org','')+': '+event[u'content'][u'body'])
	pass

mhroom.add_listener(myCallback,u'm.room.message')
matrix.start_listener_thread()

def percent_through_year(currentDT):
    today = currentDT
    day_of_year = (today - datetime.datetime(today.year, 1, 1)).days + 1
    current_year =  today.year

    if calendar.isleap(today.year):
        days_in_year = 366
    else:
        days_in_year = 365

    percent_of_year = round((float(day_of_year) / float(days_in_year) * float(100)),2)

    return ("%s is %s%% complete!" % (current_year, percent_of_year))


# init the RGB matrix as 32 Rows, 2 panels (represents 32 x 64 panel), 1 chain
MyMatrix = RGBMatrix(32, 2, 1)

# Bits used for PWM. Something between 1..11. Default: 11
MyMatrix.pwmBits = 8

# Sets brightness level. Default: 100. Range: 1..100"
MyMatrix.brightness = 75

# set colour
ColorWHI = graphics.Color(255, 255, 255)
RED = graphics.Color(255, 0, 0)
GREEN = graphics.Color(0, 255, 0)
BLUE = graphics.Color(0, 0, 255)
YELLOW = graphics.Color(255, 255, 0)
PURPLE = graphics.Color(255, 0, 255)

lastDateFlip = int(round(time.time() * 1000))
lastSecondFlip = int(round(time.time() * 1000))
lastScrollTick = int(round(time.time() * 1000))

fonts = {}

loadFont('7x13B')
loadFont('9x18B')
loadFont('6x9')

goHomeSent=False
sizeofdate=0
#scrollColour = BLUE
scroller=0

# Create the buffer canvas
MyOffsetCanvas = MyMatrix.CreateFrameCanvas()
while(1):
    currentDT = datetime.datetime.now()
    scroller = scroller-1
    if scroller <= (-sizeofdate):
        scroller = 64

        if not messageQ.empty():
            scrollColour = GREEN
            fulldate=messageQ.get()
        elif currentDT.hour < 23:
            scrollColour = BLUE
            fulldate = currentDT.strftime("%d-%m-%y  %A")
            fulldate = str(fulldate) + "  " + percent_through_year()
            #if currentDT.day < 10:
            #    fulldate = fulldate[1:]
        else:
            scrollColour = PURPLE
            fulldate = "GO HOME!!!"
            if not goHomeSent:
                mhroom.send_text(fulldate)
                goHomeSent=True

        sizeofdate = len(fulldate)*7

    Millis = int(round(time.time() * 1000))

    if Millis-lastSecondFlip > 1000:
        lastSecondFlip = int(round(time.time() * 1000))
        tick = not tick

    if Millis-lastDateFlip > 5000:
        lastDateFlip = int(round(time.time() * 1000))
        flip = not flip

    thetime = currentDT.strftime("%H"+(":" if tick else " ")+"%M")

    thetime = str.lstrip(thetime)
    sizeoftime = (25 - (len(thetime) * 9) / 2)

    # theday = currentDT.strftime("%A")
    # sizeofday = (32 - (len(theday)* 7)/2)

    pmam = currentDT.strftime("%p")

    graphics.DrawText(MyOffsetCanvas, fonts['7x13B'], scroller, 28,
                      scrollColour, fulldate)

    graphics.DrawText(MyOffsetCanvas, fonts['9x18B'], sizeoftime, 14, RED,
                      thetime)

    graphics.DrawText(MyOffsetCanvas, fonts['6x9'], 50, 14, GREEN, pmam)

    MyOffsetCanvas = MyMatrix.SwapOnVSync(MyOffsetCanvas)
    MyOffsetCanvas.Clear()
    time.sleep(0.05)
