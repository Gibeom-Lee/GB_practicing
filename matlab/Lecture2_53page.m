
clc; clear; close all;

%% 1. Given parameters
inch = 0.0254;

ri = 0.75*inch;
rc = 1.50*inch;
ro = 1.75*inch;
L = 4*inch;

k_lam = 32;
k_ep = 1.8;
k_c = 232;

h = 10;
eps = 0.7;
sigma = 5.67e-8;

T_sur = 20;
q0 = 1000;

%% 2. Heat transfer and thermal resistance
Ai = 2*pi*ri*L;
Ao = 2*pi*ro*L;

Q = q0*Ai;

f_lam = 0.065/(0.065+0.025);
f_ep = 1-f_lam;

k_eff = f_lam*k_lam + f_ep*k_ep;

R_lam = log(rc/ri)/(2*pi*L*k_eff);
R_c = log(ro/rc)/(2*pi*L*k_c);

%% 3. Calculate temperatures
Q_out = @(Ts) Ao*( ...
    h*(Ts-T_sur) + ...
    eps*sigma*((Ts+273.15)^4 ...
    -(T_sur+273.15)^4));

Ts = fzero(@(T) Q_out(T)-Q,[20 200]);

T_interface = Ts + Q*R_c;
T_inner = T_interface + Q*R_lam;

%% 4. Temperature at each point
T = [T_sur, Ts, T_interface, T_inner];

%% 5. Heat flux at each point
q_outer = Q/Ao;
q_interface = Q/(2*pi*rc*L);
q_inner = Q/Ai;

q = [NaN, q_outer, q_interface, q_inner];

%% 6. Plot
labels = {'T_{sur}','T_s','T_{interface}','T_{inner}'};
x = 1:4;

figure('Color','w','Position',[200 200 900 650]);

% Temperature plot
subplot(2,1,1)
plot(x,T,'-or','LineWidth',2,'MarkerFaceColor','r');
xticks(x);
xticklabels(labels);
xlim([0.8 4.2]);
ylabel('Temperature (°C)');
title('Temperature Distribution');
grid on;

for i = 1:4
    text(x(i),T(i)+0.5,sprintf('%.2f',T(i)), ...
        'HorizontalAlignment','center');
end

% Heat flux plot
subplot(2,1,2)
plot(x,q,'-ob','LineWidth',2,'MarkerFaceColor','b');
xticks(x);
xticklabels(labels);
xlim([0.8 4.2]);
ylim([0 1150]);
ylabel('Heat Flux (W/m^2)');
title('Heat Flux Distribution');
grid on;

for i = 2:4
    text(x(i),q(i)+35,sprintf('%.1f',q(i)), ...
        'HorizontalAlignment','center');
end

%% 7. Results
fprintf('T_sur       = %.2f C\n',T_sur);
fprintf('T_s         = %.2f C\n',Ts);
fprintf('T_interface = %.2f C\n',T_interface);
fprintf('T_inner     = %.2f C\n',T_inner);

fprintf('\nHeat flux:\n');
fprintf('Outer       = %.2f W/m^2\n',q_outer);
fprintf('Interface   = %.2f W/m^2\n',q_interface);
fprintf('Inner       = %.2f W/m^2\n',q_inner);