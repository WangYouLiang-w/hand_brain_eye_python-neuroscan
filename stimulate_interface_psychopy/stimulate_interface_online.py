from psychopy import visual,parallel
import psychopy
from psychopy.contrib.lazy_import import ImportReplacer
from psychopy.logging import data, setDefaultClock
from psychopy.tools.mathtools import length
from psychopy.visual import image, rect, text, window,circle
from psychopy import event
import json
import math
import time
import numpy as np
import pygame
from pygame.constants import FULLSCREEN
import socket


class StimulateProcess():

    def __init__(self):
        #===========================设置标签接口======================#
        self.port = parallel.ParallelPort(address=0xdefc)# 端口地址 107=0xdefc，205=52988
        self.port.setData(0)#标签置0
        

        # 建立服务端(刺激界面的接收端)
        self.SeverEyeSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SeverEyeIp = socket.gethostbyname(socket.gethostname())    #获取本地ip
        self.SeverEyeAddr = (self.SeverEyeIp, 8847)                      #设置端口号
        self.SeverEyeSocket.bind(self.SeverEyeAddr)
        self.SeverEyeSocket.setblocking(False)                           # 设置为非阻塞
        # self.eye_data_recv = self.SeverEyeSocket.recvfrom(1024)
        
        self.SeverBrianSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.SeverBrainIp = socket.gethostbyname(socket.gethostname())    #获取本地ip
        self.SeverBrianAddr = (self.SeverEyeIp, 40007)                      #设置端口号
        self.SeverBrianSocket.bind(self.SeverBrianAddr)
        self.SeverBrianSocket.setblocking(False)                           # 设置为非阻塞
        
        
        presettingfile = open('PreSettings_Single_tenclass.json')
        settings = json.load(presettingfile)
        self.stimulationLength = settings[u'stimulationLength'][0]    # 刺激时长
        self.stimulifre = settings[u'frequence']                      # 刺激频率
        self.phase = settings[u'phase']                               # 刺激相位
        self.cuelen = settings[u'cuelen'][0]                          # 提示长度
        self.textList = settings[u'controlCommand']                   # 字符列表
        self.textposition = settings[u'textposition']                 # 字符位置
        self.position = settings[u'position']                         # 刺激块的位置 
        self.framerate = 120                                          # 屏幕刷新频率
        self.cueseries =settings[u'cueSeries']                        # 
        self.stimulus_blocks = len(self.position)                 # 刺激块的个数
        
        #自定义的全局变量
        self.w = 1920
        self.h = 1080
        self.is_full_screen = True
        self.win_w = 1920
        self.win_h = 1080
        self.hc = self.h/self.win_h
        self.wc = self.w/self.win_w
        self.choice =  1
        self.dt = 1/self.framerate
        self.stim_texts = []
        self.stim_Rects = []
        self.res_time= []
        self.test_Rects = [] 
        self.eye_feedback = []
        self.brain_feedback = []
        self.c = {}
        self.position_stim =[(int(0*self.wc),int(325*self.hc)),(int(-100*self.wc),int(-325*self.hc)),(int(325*self.wc),int(325*self.hc)),(int(-300*self.wc),int(-325*self.hc)),(int(-525*self.wc),int(100*self.hc)),(int(525*self.wc),int(100*self.hc)),(int(525*self.wc),int(-100*self.hc)),(int(-525*self.wc),int(-100*self.hc)),(int(-325*self.wc),int(325*self.hc)),(int(0*self.wc),int(-125*self.hc)),(int(300*self.wc),int(-325*self.hc)),(int(100*self.wc),int(-325*self.hc))]
        self.startText = 'If you are ready, press the space bar to begin! You can press any key to exit!'

    # def run(self):
    #     self.interface()


    def interface(self):
        ''' 闪烁刺激界面 '''
        win = visual.Window(pos=(0,0),color=(0,0,0),fullscr=self.is_full_screen,colorSpace = 'rgb255',size = (self.w,self.h))
        win.mouseVisible = False # 隐藏鼠标
        
        '''开始提醒'''
        while True:
            StartTexts_Stim = visual.TextStim(win,text=self.startText,font='Times New Roman',pos=(0,0),units='pix',color=(255,255,255),colorSpace='rgb255',height=65 *self.wc)
            StartTexts_Stim.draw()
            if 'space' in event.getKeys():
                win.flip()
                break
            win.flip()

        ''' 刺激界面非闪烁下的整体效果 '''
        for i in range(len(self.position)):
            Rect_test = rect.Rect(win,pos=(self.position[str(i)][0]*self.wc,self.position[str(i)][1]*self.hc),
                                size=(150*self.wc,150*self.hc),units = 'pix',fillColor=(255,255,255),colorSpace = 'rgb255')
            self.test_Rects.append(Rect_test)

        ''' 刺激界面的提示字符 '''
        for i in range(self.stimulus_blocks):
            Texts_Stim = visual.TextStim(win,text=self.textList[str(i)],font='Times New Roman',pos=(self.textposition[str(i)][0]*self.wc,self.textposition[str(i)][1]*self.hc),units='pix',color=(0,0,0),colorSpace='rgb255',height=35*self.wc)
            self.stim_texts.append(Texts_Stim)  
        
        ''' 刺激块 '''
        for t in range(int(self.stimulationLength*self.framerate)):
            color_stim = self.stimu_sqeuence(t)
            color_stim = list(color_stim.values())
            Rects_Stim = visual.ElementArrayStim(win,fieldShape='sqr',nElements = self.stimulus_blocks,xys=self.position_stim,
                                                sizes=(150*self.wc,150*self.hc),units = 'pix',colors=color_stim,colorSpace = 'rgb255',
                                                elementTex=np.ones([150,150]),elementMask = np.ones([150,150]))
            self.stim_Rects.append(Rects_Stim)


        ''' 反馈效果 '''
        # 脑电反馈  ----绿色方框
        for i in range(self.stimulus_blocks):
            Rect_braintrack = rect.Rect(win,pos=(self.textposition[str(i)][0]*self.wc,
                                                    self.textposition[str(i)][1]*self.hc),size=(155*self.wc,155*self.hc),
                                                    units = 'pix',fillColor=(0,255,0),colorSpace = 'rgb255') 
            self.brain_feedback.append(Rect_braintrack)

        # 眼动反馈 -----红色圆圈
        for i in range(self.stimulus_blocks):
            Circle_eyetrack = circle.Circle(win,radius=15,pos=(self.textposition[str(i)][0]*self.wc,
                                    self.textposition[str(i)][1]*self.hc),
                                    units = 'pix',fillColor=(255,0,0),colorSpace = 'rgb255')
            self.eye_feedback.append(Circle_eyetrack)                                       

        """ 刺激界面显示"""
        trial = 1
        NumTrial = len(self.stimulifre)
        last_eye_data = 0
        last_brain_data = None
        while trial <= NumTrial:
                win.flip()
                ##  刺激  ##
                StimulusCount = 1
                for rect_stim in self.stim_Rects:                        
                    tic = time.time() 
                    # 打标签
                    if StimulusCount == 1:
                        self.port.setData(int(trial))

                    if StimulusCount == 3:
                        self.port.setData(0)
                    StimulusCount = StimulusCount + 1
                    
                    #%% 刺激界面接收到的反馈
                    # 脑电数据的反馈
                    try:
                        brain_data = self.SeverBrianSocket.recv(1024)
                        last_brain_data = brain_data
                    except BlockingIOError as e:
                        brain_data = last_brain_data
                    
                    if brain_data:
                        brain_decide_result = int(str(brain_data,encoding='utf8'))
                        print(brain_decide_result)
                        self.brain_feedback[brain_decide_result-1].draw()          
                        
                    # 刺激块    
                    rect_stim.draw()
                    
                    # 眼动数据的反馈
                    try:
                        eye_data = self.SeverEyeSocket.recv(1024)
                        last_eye_data = eye_data
                    except BlockingIOError as e:
                        eye_data = last_eye_data                         # 在下一个结果来之前保持输出当前注视结果
                        
                    if eye_data:
                        eye_decide_result = int(str(eye_data,encoding='utf8'))
                        if eye_decide_result != 0:      # 没有注视块则不显示反馈结果
                            self.eye_feedback[eye_decide_result-1].draw()    
                    
                    # 显示提示字符
                    [text_stim.draw() for text_stim in self.stim_texts]
                    win.flip()
                    toc = time.time()
                    T = toc-tic
                    self.res_time.append(T)
                    #print(T)
                    # 任意键退出
                    if event.getKeys():
                        print('average time{}'.format(np.average(self.res_time)))
                        win.close()
                        break    
                    
                trial = np.mod(trial,NumTrial)
                trial = trial + 1

        
        print('average time{}'.format(np.average(self.res_time)))
        win.flip()  

    
    def stimu_sqeuence(self,t):
        ''' 刺激序列 '''
        for i in range(len(self.stimulifre)):
                cor= (math.sin(2*math.pi*self.stimulifre[i]*self.dt*t+self.phase[i])+1)/2
                self.c[i] = ([int(cor*255),int(cor*255),int(cor*255)])
        return self.c 


if __name__ == '__main__':
    stimulate = StimulateProcess()
    stimulate.interface()