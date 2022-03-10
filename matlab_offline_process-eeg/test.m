subjectName = '2021';
block = 'block4';
currentFolder = ['C:\Users\wyl\Desktop','\',subjectName,'\',block,'\'];

EEG = readbdfdata({'data.bdf','evt.bdf'},'C:\Users\wyl\Desktop\wyl2\xfr\block1\');
EEG = pop_resample(EEG,250) ; % 降采样250HZ
eeg = EEG;
data = eeg.data;     %脑电数据
sumNumEpoch = 1;
template = squeeze(mean(data,3));  % 第三维求均值
save([currentFolder,['template_',num2str(sumNumEpoch)]],'template');



