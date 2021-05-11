%=======================================
% This function GF_attack performs GF flush attack after flushing 0s into scan chain and capture corresponding scan outputs.
% Input:
%	num_FF: number of flip-flops in the circuit
% 	key_gate_pos: the positions of key gates extracted from DOSC verilog
%	c_file: LFSR structure file extracted from DOSC verilog
%	scan_out_file: the file containing scan outputs after flushing 0s into scan chain.
%=======================================

function GFF_attack(num_FF, key_gate_pos, c_file, scan_out_file)
	c=readmatrix(c_file);
	scan_out=readmatrix(scan_out_file);
	Matrix_Key=readmatrix(key_gate_pos);
	num_Key=numel(Matrix_Key);
	disp(num_Key);
	fileID = fopen('outputs.txt','w');
	tic;
	A=generate_out_matrix_A_with_c(c,num_Key,num_Key,Matrix_Key);
	t1=toc;
	
	rank=gfrank(A);
	if rank==num_Key
		tic;
		recover_result=gflineq(A,scan_out,2);
		t2=toc;
	else
		A=gf(A);
		tic;
		B=gf2null(A);
		t2=toc;
	end


	if rank==num_Key
		fprintf(fileID,'Attack succeeds for num_Key=%i, time elapse=%f \n', num_Key,t1+t2);
	else
		fprintf(fileID,'Generate homogeneous solution for num_Key=%i, time elapse=%f, the rank different=%i, rank=%i\n', num_Key,t1+t2,num_Key-rank,rank);
	end
	fclose(fileID);
end

function [A] = generate_out_matrix_A_with_c(c, num_Key,num_FF, Matrix_Key)	
	pow_T= Matrix_Key(numel(Matrix_Key))+1; % first 0 arrives at last key gate
	
	B=zeros(num_Key,num_Key); % base transition matrix of LFSR
	B(num_Key,:)=c;
    for idx=num_Key:-1:2
        B(idx-1, idx)=1;
    end
    
    T=zeros(num_Key,num_Key,pow_T);
    T(:,:,1)=eye(num_Key);
    
    for idx=2:pow_T
        T(:,:,idx)=T(:,:,idx-1)*B;
        T(:,:,idx)=mod(T(:,:,idx),2);
    end
    
    r=eye(num_Key);
    A=zeros(num_Key,num_Key);
	for j=0:num_Key-1
		A(1,:)=A(1,:)+r(j+1,:)*T(:,:,Matrix_Key(1+j)+1);
	end
	A(1,:)=mod(A(1,:),2);
    
    for i=2:num_Key

		A(i,:)=A(i-1,:)*B;
        
        A(i,:)=mod(A(i,:),2);
    end
end



function Z = gf2null(A)
%GF2NULL   Null space over GF(2)
%   Z = GF2NULL(A) is an orthonormal basis for the null space of A 
%   over GF(2). That is,  A*Z becomes zero matrix.
%   size(Z,2) is the nullity of A.
%
%   Example:
%
%      A = gf( randi([0 1], 3 ));
%      A = GF(2) array. 
%      Array elements = 
%        0   0   1
%        1   1   1
%        1   1   0
%
%      Z = gf2null(A)
%      Z = GF(2) array. 
%      Array elements = 
%        1
%        1
%        0
%
%      A * Z
%      ans = GF(2) array. 
%      Array elements = 
%        0
%        0
%        0
%
%   Class support for input A:
%      gf
%
%   See also GF2RREF, RANK, NULL.
%
%   Modified by bjc97r@inu.ac.kr on 2018-11-24
%   Based on gfnull.m by Mark Wilde, 201
%         at matlabcentral/fileexchange/28633-gfnull
%   Based on null.m by MathWorks
%   Copyright 1984-2004 The MathWorks, Inc.
%   $Revision: 5.12.4.2 $  $Date: 2004/04/10 23:30:03 $
%
n = size(A, 2);
assert( isa(A,'gf'), 'gfnull expects GF(2) matrix as input.');
[R, pivcol] = gf2rref(A); % reduced row-echelon form of A over GF(2)
r = length(pivcol); % rank
nopiv = 1:n;
nopiv(pivcol) = [];
Z = gf(zeros(n,n-r));
if n > r
    Z(nopiv,:) = gf(eye(n-r,n-r));
    if r > 0
        Z(pivcol,:) = -R(1:r,nopiv);
    end
end
end

function [A,jb] = gf2rref(A)
%GF2RREF   Reduced row echelon form over GF(2)
%   R = GF2RREF(A) produces the reduced row echelon form of A over GF(2).
%
%   [R,jb] = GFRREF(A) also returns a vector, jb, so that:
%       r = length(jb) is this algorithm's idea of the rank of A,
%       x(jb) are the bound variables in a linear system, Ax = b,
%       A(:,jb) is a basis for the range of A,
%       R(1:r,jb) is the r-by-r identity matrix.
%
%   Example:
%
%      A = gf( randi([0 1], 4 ))
%
%      A = GF(2) array. 
%      Array elements = 
%         0   0   1   1
%         0   1   0   0
%         0   1   1   1
%         0   1   0   0
%      
%      [R, jb] = gf2rref(A)
%
%      R = GF(2) array. 
%      Array elements = 
%         0   1   0   0
%         0   0   1   1
%         0   0   0   0
%         0   0   0   0
%
%      jb =
%           2     3
%
%   Class support for input A:
%      gf
%
%   See also GF2NULL, RANK, RREF.
%
%
%   Modified by bjc97r@inu.ac.kr on 2018-11-24
%
%   Based on gfrref.m by Mark Wilde, 2010
%         at matlabcentral/fileexchange/28633-gfnull
%   Based on rref.m by MathWorks
%   Copyright 1984-2017 The MathWorks, Inc. 
assert(isa(A,'gf'),'A is type %s, not gf.',class(A))
[m, n] = size(A);
% Loop over the entire matrix.
i  = 1;
j  = 1;
jb = [];
while (i <= m) && (j <= n)
   % Find index of nonzero element in the remainder of column j.
   tmp1 = A(i:m,j);
   k    = find(tmp1.x,1);
   if isempty(k)
      j = j + 1;
   else
      k = k+i-1; % absolute row index
      % Remember column index
      jb = [jb j];
      % Swap i-th and k-th rows.
      A([i k],j:n) = A([k i],j:n);
      % Add the pivot row to all the other rows where j-th element is 1.
      tmp1 = A(:,j); ks = find(tmp1.x); ks(ks==i) = [];
      A(ks,j:n) = A(ks,j:n) + repmat( A(i, j:n), length(ks), 1);
      i = i + 1;
      j = j + 1;
   end
end
end
