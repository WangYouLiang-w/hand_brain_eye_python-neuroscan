%  指令集N，分类时间T，分类正确率p
%  信息传输率ITR单位 bit/min
N=11;
T=0.6; %1.8 1.8*2 1.8*3 1.8*4 1.8*5 1.8*6 1.8*7 1.8*8 1.8*9 1.8*10
p=0.8636;
            
if  p==1
    ITR=p*(log2(N))*60/(T)
else if p==0
          ITR=0;
    else
        ITR=(p*log2(p)+(1-p)*log2((1-p)/(N-1))+log2(N))*60/(T)
    end
end
%% 关于指令集M的曲线
N=1:1:300;
p=0.80;
T=1;
y1=(p*log2(p)+(1-p)*log2((1-p)./(N-1))+log2(N))*60./(T);
T=2;
y2=(p*log2(p)+(1-p)*log2((1-p)./(N-1))+log2(N))*60./(T);
T=3;
y3=(p*log2(p)+(1-p)*log2((1-p)./(N-1))+log2(N))*60./(T);
T=4;
y4=(p*log2(p)+(1-p)*log2((1-p)./(N-1))+log2(N))*60./(T);
figure
% subplot(1,2,1)
plot(N,y1,'b','linewidth',1.5);hold on
plot(N,y2,'k','linewidth',1.5);
plot(N,y3,'r','linewidth',1.5);
plot(N,y4,'color',[255,0,255]/255,'linewidth',1.5);hold off;grid on
% axis([0,500,0,270])
text(500,220,'T=1s','FontSize',10);text(500,150,'T=2s','FontSize',10);
text(500,100,'T=3s','FontSize',10);text(500,50,'T=4s','FontSize',10);
xlabel('Instruction Set','FontSize',12,'Fontname','Arial','FontWeight','bold');
ylabel('ITR bits/min','FontSize',12,'Fontname','Arial','FontWeight','bold')
% line([40 40],[0,250],'Color','k','LineWidth',1.5,'LineStyle','--');
% line([108 108],[0,250],'Color','k','LineWidth',1.5,'LineStyle','--');

%% 关于正确率p的曲线
p=0:0.01:1;
N=100;
T=1;
y1=(p.*log2(p)+(1-p).*log2((1-p)./(N-1))+log2(N))*60./(T);
T=2;
y2=(p.*log2(p)+(1-p).*log2((1-p)./(N-1))+log2(N))*60./(T);
T=3;
y3=(p.*log2(p)+(1-p).*log2((1-p)./(N-1))+log2(N))*60./(T);
T=4;
y4=(p.*log2(p)+(1-p).*log2((1-p)./(N-1))+log2(N))*60./(T);
figure
% subplot(1,2,2)
plot(p,y1,'b','linewidth',1.5);hold on
plot(p,y2,'k','linewidth',1.5);
plot(p,y3,'r','linewidth',1.5);
plot(p,y4,'color',[255,0,255]/255,'linewidth',1.5);hold off;grid on
axis([0,1,0,400])
xlabel('Accuracy','FontSize',14,'Fontname','Arial','FontWeight','bold');
ylabel('ITR bits/min','FontSize',14,'Fontname','Arial','FontWeight','bold')
text(1,220,'T=1s','FontSize',10);text(1,150,'T=2s','FontSize',10);
text(1,100,'T=3s','FontSize',10);text(1,50,'T=4s','FontSize',10);
%% 适合正确率矩阵算ITR
% load('F:\硕士文件（韩锦）\硕士文件（韩锦）\原始程序和文件备份\计算ITR\acc_ITRexample.mat')
% acc=[0.9167 0.8750 0.75 0.9167 0.7083 0.8333 0.7083 0.75 0.8750 0.75];
clc
% acc=acc0neTrca';
accBuff=acc';
N=40;
T=0.5+0.8; %1.8 1.8*2 1.8*3 1.8*4 1.8*5 1.8*6 1.8*7 1.8*8 1.8*9 1.8*10
for i=1:size(accBuff,1)
    for j=1
        if  accBuff(i,j)==1;
            ITR(i,j)=accBuff(i,j)*(log2(N))*60/(T(j));
        else if accBuff(i,j)==0;
                ITR(i,j)=0;
            else
                ITR(i,j)=(accBuff(i,j)*log2(accBuff(i,j))+(1-accBuff(i,j))*log2((1-accBuff(i,j))/(N-1))+log2(N))*60/(T(j));
            end
        end
    end
end
ave_itr=mean(ITR')
std_itr=std(ITR')