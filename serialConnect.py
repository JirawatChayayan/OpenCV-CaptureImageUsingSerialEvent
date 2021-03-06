
import threading
import time
import serial
import sys
import json
import enum

class ModeRun(enum.Enum):
    Setup = 1
    Process = 2

class TriggerCommunication:
    def __init__(self):
        self.port = 'COM8'#'/dev/ttyUSB0'
        self.buadrate = 115200
        self.serialHandle = None
        self.stopped = threading.Event()
        self.threadRead = None
        self.callbacks = []
        self.modeRun = ModeRun.Setup
        pass
    def subscribe(self, callback):
        self.callbacks.append(callback)
    def openSerialPort(self,isReconnect = False):
        self.serialHandle = None
        try:
            self.serialHandle = serial.Serial(self.port, self.buadrate)
            time.sleep(3)
            self.sendSerial(self.modeRun)
            if(not isReconnect):
                self.threadRead = threading.Thread(target=self.readSerial)
                self.threadRead.start()
            print('Opened Serial')
        except serial.SerialException as msg:
            print( "Error opening serial port %s" % msg)
            self.serialHandle = None

        except:
            exctype, errorMsg = sys.exc_info()[:2]
            print ("%s  %s" % (errorMsg, exctype))
            self.serialHandle = None

    def closeSerialPort(self,isSet=True):
        try:
            if(isSet):
                self.stopped.set()
            time.sleep(1)
            self.serialHandle.close()
            print('Closed Serial')
        except:
            pass

    def reconnect(self):
        try:
            print('Reconnect Serial')
            self.closeSerialPort(isSet=False)
            time.sleep(1)
            self.openSerialPort(True)
        except:
            pass
        
    def sendSerial(self,mode):
        if(self.serialHandle is not None):
            if(mode == ModeRun.Process):
                self.modeRun = ModeRun.Process
                self.serialHandle.write(("{\"Mode\":\"Process\"}"+"\n").encode())
            else:
                self.modeRun = ModeRun.Setup
                self.serialHandle.write(("{\"Mode\":\"Setup\"}"+"\n").encode())
            #self.serialHandle.write("\n".encode())
    def readSerial(self):
        print('Serial Ready')
        while not self.stopped.is_set():
            try:
                cc=str(self.serialHandle.readline())
                cleanMsg = cc[2:][:-5]
                splitData = cleanMsg.split(';')
                if(splitData[0]== 'Trig'):
                    cmd = json.loads(splitData[1])
                    #print('Trigger From Mode : {0}'.format(cmd['Mode']))
                    for fn in self.callbacks:
                        fn()
                else:
                    print(cleanMsg)
            
            except KeyboardInterrupt: #Capture Ctrl-C
                print ("Captured Ctrl-C")
                self.stopped.set()
                break
            
            except:
                exctype, errorMsg = sys.exc_info()[:2]
                print ("Error reading port - %s" % errorMsg)
                if(not self.stopped.is_set()):
                    self.reconnect()
        self.stopped = None
        self.threadRead = None



def trig():
    print('Recived Signal')

if __name__ == "__main__":
    Trig = TriggerCommunication()
    Trig.subscribe(trig)
    Trig.openSerialPort()

    a = input()
    Trig.closeSerialPort()