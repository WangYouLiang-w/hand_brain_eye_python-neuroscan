%%
clc;
clear;
%% 数据提取
subjectName = 'wyl';
datapath = 'E:\wyl\block';
%%%%%%%%PREDEFINE HERE%%%%%%%%%
for i = 1:6
    switch i
        case (1)
            EEG = pop_loadcnt('E:\wyl\block\1.cnt');
        case (2)
            EEG = pop_loadcnt('E:\wyl\block\2.cnt');
        case (3)
            EEG = pop_loadcnt('E:\wyl\block\3.cnt');
        case (4)
            EEG = pop_loadcnt('E:\wyl\block\4.cnt');
        case (5)
            EEG = pop_loadcnt('E:\wyl\block\5.cnt');
        case (6)
            EEG = pop_loadcnt('E:\wyl\block\6.cnt');
    end
%     EEG = pop_loadcnt([datapath '\block' num2str(i) '.cnt']);
%     EEG = pop_loadcnt('E:\wyl\block\1.cnt');
    stimulitlength = 0.4; %刺激长度 每个标签：采集250*0.5 = 125个脑电数据
    srate = 250;
    fs = 250;
    delay = 0.14;
    EEG = pop_resample(EEG,250);
    eeg = EEG;
    data = eeg.data;
    data = [data(1,:);data(3:9,:)];
    event = eeg.event;
%     triggernum = size(event,1);
    triggernum = 60;
    for eventnum = 1:triggernum
%         triggertype(eventnum,1) = str2num(event(eventnum).type);
        triggertype(eventnum,1) = event(eventnum).type;
%         triggertype(eventnum,1) = cell2mat({event(eventnum).type});
        triggerpos(eventnum,1) = event(eventnum).latency;
    end
%     triggertype = cell2mat({event.type});
%     triggerpos = round(cell2mat({event.latency}));
    uniquetrigger = unique(triggertype);
    uniquetriggernum = size(unique(triggertype),1);
    for triggernum = 1:uniquetriggernum
        currenttrigger = uniquetrigger(triggernum);
        currenttriggerpos = triggerpos(triggertype==currenttrigger);
        for j = 1:size(currenttriggerpos,1)
            epoch(:,:,j,uniquetrigger(triggernum))=data(:,floor(currenttriggerpos(j))+0.14*srate+1:floor(currenttriggerpos(j))+0.14*srate+stimulitlength*srate);
        end
    end
    epoch_mean = mean(epoch,2);
    epoch_mean = repmat(epoch_mean(:,:,:,:),1,stimulitlength*srate);
    epoch = epoch-epoch_mean;  %中心化处理
    epochdatas{1,i} = epoch;       
end
epoch = cat(3,epochdatas{1,1},epochdatas{1,2});
epoch = cat(3,epoch,epochdatas{1,3});
epoch = cat(3,epoch,epochdatas{1,4});
epoch = cat(3,epoch,epochdatas{1,5});
epoch = cat(3,epoch,epochdatas{1,6});
%%
subjectName = 'data';
block = 'block';
currentFolder = ['E:\wyl','\',subjectName,'\'];

% 这里就是为了复制一个新的4维矩阵？
allepoches{1} = epoch;
epochdata = []; 
for i = 1:size(allepoches,2)
    epochdata = cat(3,epochdata,allepoches{i});  
end
epochdata = permute(epochdata,[2,1,3,4]);

%% --滤波处理
% 陷波滤波器指的是一种可以在某一个频率点迅速衰减输入信号，
% 以达到阻碍此频率信号通过的滤波效果的滤波器。陷波滤波器属于带阻滤波器的一种，
%50HZ的陷波器
subbandNum = 1;
[f_b50,f_a50] = notch_egg(250,45);    %陷波滤波返回滤波器系数矩阵
notchdata = filtfilt(f_b50,f_a50,double(epochdata)); %

Wp=[2*6/fs 2*40/fs];%通带的截止频率为2.75hz--75hz,有纹波
Ws=[2*4/fs 2*(40+2)/fs];%阻带的截止频率
[N,Wn]=cheb1ord(Wp,Ws,4,30);  %返回Chebyshev类型I滤波器的最低阶n，该滤波器在通带中损失不超过4dB，并且在阻带中具有至少30dB的衰减。还返回相应截止频率Wp的标量（或矢量）。
[f_b,f_a] = cheby1(N,0.5,Wn);% 切比雪夫I型滤波器设计 返回滤波器系数矩阵 f_b为系统函数的分子，f_a为系统函数的分母。

for subband = 1:subbandNum                                                     
    flipdata = flip(notchdata,1); %反转每一列的元素
    currentdata = permute(filtfilt(f_b,f_a,[flipdata;notchdata;flipdata]),[2,1,3,4]); 
    filtdata{subband} = currentdata(:,size(flipdata,1)+1:2*size(flipdata,1),:,:);
end

%% 计算权重矩阵和模板
for target = 1:size(epochdata,4)   %10
    w = trca_matrix(filtdata{subband}(:,:,:,target));  % TRCA
    W(:,target) = w(:,1);                      
end
template = squeeze(mean(filtdata{subband},3));  % 第三维求均值

save([currentFolder,'template'],'template');
save([currentFolder,'W'],'W');
save([currentFolder,'data'],'epochdata');
