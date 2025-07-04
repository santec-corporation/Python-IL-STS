# -*- coding: utf-8 -*-

"""
STS Process Class.

@organization: Santec Holdings Corp.
"""

import re
import time
from array import array

# Importing classes from STSProcess DLL
from Santec.STSProcess import PDLSTS, RescalingMode, STSDataStruct, STSDataStructForMerge, Module_Type

# Importing instrument classes and sts error strings
from .sts_process import STSData
from .mpm_instrument_class import MpmInstrument
from .tsl_instrument_class import TslInstrument
from .error_handling_class import STSProcessError, sts_process_error_strings

# Import program logger
from . import logger


class StsProcess2(STSData):
    """
    STS Process class for MPM 220.

    Class to set sweep parameters,
    perform sweep operations and get sweep operation data.

    Attributes:
        _tsl (TslInstrument): TSL instrument class handle.
        _mpm (MpmInstrument): MPM instrument class handle.
        _ilsts (ILSTS): ILSTS class instance from Santec namespace.

    Parameters:
        tsl (TslInstrument): TSL instrument class instance.
        mpm (MpmInstrument): MPM instrument class instance.
    """

    def __init__(self,
                 tsl: TslInstrument,
                 mpm: MpmInstrument
                 ):
        logger.info("Initializing STS Process class.")
        self._tsl = tsl
        self._mpm = mpm

        self._ilsts = PDLSTS()
        logger.info(f"STS Process details, TslInstrument: {tsl}, MpmInstrument: {mpm}")

    @property
    def ilsts(self) -> PDLSTS:
        """
        Returns:
            ILSTS (Santec) class handle from the StsProcess class attributes.
        """
        return self._ilsts

    def set_parameters(self) -> None:
        """
        Sets the sweep parameters for an STS process operation.

        Raises:
            STSProcessError: When Reference/DUT data couldn't be erased,
                        When Wavelength table couldn't be created,
                        Error with rescaling,
                        If setting STS sweep parameters fails.
        """
        logger.info("Setting STS params")

        # Logging parameters for MPM
        self._mpm.set_logging_parameters(self._tsl.start_wavelength,
                                         self._tsl.stop_wavelength,
                                         self._tsl.sweep_step,
                                         self._tsl.sweep_speed,
                                         self._tsl.actual_step)

        time.sleep(0.1)  # Add sleep time for 100ms

        # Set Rescaling mode for STSProcess class
        logger.info("STS rescaling settings")
        sts_error = self._ilsts.Set_Rescaling_Setting(RescalingMode.Freerun_TSLMonitor,
                                                      self._mpm.get_averaging_time(),
                                                      True)

        if sts_error != 0:
            logger.error("Error while rescaling setting, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        # Make Wavelength table at sweep
        logger.info("Making sweep wavelength table")
        sts_error = self._ilsts.Make_Sweep_Wavelength_Table(self._tsl.start_wavelength,
                                                            self._tsl.stop_wavelength,
                                                            self._tsl.actual_step)

        if sts_error != 0:
            logger.error("Error while making wavelength table at sweep, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        # Make wavelength table as rescaling
        logger.info("Making target wavelength table")
        sts_error = self._ilsts.Make_Target_Wavelength_Table(self._tsl.start_wavelength,
                                                             self._tsl.stop_wavelength,
                                                             self._tsl.sweep_step)

        if sts_error != 0:
            logger.error("Error while making wavelength table as rescaling, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        # STS Process setting Class
        logger.info("Clearing STS ref data")
        sts_error = self._ilsts.Clear_Refdata()  # Reference data Clear
        if sts_error != 0:
            logger.error("Error while clearing reference data, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        logger.info("Clearing STS meas data")
        sts_error = self._ilsts.Clear_Measdata()  # Clear measurement data
        if sts_error != 0:
            logger.error("Error while clearing measurement data, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        logger.info("STS params set.")

    def set_selected_channels(self, previous_param_data: dict) -> None:
        """
        Select channels to be measured.
        It offers the user to choose between different ways to select MPM channels.

        Checks if previous sweep parameters setting available,
        if available, then loads the selected channels from the previous sweep parameters setting.

        Parameters:
            previous_param_data (dict): Previous sweep parameters settings.
        """
        logger.info("STS set selected channels for measurement")

        self.selected_chans = []
        # Array of arrays: array 0 displays the connected modules
        # The following arrays contain ints of available channels of each module
        self.all_modules = self._mpm.get_modules()
        logger.info(f"Available modules: {self.all_modules}")

        if previous_param_data is not None:
            logger.info("Loading selected channels from previous scan params")
            self.selected_chans = previous_param_data["selected_chans"]  # an array, like [1,3,5]
            allModChans = ""
            for this_mod_channel in self.selected_chans:
                allModChans += ",".join(
                    [str(element) for element in this_mod_channel]) + "; "  # contains numbers so does a conversion
            logger.info("Loaded the selected channels: " + allModChans.strip())
            print("Loaded the selected channels: " + allModChans.strip())
            return None

        print("\nAvailable modules/channels:")
        for module in self.all_modules:
            if module.module_type is None:
                continue
            print("\r" + "Module No. {}: {} - Channels: {}".format(module.module_number, module.module_type,
                                                                   module.channels))

        mpm_choices = {'1': self.set_all_channels,
                       '2': self.set_even_channels,
                       '3': self.set_odd_channels,
                       '4': self.set_special_channels}

        print("""\nChannels measurement options:\n  1. All channels\n"""
              """  2. Even channels\n  3. Odd channels\n  4. Specific channels""")
        user_selection = input("Select channels to be measured: ")
        mpm_choices[user_selection]()
        logger.info(f"Selected channels: {self.selected_chans}")
        logger.info("STS channel selection done.")

    def set_all_channels(self):
        """ Selects all modules and all channels that are connected to MPM. """
        logger.info("Selecting all channels for operation")
        for module in self.all_modules:
            for channel_number in module.channels:
                self.selected_chans.append([module.module_number, channel_number])

    def set_even_channels(self) -> None:
        """ Selects only even channels on the MPM. """
        logger.info("Selecting even channels for operation")
        for module in self.all_modules:
            for channel_number in module.channels:
                if channel_number % 2 == 0:
                    self.selected_chans.append([module.module_number, channel_number])

    def set_odd_channels(self) -> None:
        """ Selects only odd channels on the MPM. """
        logger.info("Selecting odd channels for operation")
        for module in self.all_modules:
            for channel_number in module.channels:
                if channel_number % 2 != 0:
                    self.selected_chans.append([module.module_number, channel_number])

    def set_special_channels(self) -> None:
        """ Manually enter/select the channels to be measured. """
        logger.info("Selecting specific channels for operation")
        selection = input("Input (module,channel) to be tested [ex: (0,1); (1,1)]  ")
        selection = re.findall(r"[\w']+", selection)
        logger.info("Special channel user selection: %s", selection)

        i = 0
        while i <= len(selection) - 1:
            self.selected_chans.append([selection[i], selection[i + 1]])
            i += 2
        logger.info("Special channels set.")

    def mpm_215_selection_check(self) -> bool:
        """ Checks if an MPM-215 module is present and returns a boolean. """
        modules_info = self.all_modules
        selected_channels = self.selected_chans
        use_mpm_215_flag = False

        for selection in selected_channels:
            module_no = int(selection[0])
            if modules_info[module_no].module_type == 'MPM-215':
                use_mpm_215_flag = True
        return use_mpm_215_flag

    def set_selected_ranges(self, previous_param_data: dict) -> None:
        """
        Sets the optical dynamic dynamic_range of the MPM.

        Checks if previous sweep parameters setting available,
        if available, then loads the selected ranges from the previous sweep parameters setting.

        Parameters:
            previous_param_data (dict): Previous sweep parameters settings.
        """
        logger.info("STS set selected ranges")
        if previous_param_data is not None:  # Display previously used optical dynamic ranges
            logger.info("Loading selected ranges from previous scan params")
            self.selected_ranges = previous_param_data["selected_ranges"]  # an array, like [1,3,5]
            str_all_ranges = ""
            str_all_ranges += ",".join(
                [str(elem) for elem in self.selected_ranges])  # contains numbers so does a conversion
            logger.info("Using the loaded dynamic ranges: " + str_all_ranges)
            print("Using the loaded dynamic ranges: " + str_all_ranges)

        else:
            self.selected_ranges = []
            print("\nAvailable dynamic ranges:")
            self._mpm.get_range()
            for i in range(len(self._mpm.range_data)):
                print('{}. {}'.format(i + 1, self._mpm.dynamic_ranges[i]))
            selection = input("Select a dynamic dynamic_range (Ex: 1,2,3): ")
            logger.info("User selected dynamic_range(s): %s", selection)
            self.selected_ranges = re.findall(r"[\w']+", selection)

        # Convert the string ranges to ints, because that is what the DLL is expecting.
        self.selected_ranges = [int(i) for i in self.selected_ranges]
        logger.info(f"Selected ranges: {self.selected_ranges}")

    def set_sts_data_struct(self) -> None:
        """ Create the data structures, which includes the potentially savable reference data. """
        logger.info("Set STS data struct")
        self.clear_sts_data_struct()  # Clears all the sts data struct lists.
        counter = 1

        # Configure STSDatastruct for each measurement
        logger.info("Configure STSDatastruct for each measurement")
        for m_range in self.selected_ranges:
            for ch in self.selected_chans:
                data_st = STSDataStruct()
                data_st.MPMNumber = 0
                data_st.SlotNumber = int(ch[0])  # slot number
                data_st.ChannelNumber = int(ch[1])  # channel number
                data_st.RangeNumber = m_range  # array of MPM ranges
                data_st.SweepCount = counter
                data_st.SOP = 0
                self.dut_data.append(data_st)

                range_index = self.selected_ranges.index(m_range)
                channel_index = self.selected_chans.index(ch)

                # measurement monitor data need only 1 channel for each dynamic_range.
                if channel_index == 0:
                    self.dut_monitor.append(data_st)
                    self.dynamic_range.append(m_range)

                # reference data need only 1 dynamic_range for each ch
                if range_index == 0:
                    self.ref_data.append(data_st)
                    self.ref_monitor.append(data_st)
            counter += 1

        # Configure STSDataStruct for merge
        logger.info("Configure STSDataStruct for merge")
        for ch in self.selected_chans:
            merge_sts = STSDataStructForMerge()
            merge_sts.MPMnumber = 0
            merge_sts.SlotNumber = int(ch[0])  # slot number
            merge_sts.ChannelNumber = int(ch[1])  # channel number
            merge_sts.SOP = 0
            self.merge_data.append(merge_sts)

        logger.info("STS data struct set.")

    def clear_sts_data_struct(self) -> None:
        """
        Clears all the sts data struct lists.
        Lists cleared are:
            dut_monitor
            dut_data
            merge_data
            ref_monitor
            ref_data
            dynamic_range
        """
        logger.info("Clear all the sts data struct lists.")
        self.dut_monitor.clear()
        self.dut_data.clear()
        self.merge_data.clear()
        self.ref_monitor.clear()
        self.ref_data.clear()
        self.dynamic_range.clear()

    def sts_reference(self) -> None:
        """ Take reference data for each module/channel selected by the user. """
        logger.info("STS reference operation")
        for i in self.ref_data:
            input("\nConnect Slot{} Ch{}, then press ENTER".format(i.SlotNumber, i.ChannelNumber))
            logger.info("STS reference of Slot{} Ch{}".format(i.SlotNumber, i.ChannelNumber))

            # Set MPM dynamic dynamic_range mode to AUTO
            self._mpm.set_read_range_mode()

            time.sleep(0.1)  # Add sleep time for 100ms

            # Get the read power of the MPM i.ChannelNumber
            power = self._mpm.get_read_power_channel(i.SlotNumber, i.ChannelNumber)

            # Get the reference dynamic_range based on the read power
            reference_range = self.get_reference_range(power)

            # Set the reference dynamic_range value to the MPM channel
            self._mpm.set_channel_range(i.SlotNumber, i.ChannelNumber, reference_range)

            print("\nScanning...")

            # Base sweep process
            self.base_sweep_process()

            # Get sampling data
            self.get_reference_data(i)

            # TSL sweep stop
            self._tsl.stop_sweep()

        logger.info("STS reference completed.")

    @staticmethod
    def get_reference_range(power: float):
        """ Returns the optimal dynamic_range for reference. """
        if power >= 0:
            return 1
        elif power >= -10:
            return 2
        elif power >= -20:
            return 3
        elif power >= -30:
            return 4
        else:
            return 5

    def sts_reference_from_saved_file(self) -> None:
        """
        Loading reference data from saved file.

        Raises:
            Exception: If the reference data array is null or empty.
            STSProcessError: If loading the reference data fails.
        """
        logger.info("Loading STS reference from data file.")
        if self.reference_data_array is None or len(self.reference_data_array) == 0:
            logger.error("The reference data array cannot be null or empty when loading reference data from files.")
            raise Exception(
                "\nThe reference data array cannot be null or empty when loading reference data from files.")

        if len(self.reference_data_array) != len(self.ref_data):
            logger.error(
                "The length is different between the saved reference array and the newly-obtained reference array.")
            raise Exception(
                "The length is different between the saved reference array and the newly-obtained reference array.")

        matched_data_structure = None

        for cached_ref_object in self.reference_data_array:
            # self.ref_data is an array of data structures.
            # We need to get that exact data structure because the object is special.
            # Find the matching data structure between ref_data and reference_data_array.
            for i in [
                x for x in self.ref_data
                if x.MPMNumber == cached_ref_object["MPMNumber"]
                   and x.SlotNumber == cached_ref_object["SlotNumber"]
                   and x.ChannelNumber == cached_ref_object["ChannelNumber"]
            ]:
                matched_data_structure = i

            print('Loading reference data for Slot{} Ch{}...'.format(matched_data_structure.SlotNumber,
                                                                     matched_data_structure.ChannelNumber))

            logger.info("Adding ref mpm channel data")
            errorcode = self._ilsts.Add_Ref_MPMData_CH(cached_ref_object["log_data"], matched_data_structure)
            if errorcode != 0:
                logger.error("Error while loading ref data, ",
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            logger.info("Adding ref monitor data")
            errorcode = self._ilsts.Add_Ref_MonitorData(cached_ref_object["trigger"], cached_ref_object["monitor"],
                                                        matched_data_structure)
            if errorcode != 0:
                logger.error("Error while loading ref data, ",
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            logger.info("Calling ref data for rescaling")
            errorcode = self._ilsts.Cal_RefData_Rescaling()  # Rescaling for reference data.
            if errorcode != 0:
                logger.error("Error while loading ref data, ",
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

    def sts_measurement(self) -> None:
        """
        DUT measurement operation.

        Raises:
            STSProcessError: If DUT measurement operation fails.
        """
        logger.info("STS measurement operation")

        sweep_count = 1
        for mpm_range in self.dynamic_range:
            # Set the MPM dynamic dynamic_range
            self._mpm.set_range(mpm_range)

            # Base sweep process
            self.base_sweep_process()

            # Get the measurement scan data
            _ = self.sts_get_measurement_data(sweep_count)

            sweep_count += 1

        # Call the measurement data for rescaling
        logger.info("Calling meas data for rescaling of mpm_range: ")
        errorcode = self._ilsts.Cal_MeasData_Rescaling()
        if errorcode != 0:
            logger.error("Error while performing DUT measurement, ",
                         str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # Call the IL merge data
        logger.info("Calling IL merge")
        errorcode = self._ilsts.Cal_IL_Merge(Module_Type.MPM_211)  # Range data merge
        if errorcode != 0:
            logger.error("Error while performing DUT measurement, ",
                         str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # TSL Sweep stop
        self._tsl.stop_sweep()

        # This portion of the code just to get wavelength
        # and IL data at the end of the scan
        self.wavelength_table = []
        self.il_data = []
        self.il_data_array = []

        # Get rescaling wavelength table
        for wav in list(self._ilsts.Get_Target_Wavelength_Table(None)[1]):
            self.wavelength_table.append(wav)
        if errorcode != 0:
            logger.error("Error while performing DUT measurement, ",
                         str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        for item in self.merge_data:
            # Pull out IL data of after merge
            logger.info("Getting IL merge data of: MPM%d Slot%d Ch%d SOP%d",
                        item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.SOP)
            errorcode, self.il_data = self._ilsts.Get_IL_Merge_Data(None, item)
            if errorcode != 0:
                logger.error("Error while performing DUT measurement of: MPM%d Slot%d Ch%d SOP%d, ",
                             item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.SOP,
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            self.il_data = array("d", self.il_data)  # List to Array
            self.il_data_array.append(self.il_data)
        self.il = []
        for i in self.il_data_array[0]:
            self.il.append(i)

        logger.info("STS measurement operation done.")

    def base_sweep_process(self) -> None:
        """
        Configures TSL & MPM to perform a sweep process.

        Raises:
            RuntimeError: If TSL/MPM and Daq instruments are not synchronized
            TSL or MPM times out.
            Exception: If there is an issue with TSL sweep process.
        """
        logger.info("STS sweep proces")

        # Start the TSL sweep proces
        self._tsl.start_sweep()

        # Start the MPM logging
        self._mpm.logging_start()

        try:
            # Wait until the TSL is set to "Waiting for trigger" status
            self._tsl.wait_for_sweep_status(waiting_time=5000, sweep_status=4)

            mpm_wait_time = int((self._tsl.stop_wavelength - self._tsl.start_wavelength) / self._tsl.sweep_speed * 1100)
            if mpm_wait_time < 5000:
                mpm_wait_time = 5000

            # Issue the TSL soft trigger
            self._tsl.soft_trigger()

            # Wait until the TSL is set to "Standby" status
            self._tsl.wait_for_sweep_status(waiting_time=mpm_wait_time, sweep_status=1)

            # Wait for MPM log completion
            self._mpm.wait_for_log_completion()

            # Stop the MPM logging
            self._mpm.logging_stop(True)

            # Wait until the TSL is set to "Standby" status
            self._tsl.wait_for_sweep_status(waiting_time=5000, sweep_status=1)

            # Start the TSL sweep
            self._tsl.start_sweep()

        except RuntimeError as scan_exception:
            self._tsl.stop_sweep(False)
            self._mpm.logging_stop(False)
            logger.error(scan_exception)
            raise scan_exception

        except Exception as tsl_exception:
            self._mpm.logging_stop(False)
            logger.error(tsl_exception)
            raise tsl_exception

        logger.info("STS base sweep process done.")

        return None

    def get_reference_data(self, data_struct_item: STSDataStruct) -> None:
        """
        Get the reference data by using the parameter data structure, as well as the trigger points, and monitor data.

        Parameters:
            data_struct_item (STSDataStruct): Contains all information of tested module/channel.

        Raises:
            Exception: If power monitor/MPM data were not added to the data structure,
                    Issues with the recalling process,
                    Mismatch between the length of the power monitor data and the length of the MPM data.
            STSProcessError: If getting the reference data fails.
        """
        logger.info("STS get reference data")
        # Get MPM logging data
        log_data = self._mpm.get_each_channel_log_data(data_struct_item.SlotNumber, data_struct_item.ChannelNumber)

        # Add MPM Logging data for STS Process Class
        self.log_data = array('d', log_data)  # List to Array
        logger.info(
            f"Reference log details: MPMNumber={data_struct_item.MPMNumber}, SlotNumber={data_struct_item.SlotNumber}"
            f"ChannelNumber={data_struct_item.ChannelNumber}, RangeNumber={data_struct_item.RangeNumber},"
            f"Log data length={len(log_data)}")

        logger.info("Adding ref mpm channel data.")
        errorcode = self._ilsts.Add_Ref_MPMData_CH(log_data, data_struct_item)
        if errorcode != 0:
            logger.info("Error while getting ref data, ",
                        str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # Get the trigger data from the MPM
        trigger = self._mpm.get_trigger_data(data_struct_item.SlotNumber)

        # Get the monitor data from the TSL
        monitor = self._tsl.get_power_logging_data()

        trigger_data = array("d", trigger)  # List to Array
        monitor_data = array("d", monitor)  # list to Array

        # Add Monitor data for STS Process Class
        logger.info("Adding ref monitor data.")
        errorcode = self._ilsts.Add_Ref_MonitorData(trigger_data, monitor_data, data_struct_item)
        if errorcode != 0:
            logger.info("Error while getting ref data, ",
                        str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # Rescaling for reference data.
        # We must rescale before we get the reference data.
        # Otherwise, we end up with way too many monitor and logging points.
        logger.info("Calling ref data for rescaling.")
        errorcode = self._ilsts.Cal_RefData_Rescaling()
        if errorcode != 0:
            logger.info("Error while getting ref data, ",
                        str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # After rescaling is done, get the raw reference data.
        logger.info("Getting ref raw data.")
        errorcode, rescaled_ref_pwr, rescaled_ref_mon = self._ilsts.Get_Ref_RawData(data_struct_item, None, None)
        logger.info(f"Rescaled ref raw power: {len(rescaled_ref_pwr)}, "
                    f"Rescaled red monitor: {len(rescaled_ref_mon)}")

        if errorcode != 0:
            logger.info("Error while getting ref data, ",
                        str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        logger.info("Getting target wavelength table.")
        errorcode, wavelength_array = self._ilsts.Get_Target_Wavelength_Table(None)
        logger.info(f"Wavelength table length: {len(wavelength_array)}")
        if errorcode != 0:
            logger.info("Error while getting ref data, ",
                        str(errorcode) + ": " + sts_process_error_strings(errorcode))
            raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        if (len(wavelength_array) == 0 or len(wavelength_array) != len(rescaled_ref_pwr) or len(wavelength_array)
                != len(rescaled_ref_mon)):
            logger.info(
                "The length of the wavelength array is {}, the length of the reference power array is {}, "
                "and the length of the reference monitor is {}. They must all be the same length.".format(
                    len(wavelength_array), len(rescaled_ref_pwr), len(rescaled_ref_mon)))
            raise Exception(
                "The length of the wavelength array is {}, the length of the reference power array is {}, "
                "and the length of the reference monitor is {}. They must all be the same length.".format(
                    len(wavelength_array), len(rescaled_ref_pwr), len(rescaled_ref_mon)))

        # Save all desired reference data into the reference array of this StsProcess class.
        ref_object = {
            "MPMNumber": data_struct_item.MPMNumber,
            "SlotNumber": data_struct_item.SlotNumber,
            "ChannelNumber": data_struct_item.ChannelNumber,
            "log_data": list(self.log_data),
            "trigger": list(array('d', trigger_data)),
            "monitor": list(array('d', monitor_data)),
            "rescaled_monitor": list(array('d', rescaled_ref_mon)),  # rescaled monitor data
            "rescaled_wavelength": list(array('d', wavelength_array)),  # all wavelengths, including triggers inbetween.
            "rescaled_reference_power": list(array('d', rescaled_ref_pwr)),  # rescaled reference power
        }
        self.reference_data_array.append(ref_object)

        return None

    def sts_get_measurement_data(self, sweep_count: int) -> int:
        """
        Gets logged data during DUT measurement.

        Parameters:
            sweep count (int): The number of sweep process operations.

        Raises:
            Exception: If power monitor/MPM data couldn't be added to the data structure.
            STSProcessError: If getting the measurement data fails.
        """
        logger.info("STS get measurement data")

        errorcode = 0
        for item in self.dut_data:
            if item.SweepCount != sweep_count:
                continue

            # Get MPM logging data
            log_data = self._mpm.get_each_channel_log_data(item.SlotNumber, item.ChannelNumber)
            log_data = array("d", log_data)  # List to Array
            logger.info(f"Measurement log details: MPMNumber={item.MPMNumber}, SlotNumber={item.SlotNumber}"
                        f"ChannelNumber={item.ChannelNumber}, RangeNumber={item.RangeNumber},"
                        f"Log data length={len(log_data)}")

            # Add MPM Logging data for STSProcess Class with STSDatastruct
            logger.info("Adding meas mpm channel data")
            errorcode = self._ilsts.Add_Meas_MPMData_CH(log_data, item)
            if errorcode != 0:
                logger.error("Error while getting measurement data, ",
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        # Get the trigger data from the MPM
        trigger = self._mpm.get_trigger_data(0)

        # Get the monitor data from the TSL
        monitor = self._tsl.get_power_logging_data()

        trigger_data = array("d", trigger)  # List to Array
        monitor_data = array("d", monitor)  # list to Array

        # Search place of add in
        for item in self.dut_monitor:
            if item.SweepCount != sweep_count:
                continue
            # Add Monitor data for STSProcess Class with STSDataStruct
            logger.info("Adding meas monitor data of: MPM%d Slot%d Ch%d Range%d SweepNo%d",
                        item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.RangeNumber, item.SweepCount)
            errorcode = self._ilsts.Add_Meas_MonitorData(trigger_data, monitor_data, item)
            if errorcode != 0:
                logger.error("Error while getting measurement data of: MPM%d Slot%d Ch%d Range%d SweepNo%d, ",
                             item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.RangeNumber, item.SweepCount,
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

        return errorcode

    def get_dut_data(self) -> None:
        """
        Gets DUT data of the recent STS sweep operation.

        Raises:
            STSProcessError: If getting the dut data fails.
            Exception: If the length wavelength array,
            length of the dut power array, and the dut monitor array are not equal.
        """
        logger.info("STS get dut data")

        # After rescaling is done, get the raw dut data
        for data_struct_item in self.dut_data:
            logger.info("Getting meas raw data of: MPM%d Slot%d Ch%d Range%d SweepNo%d",
                        data_struct_item.MPMNumber, data_struct_item.SlotNumber, data_struct_item.ChannelNumber,
                        data_struct_item.RangeNumber, data_struct_item.SweepCount)
            errorcode, rescaled_dut_pwr, rescaled_dut_mon = self._ilsts.Get_Meas_RawData(data_struct_item, None, None)
            if errorcode != 0:
                logger.error("Error while getting meas raw data of: , MPM%d Slot%d Ch%d Range%d SweepNo%d, ",
                             data_struct_item.MPMNumber, data_struct_item.SlotNumber, data_struct_item.ChannelNumber,
                             data_struct_item.RangeNumber, data_struct_item.SweepCount,
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            logger.info("Getting target wavelength table")
            errorcode, wavelength_array = self._ilsts.Get_Target_Wavelength_Table(None)
            if errorcode != 0:
                logger.error("Error while getting the target wavelength table, ",
                             str(errorcode) + ": " + sts_process_error_strings(errorcode))
                raise STSProcessError(str(errorcode) + ": " + sts_process_error_strings(errorcode))

            if len(wavelength_array) == 0 or len(wavelength_array) != len(rescaled_dut_pwr) or len(
                    wavelength_array) != len(rescaled_dut_mon):
                logger.error(
                    "The length of the wavelength array is {}, the length of the dut power array is {},"
                    " and the length of the dut monitor is {}. They must all be the same length.".format(
                        len(wavelength_array), len(rescaled_dut_pwr), len(rescaled_dut_mon)))
                raise Exception(
                    "The length of the wavelength array is {}, the length of the dut power array is {},"
                    " and the length of the dut monitor is {}. They must all be the same length.".format(
                        len(wavelength_array), len(rescaled_dut_pwr), len(rescaled_dut_mon))
                )

            dut_object = {
                "MPMNumber": data_struct_item.MPMNumber,
                "SlotNumber": data_struct_item.SlotNumber,
                "ChannelNumber": data_struct_item.ChannelNumber,
                "RangeNumber": data_struct_item.RangeNumber,
                "rescaled_wavelength": list(array('d', wavelength_array)),
                "rescaled_dut_monitor": list(array('d', rescaled_dut_mon)),  # rescaled monitor data
                "rescaled_dut_power": list(array('d', rescaled_dut_pwr)),  # rescaled dut power
            }
            self.dut_data_array.append(dut_object)

            logger.info("STS get dut data done.")

    def disconnect_instruments(self) -> None:
        """
        Disconnects the instrument connections.

        Raises:
            Exception: If disconnecting instruments fails.
        """
        logger.info("Disconnect instrument connections.")

        try:
            self._tsl.disconnect()
            self._mpm.disconnect()

        except Exception as e:
            logger.error("Error while disconnecting instruments, %s", e)
            raise Exception("Error while disconnecting instruments, %s", e)

        logger.info("Disconnected instrument connections.")
