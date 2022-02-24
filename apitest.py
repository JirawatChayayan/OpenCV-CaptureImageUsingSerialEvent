from camera import CameraMode,Camera
from serialConnect import TriggerCommunication
import cv2 as cv

cam = Camera(0,CameraMode.Camera)

def Capture():
    if(cam.camConnected):
        status,img = cam.grabImg()
        if(status):
            cv.imshow('frame_bgr',img)



if __name__ == '__main__':
    cam.connection()
    if(cam.camConnected):
        trig = TriggerCommunication()
        trig.subscribe(Capture)
        trig.openSerialPort()
        Capture()
        while True:
            if(cam.delay(1,'q')):
                break
        cam.disconnect()
        cv.destroyAllWindows()
        trig.closeSerialPort()