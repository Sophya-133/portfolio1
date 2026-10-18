import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from numpy_financial import npv, irr, pmt

# Входные данные проекта
initial_investment = -100000  # Начальные инвестиции (отрицательное значение)
cash_flows = [30000, 40000, 50000, 30000, 20000]  # Денежные потоки по годам (1-5)
discount_rate = 0.10  # Ставка дисконтирования (10%)

# 1. Расчёт NPV
npv_value = npv(rate=discount_rate, values=[initial_investment] + cash_flows)
print(f"NPV: {npv_value:.2f}")

# 2. Расчёт IRR
irr_value = irr(values=[initial_investment] + cash_flows)
print(f"IRR: {irr_value:.2%}")

# 3. Расчёт DPP (Discounted Payback Period)
cumulative_cash_flow = 0
discounted_cash_flows = []
for year, cf in enumerate(cash_flows, start=1):
    discounted_cf = cf / (1 + discount_rate) ** year
    discounted_cash_flows.append(discounted_cf)
    cumulative_cash_flow += discounted_cf
    if cumulative_cash_flow >= abs(initial_investment):
        dpp = year + (abs(initial_investment) - (cumulative_cash_flow - discounted_cf)) / discounted_cf
        break
print(f"DPP: {dpp:.2f} лет")

# 4. Расчёт PI (Profitability Index)
pi = (npv_value + abs(initial_investment)) / abs(initial_investment)
print(f"PI: {pi:.2f}")

# 5. Построение графика денежных потоков и NPV
years = np.arange(0, len(cash_flows) + 1)
cumulative_cash_flow_simple = [initial_investment]
cumulative_cash_flow_simple.extend([sum(cash_flows[:i+1]) for i in range(len(cash_flows))])

# График кумулятивного денежного потока (CF)
plt.figure(figsize=(12, 6))
plt.subplot(1, 2, 1)
plt.plot(years, cumulative_cash_flow_simple, marker='o', label='CF (без дисконтирования)')
plt.axhline(y=0, color='r', linestyle='--')
plt.title('Кумулятивный денежный поток (CF)')
plt.xlabel('Год')
plt.ylabel('Денежный поток ($)')
plt.grid(True)
plt.legend()

# График дисконтированного денежного потока
discounted_cumulative = [initial_investment]
discounted_cumulative.extend([sum(discounted_cash_flows[:i+1]) for i in range(len(discounted_cash_flows))])

plt.subplot(1, 2, 2)
plt.plot(years, discounted_cumulative, marker='o', color='green', label='CF (дисконтированный)')
plt.axhline(y=0, color='r', linestyle='--')
plt.title('Дисконтированный кумулятивный денежный поток')
plt.xlabel('Год')
plt.ylabel('Дисконтированный денежный поток ($)')
plt.grid(True)
plt.legend()

plt.tight_layout()
plt.show()
