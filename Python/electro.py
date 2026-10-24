import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import LabelEncoder
import json
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

# --- 1. Загрузка данных ---
# Симулируем данные, если файла нет
def generate_sample_data():
    np.random.seed(42)
    dates = pd.date_range(start="2024-05-15", end="2024-06-13 23:00:00", freq="H")
    n = len(dates)
    
    # Паттерны: утро (7–9), вечер (18–22) — пик, ночью — минимум
    hour = dates.hour
    day_of_week = dates.dayofweek  # 0=понедельник, 6=воскресенье
    
    # Базовое потребление + паттерны
    base = 0.5
    morning_peak = np.where((hour >= 7) & (hour <= 9), 1.2, 0)
    evening_peak = np.where((hour >= 18) & (hour <= 22), 1.8, 0)
    weekend_bonus = np.where(day_of_week >= 5, 0.3, 0)  # выходные — больше использования
    noise = np.random.normal(0, 0.1, n)
    
    usage = base + morning_peak + evening_peak + weekend_bonus + noise
    usage = np.clip(usage, 0.1, 4.0)  # ограничим диапазон
    
    df = pd.DataFrame({
        "datetime": dates,
        "usage_kwh": usage
    })
    df.to_csv("energy_usage.csv", index=False)
    print("[INFO] Сгенерированы симуляционные данные в 'energy_usage.csv'")
    return df

try:
    df = pd.read_csv("energy_usage.csv")
except FileNotFoundError:
    df = generate_sample_data()

# --- 2. Подготовка признаков ---
df['datetime'] = pd.to_datetime(df['datetime'])
df['hour'] = df['datetime'].dt.hour
df['day_of_week'] = df['datetime'].dt.dayofweek  # 0–6

# Кодируем день недели (можно использовать OneHot, но для простоты — LabelEncoder)
le_day = LabelEncoder()
df['day_encoded'] = le_day.fit_transform(df['day_of_week'])

# --- 3. Обучение модели ---
X = df[['hour', 'day_encoded']].values
y = df['usage_kwh'].values

model = LinearRegression()
model.fit(X, y)

print(f"[INFO] Модель обучена. Коэффициенты: {model.coef_}, смещение: {model.intercept_:.3f}")

# --- 4. Прогноз на следующие 24 часа ---
next_day = df['datetime'].max() + timedelta(hours=1)
forecast_hours = [next_day + timedelta(hours=i) for i in range(24)]
forecast_hour_vals = [h.hour for h in forecast_hours]
forecast_day_vals = [h.weekday() for h in forecast_hours]
forecast_day_encoded = le_day.transform(forecast_day_vals)

X_forecast = np.array(list(zip(forecast_hour_vals, forecast_day_encoded)))
y_forecast = model.predict(X_forecast)

# --- 5. Сохранение прогноза в JSON ---
forecast_result = {
    "forecast_start": next_day.strftime("%Y-%m-%d %H:%M:%S"),
    "predictions": [
        {
            "datetime": dt.strftime("%Y-%m-%d %H:%M:%S"),
            "predicted_usage_kwh": round(pred, 2)
        }
        for dt, pred in zip(forecast_hours, y_forecast)
    ]
}

with open("energy_forecast.json", "w", encoding="utf-8") as f:
    json.dump(forecast_result, f, indent=2, ensure_ascii=False)

print("[INFO] Прогноз сохранён в 'energy_forecast.json'")

# --- 6. Визуализация ---
plt.figure(figsize=(12, 6))
plt.plot(df['datetime'][-48:], df['usage_kwh'][-48:], label="Исторические данные (последние 48 ч)", color="blue", alpha=0.7)
plt.plot(forecast_hours, y_forecast, label="Прогноз на следующие 24 ч", color="red", linestyle="--", linewidth=2)
plt.title("Прогноз потребления электроэнергии в умном доме")
plt.xlabel("Время")
plt.ylabel("Потребление (кВт·ч)")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)
plt.tight_layout()
plt.savefig("energy_forecast_plot.png")
print("[INFO] График сохранён как 'energy_forecast_plot.png'")
plt.show()
