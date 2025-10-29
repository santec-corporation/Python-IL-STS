"""
Python program to run
the Santec IL STS operation.
"""

# Basic imports
import re, time

# Importing the basic modules from the python_il_sts directory.
from python_il_sts import (ConnectionManager, TslInstrument, MpmInstrument, DaqInstrument,
                           StsProcess, data_utils, plot_utils)

# Define Constants.
DWELL_TIME_CONSTANT = 10
MILLISECONDS_TO_SECONDS_CONSTANT = 1000


def set_all_channels(modules, selected_channels):
    """ Selects all modules and all channels that are connected to MPM. """
    for module in modules:
        for channel_number in module.channels:
            selected_channels.append([module.module_number, channel_number])


def set_even_channels(modules, selected_channels) -> None:
    """ Selects only even channels on the MPM. """
    for module in modules:
        for channel_number in module.channels:
            if channel_number % 2 == 0:
                selected_channels.append([module.module_number, channel_number])


def set_odd_channels(modules, selected_channels) -> None:
    """ Selects only odd channels on the MPM. """
    for module in modules:
        for channel_number in module.channels:
            if channel_number % 2 != 0:
                selected_channels.append([module.module_number, channel_number])


def set_special_channels(modules, selected_channels) -> None:
    """ Manually enter/select the channels to be measured. """
    selection = input("Input (module,channel) to be tested [ex: (1,1); (2,1)]  ")
    selection = re.findall(r"[\w']+", selection)

    i = 0
    while i <= len(selection) - 1:
        selected_channels.append([f"{int(selection[i]) - 1}", selection[i + 1]])
        i += 2


def select_mpm_channels(mpm):
    """
    Select the channels to be measured.
    It offers the user to choose between different ways to select MPM channels.
    """
    selected_channels = []
    modules = mpm.get_modules()

    print("\nAvailable modules/channels:")
    for module in modules:
        if module.module_type is None:
            continue
        print("\r" + "Module No. {}: {} - Channels: {}"
              .format(module.module_number, module.module_type, module.channels))

    mpm_choices = {'1': set_all_channels,
                   '2': set_even_channels,
                   '3': set_odd_channels,
                   '4': set_special_channels}

    print("""\nChannels measurement options:
              1. All channels
              2. Even channels
              3. Odd channels
              4. Specific channels""")

    user_selection = input("\nSelect channels to be measured: ")
    mpm_choices[user_selection](modules, selected_channels)

    return selected_channels


def select_dynamic_ranges(mpm):
    """
    Select the optical dynamic range of the MPM.
    """
    print("\nAvailable dynamic ranges:")
    for i in range(5):
        print('{}. {}'.format(i + 1, mpm.dynamic_ranges[i]))
    selection = input("Select a dynamic dynamic_range (Ex: 1,2,3): ")
    selected_ranges = re.findall(r"[\w']+", selection)

    # Convert the string ranges to ints, because that is what the DLL is expecting.
    selected_ranges = [int(i) for i in selected_ranges]
    return selected_ranges


def save_scan_data(ilsts: StsProcess) -> None:
    """ Save measurement and reference data to files. """
    # Save the reference scan result data.
    data_utils.save_reference_result_data(ilsts)

    # Save the measurement scan data.
    data_utils.save_dut_result_data(ilsts)

    # Save the IL data.
    data_utils.save_il_data(ilsts)


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

    print("List of Instruments: ", instrument_list)

    for dev in instrument_list:
        if "TSL" in dev:
            tsl_resource = dev
        elif "MPM" in dev:
            mpm_resource = dev
        elif "Dev" in dev:
            daq_resource = dev

    if tsl_resource == "":
        raise Exception("TSL instrument not connected. Please connect the TSL.")
    elif mpm_resource == "":
        raise Exception("MPM instrument not connected. Please connect the MPM.")

    tsl_instrument = connection_manager.connect_tsl(tsl_resource)
    mpm_instrument = connection_manager.connect_mpm(mpm_resource)

    if "210" in mpm_resource:
        daq_instrument = connection_manager.connect(daq_resource)

    return tsl_instrument, mpm_instrument, daq_instrument


def tsl_power_check(tsl: TslInstrument):
    """ Set the TSL power to 5 dBm or less. """
    power = float(input("Please input the Output Power (dBm): "))
    while power > 5.00:
        print("\nPower should be less than or equal to 5 dBm.")
        power = float(input("Please input the Output Power (dBm) again: "))

    tsl.set_power(power)


def wavelength_dependent_loss(
        tsl: TslInstrument,
        mpm: MpmInstrument,
        daq: DaqInstrument | None):
    """
    Perform the wavelength-dependent loss measurement.
    """
    is_tsl_570 = True
    if tsl.get_tsl_type_flag():
        is_tsl_570 = False

    scan_parameters = {}
    is_scan_parameters_loaded = data_utils.get_scan_parameters(scan_parameters, is_tsl_570)

    start_wavelength = scan_parameters["start_wavelength"]
    stop_wavelength = scan_parameters["stop_wavelength"]
    scan_step = scan_parameters["scan_step"]
    power = scan_parameters["power"]
    scan_speed = scan_parameters["scan_speed"]
    scan_cycles = scan_parameters["scan_cycles"]
    scan_delay = scan_parameters["scan_delay"]

    # Select the MPM module, channel and dynamic range.
    selected_channels = select_mpm_channels(mpm)
    selected_ranges = select_dynamic_ranges(mpm)

    # Create an instance and initialize the STS process class.
    ilsts = StsProcess(tsl, mpm, daq)

    # Set the parameters.
    ilsts.set_parameters(start_wavelength, stop_wavelength, scan_step, power, scan_speed,
                         selected_channels, selected_ranges)

    if mpm.mpm_215_selection_check(selected_channels):
        tsl_power_check(tsl)
        ilsts.selected_ranges = [2]

    # Load reference scan data if available
    reference_scan_data = (
        data_utils.import_reference_scan_data() if is_scan_parameters_loaded else None
    )

    # Check if reference scan data exists or not
    if not reference_scan_data:
        input("\nConnect for Reference measurement and press ENTER")
        print("Reference process...")
        ilsts.reference_scan()
    else:
        print("Loading reference data...")
        ilsts.load_reference_scan_data(reference_scan_data)

    # Measurement scan operation.
    print("\nMeasurement process...")
    user_response = "y"
    while user_response in "yY":
        input("Connect the DUT and press ENTER")
        for i in range(scan_cycles):
            scan_index = i + 1
            print("\nScan {} of {}...".format(str(scan_index), scan_cycles))

            ilsts.measurement_scan()

            user_map_display = input("\nDo you want to view the graph ?? (y/n): ")
            if user_map_display == "y":
                plot_utils.plot_wavelength_dependent_loss(ilsts.wavelength_table, ilsts.il)

            time.sleep(scan_delay)

            if scan_cycles > 1 and scan_index < scan_cycles:
                input(f"\nPress ENTER to continue to Scan {scan_index + 1}...")

        ilsts.get_dut_data()

        user_response = input("\nRedo Scan ? (y/n): ")

    # Disconnect the instruments.
    ilsts.disconnect_instruments()

    # Save the scan parameters.
    data_utils.export_scan_parameters(scan_parameters)

    # Save the reference scan data.
    data_utils.export_reference_data(ilsts)

    # Save the scan data.
    save_scan_data(ilsts)


def power_scan(tsl: TslInstrument, mpm: MpmInstrument):
    """ Performs a power scan measurement. """
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
        raw_power = mpm.query(f'READ? {mpm_mod}')[1].split(',')
        power_reading.append(float(raw_power[int(mpm_chan) - 1]))
        time.sleep(dwell_time)
        actual_pow = round(actual_pow + step_pow, 2)
        tsl.write(f'POW {actual_pow}')

    # Plot the results.
    plot_utils.plot_power_reading(power_array, power_reading)

    # Save the power scan results.
    data_utils.save_power_scan_results(power_array, power_reading)


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
