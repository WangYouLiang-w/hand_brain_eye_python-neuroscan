function ldaW = Return_GetLDAw(filtdata,step)
myslice = zeros(30,1);
for i = 1:6
    myslice((i-1)*5+1:i*5) = 1;
    testslice(:,i) = myslice;
    trainslice(:,i) = 1-myslice;
    myslice = zeros(30,1);
end
b = 1;
a = b'.^(-1.25)+0.25;
right = [];
wrong = [];
for testloop = 1:6
    traindata = filtdata(:,:,logical(trainslice(:,testloop)),:);
    testdata = filtdata(:,:,logical(testslice(:,testloop)),:);
    for target = 1:12
        w = trca_matrix(traindata(:,:,:,target));
        W(:,target) = w(:,1);
    end
    template = squeeze(mean(traindata,3));
    for testtarget = 1:size(testdata,4)
        for epochnum = 1:size(testdata,3)
            currentdata = testdata(:,:,epochnum,testtarget);
            for traintarget = 1:size(traindata,4)
                coef{testloop,epochnum}(traintarget,testtarget) = corr2(currentdata'*W(:,:),template(:,:,traintarget)'*W(:,:));
            end
        end
    end
end
%step = 2;
for block = 1:6
    for startpoint = 0:5-step
        for testtarget = 1:size(coef{1},2)
            currentdecide = zeros(12,1);
            for epoch = startpoint+1 : startpoint+step
                currentcoef = coef{block,epoch};
                decidecoef = currentcoef(:,testtarget)*a;
                currentdecide = currentdecide + decidecoef;
            end
            result = find(currentdecide == max(currentdecide));
            sortresult = sort(currentdecide,'descend');
            if result == testtarget
                right = [right,sortresult(1:2)];
            else
                wrong = [wrong,sortresult(1:2)];
            end
        end
    end
end
X = [right';wrong'];
Y = [ones(size(right,2),1);zeros(size(wrong,2),1)];
ldaW = LDA(X,Y);