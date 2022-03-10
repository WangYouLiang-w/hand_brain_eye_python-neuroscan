subjectName = 'sunjinsong';
block = 'block4';
stimulitlength = 0.5;
currentFolder = ['F:\meijie\ThesisData\',subjectName, '\', block,'\'];
load([currentFolder,'EEG'])

%%%%%%%%PREDEFINE HERE%%%%%%%%%
srate = 250;
fs = 250;
delay = 0.14;
EEG = pop_resample(EEG,250);
eeg = EEG;
data = eeg.data;
event = eeg.event;
triggernum = size(event,1);
for eventnum = 1:triggernum
    triggertype(eventnum,1) = str2num(event(eventnum).type);
    triggerpos(eventnum,1) = event(eventnum).latency;
end
uniquetrigger = unique(triggertype);
uniquetriggernum = size(unique(triggertype),1);
for triggernum = 1:uniquetriggernum
    currenttrigger = uniquetrigger(triggernum);
    currenttriggerpos = triggerpos(triggertype==currenttrigger);
    for j = 1:size(currenttriggerpos,1)
        epoch(:,:,j,uniquetrigger(triggernum))=data(:,floor(currenttriggerpos(j))+0.14*srate+1:floor(currenttriggerpos(j))+0.14*srate+stimulitlength*srate);
    end
end
epoch = (epoch - mean(epoch,2));
allepoches{1} = epoch;
epochdata = [];
for i = 1:size(allepoches,2)
    epochdata = cat(3,epochdata,allepoches{i});
end
epochdata = permute(epochdata,[2,1,3,4]);
subbandNum = 1;
load('filterModel.mat');
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

myslice = zeros(30,1);
for i = 1:6
    myslice((i-1)*5+1:i*5) = 1;
    testslice(:,i) = myslice;
    trainslice(:,i) = 1-myslice;
    myslice = zeros(30,1);
end
for testloop = 1:6
    for subband = 1:subbandNum
        traindata = filtdata{subband}(:,:,logical(trainslice(:,testloop)),:);
        testdata = filtdata{subband}(:,:,logical(testslice(:,testloop)),:);
        for target = 1:size(epochdata,4)
            w = trca_matrix(traindata(:,:,:,target));
            W(:,target,subband) = w(:,1);
        end
        template{subband} = squeeze(mean(traindata,3));
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
    for epochnum = 1:3
        count = 0;
        for testtarget = 1:12
            currentcoef = coef{testloop,epochnum}(:,:,testtarget);
            currentcoef1 = coef{testloop,epochnum+1}(:,:,testtarget);
            currentcoef2 = coef{testloop,epochnum+2}(:,:,testtarget);
            decide = (currentcoef+currentcoef1+currentcoef2)*a;
            sumcoef{epochnum}(:,testtarget) = (currentcoef+currentcoef1+currentcoef2);
            result = find(decide == max(decide));
            if result == testtarget
                count = count+1;
            end
        end
        acc(testloop,epochnum) = count/12;
    end
end
finalacc = mean(acc,2);
allacc = mean(finalacc,1);
fun_GetLDAw(coef,currentFolder);