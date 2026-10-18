def calculate_break_even_point(
    fixed_costs: float,
    variable_cost_per_unit: float,
    selling_price_per_unit: float
) -> float:
    """
    Рассчитывает точку безубыточности (в единицах продукции).

    Args:
        fixed_costs (float): Постоянные затраты (например, аренда, зарплата администрации).
        variable_cost_per_unit (float): Переменные затраты на единицу продукции (например, сырьё, упаковка).
        selling_price_per_unit (float): Цена продажи за единицу продукции.

    Returns:
        float: Объём продаж в единицах продукции, при котором предприятие выходит на безубыточность.
               Если расчёт невозможен (например, цена ниже переменных затрат), возвращает None.
    """
    if selling_price_per_unit <= variable_cost_per_unit:
        print("Ошибка: Цена продажи должна быть выше переменных затрат на единицу продукции.")
        return None

    contribution_margin_per_unit = selling_price_per_unit - variable_cost_per_unit
    break_even_volume = fixed_costs / contribution_margin_per_unit

    return break_even_volume

# Пример использования
if __name__ == "__main__":
    # Входные данные (примерные значения для предприятия)
    fixed_costs = 500000  # руб. (постоянные затраты)
    variable_cost_per_unit = 200  # руб. (переменные затраты на единицу)
    selling_price_per_unit = 500  # руб. (цена продажи за единицу)

    # Расчёт 
    break_even_volume = calculate_break_even_point(
        fixed_costs, variable_cost_per_unit, selling_price_per_unit
    )

    if break_even_volume is not None:
        print(f"Точка безубыточности: {break_even_volume:.0f} единиц продукции.")
        print(f"При этом объёме предприятие покрывает все затраты и выходит на уровень безубыточности.")
