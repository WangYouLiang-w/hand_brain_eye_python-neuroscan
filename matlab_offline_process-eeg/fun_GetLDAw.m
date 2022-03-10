function fun_GetLDAw(coef,currentFolder)
b = 1;
a = b'.^(-1.25)+0.25;
right = [];
wrong = [];
step = 3;
for block = 1:6
    for startpoint = 0:5-step
        for testtarget = 1:size(coef{1},3)
            currentdecide = zeros(12,1);
            for epoch = startpoint+1 : startpoint+step
                currentcoef = coef{block,epoch};
                decidecoef = currentcoef(:,:,testtarget)*a;
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
save([currentFolder,'ldaW'],'ldaW');