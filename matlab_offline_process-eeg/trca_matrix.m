function V= trca_matrix(X)
% Task-related component analysis (TRCA)
%   X : eeg data (Num of channels * num of sample points * number of trials)

nChans  = size(X,1);  %8
nTrials = size(X,3);  %30
S = zeros(nChans, nChans);  %8*8

% Computation of correlation matrices
           for trial_i = 1:1:nTrials
            for trial_j = 1:1:nTrials
                %if trial_i ~= trial_j
                    x_i = X(:, :, trial_i);
                    x_j = X(:, :,trial_j);
                    S = S + x_i*x_j';
                %end %if
            end % trial_j
        end % trial_i
        
X1 = X(:,:);
X1 = X1 - repmat(mean(X1,2),1,size(X1,2));
Q = X1*X1';

% TRCA eigenvalue algorithm
[V,D] = eig(Q\S);
%Y = V'*X;