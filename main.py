"""
Python program to run
the Santec IL STS operation.
"""

# Basic imports.
import re, time
from typing import List, Any, Optional, Tuple

# Importing the basic modules from the python_il_sts directory.
from python_il_sts import (ConnectionManager, TslInstrument, MpmInstrument, DaqInstrument,
                           StsProcess, data_utils, plot_utils)

# Define Constants.
DWELL_TIME_FACTOR = 10.0  # dwell time = factor × averaging time
MS_TO_SEC = 1000.0


def _filter_channels(modules: List[Any], predicate) -> List[List[int]]:
    """Helper: return module/channel pairs satisfying predicate."""
    return [
        [module.module_number, ch]
        for module in modules
        for ch in module.channels
        if predicate(ch)
    ]


def set_all_channels(modules: List[Any]) -> List[List[int]]:
    """Select all channels from all modules."""
    return _filter_channels(modules, lambda _: True)


def set_even_channels(modules: List[Any]) -> List[List[int]]:
    """Select only even channels."""
    return _filter_channels(modules, lambda ch: ch % 2 == 0)


def set_odd_channels(modules: List[Any]) -> List[List[int]]:
    """Select only odd channels."""
    return _filter_channels(modules, lambda ch: ch % 2 != 0)


def set_special_channels(modules: List[Any]) -> List[List[int]]:
    """Manually select specific module/channel pairs."""
    selection = input("Input (module number, channel number) pairs [ex: (1,1); (2,1)]: ")
    tokens = re.findall(r"\d+", selection)
    if len(tokens) % 2 != 0:
        print("⚠ Invalid input — must have module/channel pairs.")
        return []

    return [[int(tokens[i]) - 1, int(tokens[i + 1])] for i in range(0, len(tokens), 2)]


def select_mpm_channels(mpm, use_mpm_220_ref: bool, mpm_220_ref_module_info) -> List[List[int]]:
    """
    Interactively select MPM channels to measure.
    Returns a list of [module_number, channel_number] pairs.
    """
    available_modules = mpm.get_available_modules()
    print("\nAvailable modules/channels:")
    for module in available_modules:
        # Example: Module 1: MPM-211 - Channels: [1, 2, 3, 4]
        print(f"Module {module.module_number + 1}: {module.module_type} - Channels: {module.channels}")

    # Set MPM-220 channel for monitor data measurement.
    if use_mpm_220_ref:
        print("\nPlease select a reference channel for the MPM-220 instrument.")
        selection = input("Input (module number, channel number) pair. Ex: (1,1): ")
        tokens = re.findall(r"\d+", selection)

        if len(tokens) != 2:
            print("⚠ Invalid input — must be a module/channel pair. Using default (0,1).")
            mpm_220_ref_module_info = [0, 1]  # default values (0-indexed)
        else:
            module_num, channel_num = map(int, tokens)
            mpm_220_ref_module_info[:] = [module_num - 1, channel_num]

        ref_module_num, ref_channel_num = mpm_220_ref_module_info[0], mpm_220_ref_module_info[1]

        for module in available_modules:
            if module.module_number == ref_module_num:
                if str(ref_channel_num) in module.channels:
                    module.channels.remove(ref_channel_num)

    # Select MPM channels for measurement.
    choices = {
        '1': set_all_channels,
        '2': set_even_channels,
        '3': set_odd_channels,
        '4': set_special_channels,
    }

    print("""\nMeasurement channels selection options:
              1. All channels
              2. Even channels
              3. Odd channels
              4. Specific channels""")

    while True:
        user_choice = input("Select channels to be measured: ").strip()
        if user_choice in choices:
            return choices[user_choice](available_modules)
        print("⚠ Invalid selection, please enter 1–4.")


def select_dynamic_ranges(mpm) -> List[int]:
    """Select optical dynamic ranges for the MPM."""
    available_modules = mpm.get_available_modules()
    print("\nAvailable dynamic ranges:")
    for module in available_modules:
        print(f"Module {module.module_number + 1}: {module.module_type} - Dynamic Ranges: {module.ranges}")

    selection = input("Select dynamic range(s) (e.g., 1,2,3): ")
    selected_ranges = re.findall(r"\d+", selection)
    return [int(i) for i in selected_ranges]


def save_scan_data(ilsts: StsProcess) -> None:
    """ Save measurement and reference data to files. """
    # Save reference scan data as a data file.
    data_utils.export_reference_data(ilsts)

    # Save the reference scan result data.
    data_utils.save_reference_result_data(ilsts)

    # Save the measurement scan data.
    data_utils.save_measurement_result_data(ilsts)

    # Save the IL data.
    data_utils.save_il_data(ilsts)


def connection() -> Tuple["TslInstrument", "MpmInstrument", Optional["DaqInstrument"]]:
    """
    Detect and connect to the TSL, MPM, and (optionally) DAQ instruments.

    Returns:
        tuple: (tsl_instrument, mpm_instrument, daq_instrument or None)

    Raises:
        RuntimeError: If required instruments (TSL or MPM) are not found.
    """
    connection_manager = ConnectionManager()
    instruments = connection_manager.list_instruments()

    print("Detected Instruments:", instruments)

    # Identify instruments by name patterns
    tsl_resource = next((dev for dev in instruments if "TSL" in dev), None)
    mpm_resource = next((dev for dev in instruments if "MPM" in dev), None)
    daq_resource = next((dev for dev in instruments if "Dev" in dev), None)

    # Validation
    if not tsl_resource:
        raise RuntimeError("❌ TSL instrument not detected. Please connect the TSL.")
    if not mpm_resource:
        raise RuntimeError("❌ MPM instrument not detected. Please connect the MPM.")

    # Connections
    tsl_instrument = connection_manager.connect_tsl(tsl_resource)
    mpm_instrument = connection_manager.connect_mpm(mpm_resource)

    # Optional DAQ connection
    daq_instrument = None
    if "210" in mpm_resource:
        if not daq_resource:
            raise RuntimeError("❌ DAQ device not detected. Please connect the DAQ.")
        daq_instrument = connection_manager.connect(daq_resource)

    print("Instruments successfully connected.")
    return tsl_instrument, mpm_instrument, daq_instrument


def tsl_power_check(tsl: "TslInstrument") -> None:
    """Prompt user to set TSL output power to ≤ 5 dBm."""
    while True:
        try:
            power = float(input("Please input the Output Power (dBm): "))
        except ValueError:
            print("⚠ Invalid input. Please enter a numeric value.")
            continue

        if power <= 5.0:
            tsl.set_power(power)
            print(f"Power set to {power:.2f} dBm.")
            break

        print("\n⚠ Power should be ≤ 5 dBm. Please try again.")


def wavelength_dependent_loss(
    tsl: "TslInstrument",
    mpm: "MpmInstrument",
    daq: Optional["DaqInstrument"]
) -> None:
    """
    Perform a wavelength-dependent loss (WDL) measurement.

    Steps:
      1. Load or request scan parameters.
      2. Select MPM channels and dynamic ranges.
      3. Initialize STS process.
      4. Perform reference and DUT scans.
      5. Plot, save, and export all results.
    """
    # --- Identify TSL type ---
    is_tsl_570 = not tsl.get_tsl_type_flag()

    # --- Load scan parameters ---
    scan_parameters = {}
    parameters_loaded  = data_utils.get_scan_parameters(scan_parameters, is_tsl_570, "220" in mpm.product_name)

    start_wl = scan_parameters["start_wavelength"]
    stop_wl = scan_parameters["stop_wavelength"]
    step = scan_parameters["scan_step"]
    power = scan_parameters["power"]
    speed = scan_parameters["scan_speed"]
    cycles = scan_parameters["scan_cycles"]
    delay = scan_parameters["scan_delay"]
    use_high_spec_mode = scan_parameters["use_high_spec_mode"]

    # --- Reference Data Import Handling ---
    reference_data = (
        data_utils.import_reference_scan_data()
        if parameters_loaded else None
    )

    # --- MPM configuration ---
    mpm_220_ref_module_info = [-1, -1]
    if reference_data:
        channel_range_selection = reference_data[0]
        selected_channels = channel_range_selection["channel_selection"]
        selected_dynamic_ranges = channel_range_selection["dynamic_range_selection"]
        mpm_220_ref_module_info = channel_range_selection["mpm_220_reference_channel"]
        reference_data = reference_data[1:]
    else:
        selected_channels = select_mpm_channels(mpm, use_high_spec_mode, mpm_220_ref_module_info)
        selected_dynamic_ranges = select_dynamic_ranges(mpm)

    # --- MPM 215 Special Handling ---
    if mpm.mpm_215_selection_check(selected_channels):
        tsl_power_check(tsl)
        selected_dynamic_ranges = [2]

    # --- Initialize STS Process ---
    ilsts = StsProcess(tsl, mpm, daq, use_high_spec_mode)

    # --- Set STS Process parameters ---
    ilsts.set_scan_parameters(start_wl, stop_wl, step, power, speed, selected_channels,
                              selected_dynamic_ranges, mpm_220_ref_module_info)

    # --- Reference Scan Process ---
    if reference_data:
        ilsts.load_reference_scan_data(reference_data)
        print("\nLoaded reference scan data.")
    else:
        print("\nReference process...")
        input("\nPress ENTER to start the reference process ")
        ilsts.reference_scan()

    # --- Measurement Scan Process ---
    print("\nMeasurement process...")
    redo_scan = "y"

    while redo_scan.lower() == "y":
        input("Connect the DUT and Press ENTER to start the measurement process ")

        for i in range(cycles):
            print(f"\n🟢 Measurement Scan {i + 1} of {cycles}...")
            ilsts.measurement_scan()

            # Optionally show graph
            if input("\nView the graph? (y/n): ").lower() == "y":
                plot_utils.plot_wavelength_dependent_loss(
                    ilsts.wavelength_table, ilsts.il
                )

            time.sleep(delay)

            if cycles > 1 and i < cycles - 1:
                input(f"\nPress ENTER to continue to Scan {i + 2}...")

        ilsts.get_dut_data()
        redo_scan = input("\nRedo Scan? (y/n): ")

    data_utils.export_scan_parameters(scan_parameters)
    save_scan_data(ilsts)

    print("\nWavelength-dependent loss measurement completed.")


def power_scan(tsl: "TslInstrument", mpm: "MpmInstrument") -> None:
    """
    Perform a power scan measurement across a power range using TSL and MPM.

    Steps:
      1. Configure MPM (gain, averaging)
      2. Sweep TSL output power
      3. Record corresponding MPM readings
      4. Plot and save results
    """
    # --- User input ---
    try:
        mpm_mod, mpm_chan = map(int, input("\nSelect Powermeter Module and Channel (Ex: 0,1): ").split(','))
        avg_time = float(input("Set Averaging time for the powermeter (0.01~10000.00) [msec]: "))

        set_wl = float(input("Set characterization wavelength [nm]: "))
        start_pow = float(input("Input start power [dBm]: "))
        stop_pow = float(input("Input stop power [dBm]: "))
        step_pow = float(input("Input power step [dB]: "))
    except ValueError:
        print("⚠ Invalid input format. Please enter numeric values correctly.")
        return

    # --- MPM setup ---
    mpm.write("AUTO")               # Automatic gain
    mpm.write(f"AVG {avg_time}")    # Averaging time in msec

    # --- TSL setup ---
    tsl.set_wavelength(set_wl)
    tsl.write(f"POW {start_pow}")

    if start_pow > stop_pow:
        step_pow = -abs(step_pow)
    else:
        step_pow = abs(step_pow)

    dwell_time = (DWELL_TIME_FACTOR * avg_time) / MS_TO_SEC

    # --- Measurement loop ---
    power_values: List[float] = []
    readings: List[float] = []

    current_power = start_pow
    while True:
        power_values.append(current_power)

        # Query MPM reading
        response = mpm.query(f"READ? {mpm_mod}")
        try:
            data = response[1].split(',')
            reading = float(data[mpm_chan - 1])
        except (IndexError, ValueError):
            print(f"⚠ Invalid MPM response for channel {mpm_chan}: {response}")
            reading = float('nan')

        readings.append(reading)
        time.sleep(dwell_time)

        # Update next power
        current_power = round(current_power + step_pow, 2)
        tsl.write(f"POW {current_power}")

        # Exit loop safely using a float comparison tolerance
        if (step_pow > 0 and current_power > stop_pow) or (step_pow < 0 and current_power < stop_pow):
            break

    # --- Plot & Save ---
    plot_utils.plot_power_reading(power_values, readings)
    data_utils.save_power_scan_results(power_values, readings)

    print("Power scan completed successfully.")


def main() -> None:
    """
    Main entry point of the program.
    Handles device connection, measurement selection, and process execution.
    """
    print("=== Instrument Link & Measurement System ===")

    try:
        tsl, mpm, daq = connection()
    except Exception as e:
        print(f"\n❌ Connection failed: {e}")
        return

    while True:
        # --- Measurement selection ---
        print("\nMeasurement Options:")
        print("1. Wavelength Dependent Loss (IL operation)")
        print("2. Power Scan")

        choice = input("Select measurement type [1/2]: ").strip()
        if choice not in ('1', '2'):
            print("⚠ Invalid selection. Please enter '1' or '2'.")
            continue

        # --- Execute selected measurement ---
        try:
            if choice == '1':
                wavelength_dependent_loss(tsl, mpm, daq)
            else:
                power_scan(tsl, mpm)
        except KeyboardInterrupt:
            print("\n⚠ Measurement aborted by user.")
        except Exception as e:
            print(f"\n❌ Error during measurement: {e}")

        # --- Continue or exit ---
        again = input("\nWould you like to continue? (Y/n): ").strip().lower()
        if again not in ('y', 'yes', ''):
            break

    print("\nProgram completed. Closing instruments...")

    try:
        tsl.disconnect()
        mpm.disconnect()
        if daq:
            daq.disconnect()
    except Exception as ex:
        print(f"⚠ Warning: Failed to disconnect one or more instruments safely. {ex}")
    else:
        print("All instruments disconnected successfully.")


if __name__ == "__main__":
    main()
