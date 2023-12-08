from escpos.printer import Usb
from escpos.printer import Serial

useUBS = True
# 0x416 and 0x5011 are the details we extracted from lsusb
# 0x81 and 0x03 are the bEndpointAddress for input and output
printer = None
if (useUBS):
    printer = Usb(0x0fe6, 0x811e, in_ep=0x82, out_ep=0x02)#, profile="POS-5890")
else:
    printer = Serial(devfile='/dev/serial0',
                     baudrate=9600, # has to be 9600
                     bytesize=8, # has to be 8
                     parity='N', # can be N or E, but N gives correct results
                     stopbits=1, # can be 1, 1.5 or 2 (similar results)
                     timeout=0.01, # can be anything
                     xonxoff=True, # can be true of false
                     dsrdtr=False) # can be true or false
#printer.set(align='left',font='a',width=2,height=2,density=3,invert=0,smooth=False,flip=False)

#if not (printer.is_online()):
#    print("Printer is offline!")

#if (printer.paper_status() == 1):
#    print("Printer is low on paper!")
#    printer.text("rinter is low on paper! Please replace soon.\n")

#if (printer.paper_status() == 0):
#    print("Printer has no paper!")

def TestPrint():
    print("Now printing...")
    printer.text("Hello World\n")
    printer.text("test")
    print("Printing done.")

def PrintImage(imageName):
    # Print the image
    print("Printing", imageName)
    printer.image(
        imageName,
        high_density_vertical=True,
        high_density_horizontal=True,
        impl='bitImageRaster', # bitImageRaster works best, bitImageColumn prints in (visible) segments. Do not use graphics! (spews out a lot of paper)
        fragment_height=960) # kinda has to be 960 (96 works too)
    PrintLines(3)
    print("Printing done.")

def PrintLines(count=1):
    global printer
    if count < 0:
        raise ValueError("Count cannot be lesser than 0")
    if count > 0:
        printer.text("\n" * count)

def Shutdown():
    printer.close()