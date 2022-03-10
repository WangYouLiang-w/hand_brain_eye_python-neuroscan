import tobii_research as tr
import time
from tobiiresearch.implementation import EyeTracker
from tobiiresearch.implementation import GazeData
import os
from multiprocessing import Process, Manager
from tobiiresearch.interop.interop import hmd_based_calibration_collect_data
from stimulate_interface import StimulateProcess
from threading import Thread
import numpy as np




if __name__ == '__main__':
    
    # 刺激进程和主进程共享的资源
    eyetrack_flag = Manager().Value('f',0)  

    '''刺激进程'''
    stimulate = StimulateProcess(eyetrack_flag)
    stimulate.daemon = True
    stimulate.start()

 
    time.sleep(120)
  
