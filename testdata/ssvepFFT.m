
clear;
clc;
close all;

file ='fft1.txt'; 

light_= textread(file,'%s');
data_N1=length(light_);

fs = 500;          %采样率

stitime = 5;        %刺激时间
datafilter = 1;     %数据是否滤波 1 0
fitleft = 7;        %带通滤波
fitright = 20;      %带通滤波
figure(1)
lightuse = str2num (char(light_));
N = 3;
plot(lightuse(512*N+1:512*N+512));

ylabel('幅值/mV', 'fontsize', 15)
xlabel('counts','fontsize', 15);
title('原始波形','fontsize', 15) 

x_min = 0;  % 实际显示坐标轴
x_max = 60; % 实际显示坐标轴
y_min = 0;  % 实际显示坐标轴
y_max = 500;  % 实际显示坐标轴
figure(2)
 len1 = 1000;
 len1 = length(lightuse);
  Fy1 = fft(lightuse,len1);
  Pyy1 = abs(Fy1)*2/len1;             %FFT后纵坐标uv
  Pyy1_new = Pyy1(1:(len1)/2+2);
  db = 20*log10(Pyy1);
  f1 = fs/length(Pyy1)*(0:(len1)/2+1);%FFT后横坐标Hz
  plot(f1(1:(len1)/2+2),Pyy1(1:(len1)/2+2));
  axis([x_min,x_max,y_min,y_max]);




