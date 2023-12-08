from signal import pause
import pigpio
import math
from PIL import ImageColor
import multiprocessing as mp

COLOR_WHITE = '#FF6040'
COLOR_RED = '#FF0000'
COLOR_GREEN = '#00FF00'
COLOR_BLUE = '#0000FF'
COLOR_YELLOW = '#aa2000'
COLOR_ORANGE = '#FF1500'
COLOR_PURPLE = '#AA0050'
COLOR_PINK = '#961010'
COLOR_BROWN = '#800800'

testColor1 = COLOR_YELLOW
testColor2 = COLOR_ORANGE

MODE_OFF = 0
MODE_STEADY = 1
MODE_BLINK = 2
MODE_PULSE = 3
MODE_FADE_IN = 4
MODE_FADE_OUT = 5

PULSE_SPEED_SLOW = 0.001
PULSE_SPEED_MEDIUM = 0.005
PULSE_SPEED_FAST = 0.02

INITIAL_BRIGHTNESS_0 = math.pi + (math.pi * 0.5)
INITIAL_BRIGHTNESS_1 = math.pi * 0.5
STANDBY_BRIGHTNESS = 0.1
PULSE_BRIGHTNESS = 0.2

shutdownEvent = mp.Event()
pipeToMain = None

currentColorL = COLOR_WHITE
currentColorR = COLOR_WHITE
currentBrightnessL = 1
previousBrightnessL = 0
previousBrightnessIncreasingL = 0
currentBrightnessR = 1
previousBrightnessR = 0
previousBrightnessIncreasingR = 0
currentMaxBrightnessL = 1
currentMaxBrightnessR = 1
currentModeL = MODE_OFF
currentModeR = MODE_OFF
currentModeCounterL = 0
currentModeCounterR = 0
currentPulseSpeedL = PULSE_SPEED_MEDIUM
currentPulseSpeedR = PULSE_SPEED_MEDIUM
currentCallbackL = None
currentCallbackR = None
currentCyclesUntilCallbackL = 0
currentCyclesUntilCallbackR = 0

PIN_L_R = 25
PIN_L_G = 23
PIN_L_B = 24
PIN_R_R = 22
PIN_R_G = 27
PIN_R_B = 17

pi = None

def Init():
    global pi
    pi = pigpio.pi()

def SetOff(led):
    if (led == 0):
        currentModeL = MODE_OFF
        pi.set_PWM_dutycycle(PIN_L_R, 0)
        pi.set_PWM_dutycycle(PIN_L_G, 0)
        pi.set_PWM_dutycycle(PIN_L_B, 0)
    elif (led == 1):
        currentModeR = MODE_OFF
        pi.set_PWM_dutycycle(PIN_R_R, 0)
        pi.set_PWM_dutycycle(PIN_R_G, 0)
        pi.set_PWM_dutycycle(PIN_R_B, 0)

def SetColor(led, color, mode=MODE_STEADY, speed=PULSE_SPEED_MEDIUM, maxBrightness=1, callback=None, cyclesUntilCallback=1):
    pinR = 0;
    pinG = 0;
    pinB = 0;
    brightness = 0

    maxBrightness = clamp(maxBrightness, 0, 1)

    global pi
    global currentColorL
    global currentColorR
    global currentBrightnessL
    global previousBrightnessL
    global previousBrightnessIncreasingL
    global currentBrightnessR
    global previousBrightnessR
    global previousBrightnessIncreasingR
    global currentMaxBrightnessL
    global currentMaxBrightnessR
    global currentModeL
    global currentModeR
    global currentModeCounterL
    global currentModeCounterR
    global currentPulseSpeedL
    global currentPulseSpeedR
    global currentCallbackL
    global currentCallbackR
    global currentCyclesUntilCallbackL
    global currentCyclesUntilCallbackR
    global pipeToMain

    if (led == 0):
        currentColorL = color

        if not (mode == currentModeL):
            #print("Setting new mode", mode, "on led", led)
            currentCallbackL = callback
            currentCyclesUntilCallbackL = cyclesUntilCallback

            if (mode == MODE_BLINK or mode == MODE_FADE_OUT or mode == MODE_STEADY):
                currentModeCounterL = INITIAL_BRIGHTNESS_1 # this way the brightness starts at 1
                currentBrightnessL = 1
                previousBrightnessL = 2 # set it bigger so the brightness is decreasing
            else:
                currentModeCounterL = INITIAL_BRIGHTNESS_0 # this way the brightness starts at 0
                currentBrightnessL = 0
                previousBrightnessL = -1 # set it smaller so the brightness is increasing

        currentModeL = mode
        currentPulseSpeedL = speed
        currentMaxBrightnessL = maxBrightness
        pinR = PIN_L_R
        pinG = PIN_L_G
        pinB = PIN_L_B
        brightness = currentBrightnessL
        brightnessIncreasing = clamp(currentBrightnessL - previousBrightnessL, -1, 1)
        #print("Current brightness", brightness, "increasing", brightnessIncreasing)
        #text = ["Current brightness", str(brightness), "increasing", str(brightnessIncreasing), "\n"]
        #file_object.write(' '.join(text))

        callCallback = False

        # check if it's time to call the callback (fade finished)
        if (currentModeL == MODE_BLINK and previousBrightnessL != brightness and brightness == 0):
            currentCyclesUntilCallbackL -= 1
            if (currentCyclesUntilCallbackL <= 0):
                callCallback = currentCallbackL != None
        elif (currentModeL == MODE_PULSE and previousBrightnessIncreasingL < 0 and brightnessIncreasing >= 0):
            currentCyclesUntilCallbackL -= 1
            if (currentCyclesUntilCallbackL <= 0):
                callCallback = currentCallbackL != None
        elif (currentModeL == MODE_FADE_IN and brightnessIncreasing <= 0 and brightness >= 0.98):
            callCallback = currentCallbackL != None
            currentModeL = MODE_STEADY
            currentBrightnessL = brightness = 1
        elif (currentModeL == MODE_FADE_OUT and brightnessIncreasing >= 0 and brightness <= 0.02):
            callCallback = currentCallbackL != None
            currentModeL = MODE_STEADY
            currentBrightnessL = brightness = 0

        if (callCallback):
            print("Sending callback", currentCallbackL, "to pipeToMain")
            pipeToMain.send(currentCallbackL)
            currentCallbackL = None

        previousBrightnessIncreasingL = brightnessIncreasing

    elif (led == 1):
        currentColorR = color

        if not (mode == currentModeR):
            #print("Setting new mode", mode, "on led", led)
            currentCallbackR = callback
            currentCyclesUntilCallbackR = cyclesUntilCallback

            if (mode == MODE_BLINK or mode == MODE_FADE_OUT or mode == MODE_STEADY):
                currentModeCounterR = INITIAL_BRIGHTNESS_1 # this way the brightness starts at 1
                currentBrightnessR = 1
                previousBrightnessR = 1
            else:
                currentModeCounterR = INITIAL_BRIGHTNESS_0 # this way the brightness starts at 0
                currentBrightnessR = 0
                previousBrightnessR = 0

        currentModeR = mode
        currentPulseSpeedR = speed
        currentMaxBrightnessR = maxBrightness
        pinR = PIN_R_R
        pinG = PIN_R_G
        pinB = PIN_R_B
        brightness = currentBrightnessR
        brightnessIncreasing = clamp(currentBrightnessR - previousBrightnessR, -1, 1)

        # check if it's time to call the callback (fade finished)
        callCallback = False
        if (currentModeR == MODE_BLINK and previousBrightnessR != brightness and brightness == 0):
            currentCyclesUntilCallbackR -= 1
            if (currentCyclesUntilCallbackR <= 0):
                callCallback = currentCallbackR != None
        elif (currentModeR == MODE_PULSE and previousBrightnessIncreasingR < 0 and brightnessIncreasing >= 0):
            currentCyclesUntilCallbackR -= 1
            if (currentCyclesUntilCallbackR <= 0):
                callCallback = currentCallbackR != None
        elif (currentModeR == MODE_FADE_IN and brightnessIncreasing <= 0 and brightness >= 0.98):
            callCallback = currentCallbackR != None
            currentModeR = MODE_STEADY
            currentBrightnessR = brightness = 1
        elif (currentModeR == MODE_FADE_OUT and brightnessIncreasing >= 0 and brightness <= 0.02):
            callCallback = currentCallbackR != None
            currentModeR = MODE_STEADY
            currentBrightnessR = brightness = 0

        if (callCallback):
            print("Sending callback", currentCallbackR, "to pipeToMain")
            pipeToMain.send(currentCallbackR)
            currentCallbackR = None

        previousBrightnessIncreasingR = brightnessIncreasing

    colors = ImageColor.getcolor(color, "RGB")

    #if (led == 0):
        #print("Setting", led, "to", round_half_up(colors[0] * brightness * maxBrightness), round_half_up(colors[1] * brightness * maxBrightness), round_half_up(colors[2] * brightness * maxBrightness))
    pi.set_PWM_dutycycle(pinR, round_half_up(colors[0] * brightness * maxBrightness))
    pi.set_PWM_dutycycle(pinG, round_half_up(colors[1] * brightness * maxBrightness))
    pi.set_PWM_dutycycle(pinB, round_half_up(colors[2] * brightness * maxBrightness))

def TestLEDs():
    timer = 0;
    while True:
        timer += 0.001

        if (timer < 1):
            SetColor(0, COLOR_RED)
            SetColor(1, COLOR_RED)
        elif (timer < 2):
            SetColor(0, COLOR_GREEN)
            SetColor(1, COLOR_GREEN)
        elif (timer < 3):
            SetColor(0, COLOR_BLUE)
            SetColor(1, COLOR_BLUE)
        elif (timer > 3):
            timer = 0

def Shutdown():
    global pi
    pi.set_PWM_dutycycle(PIN_L_R, 0)
    pi.set_PWM_dutycycle(PIN_L_G, 0)
    pi.set_PWM_dutycycle(PIN_L_B, 0)

    pi.set_PWM_dutycycle(PIN_R_R, 0)
    pi.set_PWM_dutycycle(PIN_R_G, 0)
    pi.set_PWM_dutycycle(PIN_R_B, 0)
    pi.stop()

    global pipeToMain
    pipeToMain.close()
    pipeToMain = None

def round_half_up(n, decimals=0):
    multiplier = 10 ** decimals
    return math.floor(n*multiplier + 0.5) / multiplier

def clamp(value, min=0, max=1):
    if (value < min):
        value = min
    elif (value > max):
        value = max
    return value

def getBrightnessFromValue(value):
    return (math.sin(value) + 1.0) * 0.5

# test leds
#SetOff(0)
#SetColor(0, testColor1, MODE_STEADY)
#SetColor(0, COLOR_ORANGE, MODE_PULSE, PULSE_SPEED_SLOW)
#SetOff(1)
#SetColor(1, testColor2, MODE_STEADY)
#SetColor(1, COLOR_ORANGE, MODE_PULSE, PULSE_SPEED_SLOW)
#SetColor(1, COLOR_PURPLE, MODE_PULSE, PULSE_SPEED_FAST)
#SetColor(1, COLOR_WHITE, MODE_PULSE, PULSE_SPEED_SLOW, 0.1)
#SetColor(1, COLOR_WHITE, MODE_BLINK, PULSE_SPEED_MEDIUM, 0.5)

def Update():
    global shutdownEvent
    global currentModeCounterL
    global currentModeCounterR
    global currentModeL
    global currentModeR
    global currentBrightnessL
    global previousBrightnessL
    global currentBrightnessR
    global previousBrightnessR
    global currentColorL
    global currentColorR
    global currentPulseSpeedL
    global currentPulseSpeedR
    global currentMaxBrightnessL
    global currentMaxBrightnessR

    while True:
        if (pipeToMain.poll()):
            setColorData = pipeToMain.recv();
            if (len(setColorData) == 1):
                SetOff(setColorData[0])
            elif (len(setColorData) == 7):
                SetColor(setColorData[0], setColorData[1], setColorData[2], setColorData[3], setColorData[4], setColorData[5], setColorData[6])

        if (currentModeL > MODE_STEADY):
            if (currentModeL == MODE_PULSE or currentModeL == MODE_FADE_IN or currentModeL == MODE_FADE_OUT):
                previousBrightnessL = currentBrightnessL
                currentBrightnessL = getBrightnessFromValue(currentModeCounterL)
            elif (currentModeL == MODE_BLINK):
                previousBrightnessL = currentBrightnessL
                currentBrightnessL = round_half_up(getBrightnessFromValue(currentModeCounterL))

            #print("currentBrightnessL", currentBrightnessL, "currentModeCounterL", currentModeCounterL)
            SetColor(0, currentColorL, currentModeL, currentPulseSpeedL, currentMaxBrightnessL)
            currentModeCounterL += currentPulseSpeedL

        if (currentModeR > MODE_STEADY):
            if (currentModeR == MODE_PULSE or currentModeR == MODE_FADE_IN or currentModeR == MODE_FADE_OUT):
                previousBrightnessR = currentBrightnessR
                currentBrightnessR = getBrightnessFromValue(currentModeCounterR)
            elif (currentModeR == MODE_BLINK):
                previousBrightnessR = currentBrightnessR
                currentBrightnessR = round_half_up(getBrightnessFromValue(currentModeCounterR))

            #print("currentBrightnessR", currentBrightnessR)
            SetColor(1, currentColorR, currentModeR, currentPulseSpeedR, currentMaxBrightnessR)
            currentModeCounterR += currentPulseSpeedR

        if (shutdownEvent.is_set()):
            break