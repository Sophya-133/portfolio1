import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

# ----------------------------
# Данные: регион RegionX, годы 2023 и 2024
# Значения — условный ВВП по секторам (условные единицы)
# ----------------------------
data = [
    ("RegionX", 2023, "Agriculture", 120),
    ("RegionX", 2023, "Industry",     350),
    ("RegionX", 2023, "Services",     820),
    ("RegionX", 2023, "Construction", 180),
    ("RegionX", 2024, "Agriculture", 130),
    ("RegionX", 2024, "Industry",     370),
    ("RegionX", 2024, "Services",     900),
    ("RegionX", 2024, "Construction", 210),
]

# ----------------------------
# Подготовка данных
# ----------------------------
df = pd.DataFrame(data, columns=["region", "year", "sector", "gdp"])

# Преобразуем к таблице: сектор как индекс, год как столбец
pivot = df.pivot(index="sector", columns="year", values="gdp")
# Убеждаемся, что порядок по секторам фиксирован
pivot = pivot.reindex(["Agriculture", "Industry", "Services", "Construction"])

# Годовые итоги
tot_2023 = float(pivot[2023].sum())
tot_2024 = float(pivot[2024].sum())

# Темпы роста по секторам (2023 -> 2024)
growth_by_sector = ((pivot[2024] - pivot[2023]) / pivot[2023]).rename("growth")

# Доля сектора в базовом году (2023)
share_2023 = (pivot[2023] / tot_2023).rename("share_2023")

# Вклад сектора в рост региона (приближённо): вклад = темп роста × доля базисного года
contribution = (growth_by_sector * share_2023).rename("contribution_to_growth")

# Итоговые показатели
region_growth = (tot_2024 - tot_2023) / tot_2023

# Вывод результатов
print("Регион RegionX")
print("----------------------------")
print(f"Общий ВВП 2023: {tot_2023:,.0f}")
print(f"Общий ВВП 2024: {tot_2024:,.0f}")
print(f"Годовой рост региона (2023->2024): {region_growth:.2%}")
print()

print("Темпы роста по секторам (2023 -> 2024):")
for sector in pivot.index:
    v3 = pivot.loc[sector, 2023]
    v4 = pivot.loc[sector, 2024]
    g = growth_by_sector.loc[sector]
    print(f"  - {sector}: {g:.2%} (2023: {v3}, 2024: {v4})")
print()

print("Доля сектора в базовом году (2023):")
for sector in pivot.index:
    s = share_2023.loc[sector]
    print(f"  - {sector}: {s:.2%}")
print()

print("Вклад каждого сектора в рост региона (2023->2024):")
total_contrib = 0.0
for sector in pivot.index:
    c = contribution.loc[sector]
    total_contrib += c
    print(f"  - {sector}: {c:.2%}");  # выражено как доля от общего роста
print(f"Суммарный вклад: {total_contrib:.2%} (приближённо должен равняться росту региона)")

# ----------------------------
# Графики
# 1) Сравнение ВВП по секторам за 2023 и 2024
# 2) Тренд общего ВВП региона (2023 -> 2024)
# ----------------------------
sectors = pivot.index.tolist()
gdp_2023 = pivot[2023].values
gdp_2024 = pivot[2024].values

plt.figure(figsize=(10, 5))
bar_width = 0.35
x = np.arange(len(sectors))

plt.bar(x - bar_width/2, gdp_2023, width=bar_width, label='2023')
plt.bar(x + bar_width/2, gdp_2024, width=bar_width, label='2024')

plt.xlabel('Сектор')
plt.ylabel('ВВП по сектору (условные ед.)')
plt.title('ВВП по секторам: RegionX, 2023 vs 2024')
plt.xticks(x, sectors)
plt.legend()
plt.tight_layout()
plt.show()

# Тренд общего ВВП региона
years = [2023, 2024]
totals = [tot_2023, tot_2024]

plt.figure(figsize=(6, 4))
plt.plot(years, totals, marker='o', linestyle='-')
plt.xticks(years)
plt.xlabel('Год')
plt.ylabel('Общий ВВП региона (условные ед.)')
plt.title('Динамика общего ВВП RegionX')
plt.grid(True, linestyle='--', alpha=0.5)
plt.tight_layout()
plt.show()