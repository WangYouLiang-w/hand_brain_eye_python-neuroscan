from codeop import CommandCompiler
import numpy as np
import scipy.signal as signal
import scipy.io as scio
from scipy import trapz
from threading import Thread
import socket
import time
import heapq
from mne.time_frequency import psd_array_welch
#from numba import jit

def loadfilterModel(filename = 'filterModel'):
    '''
    Read the matlab .mat format filter model file, and reshape to python dict format.
    To use, please put the filter model file in the same path with this file. 
    '''
    notchpara = {}
    filterpara = {}
    data = scio.loadmat(filename)
    filterdata = data['filterModel']
    f_b50 = filterdata[0,0]['f_b50'][0]
    f_a50 = filterdata[0,0]['f_a50'][0]
    notchpara['f_b50'] = f_b50
    notchpara['f_a50'] = f_a50
    currentf_b = filterdata[0,0]['f_b'][0]
    currentf_a = filterdata[0,0]['f_a'][0]
    if len(currentf_b) != len(currentf_a):
        raise ValueError('f_b and f_a do not have same number of subband')
    else:
        f_b = {}
        f_a = {}
        f_b = currentf_b[0][0]
        f_a = currentf_a[0][0]
    filterpara['f_b'] = f_b
    filterpara['f_a'] = f_a
    return notchpara, filterpara
'''
def mean2(x):
    y = np.sum(x) / np.size(x)
    return y

def corr2(a,b):
    a = a - mean2(a)
    b = b - mean2(b)

    r = (a*b).sum() / math.sqrt((a*a).sum() * (b*b).sum())
    return r
'''
# offer a common test interface to any algorithm.
class preprocess():

    '''
    In general, online preprosess include notch filter and time filter,
    nearly all kind of algorithm needs this process. So this is a base 
    class for all kind of algorithm.
    '''
    def __init__(self,filterModelName):
        '''
        param: filterModelName, file name of filter Model, string format
        '''
        notchpara, filterpara = loadfilterModel(filename=filterModelName)
        self.notchpara = notchpara
        self.filterpara = filterpara
        #fusion coefficient
        self.a = np.power(np.arange(1,11),-1.25).reshape([10,1])+0.25
    
    # 陷波处理
    def notchfilter(self,rawdata):
        f_b50 = self.notchpara['f_b50']
        f_a50 = self.notchpara['f_a50']
        notchdata = signal.filtfilt(f_b50,f_a50,rawdata,axis=0)
        #TODO: Check the filtfilt result compare to matlab filtfilt
        return notchdata

    # 时间滤波
    def timefilter(self,notchdata):
        fiteredData = np.zeros((notchdata.shape[0],notchdata.shape[1]))
        f_b = self.filterpara['f_b']
        f_a = self.filterpara['f_a']
        flipdata = np.flip(notchdata, axis=0)
        currentdata = np.r_[flipdata,notchdata,flipdata]
        fiteredData= signal.filtfilt(f_b,f_a,currentdata,axis=-2,padlen= 3*(max(len(f_b),len(f_a))-1))[notchdata.shape[0]+1:2*notchdata.shape[0]+1,:]
        return fiteredData

#@jit(nopython=True,fastmath=True,cache=True)
def classfierdecide(filtdata,W,template,a):
    R = np.zeros((template.shape[2]))
    currentTestData = filtdata[:,:]
    data1 = np.dot(np.ascontiguousarray(currentTestData),np.ascontiguousarray(W))
    for target in range(template.shape[2]):
        currentTemp = template[:,:,target]
        R[target] = np.corrcoef(data1.reshape(-1),np.dot(np.ascontiguousarray(currentTemp.T),np.ascontiguousarray(W[:,:])).reshape(-1))[0][1]
    return R

class TRCA(preprocess):
    
    def __init__(self,TRCA_spatialFilter,template):
        preprocess.__init__(self,filterModelName='filterModel')
        self.W = TRCA_spatialFilter
        self.template = template
        # Pre use the numba funtion when initial to speed up the process
        #result = classfierdecide(np.squeeze(self.template[:,:]).T,self.W,self.template,self.a)
        #result = classfierdecide(np.squeeze(self.template[:,:]).T,self.W,self.template,self.a)
    
    def transform(self,rawdata):
        # notch and time filter
        notchdata = self.notchfilter(rawdata)
        self.filtdata = self.timefilter(notchdata)

    def apply(self):
        '''
        R = np.zeros((self.template[0,0].shape[2],self.subbandNum))
        for subband in range(self.subbandNum):
            currentTestData = self.filtdata[:,:,subband]
            data1 = np.dot(currentTestData.T,self.W[:,:,subband])
            for target in range(self.template[0,0].shape[2]):
                currentTemp = self.template[0,subband][:,:,target]
                R[target,subband] = np.corrcoef(data1.reshape(-1),np.dot(currentTemp.T,self.W[:,:,subband]).reshape(-1))[0][1]
        self.result = np.argmax(np.dot(R,self.a[:self.subbandNum,0]))
        '''
        # R = np.zeros([(template[0,0].shape[2]),(self.subbandNum)])
        self.result = classfierdecide(self.filtdata,self.W,self.template,self.a)

class EMGdetecter():

    def __init__(self):
        self.fs = 250
        self.beta_fmin = 14
        self.beta_fmax = 30
        self.grit_teeth_thresh = 20
        self.isGrit = 0

    def welch(self,data):
        dataPO5 = data[:,3].T
        dataPO6 = data[:,4].T
        '''
        dataPO5 -= np.mean(dataPO5,axis=0)
        print(np.mean(dataPO5))
        dataPO6 -= np.mean(dataPO6,axis=0)
        '''

        self.psdS_1, self.freqS_1 = psd_array_welch(dataPO5, sfreq=1, fmin=0, fmax=30, n_fft=100)
        self.psdS_2, self.freqS_2 = psd_array_welch(dataPO6, sfreq=1, fmin=0, fmax=30, n_fft=100)

    def bandpower(self,):
        self.beta_power_PO5 = abs(trapz(self.freqS_1[self.beta_fmin:self.beta_fmax], self.psdS_1[self.beta_fmin:self.beta_fmax]))
        self.beta_power_PO6 = abs(trapz(self.freqS_2[self.beta_fmin:self.beta_fmax], self.psdS_2[self.beta_fmin:self.beta_fmax]))

    def detector(self,data):
        self.welch(data)
        self.bandpower()
        if (self.beta_power_PO5>self.grit_teeth_thresh*10) and (self.beta_power_PO6>self.grit_teeth_thresh*10):
            self.isGrit = 1
        else:
            self.isGrit = 0

class algorithmthread(Thread):

    settingsfile ={
		"0":"TakeOff",
		"1":"Landing",
		"2":"Forward",
		"10":"Backward",
		"4":"Left",
		"5":"Right",
		"6":"CW",
		"7":"CCW",
		"8":"Up",
        "9":"Down",
        "3":"Keep",
        "11":"Hover"
			}

    def __init__(self,w,template,ldaW,datalocker,addloop):
        Thread.__init__(self)
        self.classfier = TRCA(w,template)
        self.emgdetector = EMGdetecter()
        self.gritlengthcount = 0
        self.testdata = np.array([0])
        self.resultCount = np.zeros((template.shape[2],addloop))
        self.currentPtr = 0
        self.sendresult = 0
        self.datalocker = datalocker
        self.ldaW = ldaW
        self.ldaX = np.ones((1, 3))
        # 服务端地址和端口
        self.controlCenterAddr = ('169.254.29.63', 40007)                      # ('127.0.0.1',8847) 刺激端的结果
        self.resultPtr = 0
        self.resultBuffer = np.zeros((1,3))
        self.emgcommand = 0
        self.addloop = addloop
        # 建立客户端Sokect
        self.client_ip = socket.gethostbyname(socket.gethostname())
        self.client_addr = (self.client_ip, 40008)
        self.sock_client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock_client.bind(self.client_addr)

    def recvData(self,rawdata):
        self.testdata = rawdata

    def run(self):
        while True:
            if self.testdata.shape[0] == 1:
                continue
            else:
                # detect grit teeth first
                self.emgdetector.detector(self.testdata)
                print('PSD value:',self.emgdetector.beta_power_PO5)
                # if self.emgdetector.isGrit == 1 and self.gritlengthcount < 1:
                #     print('Grit detected! UAV hover now')
                #
                #     self.emgcommand = 11 #Hover
                #     self.sendCommand(self.emgcommand)
                #     self.gritlengthcount += 1
                #     self.clearTestdata()
                #     self.datalocker.set()
                # elif self.emgdetector.isGrit == 1 and self.gritlengthcount >= 1:
                #     print('Keep gritting, UAV is backing now')
                #
                #     self.emgcommand = 10 #Backward
                #     self.sendCommand(self.emgcommand)
                #     self.gritlengthcount += 1
                #     self.clearTestdata()
                #     self.datalocker.set()

                # else:
                self.gritlengthcount = 0
                self.classfier.transform(self.testdata)   # 滤波处理
                self.classfier.apply()                    # 获取相关系数
                self.appendResult(self.classfier.result)
                self.resultDecide()                       # 发送决策结果
                self.clearTestdata()                      # 清除数据缓存
                self.datalocker.set()                     # ？？？？


    def appendResult(self,data):
        self.resultCount[:,np.mod(self.currentPtr,self.addloop)] = data    # 存放的是相关系数 叠加轮次是5轮 0-4
        self.currentPtr += 1

    def resultDecide(self):
        '''
        if np.unique(self.resultCount).shape[0]==1 and not(self.resultCount.all()==0):
            self.sendresult = self.resultCount[0]
            print('classfier result: {}'.format(self.sendresult))
            self.sendCommand(self.sendresult)
        else:
            print('Did not get a result, current result buffer: {}'.format(self.resultCount))
            pass
        '''
        char = ['a','b','c','d','e','f','g','h','i','j','k','l']
        decide = np.sum(self.resultCount,axis=1,keepdims=False)
        maxCoefs = np.array(heapq.nlargest(2,decide))              # 找出decide的最大和次大相关系数
        self.ldaX[0,1:] = maxCoefs
        ldaL = np.dot(self.ldaX,self.ldaW.T)
        ldaP = np.exp(ldaL)/np.tile(np.sum(np.exp(ldaL),axis=1),(1,2))
        if ldaP[0,0]<=ldaP[0,1]:
            self.sendresult = np.argmax(decide)                    # 最大相关系数的索引
            #self.sendCommand(self.sendresult)
            # print('Epoch result: {}'.format(self.settingsfile[str(self.sendresult)]))
            self.sendCommand(char[self.sendresult])
            print('send result!')
            # self.sendCommand(command)
        else:
            print('LDA find the result is not confidential, LDA result: {}'.format(ldaP))

    def sendCommand(self, command):
        msg = bytes(str(command), "utf8")
        print('the result is :{}'.format(msg))
        self.sock_client.sendto(msg, self.controlCenterAddr)

    def clearTestdata(self):
        self.testdata = np.array([0])


if __name__=='__main__':
    filepath = './ExperimentData/weisiwen/'
    data = scio.loadmat(filepath+'testdata.mat')
    testdata = data['testdata']
    data = scio.loadmat(filepath+'TRCA_spatial_filter.mat')
    w = data['W']
    data = scio.loadmat(filepath+'template.mat')
    template = data['template']
    classfier = TRCA(w,template)
    count = 0
    for target in range(testdata.shape[2]):
        currenttestdata = testdata[:,:,target,1]
        start = time.clock()
        classfier.transform(currenttestdata)
        stage1 = time.clock()
        classfier.apply()
        end = time.clock()
        print('Time During: stage1: {}, stage2: {}'.format((stage1-start),(end-stage1)))
        if target == classfier.result:
            count += 1
    acc = count/40
    print(acc)
