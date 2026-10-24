# generate_reference_data.py
import numpy as np
import pandas as pd

# Параметры модели (реальные, но с погрешностями)
L1_true = 0.12   # кривошип
L2_true = 0.32   # шатун
L3_true = 0.06   # смещение направляющей
omega = 10       # угловая скорость (рад/с)
t_end = 2
dt = 0.01

# Временная шкала
t = np.arange(0, t_end, dt)

# Идеальная кинематика (без погрешностей)
theta = omega * t
x_A = L1_true * np.cos(theta)
y_A = L1_true * np.sin(theta)
y_B = L3_true * np.ones_like(theta)
x_B = x_A + np.sqrt(L2_true**2 - (y_B - y_A)**2)  # правое решение
x_C = (x_A + x_B) / 2  # центр шатуна
y_C = (y_A + y_B) / 2

# Добавляем систематические ошибки (Inventor)
# - Смещение по X: +0.005 м
# - Шум по Y: ±0.002 м
# - Небольшая нелинейность в шатуне
noise_y = np.random.normal(0, 0.002, len(t))
y_C_noisy = y_C + noise_y + 0.005 * np.sin(20 * t)  # систематическая ошибка

# Сохраняем в CSV
df = pd.DataFrame({
    't': t,
    'x': x_C,
    'y': y_C_noisy
})
df.to_csv('reference_data.csv', index=False)

print("✅ Файл 'reference_data.csv' сгенерирован")
