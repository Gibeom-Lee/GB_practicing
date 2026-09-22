
% MATLAB Test

clc;
clear;
close all;

% Generate data
x = 0:0.01:2*pi;
y = sin(x);

% Plot
figure;
plot(x, y, 'r-', 'LineWidth', 5);

xlabel('Time (s)');
ylabel('Amplitude');
title('Sine Wave');
grid on;