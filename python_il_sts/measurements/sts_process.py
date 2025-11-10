"""
STS Process Class.
"""

import time
from array import array
from dataclasses import dataclass

from ..instruments.daq_instrument import DaqInstrument
from ..instruments.mpm_instrument import MpmInstrument
from ..instruments.tsl_instrument import TslInstrument
from ..utils.error_handling import STSProcessError, sts_process_error_strings
from ..drivers.santec_wrapper import (ILSTS, PDLSTS, RescalingMode, STSDataStruct,
                                      STSDataStructForMerge, ModuleType)

# Import program logger
from ..logger import get_logger


@dataclass
class STSData:
    """
    STS Process data.
    """
    scan_speed: float
    tsl_actual_step: float

    mpm_wait_time: int
    mpm_modules: dict

    wavelength_table = []

    ref_data = []
    ref_monitor = []
    dut_data = []
    dut_monitor = []
    ref_data_array = []
    dut_data_array = []
    merge_data = []

    log_data = []
    il = []
    il_data = []
    il_data_array = []

    dynamic_range = []
    selected_ranges = []
    all_modules = []
    selected_channels = []

    mpm_220_high_spec_module_info: tuple[int, int] = None

    use_mpm_216: bool = False
    use_ref_mpm_220: bool = False
    use_power_monitor_logg: bool = False


class StsProcess(STSData):
    """
    STS processing class to set scan parameters,
    perform scan operations and get scan operation data.
    """
    def __init__(self,
                 tsl: TslInstrument,
                 mpm: MpmInstrument,
                 daq: DaqInstrument | None = None,
                 high_spec_mode: bool = False):
        self._tsl = tsl
        self._mpm = mpm
        self._daq = daq
        self._ilsts = PDLSTS()

        if "220" in self._mpm.product_name:
            if high_spec_mode:
                self.use_ref_mpm_220 = True
            else:
                self.use_power_monitor_logg = True
        elif "210" in self._mpm.product_name:
            if not self._daq:
                raise RuntimeError("❌ DAQ device not set. Please initialize with the DAQ instance.")

        self.logger = get_logger(__class__.__name__)
        self.logger.info(f"TslInstrument: {tsl}, MpmInstrument: {mpm}, DaqDevice: {daq}")

    @property
    def il_sts(self) -> ILSTS:
        """
        Returns:
            ILSTS (Santec) class handle from the StsProcess class attributes.
        """
        return self._ilsts

    # region Private Methods

    def _clear_reference_data(self):
        sts_error = self._ilsts.Clear_Refdata()
        if sts_error != 0:
            self.logger.error("Error while clearing reference data, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

    def _clear_measurement_data(self):
        sts_error = self._ilsts.Clear_Measdata()
        if sts_error != 0:
            self.logger.error("Error while clearing measurement data, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

    def _clear_sts_data_struct(self) -> None:
        """ Clears all the sts data struct lists. """
        self.dynamic_range.clear()
        self.ref_data.clear()
        self.ref_monitor.clear()
        self.dut_data.clear()
        self.dut_monitor.clear()
        self.merge_data.clear()

    def _create_wavelength_table(self, start_wavelength, stop_wavelength, scan_step):
        # Make Wavelength table at sweep
        sts_error = self._ilsts.Make_Sweep_Wavelength_Table(start_wavelength,
                                                            stop_wavelength,
                                                            self.tsl_actual_step)

        if sts_error != 0:
            self.logger.error("Error while making wavelength table at scan, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

        # Make wavelength table as rescaling
        sts_error = self._ilsts.Make_Target_Wavelength_Table(start_wavelength,
                                                             stop_wavelength,
                                                             scan_step)

        if sts_error != 0:
            self.logger.error("Error while making wavelength table as rescaling, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

    def _set_sts_data_struct(self) -> None:
        """ Create the data structures, which includes the potentially savable reference data. """
        self.logger.info("Setting STS data struct")
        self._clear_sts_data_struct()  # Clears all the sts data struct lists.
        counter = 1

        # Configure STS data struct for each measurement
        self.logger.info("Configure STS data struct for each measurement")
        for m_range in self.selected_ranges:
            for ch in self.selected_channels:
                data_st = STSDataStruct()
                data_st.MPMNumber = 0
                data_st.SlotNumber = int(ch[0])  # slot number
                data_st.ChannelNumber = int(ch[1])  # channel number
                data_st.RangeNumber = m_range  # array of MPM ranges
                data_st.SweepCount = counter
                data_st.SOP = 0
                self.dut_data.append(data_st)

                range_index = self.selected_ranges.index(m_range)
                channel_index = self.selected_channels.index(ch)

                # measurement monitor data need only 1 channel for each dynamic_range.
                if channel_index == 0:
                    self.dut_monitor.append(data_st)
                    self.dynamic_range.append(m_range)

                # reference data need only 1 dynamic_range for each ch
                if range_index == 0:
                    self.ref_data.append(data_st)
                    self.ref_monitor.append(data_st)
            counter += 1

        # Configure STS data struct for merge
        self.logger.info("Configure STS data struct for merge")
        for ch in self.selected_channels:
            merge_sts = STSDataStructForMerge()
            merge_sts.MPMnumber = 0
            merge_sts.SlotNumber = int(ch[0])  # slot number
            merge_sts.ChannelNumber = int(ch[1])  # channel number
            merge_sts.SOP = 0
            self.merge_data.append(merge_sts)

    def _rescaling_settings(self):
        if self._daq:
            sts_error = self._ilsts.Set_Rescaling_Setting(RescalingMode.Freerun_SPU,
                                                          self._mpm.get_averaging_time(),
                                                          True)
        else:
            sts_error = self._ilsts.Set_Rescaling_Setting(RescalingMode.Freerun_TSLMonitor,
                                                          self._mpm.get_averaging_time(),
                                                          True)

        if sts_error != 0:
            self.logger.error("Error while rescaling setting, ",
                         str(sts_error) + ": " + sts_process_error_strings(sts_error))
            raise STSProcessError(str(sts_error) + ": " + sts_process_error_strings(sts_error))

    def _base_scan_process(self, scan_index: str = "") -> None:
        """
        Configures TSL & MPM (& DAQ) to perform a scan process.

        Parameters:
            scan_index(str): Current scanning index. Example: Range 1

        Raises:
            RuntimeError: If TSL/MPM and Daq instruments are not synchronized, TSL or MPM times out.
            Exception: If there is an issue with TSL scan process.
        """
        self.logger.info("STS scan proces")

        print(f"\n{scan_index}Scanning Process....")

        # Start the TSL scan proces
        self._tsl.start_scan()

        # Start the MPM logging
        self._mpm.logging_start()

        try:
            # Wait until the TSL is set to "Waiting for trigger" status
            self._tsl.wait_for_scan_status(waiting_time=3000, scan_status=4)

            # Start DAQ sampling
            if self._daq:
                self._daq.sampling_start()

            # Issue the TSL soft trigger
            self._tsl.soft_trigger()

            # DAQ wait for for scan completion
            if self._daq:
                self._daq.sampling_wait()

            # Wait until the TSL is set to "Standby" status
            self._tsl.wait_for_scan_status(waiting_time=self.mpm_wait_time, scan_status=1)

            # Wait for MPM log completion
            self._mpm.wait_for_log_completion()

            # Stop the MPM logging
            self._mpm.logging_stop(True)

            # Wait until the TSL is set to "Standby" status
            self._tsl.wait_for_scan_status(waiting_time=3000, scan_status=1)

            # Start the TSL scan
            self._tsl.start_scan()

        except RuntimeError as scan_exception:
            self._tsl.stop_scan(False)
            self._mpm.logging_stop(False)
            self.logger.error(scan_exception)
            raise scan_exception

        except Exception as tsl_exception:
            self._mpm.logging_stop(False)
            self.logger.error(tsl_exception)
            raise tsl_exception

        print("\n....Scan Completed")

        self.logger.info("STS base scan process done.")

        return None

    def _get_mpm_220_data(self):
        # Get the trigger data from the MPM slot
        trigger = self._mpm.get_trigger_data(self.mpm_220_high_spec_module_info[0])

        # Get the monitor data from the MPM ref channel
        monitor = self._mpm.get_each_channel_log_data(self.mpm_220_high_spec_module_info[0],
                                                      self.mpm_220_high_spec_module_info[1])
        return trigger, monitor

    def _get_reference_data(self, data_struct_item: STSDataStruct) -> None:
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
        self.logger.info("Get reference data")
        # Get MPM logging data
        log_data = self._mpm.get_each_channel_log_data(data_struct_item.SlotNumber, data_struct_item.ChannelNumber)

        # Add MPM Logging data for STS Process Class
        self.log_data = array('d', log_data)  # List to Array
        self.logger.info(
            f"Reference log details: MPMNumber={data_struct_item.MPMNumber}, SlotNumber={data_struct_item.SlotNumber}, "
            f"ChannelNumber={data_struct_item.ChannelNumber}, RangeNumber={data_struct_item.RangeNumber}, "
            f"Log data length={len(log_data)}")

        self.logger.info("Adding ref mpm channel data.")
        error_code = self._ilsts.Add_Ref_MPMData_CH(log_data, data_struct_item)
        if error_code != 0:
            self.logger.info("Error while getting ref data, ",
                        str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        # Get trigger and monitor data
        trigger = []
        monitor = []
        if self._daq:
            trigger, monitor = self._daq.get_sampling_raw_data()
        elif self.use_ref_mpm_220:
            trigger, monitor = self._get_mpm_220_data()
        elif self.use_power_monitor_logg:
            # Get the trigger data from the MPM
            trigger = self._mpm.get_trigger_data(data_struct_item.SlotNumber)

            # Get the monitor data from the TSL
            monitor = self._tsl.get_power_logging_data(self.scan_speed, self.tsl_actual_step)

        trigger_data = array("d", trigger)  # List to Array
        monitor_data = array("d", monitor)  # list to Array

        # Add Monitor data for STS Process Class
        self.logger.info("Adding ref monitor data.")
        error_code = self._ilsts.Add_Ref_MonitorData(trigger_data, monitor_data, data_struct_item)
        if error_code != 0:
            self.logger.info("Error while getting ref data, ",
                        str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        # Rescaling for reference data.
        # We must rescale before we get the reference data.
        # Otherwise, we end up with way too many monitor and logging points.
        self.logger.info("Calling ref data for rescaling.")
        error_code = self._ilsts.Cal_RefData_Rescaling()
        if error_code != 0:
            self.logger.info("Error while getting ref data, ",
                        str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        # After rescaling is done, get the raw reference data.
        self.logger.info("Getting ref raw data.")
        error_code, rescaled_ref_pwr, rescaled_ref_mon = self._ilsts.Get_Ref_RawData(data_struct_item, None, None)
        self.logger.info(f"Rescaled ref raw power: {len(rescaled_ref_pwr)}, "
                    f"Rescaled red monitor: {len(rescaled_ref_mon)}")

        if error_code != 0:
            self.logger.info("Error while getting ref data, ",
                        str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        self.logger.info("Getting target wavelength table.")
        error_code, wavelength_array = self._ilsts.Get_Target_Wavelength_Table(None)
        self.logger.info(f"Wavelength table length: {len(wavelength_array)}")
        if error_code != 0:
            self.logger.info("Error while getting ref data, ",
                        str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        if (len(wavelength_array) == 0 or len(wavelength_array) != len(rescaled_ref_pwr) or len(wavelength_array)
                != len(rescaled_ref_mon)):
            self.logger.info(
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
            "rescaled_wavelength": list(array('d', wavelength_array)),
            "rescaled_monitor": list(array('d', rescaled_ref_mon)),  # rescaled monitor data
            "rescaled_reference_power": list(array('d', rescaled_ref_pwr)),  # rescaled reference power
        }
        self.ref_data_array.append(ref_object)

        return None

    def _get_measurement_data(self, scan_count: int) -> int:
        """
        Gets logged data during DUT measurement.

        Parameters:
            scan count (int): The number of scan process operations.

        Raises:
            Exception: If power monitor/MPM data couldn't be added to the data structure.
            STSProcessError: If getting the measurement data fails.
        """
        self.logger.info("STS get measurement data")

        error_code = 0
        for item in self.dut_data:
            if item.SweepCount != scan_count:
                continue

            # Get MPM logging data
            log_data = self._mpm.get_each_channel_log_data(item.SlotNumber, item.ChannelNumber)
            log_data = array("d", log_data)  # List to Array
            self.logger.info(f"Measurement log details: MPMNumber={item.MPMNumber}, SlotNumber={item.SlotNumber}"
                        f"ChannelNumber={item.ChannelNumber}, RangeNumber={item.RangeNumber},"
                        f"Log data length={len(log_data)}")

            # Add MPM Logging data for STSProcess Class with STSDatastruct
            self.logger.info("Adding meas mpm channel data")
            error_code = self._ilsts.Add_Meas_MPMData_CH(log_data, item)
            if error_code != 0:
                self.logger.error("Error while getting measurement data, ",
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        # Get trigger and monitor data
        trigger = []
        monitor = []
        if self._daq:
            trigger, monitor = self._daq.get_sampling_raw_data()
        elif self.use_ref_mpm_220:
            trigger, monitor = self._get_mpm_220_data()
        elif self.use_power_monitor_logg:
            # Get the trigger data from the MPM slot number 0.
            trigger = self._mpm.get_trigger_data(0)

            # Get the monitor data from the TSL.
            monitor = self._tsl.get_power_logging_data(self.scan_speed, self.tsl_actual_step)

        trigger_data = array("d", trigger)  # List to Array
        monitor_data = array("d", monitor)  # list to Array

        # Search place of add in
        for item in self.dut_monitor:
            if item.SweepCount != scan_count:
                continue
            # Add Monitor data for STSProcess Class with STSDataStruct
            self.logger.info("Adding meas monitor data of: MPM%d Slot%d Ch%d Range%d SweepNo%d",
                        item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.RangeNumber, item.SweepCount)
            error_code = self._ilsts.Add_Meas_MonitorData(trigger_data, monitor_data, item)
            if error_code != 0:
                self.logger.error("Error while getting measurement data of: MPM%d Slot%d Ch%d Range%d SweepNo%d, ",
                             item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.RangeNumber, item.SweepCount,
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        return error_code

    def _call_measurement_data_for_rescaling(self):
        self.logger.info("Calling meas data for rescaling of mpm_range: ")
        error_code = self._ilsts.Cal_MeasData_Rescaling()
        if error_code != 0:
            self.logger.error("Error while performing DUT measurement, ",
                         str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

    def _call_il_data_for_merge(self):
        self.logger.info("Calling IL merge")
        error_code = self._ilsts.Cal_IL_Merge(ModuleType.MPM_211)  # Range data merge
        if error_code != 0:
            self.logger.error("Error while performing DUT measurement, ",
                         str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

    def _get_il_data(self):
        # This portion of the code just to get wavelength
        # and IL data at the end of the scan
        self.wavelength_table = []
        self.il_data = []
        self.il_data_array = []

        # Get rescaling wavelength table
        for wav in list(self._ilsts.Get_Target_Wavelength_Table(None)[1]):
            self.wavelength_table.append(wav)

        # Pull out IL data of after merge
        for item in self.merge_data:
            self.logger.info("Getting IL merge data of: MPM%d Slot%d Ch%d SOP%d",
                        item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.SOP)
            error_code, self.il_data = self._ilsts.Get_IL_Merge_Data(None, item)
            if error_code != 0:
                self.logger.error("Error while performing DUT measurement of: MPM%d Slot%d Ch%d SOP%d, ",
                             item.MPMNumber, item.SlotNumber, item.ChannelNumber, item.SOP,
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

            self.il_data = array("d", self.il_data)  # List to Array
            self.il_data_array.append(self.il_data)
        self.il = []
        for i in self.il_data_array[0]:
            self.il.append(i)

    def _set_tsl_parameters(self, start_wavelength, stop_wavelength, scan_step,
                       power, scan_speed):
        self._tsl.set_power(power)

        average_wavelength = (start_wavelength + stop_wavelength) / 2
        self._tsl.set_wavelength(average_wavelength)

        self.scan_speed = scan_speed
        self.tsl_actual_step = self._tsl.set_scan_parameters(start_wavelength, stop_wavelength, scan_step, scan_speed)

    def _set_mpm_parameters(self, start_wavelength, stop_wavelength, scan_step, scan_speed):
        actual_step = 0.0
        if not self._daq:
            actual_step = self.tsl_actual_step

        self._mpm.set_logging_parameters(start_wavelength,
                                         stop_wavelength,
                                         scan_step,
                                         scan_speed,
                                         actual_step)

    def _set_daq_parameters(self, start_wavelength, stop_wavelength, scan_speed):
        if self._daq:
            self._daq.set_logging_parameters(start_wavelength,
                                             stop_wavelength,
                                             scan_speed,
                                             self.tsl_actual_step)

            # Set the DAQ averaging time.
            self._daq.AveragingTime = self._mpm.get_averaging_time()

    def _clear_scan_data(self):
        # Reference data Clear
        self._clear_reference_data()

        # Clear measurement data
        self._clear_measurement_data()

    def _set_reference_dynamic_range(self, slot_no, channel_no):
        # Set MPM dynamic range mode to AUTO
        self._mpm.set_read_range_mode()

        time.sleep(0.1)  # Add sleep time for 100ms

        # Get the MPM channel number power
        power = self._mpm.get_read_power_channel(slot_no, channel_no)

        # Get the dynamic range based on the channel power.
        reference_range = self._get_reference_range(power)

        # Set the reference dynamic range value.
        self._mpm.set_channel_range(slot_no, channel_no, reference_range)

    @staticmethod
    def _get_reference_range(power: float):
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

    # endregion

    def set_scan_parameters(self, start_wavelength, stop_wavelength, scan_step, power, scan_speed,
                            selected_channels, selected_ranges, mpm_220_ref_module_info = None):

        is_valid, errors = self._tsl.validate_scan_parameters(start_wavelength, stop_wavelength,
                                                                 scan_step, power, scan_speed)
        if not is_valid:
            raise Exception(errors)

        is_valid, errors = self._mpm.validate_selected_channels_ranges(selected_channels,
                                                                       selected_ranges,
                                                                       mpm_220_ref_module_info)
        if not is_valid:
            raise Exception(errors)

        scan_step = scan_step / 1000

        self._set_tsl_parameters(start_wavelength, stop_wavelength, scan_step,
                                 power, scan_speed)
        self._set_mpm_parameters(start_wavelength, stop_wavelength, scan_step, scan_speed)
        self._set_daq_parameters(start_wavelength, stop_wavelength, scan_speed)

        self.mpm_220_high_spec_module_info = mpm_220_ref_module_info

        # Calculate the mpm wait time
        self.mpm_wait_time = int((stop_wavelength - start_wavelength) / scan_speed * 1100)
        if self.mpm_wait_time < 5000:
            self.mpm_wait_time = 5000

        self.selected_channels = selected_channels
        self.selected_ranges = selected_ranges

        self._clear_scan_data()

        # Add sleep time for 100ms
        time.sleep(0.1)

        # Create scan wavelength table
        self._create_wavelength_table(start_wavelength, stop_wavelength, scan_step)

        # Create the IL STS data structure
        self._set_sts_data_struct()

        # Set Rescaling mode for STSProcess class
        self._rescaling_settings()

    def reference_scan(self):
        self.logger.info("Reference operation...")

        for i in self.ref_data:
            input("\nPerforming reference scan on slot {} channel {}...Press ENTER to start"
                  .format(i.SlotNumber + 1, i.ChannelNumber))
            self.logger.info("STS reference of Slot{} Ch{}".format(i.SlotNumber + 1, i.ChannelNumber))

            # Set the MPM optimal dynamic range.
            self._set_reference_dynamic_range(i.SlotNumber, i.ChannelNumber)

            # Base scan process
            self._base_scan_process()

            # Get sampling data & Add in STSProcess Class
            self._get_reference_data(i)

            # TSL scan stop
            self._tsl.stop_scan()

            time.sleep(0.5)
        self.logger.info("Reference completed.")

    def measurement_scan(self):
        self.logger.info("Measurement operation...")

        scan_count = 1
        for mpm_range in self.dynamic_range:
            # Set the MPM dynamic dynamic_range
            self._mpm.set_range(mpm_range)

            # Base scan process
            self._base_scan_process(f"Range {mpm_range} ")

            # Get the measurement scan data
            _ = self._get_measurement_data(scan_count)

            scan_count += 1

        # Call the measurement data for rescaling
        self._call_measurement_data_for_rescaling()

        # Call the IL merge data
        self._call_il_data_for_merge()

        # TSL scan stop
        self._tsl.stop_scan()

        # Get the IL data
        self._get_il_data()

        self.logger.info("Measurement completed.")

    def get_channel_range_selection(self):
        channel_selection = self.selected_channels
        dynamic_range_selection = self.selected_ranges
        mpm_220_reference_channel = self.mpm_220_high_spec_module_info

        return {
            "channel_selection": channel_selection,
            "dynamic_range_selection": dynamic_range_selection,
            "mpm_220_reference_channel": mpm_220_reference_channel
        }

    def disconnect_instruments(self):
        self._tsl.disconnect()
        self._mpm.disconnect()
        self._daq.disconnect()
        self.logger.info("Disconnected instruments.")

    def load_reference_scan_data(self, reference_scan_data) -> None:
        """
        Loading reference data from saved file.

        Raises:
            Exception: If the reference data array is null or empty.
            STSProcessError: If loading the reference data fails.
        """
        self.logger.info("Loading STS reference from data file.")
        self.ref_data_array = reference_scan_data
        if self.ref_data_array is None or len(self.ref_data_array) == 0:
            self.logger.error("The reference data array cannot be null or empty when loading reference data from files.")
            raise Exception(
                "\nThe reference data array cannot be null or empty when loading reference data from files.")

        if len(self.ref_data_array) != len(self.ref_data):
            self.logger.error(
                "The length is different between the saved reference array and the newly-obtained reference array.")
            raise Exception(
                "The length is different between the saved reference array and the newly-obtained reference array.")

        matched_data_structure = None

        for cached_ref_object in self.ref_data_array:
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

            self.logger.info("Adding ref mpm channel data")
            error_code = self._ilsts.Add_Ref_MPMData_CH(cached_ref_object["log_data"], matched_data_structure)
            if error_code != 0:
                self.logger.error("Error while loading ref data, ",
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

            self.logger.info("Adding ref monitor data")
            error_code = self._ilsts.Add_Ref_MonitorData(cached_ref_object["trigger"], cached_ref_object["monitor"],
                                                        matched_data_structure)
            if error_code != 0:
                self.logger.error("Error while loading ref data, ",
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

            self.logger.info("Calling ref data for rescaling")
            error_code = self._ilsts.Cal_RefData_Rescaling()  # Rescaling for reference data.
            if error_code != 0:
                self.logger.error("Error while loading ref data, ",
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

    def get_dut_data(self) -> None:
        """
        Gets DUT data of the recent STS scan operation.

        Raises:
            STSProcessError: If getting the dut data fails.
            Exception: If the length wavelength array,
            length of the dut power array, and the dut monitor array are not equal.
        """
        self.logger.info("STS get dut data")

        # After rescaling is done, get the raw dut data
        for data_struct_item in self.dut_data:
            self.logger.info("Getting meas raw data of: MPM%d Slot%d Ch%d Range%d SweepNo%d",
                        data_struct_item.MPMNumber, data_struct_item.SlotNumber, data_struct_item.ChannelNumber,
                        data_struct_item.RangeNumber, data_struct_item.SweepCount)
            error_code, rescaled_dut_pwr, rescaled_dut_mon = self._ilsts.Get_Meas_RawData(data_struct_item, None, None)
            if error_code != 0:
                self.logger.error("Error while getting meas raw data of: , MPM%d Slot%d Ch%d Range%d SweepNo%d, ",
                             data_struct_item.MPMNumber, data_struct_item.SlotNumber, data_struct_item.ChannelNumber,
                             data_struct_item.RangeNumber, data_struct_item.SweepCount,
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

            self.logger.info("Getting target wavelength table")
            error_code, wavelength_array = self._ilsts.Get_Target_Wavelength_Table(None)
            if error_code != 0:
                self.logger.error("Error while getting the target wavelength table, ",
                             str(error_code) + ": " + sts_process_error_strings(error_code))
                raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

            if len(wavelength_array) == 0 or len(wavelength_array) != len(rescaled_dut_pwr) or len(
                    wavelength_array) != len(rescaled_dut_mon):
                self.logger.error(
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

            self.logger.info("STS get dut data done.")

    def get_wavelength_table(self, data_struct_item: STSDataStruct, trigger_length: int) -> None:
        """
        Gets the list of wavelengths from the most recent scan.

        Parameters:
            data_struct_item (STSDataStruct): Contains all information of tested module/channel.
            trigger_length (int): Length of a TSL trigger.

        Raises:
            Exception: If the length of wavelength array and trigger array are different.
            STSProcessError: If getting the target wavelength fails.
        """
        self.logger.info("STS get wavelength table")
        datapoint_count = 0
        wavelength_array = []

        # Rescaling for reference data
        self.logger.info("Calling ref data for rescaling")
        error_code = self._ilsts.Cal_RefData_Rescaling()
        if error_code != 0:
            self.logger.error("Error while getting the target wavelength, ",
                         str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        error_code, ref_pwr, ref_mon = self._ilsts.Get_Ref_RawData(data_struct_item, None, None)  # testing 2...
        self.logger.info("Getting target wavelength table")
        error_code, wavelength_table = self._ilsts.Get_Target_Wavelength_Table(None)
        self.logger.info("Received wavelength table length: %d", len(wavelength_table))
        # error_code,wavelength_table = self._ilsts.Get_Target_Wavelength_Table(wavelength_array)   # TODO; testing.....
        if error_code != 0:
            self.logger.error("Error while getting the target wavelength, ",
                         str(error_code) + ": " + sts_process_error_strings(error_code))
            raise STSProcessError(str(error_code) + ": " + sts_process_error_strings(error_code))

        if len(wavelength_table) != trigger_length:
            self.logger.error("The length of the wavelength array is {} but the length of the trigger array is {}. "
                         "They should have been the same. ".format(len(wavelength_table), trigger_length))
            raise Exception(
                "The length of the wavelength array is {} but the length of the trigger array is {}. "
                "They should have been the same. ".format(len(wavelength_table), trigger_length))
        self.logger.info("Wavelength table length: %d", len(wavelength_table))
        return wavelength_table