function [num,den]=notch_egg(fs,value)
%陷波
w0=50/(fs/2); 
bw=w0/value;
ab = 10;
[num,den] = iirnotch(w0,bw,ab);

%     设计一个数字滤波器，滤除信号中频率为60Hz的频谱成分。设信号采样频率为300Hz，滤波器品质因素为35。
%     MATLAB代码如下
%     Fs = 300;
%     Fo = 60;   想要滤除的信号值
%     Q  = 35;     
%     Wo = Fo/(Fs/2);    %要清除的频率
%     BW = Wo/Q;         %带宽
%     [b, a] = iirnotch(Wo, BW);
%     freqz（b, a, 1024）;

