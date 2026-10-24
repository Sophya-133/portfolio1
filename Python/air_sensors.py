import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import json

# --- 1. Генерация или загрузка данных ---
def generate_sample_air_data():
    np.random.seed(42)
    # Исправлено: freq="h" вместо freq="H"
    timestamps = pd.date_range(start="2024-05-15", end="2024-05-21 23:00:00", freq="h")
    n = len(timestamps)

    # Реалистичные паттерны: PM2.5 выше в часы пик, ниже ночью
    base_pm25 = np.random.normal(15, 5, n)
    hour = timestamps.hour
    # Пик в часы пробок (7–10 и 17–20)
    base_pm25 += np.where((hour >= 7) & (hour <= 10), 10, 0)
    base_pm25 += np.where((hour >= 17) & (hour <= 20), 12, 0)

    # Нормальные колебания температуры и влажности
    temperature = np.random.normal(22, 3, n)
    humidity = np.random.normal(50, 8, n)

    # Вставляем 3 симулированных сбоя датчика (аномалии)
    anomaly_indices = [10, 80, 150]  # дни: 0, 3, 6
    base_pm25[anomaly_indices] = [250, 300, 280]  # ложные высокие значения

    df = pd.DataFrame({
        "timestamp": timestamps,
        "pm25": np.clip(base_pm25, 0, 300),
        "temperature": np.clip(temperature, 10, 35),
        "humidity": np.clip(humidity, 20, 90)
    })
    df.to_csv("air_quality_sensors.csv", index=False)
    print("[INFO] Сгенерированы симуляционные данные в 'air_quality_sensors.csv'")
    return df

try:
    df = pd.read_csv("air_quality_sensors.csv")
except FileNotFoundError:
    df = generate_sample_air_data()

# --- 2. Создание столбца 'date' ДО любого использования ---
df["timestamp"] = pd.to_datetime(df["timestamp"])  # Убедимся, что timestamp — datetime
df["date"] = df["timestamp"].dt.date  # ✅ Создаём столбец date ПЕРЕД группировкой

# --- 3. Подготовка признаков для Isolation Forest ---
X = df[["pm25", "temperature", "humidity"]].values

# --- 4. Обучение модели Isolation Forest ---
iso_forest = IsolationForest(
    contamination=0.05,
    random_state=42,
    n_estimators=100
)
df["anomaly"] = iso_forest.fit_predict(X)  # -1 = аномалия, 1 = норма

# --- 5. Фильтрация аномалий ---
anomalies = df[df["anomaly"] == -1]
print(f"[INFO] Обнаружено {len(anomalies)} аномалий из {len(df)} записей.")

# --- 6. Группировка аномалий по дням (теперь 'date' существует!) ---
anomaly_counts_by_day = anomalies.groupby("date").size()
print("\n[Аномалии по дням]:")
for date, count in anomaly_counts_by_day.items():
    print(f" {date}: {count} аномалий")

# --- 7. Уведомление: если >5 аномалий за сутки ---
critical_days = anomaly_counts_by_day[anomaly_counts_by_day > 5]
if len(critical_days) > 0:
    print("\n⚠️ [ВНИМАНИЕ!] Обнаружены дни с >5 аномалий:")
    for date, count in critical_days.items():
        print(f" {date} — {count} аномалий (отправка SMS-оповещения...)")
else:
    print("\n✅ Все дни в норме — оповещения не требуются.")

# --- 8. Сохранение аномалий в CSV ---
anomalies.to_csv("anomalies_detected.csv", index=False)
print("[INFO] Аномалии сохранены в 'anomalies_detected.csv'")

# --- 9. Визуализация ---
plt.figure(figsize=(14, 6))

# График PM2.5
plt.subplot(1, 2, 1)
plt.plot(df["timestamp"], df["pm25"], label="PM2.5", color="blue", alpha=0.7)
plt.scatter(anomalies["timestamp"], anomalies["pm25"], color="red", s=60, label="Аномалии", edgecolor="black", zorder=5)
plt.title("PM2.5 с обнаруженными аномалиями")
plt.xlabel("Время")
plt.ylabel("PM2.5 (мкг/м³)")
plt.xticks(rotation=45)
plt.legend()
plt.grid(True)

# Распределение аномалий
plt.subplot(1, 2, 2)
plt.hist(df["anomaly"], bins=[-1.5, -0.5, 0.5], edgecolor="black", color=["red", "green"])
plt.xticks([-1, 1], ["Аномалия", "Норма"])
plt.title("Распределение: Норма vs Аномалия")
plt.ylabel("Количество записей")

plt.tight_layout()
plt.savefig("anomaly_detection_plot.png")
print("[INFO] График сохранён как 'anomaly_detection_plot.png'")
plt.show()

# --- 10. Сохранение метаданных в JSON ---
summary = {
    "total_records": len(df),
    "anomalies_detected": len(anomalies),
    "anomalies_by_day": anomaly_counts_by_day.to_dict(),
    "critical_days": list(critical_days.index),
    "model": "IsolationForest",
    "contamination": 0.05
}
with open("anomaly_summary.json", "w", encoding="utf-8") as f:
    json.dump(summary, f, indent=2, ensure_ascii=False)
print("[INFO] Сводка сохранена в 'anomaly_summary.json'")
