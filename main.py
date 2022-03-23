from typing import Optional
from fastapi import FastAPI
import uvicorn
from starlette.middleware.cors import CORSMiddleware
from camera import Camera,CameraMode
from serialConnect import TriggerCommunication,ModeRun, trig
import cv2 as cv
import time
import os
import threading
import sys
import paho.mqtt.client as mqtt
import json

class MQTT:
    def __init__(self):
        self.MQTTserver = '10.151.27.1'
        self.MQTTConnected = False
        self.mqtt_client = mqtt.Client()
        self.mqtt_client.on_connect = self.onConnectedMqtt
        self.machineID = 'AI'
        self.previousMode = []
        pass

    def topic(self):
        #publish
        pub_modeChange = '{}/mode'.format(self.machineID)
        pub_grabSignal = '{}/grab'.format(self.machineID)
        return [pub_modeChange,pub_grabSignal]
    
    def connectMqtt(self):
        if(self.MQTTConnected):
            return
        try:
            print('Connecting')
            port = 1883
            self.mqtt_client.connect(self.MQTTserver, port)
            self.mqtt_client.loop_start()
        except:
            self.MQTTConnected = False
            pass
    def disconnectMQTT(self):
        try:
            self.mqtt_client.disconnect()
            self.mqtt_client.loop_stop()
        except:
            pass
    def onConnectedMqtt(self,client, userdata, flags, rc):
        time.sleep(2)
        print('Connected.')
        self.MQTTConnected = True

    def publish(self,msg,i):
        print(msg)
        if(self.MQTTConnected):
            topic = self.topic()
            self.mqtt_client.publish(topic[i],msg)
    
    def sendGrabSignal(self,modeRun,filename):
        try:
            run = 1
            if(modeRun == ModeRun.Process):
                run = 1
            else:
                run = 2
            param = {
                        "modeRun":run,
                        "fileName":filename,
            }
            self.publish(json.dumps(param),1)
        except:
            pass
    def sendModeChange(self,modeRun):
        try:
            if(modeRun == self.previousMode):
                return
            run = 1
            if(modeRun == ModeRun.Process):
                run = 2
            else:
                run = 1
            param = {
                        "modeRun": run
            }
            data = json.dumps(param)
            self.publish(data,0)
            self.previousMode = modeRun
        except Exception as e:
            print(e)
            pass


class ProcessCamera:
    def __init__(self):
        self.initialPath()
        self.cam = Camera(0,CameraMode.Camera)
        self.saveThisImage = False
        self.trig = TriggerCommunication()
        self.trig.subscribe(self.trigger)
        self.threadRead = threading.Thread(target=self.processLoop)
        self.stopped = threading.Event()
        self.mqtt = MQTT()
        self.mqtt.connectMqtt();
        self.saveThisImageAPITest = False
        self.saveThisImageAPITrain = False
        pass
    
    def capture(self):
        if(self.cam.camConnected):
            status,img = self.cam.grabImg()
        if(status):
            return img

    def trigger(self):
        self.saveThisImage = True

    def createDir(self,path):
        if not os.path.exists(path):
            os.makedirs(path)
    
    def initialPath(self):
        pathMain =  'D:/ImgScreenSave'#'/home/j/ImgScreenSave'
        pathSetup = '{}/SetupMode'.format(pathMain)
        pathProcess = '{}/ProcessMode'.format(pathMain)
        pathSetupTrain = '{}/Train'.format(pathSetup)
        pathSetupTest = '{}/Test'.format(pathSetup)
        self.createDir(pathMain)
        self.createDir(pathSetup)
        self.createDir(pathProcess)
        self.createDir(pathSetupTrain)
        self.createDir(pathSetupTest)
        return pathMain,pathSetup,pathProcess,pathSetupTrain,pathSetupTest

    def selectDir(self,mode = None):
        pathMain,pathSetup,pathProcess,pathSetupTrain,pathSetupTest = self.initialPath()
        if(mode == ModeRun.Setup):
            return pathSetup
        elif(mode == ModeRun.Process):
            return pathProcess
        else:
            return pathMain
    
    def setupDir(self,Train = True):
        pathMain,pathSetup,pathProcess,pathSetupTrain,pathSetupTest = self.initialPath()
        if(Train):
            return pathSetupTrain
        else:
            return pathSetupTest

    def saveImg(self,img,mode):
        path = self.selectDir(mode)+'/'+str(time.time())+'.png'
        cv.imwrite(path,img)
        self.mqtt.sendGrabSignal(mode,path)
        print ('Save img at {}'.format(path))

    def saveImgSetup(self,img,Train = True):
        path = self.setupDir(Train)+'/'+str(time.time())+'.png'
        cv.imwrite(path,img)
        self.mqtt.sendGrabSignal(ModeRun.Setup,path)
        print ('Save img at {}'.format(path))

    def connect(self):
        self.initialPath()
        self.cam.connection(1280,720)
        if(self.cam.camConnected == False):
            self.disconnect()
            return False
        self.trig.openSerialPort()
        if(self.trig.serialHandle == None):
            self.disconnect()
            return False
        if(self.trig.serialHandle.is_open == False):
            self.disconnect()
            return False
        self.threadRead.start()

    
    def disconnect(self):
        self.stopped.set()
        time.sleep(2)
        try:
            self.cam.disconnect()
        except:
            pass
        try:
            self.trig.closeSerialPort()
            self.mqtt.disconnectMQTT()
        except:
            pass


    def processLoop(self):
        try:
            while not self.stopped.is_set():
                img = self.capture()
                key = cv.waitKey(1)
                procCam.mqtt.sendModeChange(procCam.trig.modeRun)
                if(self.saveThisImage):
                    try:
                        self.saveImg(img,self.trig.modeRun)
                        self.saveThisImage = False
                    except Exception as e:
                        print(e)
                        pass
                if(self.saveThisImageAPITest):
                    try:
                        self.saveImgSetup(img,False)
                        self.saveThisImageAPITest = False
                    except Exception as e:
                        print(e)
                        pass
                if(self.saveThisImageAPITrain):
                    try:
                        self.saveImgSetup(img,True)
                        self.saveThisImageAPITrain = False
                    except Exception as e:
                        print(e)
                        pass
                if(key == ord('q')):
                    break
                elif(key == ord('s')):
                    self.trig.sendSerial(False)
                elif(key == ord('p')):
                    self.trig.sendSerial(True)
                pass
            print('close')
            cv.destroyAllWindows()
            self.disconnect()

        except KeyboardInterrupt:
            print('Keyboard Interrupt')
            cv.destroyAllWindows()
            self.disconnect()
        except:
            print('Error')
            cv.destroyAllWindows()
            self.disconnect()
       
        

procCam = ProcessCamera()

app = FastAPI(
    title="SYSTEM CONFIG",
    description="EDIT CONFIC SYSTEM BELOW",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
@app.get("/getmode/")
def get_mode():
    procCam.mqtt.sendModeChange(procCam.trig.modeRun)
    return {
        "modeRun" : procCam.trig.modeRun,
        "isRunning": procCam.trig.serialHandle.is_open and procCam.cam.camConnected
    }
@app.get("/setmode/{mode}")
def get_mode(mode : int):
    if(mode == 2):
        procCam.trig.sendSerial(ModeRun.Process)
    else:
        procCam.trig.sendSerial(ModeRun.Setup)
    procCam.mqtt.sendModeChange(procCam.trig.modeRun)
    return {
        "modeRun" : procCam.trig.modeRun,
        "isRunning": procCam.trig.serialHandle.is_open and procCam.cam.camConnected
    }
@app.get("/saveImageTrain")
def get_train():
    if(procCam.trig.serialHandle.is_open and procCam.cam.camConnected):
        procCam.saveThisImageAPITrain = True
        return True
    return False

@app.get("/saveImageTest")
def get_test():
    if(procCam.trig.serialHandle.is_open and procCam.cam.camConnected):
        procCam.saveThisImageAPITest = True
        return True
    return False


@app.on_event("startup")
def startup():
    procCam.connect()

@app.on_event("shutdown")
def shutdown():
    procCam.stopped.set()
    procCam.disconnect()
    try:
        sys.exit(0)
    except SystemExit:
        os._exit(0)

if __name__ == "__main__":
    try:
        uvicorn.run(app, host="0.0.0.0", port=8081, log_level="info")
    except KeyboardInterrupt:
        pass

