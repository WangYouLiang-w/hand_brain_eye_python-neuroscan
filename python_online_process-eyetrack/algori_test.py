from codeop import CommandCompiler
import numpy as np
import scipy.signal as signal
import scipy.io as scio
from scipy import trapz
from threading import Thread
import socket


class algorithmthread(Thread):

    def __init__(self,eye_decide_result,send_flag):
        Thread.__init__(self)
        self.client_ip = socket.gethostbyname(socket.gethostname())
        self.client_addr = (self.client_ip, 8848)
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.controlCenterAddr = (self.client_ip,8847)                   # ('127.0.0.1',8847)
        self.eye_track_result = eye_decide_result
        self.eye_send_flag = send_flag
        

    def run(self):
        while True:
            if  self.eye_send_flag.value == 1:
                eye_decide_result = self.eye_track_result.value
                print("eye_decide_result:{}".format(eye_decide_result))
                self.sendCommand(eye_decide_result) 
                self.eye_send_flag.value  = 0
               
                
    def sendCommand(self,command):
        msg = bytes(str(command), "utf8")
        self.client_socket.sendto(msg,self.controlCenterAddr)


