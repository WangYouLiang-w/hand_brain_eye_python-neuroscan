function [num,den]=notch_egg(fs,value)
%�ݲ�
w0=50/(fs/2); 
bw=w0/value;
ab = 10;
[num,den] = iirnotch(w0,bw,ab);

%     ���һ�������˲������˳��ź���Ƶ��Ϊ60Hz��Ƶ�׳ɷ֡����źŲ���Ƶ��Ϊ300Hz���˲���Ʒ������Ϊ35��
%     MATLAB��������
%     Fs = 300;
%     Fo = 60;   ��Ҫ�˳����ź�ֵ
%     Q  = 35;     
%     Wo = Fo/(Fs/2);    %Ҫ�����Ƶ��
%     BW = Wo/Q;         %����
%     [b, a] = iirnotch(Wo, BW);
%     freqz��b, a, 1024��;

