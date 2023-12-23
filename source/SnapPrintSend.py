#!/usr/bin/env python3

from gpiozero import Button
from gpiozero import LED
from signal import pause
import time
from time import sleep
import os
import sys
import logging
import multiprocessing as mp
from multiprocessing import Process
import subprocess

# import other scripts
import PrinterControl as printer
import CameraControl as camera
import LedControl as led
import VersionControl as updater

# Init variables
enablePrinting = True
takingPicture = False
sleepTimeBeforeCapture = 2
sleepTimeBeforeUpdate = 5
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
ledCtrl = None
exePath = ""
sourcePath = ""

# Init logging
logger = logging.getLogger()
logger.setLevel(logging.DEBUG)

handler = logging.StreamHandler(sys.stdout)
handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

def SetLEDColor(ledNo, color, mode=led.MODE_STEADY, speed=led.PULSE_SPEED_MEDIUM, maxBrightness=1, callback=None, cyclesUntilCallback=1):
    setColorData = [ledNo, color, mode, speed, maxBrightness, callback, cyclesUntilCallback]
    pipeToLed.send(setColorData)

def SetLEDOff(ledNo):
    setOffData = [ledNo]
    pipeToLed.send(setOffData)

def OnReadyAgain():
    logger.info("Sytem ready.")
    SetLEDColor(0, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)

def TakePicture():
    global shutdown
    if (shutdown):
        logger.info("System is shut down. Initializing before taking a picture...")
        Init()
        return

    logger.info("Initialize taking picture...")

    global takingPicture
    if (takingPicture):
        logger.info("System already taking a picture. Aborting...")
        return

    takingPicture = True;

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_FAST, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_FAST, led.STANDBY_BRIGHTNESS, OnContinueTakingPicture)

def OnContinueTakingPicture():
    logger.info("Initializing camera...")
    global cam
    cam = camera.InitCamera()
    logger.info("Camera initialized.")

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_BLINK, led.PULSE_SPEED_FAST)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_BLINK, led.PULSE_SPEED_FAST, 1, OnContinueTakingPicture2, 3)

def OnContinueTakingPicture2():
    global cam
    global printer
    global enablePrinting
    global takingPicture

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_STEADY)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_STEADY)

    logger.info("Waiting for camera to focus & balance...")
    sleep(sleepTimeBeforeCapture)

    logger.info("Taking picture...")
    imageName = camera.TakePicture(cam)
    cam = None
    logger.info("Took picture", imageName)

    logger.info("Processing picture...")
    SetLEDColor(0, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM, led.PULSE_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM, led.PULSE_BRIGHTNESS)

    camera.ProcessPicture()

    logger.info("Printing picture...")
    if (enablePrinting):
        printer.PrintImage(imageName)
    else:
        sleep(10)

    takingPicture = False
    logger.info("Picture taken & printed.")
    
    SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS, OnReadyAgain)

def Init():
    logger.info("System initializing...")

    # Print out the working directory
    pwdResult = subprocess.run(['pwd'], capture_output=True, text=True)
    logger.info("Working directory: " + pwdResult.stdout)
    
    # Check if we got an exe path as an argument
    global exePath
    if len(sys.argv) > 1:
        exePath = sys.argv[1]
       
    # Check if we got a source path as an argument
    global sourcePath
    if len(sys.argv) > 2:
        sourcePath = sys.argv[2]

    global ledCtrl
    ledCtrl = led
    
    global ledUpdateProcesses

    if __name__ == '__main__':
        logger.info("Starting LED service...")
        ledCtrl.shutdownEvent.set()

        global pipeToLed
        pipeToLed, pipeToMain = mp.Pipe(duplex=True)
        ledCtrl.pipeToMain = pipeToMain

        while (len(ledUpdateProcesses) > 0):
            ledUpdateProcesses[0].join()
            ledUpdateProcesses.pop()

        ledCtrl.Init()
        ledUpdateProcesses.append(Process(target=ledCtrl.Update))
        ledCtrl.shutdownEvent.clear()
        ledUpdateProcesses[0].start()
        logger.info("LED service started.")

    SetLEDColor(0, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM)
    SetLEDColor(1, led.COLOR_ORANGE, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM)

    # Check if we're running from IDE
    if not exePath:
        logger.info("Exe path not set, skipping update procedure.")
        
        # Skip the auto-update if running from IDE
        OnInitFinish()
        return
    
    if not sourcePath:
        logger.info("Source path not set, skipping update procedure.")
        
        # Skip the auto-update if running from IDE
        OnInitFinish()
        return
    
    global sleepTimeBeforeUpdate
    sleep(sleepTimeBeforeUpdate)
    
    logger.info("Checking for updates...")
    currentVersion = updater.GetCurrentVersion(sourcePath);
    logger.info("Current version is " + str(currentVersion))
    newVersion = currentVersion

    os.popen("chmod +x " + exePath + "/update.sh")
    updateResult = subprocess.run(['sh ' + exePath + '/update.sh ' + sourcePath], shell=True, capture_output=True, text=True)
    logger.info("update.sh out: " + str(updateResult.stdout))
    logger.info("update.sh errors: " + str(updateResult.stderr))
    logger.info("Update script finished.")

    if updateResult.returncode == 1:
        # Get the new version after updating the source files
        newVersion = updater.GetCurrentVersion(sourcePath);
        logger.info("New version is " + str(newVersion))
    else:
        logger.info("No need to update program files.")

    if newVersion != currentVersion:
        SetLEDColor(0, led.COLOR_GREEN, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM)
        SetLEDColor(1, led.COLOR_GREEN, led.MODE_PULSE, led.PULSE_SPEED_MEDIUM)
        
        logger.info("Copying updated files to program directory...")
        os.popen("chmod +x " + exePath + "/copy.sh")
        copyResult = subprocess.run(['sh ' + exePath + '/copy.sh ' + exePath + ' ' + sourcePath], shell=True, capture_output=True, text=True)
        logger.info("copy.sh out: " + str(copyResult.stdout))
        logger.info("copy.sh errors: " + str(copyResult.stderr))
        
        global rebootAfterShutdown
        rebootAfterShutdown = True
        logger.info("Initializing reboot after update...")
        Shutdown();
    else:
        logger.info("Initialization continues...")
        global button
        button.when_pressed = TakePicture

        SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
        SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_IN, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS, OnInitFinish)

def OnInitFinish():
    logger.info("Finishing initialization...")
    SetLEDColor(0, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_STEADY, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)

    global shutdown
    shutdown = False

    global takingPicture
    takingPicture = False

    global startTime
    startTime = time.time()

    logger.info("System running.")

def Shutdown():
    global shutdown
    if (shutdown):
        logger.info("System already shut down.")
        return

    logger.info("System stopping...")
    global shuttingDown
    shuttingDown = True

    SetLEDColor(0, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS)
    SetLEDColor(1, led.COLOR_WHITE, led.MODE_FADE_OUT, led.PULSE_SPEED_MEDIUM, led.STANDBY_BRIGHTNESS, OnShutdownContinue)

def OnShutdownContinue():
    global shutdown
    shutdown = True

    global printer
    printer.Shutdown()

    global ledCtrl
    ledCtrl.shutdownEvent.set()

    global ledUpdateProcesses
    while (len(ledUpdateProcesses) > 0):
        ledUpdateProcesses[0].join()
        ledUpdateProcesses.pop()

    ledCtrl.Shutdown()

    global pipeToLed
    pipeToLed.close()
    pipeToLed = None

    # set the button to re-init the system when pressed
    global button
    button.when_pressed = Init

    global shuttingDown
    shuttingDown = False
    logger.info("System stopped.")

    global rebootAfterShutdown
    if rebootAfterShutdown:
        logger.info("System rebooting...")
        os.popen("sudo reboot")

Init()

while True:
    try:
        if not shutdown:
            currentTime = time.time()
            timeDiff = currentTime - startTime

            if (timeoutEnabled and timeDiff > systemTimeoutS and not shuttingDown):
                logger.info("Shutting down due to timeout")
                Shutdown()
                #os.system("sudo shutdown -h now")
                #logger.info("Shutdown command sent to OS")

            #logger.info("polling pipe to ledCtrl", str(pipeToLed))
            if (pipeToLed.poll()):
                logger.info("Got callback function from pipe")
                callbackFunction = pipeToLed.recv()
                callbackFunction()

    except KeyboardInterrupt:
        Shutdown()