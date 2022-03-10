from dataServer import dataserver_thread
import numpy as np
import scipy.io as scio
from scipy.signal import resample
import time
from algorithmInterface import algorithmthread
from threading import Event
from multiprocessing import Process, Manager


if __name__ == '__main__':

    # 子线程和主线程共享的资源
    eyetrack_flag = Manager().Value('d',0)  
    
    # load data
    filepath = 'E:/wyl/data/'
    # 获得空间滤波器
    data = scio.loadmat(filepath+'W.mat')
    w = data['W']

    # 获得模板信号
    data = scio.loadmat(filepath+'template.mat')
    template = data['template']

    # 获得LDA分类器
    data = scio.loadmat(filepath+'ldaW_4.mat')
    ldaW = data['ldaW']

    flagstop = False
    n_chan = 8
    hostname = '127.0.0.1'        
    port = 8712                       # 端口号
    srate = 1000                      # 采样频率
    time_buffer = 1.5 # second        # 数据buffer
    epochlength = int(srate*0.54)     # 数据长度
    delay = int(srate*0.14)           # 延迟时间
    addloop = 4                       # 轮次

    datalocker = Event()             
    
    # 数据处理的线程  mj
    dataRunner = algorithmthread(w,template,ldaW,datalocker,addloop)  
    dataRunner.Daemon = True
    dataRunner.start()

     # 数据获取的线程  xfr
    thread_data_server = dataserver_thread(time_buffer=time_buffer)
    thread_data_server.Daemon = True
    notconnect = thread_data_server.connect_tcp()
    if notconnect:
        raise TypeError("Can't connect recoder, Please open the hostport")
    else:   
        thread_data_server.start_acq()
        thread_data_server.start()
        print('Data server connected')
    

    while not flagstop:
        nUpdate = thread_data_server.get_bufferNupdate()
        if nUpdate > int(0.3*srate)-1:
            data1 = thread_data_server.get_buffer_data()
            #选择通道数据
            data, eventline = thread_data_server.channel_selected(data1) # N_chan+1 最后一行是标签行（没出现的时候都是0，出现标签对应位置置1
            triggerPos = np.nonzero(eventline)[0]  # 找到非零元素的索引
            if triggerPos.shape[0] <= 1:          
                thread_data_server.set_bufferNupdate(0)
                continue
            else:
                currentTriggerPos = triggerPos[-2]
                if data[:,currentTriggerPos+1:].shape[1]>=epochlength:
                    cutdata = data[:, currentTriggerPos+1:]
                    epochdata = cutdata[:, delay-1:epochlength-1]
                    #np.savetxt('data{}.out'.format(eventline[currentTriggerPos]), epochdata)
                    if datalocker.is_set() == True:
                        datalocker.clear()
                    epochdata = resample(epochdata, 100, axis=1)
                    dataRunner.recvData(epochdata.T)
                    print('Trigger name: {}, shape as: {}'.format(eventline[currentTriggerPos], epochdata.shape))
                    datalocker.wait()
                    thread_data_server.set_bufferNupdate(0)
                else:
                    thread_data_server.set_bufferNupdate(0)
                    continue

    thread_data_server.stop()
