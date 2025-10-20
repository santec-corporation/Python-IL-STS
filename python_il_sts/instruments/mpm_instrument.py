"""
MPM Instrument Class.
"""

from ..drivers.santec_wrapper import MPM
from .base_instrument import BaseInstrument

# Importing instrument error strings
from ..utils.error_handling_class import InstrumentError, instrument_error_strings

# Import program logger
from ..logger import get_logger


class ModuleData:
    """
    A class to represent the module information of an MPM.

    Attributes:
        module_number (int): The MPM module number.
        module_type (str | None): The MPM module type.
        channels (list): The list of channels of an MPM module.
    """
    module_number: int
    module_type: str | None
    channels: list = []

    def __init__(self, module_number: int,
                 module_type: str | None,
                 channels: list):
        self.module_number = module_number
        self.module_type = module_type
        self.channels = channels


class MpmData:
    """
    A class to represent the data for an MPM.

    Attributes:
        averaging_time (float): The averaging time of the MPM.
        range_data (list): The list of dynamic_range count values of an MPM module.
        modules (list): The list of modules of an MPM.
    """
    averaging_time: float = 0.0
    range_data: list = []
    modules: list = []
    dynamic_ranges = [
        '-30 ~ +10dBm',
        '-40 ~ 0dBm',
        '-50 ~ -10dBm',
        '-60 ~ -20dBm',
        '-80 ~ -30dBm'
    ]


class MpmInstrument(MpmData, BaseInstrument):
    """
    A class to represent the data for an MPM.
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__class__.__name__)
        self._instrument = MPM()

    def get_modules(self) -> list:
        """
        Detects all the modules that are mounted on the MPM (looping on the five possible slots).
        If the detected module is an MPM-212, then the possible optical channels are numbered 1 and 2
        Else, then the possible optical channels are numbered from 1 to 4.
        If no module is detected, then the method assigns an empty list.

        Raises:
            Exception: In case no modules were detected on the MPM.

        Returns:
            list: A list of the MPM modules.
        """
        self.logger.info("Get the MPM modules")

        for slot_count in range(5):
            module_info = self._instrument.Information.ModuleType[slot_count]
            if self._instrument.Information.ModuleEnable[slot_count] is True:
                if self.check_mpm_212(slot_count):
                    self.modules.append(ModuleData(slot_count, "MPM-212", [1, 2]))
                else:
                    self.modules.append(ModuleData(slot_count, module_info, [1, 2, 3, 4]))
            else:
                self.modules.append(ModuleData(slot_count, None, []))
        if len(self.modules) == 0:
            self.logger.warning("No MPM modules were detected.")
            raise Exception("No modules were detected.")
        self.logger.info(f"Detected MPM modules: {self.modules}")
        return self.modules

    def check_module_type(self) -> tuple[bool, bool]:
        """
        Checks the type of modules that are mounted to the MPM.
        This method calls check_mpm_215 and check_mpm_213 methods.

        Raises:
            Exception: MPM-215 can't be used with other MPM modules.

        Returns:
            tuple[bool, bool]: True, True if the MPM-215 and MPM-213 modules are detected.
        """
        self.logger.info("MPM check module type")
        flag_215 = False
        flag_213 = False
        slot = 0
        count_215 = 0

        for slot_count in range(5):
            if self._instrument.Information.ModuleEnable[slot_count] is True:
                flag_215 = self.check_mpm_215(slot_count)
                flag_213 = self.check_mpm_213(slot_count)
                slot += 1
                if flag_215:
                    count_215 += 1

        if flag_215 is True and count_215 != slot:
            self.logger.error("MPM-215 can't use with other modules.")
            raise Exception("MPM-215 can't use with other modules.")
        self.logger.info(f"MPM module type check: flag_215={flag_215}, flag_213={flag_213}")
        return flag_215, flag_213

    def check_mpm_215(self, slot_num: int) -> bool:
        """
        Checks if the mounted module at the given slot number is an MPM-215 module.

        Parameters:
            slot_num (int): The module number (0~4) of the MPM.

        Returns:
            bool: True if an MPM-215 is detected.
        """
        self.logger.info("MPM check if module 215")
        check = bool(self._instrument.Information.ModuleType[slot_num] == "MPM-215")
        self.logger.info(f"MPM module 215: {check}")
        return check

    def check_mpm_213(self, slot_number: int) -> bool:
        """
        Checks if the mounted module at the given slot number is an MPM-213 module.

        Parameters:
            slot_number (int): The module number (0~4) of the MPM.

        Returns:
            bool: True if an MPM-213 is detected.
        """
        self.logger.info("MPM check if module 213")
        check = bool(self._instrument.Information.ModuleType[slot_number] == "MPM-213")
        self.logger.info(f"MPM module 213: {check}")
        return check

    def check_mpm_212(self, slot_number: int) -> bool:
        """
        Checks if the mounted module at the given slot number is an MPM-212 module.

        Parameters:
            slot_number (int): The module number (0~4) of the MPM.

        Returns:
            bool: True if an MPM-212 is detected.
        """
        self.logger.info("MPM check if module 212")
        check = bool(self._instrument.Information.ModuleType[slot_number] == "MPM-212")
        self.logger.info(f"MPM module 212: {check}")
        return check

    def get_range(self) -> None:
        """
        Gets the measurement dynamic dynamic_range of the MPM module.
        Depending on the module type, the dynamic dynamic_range varies.

        The method appends the dynamic_range values to range_data attribute of the class.

        Example:
                list: if MPM-215: [1],
                    if module MPM-213: [1,2,3,4],
                    if other modules: [1,2,3,4,5]
        """
        self.logger.info("MPM get dynamic ranges of modules")
        self.range_data = []
        if self.check_mpm_215:
            self.range_data = [1]
        elif self.check_mpm_213:
            # 213 have 4 ranges
            self.range_data = [1, 2, 3, 4]
        else:
            self.range_data = [1, 2, 3, 4, 5]
        self.logger.info(f"MPM dynamic_range data: {self.range_data}")

    def set_range(self, power_range: int) -> None:
        """
        Sets the dynamic dynamic_range value of the MPM.

        Args:
            power_range (int): The dynamic dynamic_range value to be set.

        **Information**
            Check get_range method for available dynamic ranges.

        Raises:
            InstrumentError: In case the MPM is busy,
                            or in case the wrong value for power_range is entered,
                            or if setting MPM dynamic_range fails.
        """
        self.logger.info("MPM set dynamic_range")
        error_code = self._instrument.Set_Range(power_range)

        if error_code != 0:
            self.logger.error("Error while setting MPM dynamic_range, ", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("MPM dynamic_range set.")

    def set_channel_range(self, slot_number: int, channel_number: int, range_value: int) -> None:
        """
        Sets the dynamic dynamic_range value of the MPM channel.
        """
        self.logger.info("MPM set channel dynamic_range")
        error_code = self._instrument.Set_Range_Each_Channel(slot_number, channel_number, range_value)

        if error_code != 0:
            self.logger.error("Error while setting MPM channel dynamic_range, ", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM channel dynamic_range set to {range_value}.")

    def set_read_range_mode(self, mode: str = "AUTO") -> None:
        """
        Sets the dynamic dynamic_range mode of the MPM.
        """
        self.logger.info("MPM set dynamic_range mode.")
        if mode == "AUTO":
            error_code = self._instrument.Set_READ_Range_Mode(MPM.READ_Range_Mode.Auto)
        else:
            return

        if error_code != 0:
            self.logger.error("Error while setting MPM dynamic_range mode, ", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM dynamic_range mode set to {mode}.")

    def get_read_power_channel(self, slot_number: int, channel_number: int) -> float:
        """ Gets the read power of a channel."""
        self.logger.info("MPM Get_READ_Power_Channel.")
        error_code, power = self._instrument.Get_READ_Power_Channel(slot_number, channel_number, 0)

        if error_code != 0:
            self.logger.error("Error while Get_READ_Power_Channel, ", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM Get_READ_Power_Channel, power: {power}.")
        return power

    def zeroing(self) -> str | int:
        """
        Performs a Zeroing on all the MPM modules and channels.

        **Note**
            All the channels must be closed with respective back caps before
            performing this operation.

        Raises:
            InstrumentError: In case the MPM is busy,
                        or in case wrong value for power_range is entered,
                        or in case the MPM returns an error,
                        or if performing MPM zeroing fails.

        Returns:
            str: Success.
        """
        self.logger.info("MPM perform zeroing")
        error_code = self._instrument.Zeroing()

        if error_code != 0:
            self.logger.error("Error while performing MPM zeroing, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM zeroing done.")
        return error_code

    def get_averaging_time(self) -> float:
        """
        Gets the averaging time of the MPM.

        Raises:
            InstrumentError: In case the MPM is busy,
                        or if getting the averaging time fails.

        Returns:
            float: Averaging time of the MPM.
        """
        self.logger.info("MPM get averaging time")
        error_code, self.averaging_time = self._instrument.Get_Averaging_Time(0)

        if error_code != 0:
            self.logger.error("Error while getting MPM averaging time, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM averaging time: {self.averaging_time}")
        return self.averaging_time

    def logging_start(self) -> None:
        """
        Starts MPM logging.

        Raises:
            InstrumentError: In case the MPM is busy,
                        or fails to start MPM logging.
        """
        self.logger.info("MPM start logging")
        error_code = self._instrument.Logging_Start()
        if error_code != 0:
            self.logger.error("Error while MPM start logging, ", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("MPM logging started.")

    def logging_stop(self, except_if_error: bool = True) -> None:
        """
        Stops the MPM logging.

        Parameters:
            except_if_error (bool | optional): Set True if raising exception is needed within this method.
            Else, i.e.,
            if this method is inserted within STS then set False
            so the exception will be raised from STS method.
            Default value: True.

        Raises:
            InstrumentError: In case of failure in stopping the MPM logging.
        """
        self.logger.info("MPM stop logging")
        error_code = self._instrument.Logging_Stop()

        if error_code != 0 and except_if_error is True:
            self.logger.error("Error while MPM stop logging, ", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("MPM logging stopped.")

    def get_each_channel_log_data(self,
                                  slot_number: int,
                                  channel_number: int) -> list:
        """
        Gets log data for specified slot and channel number.

        Parameters:
            slot_number (int): Module number (0~4) of the MPM.
            channel_number (int): Channel number (1~4) of the MPM module.

        Raises:
            InstrumentError: In case wrong arguments are passed,
                            or fails to get log data from the MPM.

        Returns:
            list: List of log data.
        """
        self.logger.info(f"MPM get each channel log data, slot_number={slot_number}, channel_number={channel_number}")
        error_code, log_data = self._instrument.Get_Each_Channel_Logdata(slot_number, channel_number, None)
        if error_code != 0:
            self.logger.error("Error while getting channel log data, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM slot {slot_number} channel {channel_number}, log data length: {len(list(log_data))}")
        return list(log_data)

    def get_trigger_data(self, slot_number) -> list[float]:
        """
        Gets the MPM trigger data.

        Raises:
            InstrumentError: In case the MPM is busy,
                        or if getting the averaging time fails.

        Returns:
            list[float]: List of trigger values.
        """
        self.logger.info("MPM get 216 trigger data.")
        error_code, trigger = self._instrument.Get_216_Triggerdata(slot_number, None)
        if error_code != 0:
            self.logger.error("Error while getting MPM trigger data, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM trigger data length: {len(trigger)}")
        return trigger

    def set_logging_parameters(self,
                               start_wavelength: float,
                               stop_wavelength: float,
                               scan_step: float,
                               scan_speed: float,
                               trigger_step: float = 0.0) -> None:
        """
        Sets the logging parameter of the MPM instrument.

        Parameters:
            start_wavelength (float): The starting wavelength for the scan.
            stop_wavelength (float): The stopping wavelength for the scan.
            scan_step (float): The step wavelength of a scan.
            scan_speed (float): The speed of a scan.
            trigger_step (float): (Not necessary value) The step size (nm) between two TSL triggers.
                                Default value: 0.0

        Raises:
            InstrumentError: If setting the logging parameters to the MPM fails.
        """
        self.logger.info(f"Set MPM logging params: start_wavelength={start_wavelength}, stop_wavelength={stop_wavelength}, "
                    f"scan_step={scan_step}, scan_speed={scan_speed}, trigger_step={trigger_step}")
        error_code = self._instrument.Set_Logging_Paremeter_for_STS(start_wavelength,
                                                             stop_wavelength,
                                                             scan_step,
                                                             trigger_step,
                                                             scan_speed,
                                                             self._instrument.Measurement_Mode.Freerun)

        if error_code != 0:
            self.logger.error("Error while setting MPM logging params",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM logging params set.")

    def wait_for_log_completion(self) -> None:
        """
        Waits for MPM log completion.

        Raises:
            RuntimeError: If the MPM Trigger received an error!
            Please check trigger cable connection.
            InstrumentError: If the wait for MPM log completion fails.
        """
        self.logger.info("MPM wait for log completion")
        error_code = None
        status = 0  # MPM Logging status 0: During logging 1: Completed, -1:stopped, 10:stopped

        logging_point = None
        # Constantly get the status in a loop. Increase the MPM timeout for this process.
        while status == 0:
            # Updates status, which should break us out of the loop.
            error_code, status, logging_point = self._instrument.Get_Logging_Status(0, 0)
            break

        if error_code == -999:
            error_string = "MPM Trigger received an error! Please check trigger cable connection."
            self.logger.critical(error_string)
            raise RuntimeError(error_string)

        if error_code != 0 and status != -1:  # It's a success if either the error code is 0,
            # or the status is -1, otherwise, throw.
            self.logger.error("Error while waiting for MPM log completion, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"MPM logging completed. logging_point={logging_point}")
