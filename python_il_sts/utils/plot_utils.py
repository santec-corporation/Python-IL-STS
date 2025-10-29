"""
Plotting utility module.
"""

import numpy as np
import matplotlib.pyplot as plt

def plot_wavelength_dependent_loss(wavelength: list, il_data: list):
    """
    Plot the Wavelength-Dependent Loss results.

    Args:
        wavelength (list): Array of wavelength values.
        il_data (list): Array of Insertion loss values.
    """
    try:
        plt.plot(wavelength, il_data)
        plt.show()
    except Exception as e:
        print(f"Error while displaying graph, {e}")


def plot_power_reading(power_array, power_reading):
    """
    Plot the power scan results.

    Args:
        power_array (list): Array of power values.
        power_reading (list): Corresponding power readings.
    """
    try:
        print("Displaying power scan results.")
        plt.plot(power_array, power_reading)
        max_y_axis = max(power_reading)
        min_y_axis = min(power_reading)
        step_y_axis = (max_y_axis - min_y_axis) / 10
        plt.yticks(np.arange(min_y_axis, max_y_axis, step_y_axis))
        plt.show()
    except Exception as e:
        print(f"Error while displaying power scan results, {e}")
