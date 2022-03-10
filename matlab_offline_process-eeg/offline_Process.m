srate = 250;
fs = 250;
stimulitlength = 0.6;
delay = 0.14;
finalacc = zeros(6,16);
for notchvalue = 15
    for i = 3
        %eeg = readbdfdata({'data.bdf','evt.bdf'},[pathname,'\',filename,'\']);
        eeg = EEG;
        eeg = pop_resample(eeg,srate);
        data = eeg.data;
        event = eeg.event;
        triggernum = size(event,1);
        for eventnum = 1:triggernum
            triggertype(eventnum,1) = str2double(event(eventnum).type);
            triggerpos(eventnum,1) = event(eventnum).latency;
        end
        uniquetrigger = unique(triggertype);
        uniquetriggernum = size(unique(triggertype),1);
        for triggernum = 1:uniquetriggernum
            currenttrigger = uniquetrigger(triggernum);
            currenttriggerpos = triggerpos(triggertype==currenttrigger);
            stinum = length(currenttriggerpos)/5;
            for j = 1:stinum
                for step = 1:3
                    epoch(:,:,(j-1)*3+step,uniquetrigger(triggernum))=data(:,floor(currenttriggerpos((j-1)*5+step))+0.14*srate+1:floor(currenttriggerpos((j-1)*5+step))+0.14*srate+stimulitlength*srate);
                    %epoch(:,:,(j-1)+step,uniquetrigger(triggernum))=data(:,floor(currenttriggerpos((j-1)+step))+0.14*srate+1:floor(currenttriggerpos((j-1)+step))+0.14*srate+stimulitlength*srate);
                end
            end
        end
        epoch = (epoch - mean(epoch,2));
        allepoches{i-2} = epoch;
    end
    epochdata = [];
    for i = 1:size(allepoches,2)
        epochdata = cat(3,epochdata,allepoches{i});
    end
    %channels = [43,50,51,52,53,54,57,58,59];
    % Filter
    subbandNum = 1;
    load('filterModel.mat');
    epochdata = permute(epochdata,[2,1,3,4]);
    % Notch
    % f_b50 = filterModel.f_b50;
    % f_a50 = filterModel.f_a50;
    [f_b50,f_a50] = notch_egg(srate,notchvalue);
    notchdata = filtfilt(f_b50,f_a50,double(epochdata));
    
    
    Wp=[2*6/fs 2*40/fs];%通带的截止频率为2.75hz--75hz,有纹波
    Ws=[2*4/fs 2*(40+2)/fs];%阻带的截止频率
    [N,Wn]=cheb1ord(Wp,Ws,4,30);
    [f_b,f_a] = cheby1(N,0.5,Wn);%f_b为系统函数的分子，f_a为系统函数的分母。
    
    
    for subband = 1:subbandNum
%         f_b = filterModel.f_b{subband};
%         f_a = filterModel.f_a{subband};
        filtdata{subband} = permute(filtfilt(f_b,f_a,notchdata),[2,1,3,4]);
    end
        myslice = zeros(18,1);
        for i = 1:6
            myslice((i-1)*3+1:i*3) = 1;
            testslice(:,i) = myslice;
            trainslice(:,i) = 1-myslice;
            myslice = zeros(18,1);
        end
%     myslice = zeros(6,1);
%     for i = 1:6
%         myslice((i-1)+1) = 1;
%         testslice(:,i) = myslice;
%         trainslice(:,i) = 1-myslice;
%         myslice = zeros(6,1);
%     end
    
    %%%%%%%%Delate Later%%%%%%%%
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
        b = 1:5;
        a = b'.^(-1.25)+0.25;
        count = 0;
        % for testtarget = 1:11
        %     decide = coef(:,:,testtarget)*a;
        %     result = find(decide == max(decide));
        %     if result == testtarget
        %         count = count+1;
        %     end
        % end
        % acc = count/11;
        
        %     for loop = 1:size(testdata,3)
        %         currentcoef = coef{loop};
        %         count = 0;
        %         for testtarget = 1:11
        %             decide = currentcoef(:,:,testtarget)*a;
        %             result = find(decide == max(decide));
        %             if result == testtarget
        %                 count = count+1;
        %             end
        %         end
        %         acc(testloop,loop) = count/11;
        %     end
        for loop = 1:3
            count = 0;
            for testtarget = 1:11
                currentcoef = coef{testloop,loop};
                currentdecide = currentcoef(:,:,testtarget);
                result = find(currentdecide == max(currentdecide));
                if result == testtarget
                    count = count+1;
                end
            end
            acc(testloop,loop) = count/11;
        end
        
        %         for testtarget = 1:11
        %             currentdecide = zeros(11,1);
        %             for loop = 1:notchvalue
        %                 currentcoef = coef{testloop,loop};
        %                 decide = currentcoef(:,:,testtarget)*a;
        %                 currentdecide = currentdecide + decide;
        %             end
        %             result = find(currentdecide == max(currentdecide));
        %             if result == testtarget
        %                 count = count+1;
        %             end
        %         end
        %         acc(testloop) = count/11;
        %     end
        %
        %     accfinal(notchvalue,:) = acc;
        
        %     temp = template;
        %     template = [];
        %     for i = 1:size(temp,2)
        %         template = cat(4,template,temp{i});
        %     end
    end
    finalacc(:,notchvalue/5) = mean(acc,2);
end




%%%%%%%%Keep Later%%%%%%%%%%
% % Get spatial filter of TRCA
% for target = 1:size(epochdata,4)
%     for subband = 1:subbandNum
%         w = trca_matrix(filtdata{subband}(:,:,:,target));
%         W(:,target,subband) = w(:,1);
%     end
% end
% % Get template
% for subband = 1:subbandNum
%     template{subband} = squeeze(mean(filtdata{subband},3));
% end
