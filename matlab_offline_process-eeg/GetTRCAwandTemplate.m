%%
clc;
clear;
%% ������ȡ
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
    stimulitlength = 0.4; %�̼����� ÿ����ǩ���ɼ�250*0.5 = 125���Ե�����
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
    epoch = epoch-epoch_mean;  %���Ļ�����
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

% �������Ϊ�˸���һ���µ�4ά����
allepoches{1} = epoch;
epochdata = []; 
for i = 1:size(allepoches,2)
    epochdata = cat(3,epochdata,allepoches{i});  
end
epochdata = permute(epochdata,[2,1,3,4]);

%% --�˲�����
% �ݲ��˲���ָ����һ�ֿ�����ĳһ��Ƶ�ʵ�Ѹ��˥�������źţ�
% �Դﵽ�谭��Ƶ���ź�ͨ�����˲�Ч�����˲������ݲ��˲������ڴ����˲�����һ�֣�
%50HZ���ݲ���
subbandNum = 1;
[f_b50,f_a50] = notch_egg(250,45);    %�ݲ��˲������˲���ϵ������
notchdata = filtfilt(f_b50,f_a50,double(epochdata)); %

Wp=[2*6/fs 2*40/fs];%ͨ���Ľ�ֹƵ��Ϊ2.75hz--75hz,���Ʋ�
Ws=[2*4/fs 2*(40+2)/fs];%����Ľ�ֹƵ��
[N,Wn]=cheb1ord(Wp,Ws,4,30);  %����Chebyshev����I�˲�������ͽ�n�����˲�����ͨ������ʧ������4dB������������о�������30dB��˥������������Ӧ��ֹƵ��Wp�ı�������ʸ������
[f_b,f_a] = cheby1(N,0.5,Wn);% �б�ѩ��I���˲������ �����˲���ϵ������ f_bΪϵͳ�����ķ��ӣ�f_aΪϵͳ�����ķ�ĸ��

for subband = 1:subbandNum                                                     
    flipdata = flip(notchdata,1); %��תÿһ�е�Ԫ��
    currentdata = permute(filtfilt(f_b,f_a,[flipdata;notchdata;flipdata]),[2,1,3,4]); 
    filtdata{subband} = currentdata(:,size(flipdata,1)+1:2*size(flipdata,1),:,:);
end

%% ����Ȩ�ؾ����ģ��
for target = 1:size(epochdata,4)   %10
    w = trca_matrix(filtdata{subband}(:,:,:,target));  % TRCA
    W(:,target) = w(:,1);                      
end
template = squeeze(mean(filtdata{subband},3));  % ����ά���ֵ

save([currentFolder,'template'],'template');
save([currentFolder,'W'],'W');
save([currentFolder,'data'],'epochdata');
