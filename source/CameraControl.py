from picamera import PiCamera
from PIL import Image, ImageFile, ImageOps
from time import sleep

# camera settings
resolution = (384, 512)
framerate = 15
brightness = 65
contrast = 30

def InitCamera():
    global resolution
    global framerate
    global brightness
    global contrast

    camera = PiCamera()
    camera.resolution = resolution
    camera.framerate = framerate
    camera.brightness = brightness
    camera.contrast = contrast
    camera.start_preview()
    return camera

def TakePicture(camera):
    print("Taking picture with camera",str(camera))
    imageName = 'capture.jpg'
    camera.capture(imageName)
    camera.stop_preview()
    camera.close()
    return imageName

def ProcessPicture():
    img = Image.open(r'capture.jpg')
    img = img.convert('P')
    img.save('capture.png', optimize=True, format="PNG")

    png = Image.open(r'capture.png')

    palette = png.getpalette()
    for i in range(len(palette)//3):
        gray = (palette[3*i]*299 + palette[3*i+1]*587 + palette[3*i+2]*114)//1000
        palette[3*i:3*i+3] = [gray,gray,gray]

    png.putpalette(palette)
    png.save('capture.png', optimize=True, format="PNG")
    return 'capture.png'