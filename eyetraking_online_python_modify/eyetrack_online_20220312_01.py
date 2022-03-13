import numpy as np
from scipy.signal import resample
import time
from tobiiresearch.implementation import EyeTracker
from tobiiresearch.interop import interop
from multiprocessing import Process, Manager
from threading import Thread
import socket

# Step1:find eye tracker
found_eyetrakers = EyeTracker.find_all_eyetrackers()      # 寻找通过usb或以太网电缆直接连接到您的计算机的眼动仪，以及连接到与您的计算机相同网络的眼动仪。
my_eyetraker = found_eyetrakers[0]
print("Address:" + my_eyetraker.address)
print("Model:" + my_eyetraker.model)
print("Name(It's OK if this is empty):" + my_eyetraker.device_name)
print("Serial number:" + my_eyetraker.serial_number)

#%%
def gaze_data_callback1(gaze_data):

    # 获取眼动数据
    gaze_right_eye[0] = gaze_data['right_gaze_point_on_display_area'][0]
    gaze_right_eye[1] = gaze_data['right_gaze_point_on_display_area'][1]
    # print("1")
    # print('gaze_right_eye:{}'.format(gaze_right_eye))
    gaze_left_eye[0]  = gaze_data['left_gaze_point_on_display_area'][0]
    gaze_left_eye[1]  = gaze_data['left_gaze_point_on_display_area'][1]
    send_flag.value = 1

#%%
class EyeTracking(Thread):
    def __init__(self,right_eye,left_eye,flag):
        Thread.__init__(self)
        
        # 发送端的地址
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.client_ip = socket.gethostbyname(socket.gethostname())
        self.client_addr = (self.client_ip, 8848)
        self.client_socket.bind(self.client_addr)
        
        self.controlCenterAddr = (self.client_ip,8847)                   # ('127.0.0.1',8847) 接收端的地址

        self.W_screen = 1/1920         #注视点的归一化范围        
        self.H_screen = 1/1080
        self.send_flag = flag
        self.gaze_points = np.zeros((1,12))    # 注视块的数目

        self.position_stim = [(0.5+(0*self.W_screen),0.5-(325*self.H_screen)),(0.5+(-100*self.W_screen),0.5-(-325*self.H_screen)),
                (0.5+(325*self.W_screen),0.5-(325*self.H_screen)),(0.5+(-300*self.W_screen),0.5-(-325*self.H_screen)),
                (0.5+(-525*self.W_screen),0.5-(100*self.H_screen)),(0.5+(525*self.W_screen),0.5-(100*self.H_screen)),
                (0.5+(525*self.W_screen),0.5-(-100*self.H_screen)),(0.5+(-525*self.W_screen),0.5-(-100*self.H_screen)),
                (0.5+(-325*self.W_screen),0.5-(325*self.H_screen)),(0.5+(0*self.W_screen),0.5-(-125*self.H_screen)),
                (0.5+(300*self.W_screen),0.5-(-325*self.H_screen)),(0.5+(100*self.W_screen),0.5-(-325*self.H_screen))]            # 注视刺激块的范围
        
        self.gaze_right_eye = right_eye    # 右眼注视数据
        self.gaze_left_eye =  left_eye      # 左眼注视数据
        
        self.SuitPoint = 0
        self.sys_time_stamp_init = interop.get_system_time_stamp()     # 初始系统时间戳
        self.block_size = 150   # 块的大小
        self.sample_fre = 120   # 眼动仪的采样频率
        self.time_interval = 400 # 400ms
        self.eyetrack_threshold = int(self.sample_fre*(self.time_interval/1000)* 0.6)   # 所占比例0.6


    def run(self):
        while True:
            if self.send_flag.value == 1:        # 有眼动数据进来
                # 双眼数据有效
                if ((self.gaze_right_eye[0] > 0.05 and self.gaze_right_eye[0] < 0.95) and (self.gaze_right_eye[1] > 0.05 and self.gaze_right_eye[1] < 0.95)) and ((self.gaze_left_eye[0] > 0.05 and self.gaze_left_eye[0] < 0.95) and (self.gaze_left_eye[1] > 0.05 and self.gaze_left_eye[1] < 0.95)):
                    gaze_right_left_eyes = ((self.gaze_right_eye[0]+self.gaze_left_eye[0])/2,(self.gaze_right_eye[1]+self.gaze_left_eye[1])/2)
                    self.SuitPoint = self.SuitPoint + 1
                    k = 0
                    for position in self.position_stim:
                        if (gaze_right_left_eyes[0] > position[0]- self.block_size/1920 and gaze_right_left_eyes[0] < position[0]+ self.block_size/1920) and (gaze_right_left_eyes[1] > position[1]- self.block_size/1080 and gaze_right_left_eyes[1] < position[1]+ self.block_size/1080):
                            self.gaze_points[0][k] = self.gaze_points[0][k] + 1
                        k = k + 1
                
                # 计算时间
                time1 = interop.get_system_time_stamp()
                time_delay1 = (time1 - self.sys_time_stamp_init)/1000

                if time_delay1 >= self.time_interval:   #到达400ms
                    self.SuitPoint = 0 
                    if max(self.gaze_points[0]) > self.eyetrack_threshold:
                        eye_decide_result = np.argmax(self.gaze_points[0])+1
                        self.gaze_points[0] = 0
                    else:
                        eye_decide_result = 0 
                    print('time_delay1:{}, suitpoint:{}, eye_decide_result:{}, send_flag{}'.format(time_delay1,self.SuitPoint,eye_decide_result,self.send_flag.value))
                    self.sendCommand(eye_decide_result) 
                    ##
                    self.send_flag.value = 0
                    self.sys_time_stamp_init = interop.get_system_time_stamp()

            # 没有眼动数据进来
            else:
                # 计算时间
                time2 = interop.get_system_time_stamp()
                time_delay2 = (time2 - self.sys_time_stamp_init)/1000
                if time_delay2 >= self.time_interval:
                    eye_decide_result = 0 
                    self.sendCommand(eye_decide_result) 
                    print('time_delay2:{}, suitpoint:{}, eye_decide_result:{}, send_flag:{}'.format(time_delay2,self.SuitPoint,eye_decide_result,self.send_flag.value))
                    self.sys_time_stamp_init = interop.get_system_time_stamp()


             
    def sendCommand(self,command):
        msg = bytes(str(command), "utf8")
        self.client_socket.sendto(msg,self.controlCenterAddr)



#%%
if __name__ == '__main__':
    # 子线程和主线程共享的资源  
    gaze_right_eye = Manager().list([0,0])  # 存放右眼追踪数据
    gaze_left_eye = Manager().list([0,0])   # 存放左眼追踪数据
    send_flag = Manager().Value('d',0)      # 数据发送标志位

    
    #%% 数据发送的线程  mj
    dataRunner = EyeTracking(gaze_right_eye,gaze_left_eye,send_flag)  
    dataRunner.daemon = True
    dataRunner.start()

    #%% 主线程
    # 现在我们只需要告诉SDK当有新的凝视数据时应该调用这个函数。告诉眼动仪开始追踪!
    my_eyetraker.subscribe_to(EyeTracker.EYETRACKER_GAZE_DATA, gaze_data_callback1, as_dictionary=True)
    time.sleep(1200)
    my_eyetraker.unsubscribe_from(EyeTracker.EYETRACKER_GAZE_DATA, gaze_data_callback1)
# %%

''' 拟解决决策时间不稳定输出的问题 '''
#采用系统时间戳调用，稳定400ms（0.5-1ms）的误差



''' 拟解决眼动和脑电的软件同步？'''

# 刺激开始给眼动处理发送一个时间同步信号

# 眼动处理等收到时间同步信号的时候开始计时








