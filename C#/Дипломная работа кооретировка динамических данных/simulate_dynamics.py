import numpy as np
import matplotlib.pyplot as plt
from scipy.integrate import odeint

def crank_slider_dynamics(y, t, l1, l2, e, phi_dot, mu, m):
    x, v = y
    phi = phi_dot * t 

    
    x_ideal = l2 * np.sin(phi) + e * np.cos(phi)

    
    dx_dphi = l2 * phi_dot * np.cos(phi) - e * phi_dot * np.sin(phi)
    dx_dt = dx_dphi 

    
    d2x_dphi2 = -l2 * phi_dot**2 * np.sin(phi) - e * phi_dot**2 * np.cos(phi)
    a = d2x_dphi2  

    return [dx_dt, a] 

def simulate_with_friction(l1, l2, e, phi_dot, mu, m, t_max, dt):
    
    t = np.arange(0, t_max, dt)
    y0 = [0.0, 0.0]  # [x, v]
    sol = odeint(crank_slider_dynamics, y0, t, args=(l1, l2, e, phi_dot, mu, m))
    x, v = sol.T
    return t, x, v

def plot_results(t, x, v, title_suffix=""):
  
    plt.figure(figsize=(12, 8))

  
    plt.subplot(2, 2, 1)
    plt.plot(t, x, label='Положение', color='blue')
    plt.xlabel('Время (с)')
    plt.ylabel('Положение (м)')
    plt.title(f'Положение ползуна{title_suffix}')
    plt.grid()
    plt.legend()

    
    plt.subplot(2, 2, 2)
    plt.plot(t, v, label='Скорость', color='green')
    plt.xlabel('Время (с)')
    plt.ylabel('Скорость (м/с)')
    plt.title(f'Скорость ползуна{title_suffix}')
    plt.grid()
    plt.legend()

    
    a = np.gradient(v, dt)
    plt.subplot(2, 2, 3)
    plt.plot(t, a, label='Ускорение', color='red')
    plt.xlabel('Время (с)')
    plt.ylabel('Ускорение (м/с²)')
    plt.title(f'Ускорение ползуна{title_suffix}')
    plt.grid()
    plt.legend()

  
    plt.subplot(2, 2, 4)
    plt.plot(x, v, label='Фазовая траектория', color='purple')
    plt.xlabel('Положение (м)')
    plt.ylabel('Скорость (м/с)')
    plt.title(f'Фазовая траектория{title_suffix}')
    plt.grid()
    plt.legend()

    plt.tight_layout()
    clean_title = title_suffix.replace(' ', '_').replace('рад/с', 'rad_s')
    plt.savefig(f'dynamics_results{clean_title}.png', dpi=300)
    plt.show()

if __name__ == "__main__":
    
    l1, l2, e = 0.5, 0.5, 0.1  # м
    t_max, dt = 2.0, 0.01  # с

    phi_dot, mu, m = 5.0, 0.0, 1.0
    t, x, v = simulate_with_friction(l1, l2, e, phi_dot, mu, m, t_max, dt)
    plot_results(t, x, v, title_suffix="(гармоническое_движение)")
