#!/usr/bin/env python3

from gpiozero import Button
from gpiozero import LED
from signal import pause
import time
from time import sleep
import os
import multiprocessing as mp
from multiprocessing import Process
import subprocess

# import other scripts
import PrinterControl as printer
import CameraControl as camera
import LedControl as led
import VersionControl as updater

enablePrinting = True
takingPicture = False
sleepTimeBeforeCapture = 2
timeoutEnabled = False
systemTimeoutS = 5
shutdown = False
shuttingDown = False
rebootAfterShutdown = False
startTime = time.time()
ledUpdateProcesses = []
pipeToLed = None
button = Button(3, pull_up = True)
cam = None

def SetLEDColor(ledNo, color, mode=led.MODE_STEADY, speed=led.PULSE_SPEED_MEDIUM, maxBrightness=1, callback=None, cyclesUntilCallback=1):
    setColorData = [ledNo, color, mode, speed, maxBrightness, callback, cyclesUntilCallback]
    pipeToLed.send(setColorData)

def SetLEDOff(ledNo):
    setOffData = [ledNo]
    pipeToLed.send(setOffData)

def OnReadyAgain():
    print("Sytem ready.")
    SetLEDColor(0, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)

def TakePicture():
    global shutdown
    if (shutdown):
        print("System is shut down. Initializing before taking a picture...")
        Init()
        return

    print("Initialize taking picture...")

    global takingPicture
    if (takingPicture):
        print("System already taking a picture. Aborting...")
        return

    takingPicture = True;

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_FAST, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_FAST, led.STANDBY_BRIGHTNESS, OnContinueTakingPicture)

def OnContinueTakingPicture():
    print("Initializing camera...")
    global cam
    cam = camera.InitCamera()
    print("Camera initialized.")

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_BLINK, led.PULSE_SPEED_FAST)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_BLINK, led.PULSE_SPEED_FAST, 1, OnContinueTakingPicture2, 3)

def OnContinueTakingPicture2():
    global cam
    global printer
    global enablePrinting
    global takingPicture

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_STEADY)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_STEADY)

    print("Waiting for camera to focus & balance...")
    sleep(sleepTimeBeforeCapture)

    print("Taking picture...")
    imageName = camera.TakePicture(cam)
    cam = None
    print("Took picture", imageName)

    print("Processing picture...")
    SetLEDColor(0, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM, led.PULSE_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM, led.PULSE_BRIGHTNESS)

    camera.ProcessPicture()

    print("Printing picture...")
    if (enablePrinting):
        printer.PrintImage(imageName)
    else:
        sleep(10)

    takingPicture = False
    print("Picture taken & printed.")
    SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS, OnReadyAgain)

def Init():
    print("System initializing...")
    global led
    global ledUpdateProcesses

    if __name__ == '__main__':
        print("Starting LED service...")
        led.shutdownEvent.set()

        global pipeToLed
        pipeToLed, pipeToMain = mp.Pipe(duplex=True)
        led.pipeToMain = pipeToMain

        while (len(ledUpdateProcesses) > 0):
            ledUpdateProcesses[0].join()
            ledUpdateProcesses.pop()

        led.Init()
        ledUpdateProcesses.append(Process(target=led.Update))
        led.shutdownEvent.clear()
        ledUpdateProcesses[0].start()

    SetLEDColor(0, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM)
    SetLEDColor(1, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM, 1, OnInitContinue, 2)

def OnInitContinue():
    print("Checking for updates...")
    currentversion = updater.GetCurrentVersion();
    print("Current version is")
    print(currentversion)

    updateResult = subprocess.Popen("./update.sh")
    updateReturnCode = updateResult.returncode

    if updateReturnCode == 1:
        rebootAfterShutdown = True
        Shutdown();
    else:
        print("Initialization continues...")
        global button
        button.when_pressed = TakePicture

        global led
        SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
        SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS, OnInitFinish)

def OnInitFinish():
    print("Finishing initialization...")
    SetLEDColor(0, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)

    global shutdown
    shutdown = False

    global takingPicture
    takingPicture = False

    global startTime
    startTime = time.time()

    print("System running.")

def Shutdown():
    global shutdown
    if (shutdown):
        print("System already shut down.")
        return

    print("System stopping...")
    global shuttingDown
    shuttingDown = True

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS, OnShutdownContinue)

def OnShutdownContinue():
    global shutdown
    shutdown = True

    global printer
    printer.Shutdown()

    global led
    led.shutdownEvent.set()

    global ledUpdateProcesses
    while (len(ledUpdateProcesses) > 0):
        ledUpdateProcesses[0].join()
        ledUpdateProcesses.pop()

    led.Shutdown()

    global pipeToLed
    pipeToLed.close()
    pipeToLed = None

    # set the button to re-init the system when pressed
    global button
    button.when_pressed = Init

    global shuttingDown
    shuttingDown = False
    print("System stopped.")

    if rebootAfterShutdown:
        os.popen("sudo reboot")

Init()

while True:
    try:
        if not shutdown:
            currentTime = time.time()
            timeDiff = currentTime - startTime

            if (timeoutEnabled and timeDiff > systemTimeoutS and not shuttingDown):
                print("Shutting down due to timeout")
                Shutdown()
                #os.system("sudo shutdown -h now")
                #print("Shutdown command sent to OS")

            #print("polling pipe to led", str(pipeToLed))
            if (pipeToLed.poll()):
                print("Got callback function from pipe")
                callbackFunction = pipeToLed.recv()
                callbackFunction()

    except KeyboardInterrupt:
        Shutdown()