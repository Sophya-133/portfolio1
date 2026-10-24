import numpy as np
from scipy.optimize import fsolve
import matplotlib.pyplot as plt
import pandas as pd
import os

a = 0.6  
b = 1.3  
c = 1.0  
d = 1.0  


m1 = 0.8  
m2 = 1.2  
m3 = 1.0  
g = 9.81 


omega1 = 2.0  

N = 720
theta1_arr = np.linspace(0, 2 * np.pi, N)


def solve_angles(theta1, guess):
    # неизвестные
    def f(x):
        return [a * np.cos(theta1) + b * np.cos(x[0]) - c * np.cos(x[1]) - d,
                a * np.sin(theta1) + b * np.sin(x[0]) - c * np.sin(x[1])]

    sol, info, ier, mesg = fsolve(f, guess, full_output=True)
    if ier != 1:
       
        sol = fsolve(f, [guess[0] + 0.1, guess[1] - 0.1])
    return sol


theta2_arr = np.zeros(N)
theta4_arr = np.zeros(N)
omega2_arr = np.zeros(N)
omega4_arr = np.zeros(N)


for i, theta1 in enumerate(theta1_arr):
    guess = [np.pi / 2, np.pi / 2] 
    sol = solve_angles(theta1, guess)
    theta2_arr[i] = sol[0]
    theta4_arr[i] = sol[1]
    omega2_arr[i] = omega1 * b / a
    omega4_arr[i] = omega1 * c / a


plt.figure(figsize=(10, 6))
plt.subplot(1, 2, 1)
plt.plot(theta1_arr, theta2_arr)
plt.xlabel(r'$\theta_1$ (рад)')
plt.ylabel(r'$\theta_2$ (рад)')
plt.title('График $\theta_2(\theta_1)$')
plt.subplot(1, 2, 2)
plt.plot(theta1_arr, omega2_arr)
plt.xlabel(r'$\theta_1$ (рад)')
plt.ylabel(r'$\omega_2$ (рад/с)')
plt.title('График $\omega_2(\theta_1)$')
plt.tight_layout()
plt.show()


df = pd.DataFrame({
    'theta1': theta1_arr,
    'theta2': theta2_arr,
    'theta4': theta4_arr,
    'omega2': omega2_arr,
    'omega4': omega4_arr
})
df.to_csv('results.csv', index=False)


