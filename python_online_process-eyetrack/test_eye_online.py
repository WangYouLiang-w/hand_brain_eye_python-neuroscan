import numpy as np
import scipy.io as scio
from scipy.signal import resample
import time
from algori_test import algorithmthread
from threading import Event
import tobii_research as tr
from tobiiresearch.implementation import EyeTracker
from multiprocessing import Process, Manager

# 全局变量
W_screen = 1/1920
H_screen = 1/1080
T_count  = 0
SuitPoint = 0
gaze_points = np.zeros((1,12))
sample_fre = 120   # 眼动仪的采样频率 
block_size = 150   # 块的大小
position_stim = [(0.5+(0*W_screen),0.5-(325*H_screen)),(0.5+(-100*W_screen),0.5-(-325*H_screen)),
                (0.5+(325*W_screen),0.5-(325*H_screen)),(0.5+(-300*W_screen),0.5-(-325*H_screen)),
                (0.5+(-525*W_screen),0.5-(100*H_screen)),(0.5+(525*W_screen),0.5-(100*H_screen)),
                (0.5+(525*W_screen),0.5-(-100*H_screen)),(0.5+(-525*W_screen),0.5-(-100*H_screen)),
                (0.5+(-325*W_screen),0.5-(325*H_screen)),(0.5+(0*W_screen),0.5-(-125*H_screen)),
                (0.5+(300*W_screen),0.5-(-325*H_screen)),(0.5+(100*W_screen),0.5-(-325*H_screen))]

sys_time_stamp_init = 0

# Step1:find eye tracker
found_eyetrakers = EyeTracker.find_all_eyetrackers()      # 寻找通过usb或以太网电缆直接连接到您的计算机的眼动仪，以及连接到与您的计算机相同网络的眼动仪。
my_eyetraker = found_eyetrakers[0]
print("Address:" + my_eyetraker.address)
print("Model:" + my_eyetraker.model)
print("Name(It's OK if this is empty):" + my_eyetraker.device_name)
print("Serial number:" + my_eyetraker.serial_number)


def gaze_data_callback1(gaze_data):
    global SuitPoint
    global gaze_points
    global eyetrack_flag
    global sys_time_stamp_init
    global send_flag

    # 获取眼动数据
    gaze_right_eye=gaze_data['right_gaze_point_on_display_area']
    gaze_left_eye = gaze_data['left_gaze_point_on_display_area']
    
    # 双眼数据有效
    if ((gaze_right_eye[0] > 0.05 and gaze_right_eye[0] < 0.95) and (gaze_right_eye[1] > 0.05 and gaze_right_eye[1] < 0.95)) and ((gaze_left_eye[0] > 0.05 and gaze_left_eye[0] < 0.95) and (gaze_left_eye[1] > 0.05 and gaze_left_eye[1] < 0.95)):
        gaze_right_left_eyes = ((gaze_right_eye[0]+gaze_left_eye[0])/2,(gaze_right_eye[1]+gaze_left_eye[1])/2)
        SuitPoint = SuitPoint + 1
        if SuitPoint == 1:
             sys_time_stamp_init = gaze_data['system_time_stamp']
        k = 0
        for position in position_stim:
            if (gaze_right_left_eyes[0] > position[0]-150/1920 and gaze_right_left_eyes[0] < position[0]+150/1920) and (gaze_right_left_eyes[1] > position[1]-150/1080 and gaze_right_left_eyes[1] < position[1]+150/1080):
                gaze_points[0][k] = gaze_points[0][k] + 1
            k = k + 1
    
    # 计算时间
    time1 = gaze_data["system_time_stamp"]
    time_delay = (time1 - sys_time_stamp_init)/1000
    
    send_flag.value = 0
    if time_delay >= 400:
        send_flag.value = 1 
        print('time_delay：{}，suitpoint:{}，gaze_data:{},send_flag{}'.format(time_delay,SuitPoint,gaze_right_left_eyes,send_flag.value))
        SuitPoint = 0
        if max(gaze_points[0]) > 18:
            eyetrack_flag.value = np.argmax(gaze_points[0])+1
            gaze_points[0] = 0
        else:
            eyetrack_flag.value = 0 
   


if __name__ == '__main__':
    # 子线程和主线程共享的资源
    eyetrack_flag = Manager().Value('d',0)   
    send_flag = Manager().Value('d',0) 

    flagstop = False
    hostname = '127.0.0.1'        
    port = 8712                       # 端口号
    datalocker = Event()             
    
    # 数据处理的线程  mj
    dataRunner = algorithmthread(eyetrack_flag,send_flag)  
    dataRunner.Daemon = True
    dataRunner.start()

    # 主线程
    # 现在我们只需要告诉SDK当有新的凝视数据时应该调用这个函数。告诉眼动仪开始追踪!
    my_eyetraker.subscribe_to(EyeTracker.EYETRACKER_GAZE_DATA, gaze_data_callback1, as_dictionary=True)
    time.sleep(1200)
    my_eyetraker.unsubscribe_from(EyeTracker.EYETRACKER_GAZE_DATA, gaze_data_callback1)