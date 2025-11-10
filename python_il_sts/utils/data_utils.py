"""
Data utility module.
"""

# Basic imports.
import os, json, csv
from array import array
from datetime import datetime

# Importing STS process and instrument classes
from ..measurements.sts_process import StsProcess
from ..utils.error_handling import sts_process_error_strings, STSProcessError

# Get the current date and time
now = datetime.now()
# Format the date and time as YYYY-MM-DD HH:MM:SS
formatted_datetime = now.strftime("%Y%m%d_%Hhr%Mm%Ssec")

# Ensure log directory exists.
LOG_DIR = "scan_data"
os.makedirs(LOG_DIR, exist_ok=True)

# Config save file names.
SCAN_PARAMETERS_CONFIG = os.path.join(LOG_DIR, "scan_parameters_config.json")
REFERENCE_SCAN_DATA = os.path.join(LOG_DIR, "reference_scan_data.dat")

# Scan data save file names.
FILE_REFERENCE_DATA_RESULTS = os.path.join(LOG_DIR, f"Reference_Data_{formatted_datetime}.csv")
FILE_MEASUREMENT_DATA_RESULTS = os.path.join(LOG_DIR, f"Measurement_Data_{formatted_datetime}.csv")
FILE_IL_DATA_RESULTS = os.path.join(LOG_DIR, f"IL_Data_{formatted_datetime}.csv")
FILE_POWER_SCAN_RESULTS = os.path.join(LOG_DIR, f"Power_Scan_Results_{formatted_datetime}.csv")


def import_scan_parameters(scan_parameters: dict):
    if os.path.exists(SCAN_PARAMETERS_CONFIG):
        user_choice = input("\nWould you like to load the most recent parameter settings from {}? "
                            "[y|n]: ".format(SCAN_PARAMETERS_CONFIG))

        if user_choice in "Yy":
            with open(SCAN_PARAMETERS_CONFIG, encoding='utf-8') as json_file:
                scan_parameters.update(json.load(json_file))
            print("\nLoaded scan parameters.")
            print("Start Wavelength (nm):", scan_parameters["start_wavelength"])
            print("Stop Wavelength (nm):", scan_parameters["stop_wavelength"])
            print("Scan Step (pm):", scan_parameters["scan_step"])
            print("Output Power (dBm):", scan_parameters["power"])
            print("Scan Speed (nm/s):", scan_parameters["scan_speed"])
            print("Scan Cycles:", scan_parameters["scan_cycles"])
            # print("Scan Delay:", scan_parameters["scan_delay"])
            print("Use High-Spec Mode:", scan_parameters["use_high_spec_mode"])
            return True
        else:
            return False
    else:
        print(f"{SCAN_PARAMETERS_CONFIG} file not found. Continuing...")
        return False


def import_reference_scan_data() -> dict | None:
    """ Ask user if they want to use the previous reference data if it exists. """
    if not os.path.exists(REFERENCE_SCAN_DATA):
        return None

    ans = input("\nWould you like to use the most recent reference data from file '{}'? [y|n]: "
                .format(REFERENCE_SCAN_DATA))

    if ans not in "Yy":
        return None

    # # Get the file size.
    # int_file_size = int(os.path.getsize(REFERENCE_SCAN_DATA))
    # str_file_size = f"{int_file_size / 1000000:.2f} MB" if int_file_size > 1000000 else f"{int_file_size / 1000:.2f} KB"
    # print("Opening " + str_file_size + " file '" + REFERENCE_SCAN_DATA + "'...")

    with open(REFERENCE_SCAN_DATA, 'r', encoding='utf-8') as file:
        data = file.read()
        reference_scan_data = json.loads(data)

    return reference_scan_data


def get_tsl_scan_speed(step_wavelength) -> int:
    """
    Displays the TSL speed table
    and gets the scan speed from the user.

    Step wavelength in pm.

    :return: int | TSL scan speed
    """
    speed_table = {}

    thresholds = [(0.2, "1", 1), (0.2, "2", 2), (0.5, "3", 5), (1, "4", 10),
                  (1, "5", 20), (2.5, "6", 50), (5, "7", 100), (100, "8", 200)]

    for limit, key, value in thresholds:
        if step_wavelength >= limit:
            speed_table[key] = value

    print("\nTSL Speed Table:")
    for speed in speed_table:
        print(f"No. {speed} - {speed_table[speed]} nm/s")

    # print("\nRecommended, use lower speeds for better accuracy")
    user_select_scan_speed = input("Select the scan speed no.: ")
    return speed_table[user_select_scan_speed]


def get_scan_parameters(scan_parameters: dict, is_tsl_570 = True, is_mpm_220 = False):
    load_scan_parameters = import_scan_parameters(scan_parameters)
    if not load_scan_parameters:
        scan_parameters["start_wavelength"] = float(input("\nInput Start Wavelength (nm): "))
        scan_parameters["stop_wavelength"] = float(input("Input Stop Wavelength (nm): "))
        scan_parameters["scan_step"] = float(input("Input Scan Step (pm): "))
        scan_parameters["power"] = float(input("Input Output Power (dBm): "))
        scan_parameters["scan_cycles"] = int(input("Input Scan Cycles: "))
        scan_parameters["scan_delay"] = 0
        if is_tsl_570:
            scan_parameters["scan_speed"] = get_tsl_scan_speed(scan_parameters["scan_step"])
        else:
            scan_parameters["scan_speed"] = int(input("Input Scan Speed (nm/s): "))

        # --- Identify MPM type and select the operation mode ---
        if is_mpm_220:
            print("\nMPM-220 instrument detected. Please select the operation mode.")
            choice = input("Select measurement type [1: Standard / 2: High-spec]: ").strip()

            if choice not in ('1', '2'):
                raise ValueError("⚠ Invalid selection. Please enter 1 or 2.")

            scan_parameters["use_high_spec_mode"] = (choice == '2')
        else:
            scan_parameters["use_high_spec_mode"] = False
    return load_scan_parameters


def export_scan_parameters(scan_parameters: dict):
    json_data = {
        "start_wavelength": scan_parameters["start_wavelength"],
        "stop_wavelength": scan_parameters["stop_wavelength"],
        "scan_step": scan_parameters["scan_step"],
        "power": scan_parameters["power"],
        "scan_speed": scan_parameters["scan_speed"],
        "scan_cycles": scan_parameters["scan_cycles"],
        "scan_delay": scan_parameters["scan_delay"],
        "use_high_spec_mode": scan_parameters["use_high_spec_mode"]
    }

    with open(SCAN_PARAMETERS_CONFIG, 'w', encoding='utf8') as export_file:
        json.dump(json_data, export_file, indent=4)

    print("\nSaved scan parameters to the file " + SCAN_PARAMETERS_CONFIG + ".")


def export_reference_data(ilsts: StsProcess):
    """ Save reference data as a data file. """
    reference_data_array = [ilsts.get_channel_range_selection()]
    reference_data_array.extend(ilsts.ref_data_array)

    data = json.dumps(reference_data_array, indent=4).replace("'", '"')
    with open(REFERENCE_SCAN_DATA, 'w', encoding='utf-8') as file:
        file.write(data)

    print("\nSaved reference data to the file " + REFERENCE_SCAN_DATA + ".")


def check_and_rename_old_file(filename: str):
    """ Check and rename old file. """
    if os.path.exists(filename):

        # Create a new subfolder if it doesn't already exist.
        str_previous_folder = "previous"
        if not os.path.exists(r"./" + str_previous_folder):
            os.mkdir(str_previous_folder)

        time_now = datetime.now()
        str_new_filename_and_path = str_previous_folder + "/" + time_now.strftime("%Y%m%d_%H%M%S") + "_" + filename

        try:
            os.rename(filename, str_new_filename_and_path)
        except Exception as ex:
            print("Failed to rename and move file %s to %s.", filename, str_new_filename_and_path)
            print(str(ex))
            print("Press ENTER to attempt to move the file again.")
            input()
            os.rename(filename, str_new_filename_and_path)


def save_reference_result_data(ilsts: StsProcess):
    """ Save reference data to CSV for human consumption. Differs from the json data. """
    check_and_rename_old_file(FILE_REFERENCE_DATA_RESULTS)

    print("Saving Reference data to the csv file " + FILE_REFERENCE_DATA_RESULTS + "...")

    # Create a CSV file that has columns similar to...
    # Wavelength Slot1Ch1_PowerMonitor Slot1Ch1_MPMPower Slot1Ch2_PowerMonitor Slot1Ch2_MPMPower

    ref_data_array = ilsts.ref_data_array

    # Header wavelength is static. There could be any number of slots and channels.
    header = ["Wavelength(nm)"]
    for item in ref_data_array:
        header.append("Slot{}Ch{}_MPMPower".format(str(item["SlotNumber"] + 1), str(item["ChannelNumber"])))
        header.append("Slot{}Ch{}_PowerMonitor".format(str(item["SlotNumber"] + 1), str(item["ChannelNumber"])))

    all_rows = []  # our row array will contain one array for each line.

    # All the wavelengths are all the same for any slot and channel. So just get the first one.
    wavelength_table = ref_data_array[0]["rescaled_wavelength"]
    # error_code, wavelength table = ilsts.ilsts.Get_Target_Wavelength_Table(None)

    # For each wavelength, get the data
    i = 0
    for this_wavelength in wavelength_table:
        this_row_array = [this_wavelength]  # wavelength
        for this_refdata in ref_data_array:
            this_row_array.append(str(this_refdata["rescaled_reference_power"][i]))  # MPM power
            this_row_array.append(str(this_refdata["rescaled_monitor"][i]))  # Power monitor data

        all_rows.append(this_row_array)
        i += 1

    with open(FILE_REFERENCE_DATA_RESULTS, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        # write the header
        writer.writerow(header)
        # write all rows
        writer.writerows(all_rows)


def save_measurement_result_data(ilsts: StsProcess):
    """ Save dut data to CSV for human consumption. """
    check_and_rename_old_file(FILE_MEASUREMENT_DATA_RESULTS)

    print("Saving Raw data to the csv file " + FILE_MEASUREMENT_DATA_RESULTS + "...")

    # Create a CSV file that has columns similar to...
    # Wavelength Slot1Ch1_PowerMonitor Slot1Ch1_MPMPower Slot1Ch2_PowerMonitor Slot1Ch2_MPMPower

    dut_data_array = ilsts.dut_data_array

    # Header wavelength is static. There could be any number of slots and channels.
    header = ["Wavelength(nm)"]
    for item in dut_data_array:
        header.append("Slot{}Ch{}R{}_MPMPower"
                      .format(str(item["SlotNumber"] + 1), str(item["ChannelNumber"]), str(item["RangeNumber"])))
        header.append("Slot{}Ch{}R{}_PowerMonitor"
                      .format(str(item["SlotNumber"] + 1), str(item["ChannelNumber"]), str(item["RangeNumber"])))

    all_rows = []  # our row array will contain one array for each line.

    # All the wavelengths are all the same for any slot and channel. So just get the first one.
    wavelength_table = dut_data_array[0]["rescaled_wavelength"]
    # error_code, wavelength table = ilsts.ilsts.Get_Target_Wavelength_Table(None)

    # For each wavelength, get the data
    i = 0
    for this_wavelength in wavelength_table:
        this_row_array = [this_wavelength]  # wavelength
        for dut_data in dut_data_array:
            this_row_array.append(str(dut_data["rescaled_dut_power"][i]))  # MPM power data
            this_row_array.append(str(dut_data["rescaled_dut_monitor"][i]))  # Power monitor data

        all_rows.append(this_row_array)
        i += 1

    with open(FILE_MEASUREMENT_DATA_RESULTS, 'w', encoding='UTF8', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(header)
        writer.writerows(all_rows)


def save_il_data(ilsts: StsProcess):
    """ Save IL data. """
    check_and_rename_old_file(FILE_IL_DATA_RESULTS)

    print("Saving IL data to the csv file " + FILE_IL_DATA_RESULTS + "...")

    ilsts.il_data = []
    il_data_array = []

    # Get rescaling wavelength table
    error_code, wavelength_table = ilsts.il_sts.Get_Target_Wavelength_Table(None)
    if error_code != 0:
        raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

    for item in ilsts.merge_data:
        # Pull out IL data of after merge
        error_code, ilsts.il_data = ilsts.il_sts.Get_IL_Merge_Data(None, item)
        if error_code != 0:
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        ilsts.il_data = array("d", ilsts.il_data)  # List to Array
        il_data_array.append(ilsts.il_data)

    # Open file And write data for .csv
    with open(FILE_IL_DATA_RESULTS, "w", newline="", encoding='utf-8') as f:
        writer = csv.writer(f)

        header = ["Wavelength(nm)"]
        writestr = []

        # header
        for item in ilsts.merge_data:
            ch = "Slot" + str(item.SlotNumber + 1) + "Ch" + str(item.ChannelNumber)
            header.append(ch)

        writer.writerow(header)
        counter = 0
        for wave in wavelength_table:
            writestr.append(str(wave))

            for item in il_data_array:
                data = item[counter]
                writestr.append(data)
            writer.writerow(writestr)
            writestr.clear()
            counter += 1
    f.close()


def save_rawdata_unused(ilsts: StsProcess,
                        fpath: str,
                        mpm_range):
    """
    Save measurement Rawdata for specific dynamic_range.
    Saves raw data (MPM and power monitor) during DUT measurement
    Args:
        ilsts (StsProcess)
        fpath (str): path and file name
        mpm_range (int): Optical dynamic dynamic_range of interest
    """
    error_code, wavelength_table = ilsts.il_sts.Get_Target_Wavelength_Table(None)
    if error_code != 0:
        raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

    lst_pow = []
    dut_mon = []
    for item in ilsts.dut_data:
        print(item)
        if item.RangeNumber != mpm_range:
            print(item.RangeNumber)
            input()
            continue
        # Pull out measurement raw data of after rescaling
        error_code, dut_pwr, dut_mon = ilsts.il_sts.Get_Meas_RawData(item, None, None)
        if error_code != 0:
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        dut_pwr = array("d", dut_pwr)  # List to Array
        dut_mon = array("d", dut_mon)  # List to Array
        lst_pow.append(dut_pwr)

    # for header
    header = ["Wavelength(nm)"]

    for item in ilsts.dut_data:
        if item.RangeNumber != mpm_range:
            continue
        header_str = "Slot" + str(item.SlotNumber + 1) + "Ch" + str(item.ChannelNumber)
        header.append(header_str)

    header_str = "Monitor"
    header.append(header_str)

    # Open file and write data for .csv
    with open(fpath, "w", newline="", encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(header)

        # for data
        write_st = []
        counter = 0
        for wave in wavelength_table:
            write_st.append(wave)
            # power data
            for item in lst_pow:
                data = item[counter]
                write_st.append(data)
            # monitor data
            data = dut_mon[counter]
            write_st.append(data)
            writer.writerow(write_st)
            write_st.clear()
            counter += 1
        f.close()


def save_power_scan_results(power_array: list, power_reading: list):
    """ Save power scan data. """
    check_and_rename_old_file(FILE_POWER_SCAN_RESULTS)

    print("\nSaving power scan data to file " + FILE_POWER_SCAN_RESULTS + "...")

    with open(FILE_POWER_SCAN_RESULTS, mode='w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Power Array (dBm)', 'Power Reading (dBm)'])
        writer.writerows(zip(power_array, power_reading))

    print(f"Data successfully saved to {FILE_POWER_SCAN_RESULTS}")

