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
%sumNumEpoch = 3;
% %% 数据提取
% %%%%%%%%PREDEFINE HERE%%%%%%%%%
% stimulitlength = 0.4;
% srate = 250;
% fs = 250;
% delay = 0.14;
% EEG = pop_resample(EEG,250);
% eeg = EEG;
% data = eeg.data;
% event = eeg.event;
% triggernum = size(event,1);
% for eventnum = 1:triggernum
%     triggertype(eventnum,1) = str2num(event(eventnum).type);
%     triggerpos(eventnum,1) = event(eventnum).latency;
% end
% uniquetrigger = unique(triggertype);
% uniquetriggernum = size(unique(triggertype),1);
% for triggernum = 1:uniquetriggernum
%     currenttrigger = uniquetrigger(triggernum);
%     currenttriggerpos = triggerpos(triggertype==currenttrigger);
%     for j = 1:size(currenttriggerpos,1)
%         epoch(:,:,j,uniquetrigger(triggernum))=data(:,floor(currenttriggerpos(j))+0.14*srate+1:floor(currenttriggerpos(j))+0.14*srate+stimulitlength*srate);
%     end
% end
% epoch_mean = mean(epoch,2)
% epoch_mean = repmat(epoch_mean(:,:,:,:),1,100)
% epoch = epoch-epoch_mean;  %中心化处理

%% 滤波
allepoches{1} = epoch;
epochdata = [];
for i = 1:size(allepoches,2)
    epochdata = cat(3,epochdata,allepoches{i});
end
epochdata = permute(epochdata,[2,1,3,4]);
subbandNum = 1;
[f_b50,f_a50] = notch_egg(250,45);
notchdata = filtfilt(f_b50,f_a50,double(epochdata));
Wp=[2*6/fs 2*40/fs];%通带的截止频率为2.75hz--75hz,有纹波
Ws=[2*4/fs 2*(40+2)/fs];%阻带的截止频率
[N,Wn]=cheb1ord(Wp,Ws,4,30);
[f_b,f_a] = cheby1(N,0.5,Wn);%f_b为系统函数的分子，f_a为系统函数的分母。
for subband = 1:subbandNum
    flipdata = flip(notchdata,1);
    currentdata = permute(filtfilt(f_b,f_a,[flipdata;notchdata;flipdata]),[2,1,3,4]);
    filtdata{subband} = currentdata(:,size(flipdata,1)+1:2*size(flipdata,1),:,:);
end
%%
myslice = zeros(30,1); %切片
% 得到训练数据和测试数据的切片
for i = 1:6                                    
    myslice((i-1)*5+1:i*5) = 1;
    testslice(:,i) = myslice;
    trainslice(:,i) = 1-myslice;
    myslice = zeros(30,1);
end

for sumNumEpoch = 1:5
    acc = [];
    for testloop = 1:6
        for subband = 1:subbandNum
            traindata = filtdata{subband}(:,:,logical(trainslice(:,testloop)),:);   % 训练数据 每一类别的5组
            testdata = filtdata{subband}(:,:,logical(testslice(:,testloop)),:);     % 测试数据 每一类别的25组
            for target = 1:size(epochdata,4)
                w = trca_matrix(traindata(:,:,:,target));
                W(:,target,subband) = w(:,1);
            end
            template{subband} = squeeze(mean(traindata,3));
%%
            for testtarget = 1:size(testdata,4)
                for epochnum = 1:size(testdata,3)
                    currentdata = testdata(:,:,epochnum,testtarget);
                    for traintarget = 1:size(traindata,4)
                        coef{testloop,epochnum}(traintarget,subband,testtarget) = corr2(currentdata'*W(:,:,subband),template{subband}(:,:,traintarget)'*W(:,:,subband));
                    end
                end
            end
        end
        b = 1:subbandNum;
        a = b'.^(-1.25)+0.25;
        for epochnum = 1:6-sumNumEpoch
            count = 0;
            for testtarget = 1:10
                decide = 0;
                for add = 1 : sumNumEpoch
                    decide = decide+coef{testloop,epochnum+add-1}(:,:,testtarget);  %提取相关系数
                end
                result = find(decide == max(decide));
                if result == testtarget
                    count = count+1;
                end
            end
            acc(testloop,epochnum) = count/10;
        end
    end
    finalacc(:,sumNumEpoch) = mean(acc,2);
    allacc(sumNumEpoch) = mean(finalacc(:,sumNumEpoch),1);
    fun_GetLdaWIndividual(coef,currentFolder,sumNumEpoch);
end