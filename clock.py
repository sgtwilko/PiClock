#!/usr/bin/env python
"""This programme displays the date and time on an RGBMatrix display."""

import time
import datetime
import calendar
import colorsys
import Queue
import hashlib
import signal
from espeak import espeak
from rgbmatrix import graphics
from rgbmatrix import RGBMatrix
from matrix_client import client

#time.sleep(60) # Wait for network
espeak.synth("Hello Hackspace")

# Load up the font (use absolute paths so script can be invoked
# from /etc/rc.local correctly)
# We no longer run from rc.local, we're using a service file to start after networking.
def loadFont(font):
    global fonts
    fonts[font] = graphics.Font()
    fonts[font].LoadFont("/home/pi/rpi-rgb-led-matrix/fonts/" + font + ".bdf")

flip = True
tick = True
scroller = 64

# Monitor service
class ServiceMonitor:
    running = True
    def __init__(self):
        signal.signal(signal.SIGINT, self.timeToQuit)
        signal.signal(signal.SIGTERM, self.timeToQuit)

    def timeToQuit(self,signum, frame):
        self.running = False

myService=ServiceMonitor()

# Create matrix object and Login
matrix=client.MatrixClient("https://matrix.org")
matrix_token=matrix.login("PiClock","me141hh")

# Join room
mhroom=matrix.join_room("#maidstone-hackspace:matrix.org")

# Probably want to try to detect if this is in testing or a real startup...
mhroom.send_text("The PiClock has started, therefore the Hackspace must be open!")
# To-Do: add system monitoring so that when the system is shutdown we send a message about space closing...

# room messages list
messageQ = Queue.Queue()

# Add Listener
def myCallback(room, event):
	#print(event)
	messageQ.put(event[u'sender'].replace(':matrix.org','')+': '+event[u'content'][u'body'])
	pass

mhroom.add_listener(myCallback,u'm.room.message')
matrix.start_listener_thread()


def shiftIt(val, places):
	return (val & (pow(2,places)-1), val >> places)

def colourFromName(aVal, colourSpaceBitSize, offset, shift):
    colourSpace=pow(2,colourSpaceBitSize)-1
    aNum=(int(hashlib.sha1(aVal).hexdigest(),16) >> shift)+offset & colourSpace
    r,g,b=tuple(int(i*255) for i in colorsys.hsv_to_rgb(aNum/float(colourSpace),1,1))
    return((r,g,b))


def percent_through_year(currentDT):
    #Grab year start & end, the work out number of seconds we are through the year, simples!
    ys=datetime.datetime(currentDT.year,1,1)
    ye=datetime.datetime(currentDT.year,12,31,23,59,59)
    percent_of_year=round(((currentDT-ys).total_seconds()/(ye-ys).total_seconds())*100,4)
    return ("%s is %s%% complete!" % (currentDT.year, percent_of_year))


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
sleepTime=0.04

# Create the buffer canvas
MyOffsetCanvas = MyMatrix.CreateFrameCanvas()
while(myService.running):
    currentDT = datetime.datetime.now()
    scroller = scroller-1
    if scroller <= (-sizeofdate):
        scroller = 64
        if not messageQ.empty():
            # To-Do: Make a noise, oh and add hardware to be able to hear the noise...
            sleepTime=0.03
            fulldate=messageQ.get()
            name=fulldate[1:fulldate.find(":")]
            print(name)
            r,g,b=colourFromName(name, 5, 23, 0)
            print((r,g,b))
            scrollColour = graphics.Color(r, g, b)
            #espeak.synth(fulldate)
        elif currentDT.hour < 23:
            sleepTime=0.04
            scrollColour = BLUE
            fulldate = currentDT.strftime("%d-%m-%y  %A")
            fulldate = str(fulldate) + "  " + percent_through_year(currentDT)
        else:
            sleepTime=0.02
            scrollColour = PURPLE
            fulldate = "GO HOME!!!"
            if not goHomeSent:
                mhroom.send_text(fulldate)
                goHomeSent=True

        sizeofdate = len(fulldate)*7
        #print(fulldate)

    Millis = int(round(time.time() * 1000))

    # To-Do: Replace with seconds modulus?
    if Millis-lastSecondFlip > 1000:
        lastSecondFlip = int(round(time.time() * 1000))
        tick = not tick

    #if Millis-lastDateFlip > 5000:
    #    lastDateFlip = int(round(time.time() * 1000))
    #    flip = not flip

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
    time.sleep(sleepTime)

print("service shutting down")
#espeak.synth("Shutting down")
mhroom.send_text("The PiClock has stopped!")
#while espeak.is_playing:
#    pass

time.sleep(2)
