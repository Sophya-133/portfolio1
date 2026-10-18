import numpy as np
import matplotlib.pyplot as plt
from scipy.optimize import least_squares

def forward_kinematics(phi, l1, l2, e):
    """
    Прямая задача кинематики для КШМ.
    Возвращает только конечные значения, заменяя некорректные на крайние точки.
    """
    term = e - l1 * np.sin(phi)
    # Условие корректности для подкоренного выражения
    valid_mask = (term**2 <= l2**2)
    x = np.full_like(phi, np.nan)  # Инициализация NaN
    x[valid_mask] = l1 * np.cos(phi[valid_mask]) + np.sqrt(l2**2 - term[valid_mask]**2)

    # Для некорректных углов возвращаем минимальное/максимальное значение из корректной области
    if not np.all(valid_mask):
        x[~valid_mask] = np.min(x[valid_mask]) if np.any(x[valid_mask]) else 0.0
    return x

def residuals(params, x_measured, phi_measured):
    """
    Функция ошибки для калибровки параметров l1, l2, e.
    Возвращает только конечные значения (заменяет NaN на большие штрафы).
    """
    x_calculated = forward_kinematics(phi_measured, *params)
    # Замена NaN на большое число, чтобы оптимизатор их избегал
    x_calculated = np.where(np.isnan(x_calculated), 1e6, x_calculated)
    return x_calculated - x_measured

def calibrate_geometry(x_measured, phi_measured, initial_guess):
    """
    Калибровка геометрических параметров механизма с ограничениями.
    """
    bounds = (
        [0.01, 0.01, -0.5],  # Нижние границы
        [1.0, 1.0, 0.5]       # Верхние границы
    )
    result = least_squares(
        residuals,
        initial_guess,
        bounds=bounds,
        args=(x_measured, phi_measured),  # Важно: x_measured и phi_measured должны иметь одинаковый размер!
        loss='soft_l1',
        max_nfev=1000,
        ftol=1e-8,
        xtol=1e-8
    )
    if not result.success:
        raise RuntimeError(f"Оптимизация не сошлась: {result.message}")
    l1_opt, l2_opt, e_opt = result.x
    print(f"Калиброванные параметры: l1={l1_opt:.4f} м, l2={l2_opt:.4f} м, e={e_opt:.4f} м")
    return l1_opt, l2_opt, e_opt

# --- Пример использования ---
if __name__ == "__main__":
    # Данные из Autodesk Inventor (экспериментальные)
    # Убедитесь, что phi_measured и x_measured имеют ОДИНАКОВЫЙ размер!
    phi_measured = np.linspace(0, 2*np.pi, 10)  # Углы кривошипа (рад) - размер 10
    x_measured = np.array([0.1, 0.15, 0.22, 0.28, 0.31, 0.30, 0.25, 0.18, 0.08, -0.05])  # м - размер 10

    initial_guess = [0.1, 0.3, 0.02]  # [l1, l2, e]

    try:
        l1_opt, l2_opt, e_opt = calibrate_geometry(x_measured, phi_measured, initial_guess)
        x_calibrated = forward_kinematics(phi_measured, l1_opt, l2_opt, e_opt)

        # Визуализация
        plt.figure(figsize=(12, 6))
        plt.subplot(1, 2, 1)
        plt.plot(phi_measured, x_measured, 'o', label='Autodesk Inventor', color='red')
        plt.plot(phi_measured, forward_kinematics(phi_measured, *initial_guess), '-', label='Исходная модель', color='blue')
        plt.plot(phi_measured, x_calibrated, '--', label='Калиброванная модель', color='green')
        plt.xlabel('Угол кривошипа (рад)'); plt.ylabel('Положение ползуна (м)')
        plt.title('Сравнение моделей'); plt.legend(); plt.grid()

        plt.subplot(1, 2, 2)
        plt.plot(phi_measured, x_calibrated - x_measured, label='Ошибка', color='purple')
        plt.xlabel('Угол кривошипа (рад)'); plt.ylabel('Ошибка (м)')
        plt.title('Ошибка калибровки'); plt.legend(); plt.grid()
        plt.tight_layout(); plt.savefig('calibration_results.png', dpi=300); plt.show()

        plt.figure(figsize=(12,6))
        plt.subplot(1,2,1)
        plt.pot(phi_measured,x_measured,'o',label='Inventor', color='red')
        plt.plot(phi_measured, forward_kinematics)

        # Вычисленные выводы
        print("\nВычисленные выводы:")
        print(f"1. Исходные параметры: l1={initial_guess[0]:.4f} м, l2={initial_guess[1]:.4f} м, e={initial_guess[2]:.4f} м")
        print(f"2. Калиброванные параметры: l1={l1_opt:.4f} м, l2={l2_opt:.4f} м, e={e_opt:.4f} м")

        # Убедитесь, что x_calibrated[:len(x_measured)] и x_measured имеют одинаковый размер
        error_before = np.sqrt(np.nanmean((forward_kinematics(phi_measured, *initial_guess) - x_measured)**2))
        error_after = np.sqrt(np.nanmean((x_calibrated - x_measured)**2))
        print(f"3. Среднеквадратичная ошибка до калибровки: {error_before:.6f} м")
        print(f"4. Среднеквадратичная ошибка после калибровки: {error_after:.6f} м")
        print(f"5. Уменьшение ошибки: {1 - error_after / error_before:.2%}")

    except Exception as e:
        print(f"Ошибка при калибровке: {e}")



