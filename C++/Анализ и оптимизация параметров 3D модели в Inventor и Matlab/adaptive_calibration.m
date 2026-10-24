%% adaptive_calibration.m
% Адаптивная калибровка модели кривошипно-шатунного механизма
% на основе дифференциальной эволюции (DE) с использованием данных из CSV

clear; clc; close all;

%% 1. Загрузка "реальных" данных (Inventor)
data_ref = readmatrix('reference_data.csv');
t_ref = data_ref(:,1);
x_ref = data_ref(:,2);
y_ref = data_ref(:,3);

%% 3. Целевая функция: RMSE между моделью и "реальными" данными
obj_fun = @(params) objective_function(params, t_ref, x_ref, y_ref);

%% 4. Ограничения на параметры (мeters)
bounds = [
    0.08, 0.16;  % L1: кривошип
    0.28, 0.36;  % L2: шатун
    0.04, 0.08   % L3: смещение
];

%% 5. Оптимизация с помощью дифференциальной эволюции (DE)
options = optimoptions('ga', ...
    'PopulationSize', 40, ...
    'MaxGenerations', 100, ...
    'Display', 'iter', ...
    'PlotFcn', {@gaplotbestf, @gaplotbestindiv});

fprintf('🚀 Запуск адаптивной калибровки...\n');
[best_params, rmse_best] = ga(obj_fun, 3, [], [], [], [], bounds(:,1), bounds(:,2), [], options);

fprintf('\n✅ Калибровка завершена:\n');
fprintf(' L1 = %.6f м\n', best_params(1));
fprintf(' L2 = %.6f м\n', best_params(2));
fprintf(' L3 = %.6f м\n', best_params(3));
fprintf(' RMSE = %.6f м\n', rmse_best);

%% 6. Визуализация: до и после калибровки
L1_init = mean(bounds(:,1)); % начальное приближение
L2_init = mean(bounds(:,2));
L3_init = mean(bounds(:,3));

[t_init, x_init, y_init] = crank_slider_model(L1_init, L2_init, L3_init, 10, 2, 0.01);
[t_opt, x_opt, y_opt] = crank_slider_model(best_params(1), best_params(2), best_params(3), 10, 2, 0.01);

% Интерполяция на реальные временные точки
x_init_interp = interp1(t_init, x_init, t_ref, 'linear', 'extrap');
y_init_interp = interp1(t_init, y_init, t_ref, 'linear', 'extrap');
x_opt_interp = interp1(t_opt, x_opt, t_ref, 'linear', 'extrap');
y_opt_interp = interp1(t_opt, y_opt, t_ref, 'linear', 'extrap');

% Построение графиков
figure('Position', [100, 100, 1200, 600]);

% График 1: Траектория X
subplot(1,2,1);
plot(t_ref, x_ref, 'k-', 'LineWidth', 1.5, 'DisplayName', 'Имитация Inventor');
hold on;
plot(t_ref, x_init_interp, 'r--', 'LineWidth', 1.2, 'DisplayName', 'Модель до калибровки');
plot(t_ref, x_opt_interp, 'b-', 'LineWidth', 1.5, 'DisplayName', 'Модель после калибровки');
title('Координата X центра шатуна');
xlabel('Время, с');
ylabel('X, м');
grid on;
legend('Location', 'best');

% График 2: Траектория Y
subplot(1,2,2);
plot(t_ref, y_ref, 'k-', 'LineWidth', 1.5, 'DisplayName', 'Имитация Inventor');
hold on;
plot(t_ref, y_init_interp, 'r--', 'LineWidth', 1.2, 'DisplayName', 'Модель до калибровки');
plot(t_ref, y_opt_interp, 'b-', 'LineWidth', 1.5, 'DisplayName', 'Модель после калибровки');
title('Координата Y центра шатуна');
xlabel('Время, с');
ylabel('Y, м');
grid on;
legend('Location', 'best');

suptitle('Адаптивная калибровка модели кривошипно-шатунного механизма');

%% 2. Модель кривошипно-шатунного механизма (аналитическая)
function [t, x_C, y_C] = crank_slider_model(L1, L2, L3, omega, t_end, dt)
    % Проверка на допустимость параметров
    if L1 <= 0 || L2 <= 0 || L3 < 0
        t = [];
        x_C = [];
        y_C = [];
        return;
    end

    t = 0:dt:t_end;
    theta = omega * t;
    x_A = L1 * cos(theta);
    y_A = L1 * sin(theta);
    y_B = L3 * ones(size(theta));

    % Проверка: чтобы выражение под корнем было неотрицательным
    diff_sq = (y_B - y_A).^2;
    radicand = L2^2 - diff_sq;

    % Если хотя бы один элемент отрицательный — возвращаем NaN
    if any(radicand < 0)
        % Возвращаем "плохой" результат — GA будет его отбрасывать
        x_C = NaN(size(t));
        y_C = NaN(size(t));
        return;
    end

    x_B = x_A + sqrt(radicand);  % правое решение
    x_C = (x_A + x_B) / 2;
    y_C = (y_A + y_B) / 2;
end

%% 3. Целевая функция: RMSE между моделью и "реальными" данными
function rmse = objective_function(params, t_ref, x_ref, y_ref)
    L1 = params(1);
    L2 = params(2);
    L3 = params(3);
    omega = 10; % фиксировано
    t_end = 2;
    dt = 0.01;

    [t_model, x_C_model, y_C_model] = crank_slider_model(L1, L2, L3, omega, t_end, dt);

    % Если модель вернула пустые или невалидные данные — штраф
    if isempty(t_model) || any(isnan(x_C_model)) || any(isnan(y_C_model))
        rmse = 1e6; % Большой штраф
        return;
    end

    % Интерполяция на реальные временные точки
    x_model_interp = interp1(t_model, x_C_model, t_ref, 'linear', 'extrap');
    y_model_interp = interp1(t_model, y_C_model, t_ref, 'linear', 'extrap');

    % Проверка интерполяции
    if any(isnan(x_model_interp)) || any(isnan(y_model_interp))
        rmse = 1e6;
        return;
    end

    % RMSE
    dx = x_model_interp - x_ref;
    dy = y_model_interp - y_ref;
    rmse = sqrt(mean(dx.^2 + dy.^2));
end


