"""
Python IL STS
"""

import os
import json
import time
import numpy as np
import matplotlib.pyplot as plt

# Importing modules from the santec directory
from python_il_sts.connections.connection_manager import ConnectionManager
from python_il_sts import TslInstrument, MpmInstrument, DaqInstrument, StsProcess, file_saving


DWELL_TIME_CONSTANT = 10
MILLISECONDS_TO_SECONDS_CONSTANT = 1000



def prompt_and_get_previous_param_data(file_last_scan_params: str) -> dict | None:
    """
    Prompt user to load previous parameter settings if available.

    Parameters:
        file_last_scan_params (str): Path to the file containing last scan parameters.

    Returns:
        dict: Previous settings loaded from the file, or None if not available.
    """
    if not os.path.exists(file_last_scan_params):
        return None

    ans = input("\nWould you like to load the most recent parameter settings from {}? [y|n]: "
                .format(file_last_scan_params))
    if ans not in "Yy":
        return None

    # Load the json data.
    with open(file_last_scan_params, encoding='utf-8') as json_file:
        previous_settings = json.load(json_file)

    return previous_settings


def prompt_and_get_previous_reference_data() -> dict | None:
    """
    Ask user if they want to use the previous reference data if it exists.

    Returns:
        dict: Previous reference data loaded from the file,
        None: if reference data is not available.
    """
    if not os.path.exists(file_saving.FILE_LAST_SCAN_REFERENCE_DATA):
        return None

    ans = input("\nWould you like to use the most recent reference data from file '{}'? [y|n]: "
                .format(file_saving.FILE_LAST_SCAN_REFERENCE_DATA))

    if ans not in "Yy":
        return None

    # Get the file size.
    int_file_size = int(os.path.getsize(file_saving.FILE_LAST_SCAN_REFERENCE_DATA))
    str_file_size = f"{int_file_size / 1000000:.2f} MB" if int_file_size > 1000000 else f"{int_file_size / 1000:.2f} KB"

    print("Opening " + str_file_size + " file '" + file_saving.FILE_LAST_SCAN_REFERENCE_DATA + "'...")
    with open(file_saving.FILE_LAST_SCAN_REFERENCE_DATA, 'r', encoding='utf-8') as file:
        data = file.read()
        previous_reference = json.loads(data)
    return previous_reference


def save_all_data(ilsts: StsProcess) -> None:
    """
    Save measurement and reference data to files.

    Parameters:
        ilsts (StsProcess): Instance of the ILSTS class.

    Returns:
        None
    """
    print("\n")
    # Saving reference data to file
    file_saving.save_reference_data(ilsts, file_saving.FILE_LAST_SCAN_REFERENCE_DATA)

    print("Saving Reference data csv to file " + file_saving.FILE_REFERENCE_DATA_RESULTS + "...")
    file_saving.save_reference_result_data(ilsts, file_saving.FILE_REFERENCE_DATA_RESULTS)

    print("Saving Raw data to csv file " + file_saving.FILE_RAW_DATA_RESULTS + "...")
    file_saving.save_dut_result_data(ilsts, file_saving.FILE_RAW_DATA_RESULTS)

    print("Saving IL data to csv file " + file_saving.FILE_IL_DATA_RESULTS + "...")
    file_saving.save_measurement_data(ilsts, file_saving.FILE_IL_DATA_RESULTS)


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


def connection():
    """ Detect and connect to the TSL, MPM and DAQ instruments. """
    tsl_resource = ""
    mpm_resource = ""
    daq_resource = ""

    tsl_instrument: TslInstrument
    mpm_instrument: MpmInstrument
    daq_instrument = DaqInstrument | None

    connection_manager = ConnectionManager()
    instrument_list = connection_manager.list_instruments()

    for dev in instrument_list:
        if "TSL" in dev:
            tsl_resource = dev
        elif "MPM" in dev:
            mpm_resource = dev
        elif "Dev" in dev:
            daq_resource = dev

    tsl_instrument = connection_manager.connect_tsl(tsl_resource)
    mpm_instrument = connection_manager.connect_mpm(mpm_resource)

    if "210" in mpm_resource:
        daq_instrument = connection_manager.connect(daq_resource)

    return tsl_instrument, mpm_instrument, daq_instrument


def tsl_power_check(tsl: TslInstrument):
    """ Check and limit TSL power to 5dBm. """
    current_set_power = tsl.power
    power = 0.00
    if current_set_power > 5.00:
        print("\nPower value should not be greater than 5 dBm.")
        power = float(input("Please input Output Power (dBm) again: "))
        while power > 5.00:
            print("\nInvalid value of Output Power ( <=5 dBm )")
            power = float(input("Please input Output Power (dBm): "))

    tsl.set_power(power)


def wavelength_dependent_loss(tsl: TslInstrument, mpm: MpmInstrument, daq: DaqInstrument | None):
    """
    Perform the wavelength-dependent loss measurement.

    Args:
        tsl: The tsl instrument.
        mpm: The mpm instrument.
        daq: The daq device.
    """
    # Set the TSL properties
    previous_parameter_data = prompt_and_get_previous_param_data(file_saving.FILE_LAST_SCAN_PARAMS)

    # Initiate and run the ILSTS
    ilsts = StsProcess(tsl, mpm, daq)
    ilsts.setting_tsl_scan_params(previous_parameter_data)

    # Select channels to be measured.
    ilsts.set_selected_channels(previous_parameter_data)
    if ilsts.mpm_215_selection_check():
        tsl_power_check(tsl)
        ilsts.selected_ranges = [2]
    else:
        ilsts.set_selected_ranges(previous_parameter_data)

    # Set scan parameters to MPM and DAQ
    ilsts.set_parameters()

    # Check for previously saved reference data
    previous_ref_data_array = None
    if previous_parameter_data:
        previous_ref_data_array = prompt_and_get_previous_reference_data()
    if previous_ref_data_array:
        ilsts.reference_data_array = previous_ref_data_array

    # Saving parameters to file
    if not previous_parameter_data:
        file_saving.save_sts_parameter_data(tsl, ilsts, file_saving.FILE_LAST_SCAN_PARAMS)

    # Run a reference scan if previously saved reference data not found
    if len(ilsts.reference_data_array) == 0:
        print("\nConnect for Reference measurement and press ENTER")
        print("Reference process:")
        # IL STS reference scan
        ilsts.sts_reference()
    else:
        print("Loading reference data...")
        ilsts.sts_reference_from_saved_file()

    # Perform the scan operation
    ans = "y"
    while ans in "yY":
        print("\nDUT measurement")
        while True:
            reps = int(input("Input DUT scan repeat count (greater than 0): "))
            if reps > 0:
                break
            print("Invalid repeat count, enter a positive number.\n")
        input("Connect the DUT and press ENTER")
        for i in range(reps):
            scan_index = i + 1
            print("\nScan {} of {}...".format(str(scan_index), reps))

            # IL STS measurement scan
            ilsts.sts_measurement()

            user_map_display = input("\nDo you want to view the graph ?? (y/n): ")
            if user_map_display == "y":
                plot_wavelength_dependent_loss(ilsts.wavelength_table, ilsts.il)

            if reps > 1 and scan_index < reps:
                input(f"\nPress ENTER to continue to Scan {scan_index + 1}...")
        ilsts.get_dut_data()  # Get and store DUT scan data

        ans = input("\nRedo Scan ? (y/n): ")

    save_all_data(ilsts)



def power_scan(tsl, mpm):
    """
    Perform a power scan measurement.

    Args:
        tsl: The tsl device.
        mpm: The powermeter (mpm).
    """
    # MPM setting
    mpm_mod, mpm_chan = input('\nSelect Powermeter Module and Channel (Ex: Module,Channel => 0,1): ').split(',')
    avg_time = float(input('Set Averaging time for the powermeter (0.01~10000.00) [msec]: '))

    mpm.write('AUTO')  # Set automatic gain for the powermeter
    mpm.write(f'AVG {avg_time}')

    # TSL setting
    set_wl = float(input('Set characterization wavelength [nm]: '))
    start_pow = float(input('Input start power [dBm]: '))
    stop_pow = float(input('Input stop power [dBm]: '))
    step_pow = float(input('Input power step [dB]: '))

    tsl.set_wavelength(set_wl)
    tsl.write(f'POW {start_pow}')

    if start_pow > stop_pow:
        step_pow = -step_pow

    # The dwelling time is set 10 times longer than the averaging time of the powermeter
    dwell_time = DWELL_TIME_CONSTANT * avg_time / MILLISECONDS_TO_SECONDS_CONSTANT

    power_reading, power_array = [], []
    actual_pow = start_pow
    while actual_pow != stop_pow + step_pow:
        # print(actual_pow)
        power_array.append(actual_pow)

        # Read power from the MPM
        raw_pow = mpm.query(f'READ? {mpm_mod}')[1].split(',')
        power_reading.append(
            float(raw_pow[int(mpm_chan) - 1]))  # Channels are from 1 to 4 and arrays are from 0 to 3, thus "-1"
        time.sleep(dwell_time)
        actual_pow = round(actual_pow + step_pow, 2)
        tsl.write(f'POW {actual_pow}')

    # Plot results
    plot_power_reading(power_array, power_reading)

    print("\nSaving power scan data to file " + file_saving.FILE_POWER_SCAN_RESULTS + "...")
    file_saving.save_power_scan_results(power_array, power_reading, file_saving.FILE_POWER_SCAN_RESULTS)


def main() -> None:
    """
    Main method of the project.
    Connects to devices, sets parameters, and performs measurements.

    Returns:
        None
    """
    tsl, mpm, daq = connection()

    break_script = 'Y'
    while break_script in 'Yy':
        choice = ''
        while choice not in ['1', '2']:
            choice = input("\nMeasurement Options:"
                           "\n1. Wavelength Dependent Loss (IL operation)"
                           "\n2. Power scan"
                           "\nSelect measurement type: ")
        if choice == '1':
            wavelength_dependent_loss(tsl, mpm, daq)
        else:
            power_scan(tsl, mpm)

        break_script = input('\nDo you want to continue? (Y/n): ')

    print("\nClosing program.")


if __name__ == "__main__":
    main()
