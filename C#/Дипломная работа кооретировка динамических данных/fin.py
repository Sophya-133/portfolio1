m1 = 1.0  
m2 = 1.0  
L1 = 1.0  
L2 = 1.0 
g = 9.81 


def model(state, t):
    x1, v1, x2, v2 = state
    a1 = (-g * (2 * m1 + m2)) / (m1 * (L1 + L2)) - (m2 * g) / (m1 * (L1 + L2)) * (x1 - x2) / L2
    a2 = (2 * g * (m1 + m2)) / (m2 * (L1 + L2)) + (g * (m1 + m2)) / (m2 * L2) * (x1 - x2) / L2
    return [v1, a1, v2, a2]


t = 0
state = [0, 0, 0, 0]
for i in range(100):
    state = [state[0] + state[1]*0.1, state[1] + model(state, t)[1]*0.1, state[2] + model(state, t)[2]*0.1, state[3] + model(state, t)[3]*0.1]
    t += 0.1
    print(f"Время: {t}, Кинематические координаты: {state}")

print("\nКинематические координаты четырехзвенного кривошипно-шатунного механизма:")
print(f"Координата кривошпинного вала: {state[0]}")
print(f"Скорость кривошпинного вала: {state[1]}")
print(f"Координата шатунного вала: {state[2]}")
print(f"Скорость шатунного вала: {state[3]}")
