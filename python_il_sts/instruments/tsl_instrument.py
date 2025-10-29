"""
TSL Instrument Class.
"""

from ..drivers.santec_wrapper import TSL, ExceptionCode

# Importing instrument error strings
from ..utils.error_handling import InstrumentError, instrument_error_strings
from .base_instrument import BaseInstrument

# Import program logger
from ..logger import get_logger


class TslData:
    """
    A class to represent the data for a TSL.

    Attributes:
        max_power (float): The maximum power output of the TSL.
        spec_max_wav (float): The maximum wavelength of the spectral dynamic_range of the TSL.
        spec_min_wav (float): The minimum wavelength of the spectral dynamic_range of the TSL.
        scan_speed_table (list): A table of TSL scan speeds.
    """
    max_power: float = 0.0
    spec_max_wav: float = 0.0
    spec_min_wav: float = 0.0
    scan_speed_table: list = []


class TslInstrument(TslData, BaseInstrument):
    """
    Class to control and command the TSL instrument.
    """

    def __init__(self):
        super().__init__()
        self.logger = get_logger(__class__.__name__)
        self._instrument = TSL()

    def check_laser_diode_status(self) -> int:
        """
        Checks if the TSL laser diode is switched ON, else throws a RuntimeError.

        Returns:
            int: The error_code of the laser diode status read operation.
                error_code = 0, means read operation successful.
                error_code != 0, means read operation failed.

        Raises:
            InstrumentError: If checking laser diode status fails.
            RuntimeError: If laser diode is not switched ON.
        """
        self.logger.info("Checking laser diode status")
        ld_status = TSL.LD_Status
        status = ld_status.LD_OFF
        error_code, status = self._instrument.Get_LD_Status(status)
        if error_code != 0:
            self.logger.warning("Error while checking TSL ld status",
                           str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        while status != ld_status.LD_ON:
            self.logger.critical("TSL Laser Diode not switched ON.")
            print("\nTSL laser diode not switched ON.")
            print("Please switch ON the laser diode.")
            input("Once the laser diode is switched ON, press Enter...")

            error_code, status = self._instrument.Get_LD_Status(status)     # Get the laser diode status

        self.logger.info("Laser diode ON.")
        return error_code

    def set_laser_diode_status(self, state: str = 'on') -> int:
        """
        Sets the TSL laser diode status.

        Parameters:
            state (str): State of the laser diode, 'on' or 'off'.

        Returns:
            int: The error_code of the laser diode status read operation.
                error_code = 0, means read operation successful.
                error_code != 0, means read operation failed.

        Raises:
            InstrumentError: If setting the laser diode fails.
        """
        self.logger.info("Setting laser diode status to: %s", state)
        ld_status = TSL.LD_Status
        status = ld_status.LD_ON
        if 'off' in state.lower():
            status = ld_status.LD_OFF
        error_code = self._instrument.Set_LD_Status(status)
        if error_code != 0:
            self.logger.warning("Error while setting TSL ld status",
                           str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("Laser diode status set to: %s", state)
        return error_code

    def get_tsl_type_flag(self) -> bool:
        """
        Checks if the connected TSL is of the type:
            TSL-510, TSL-550 or TSL-710.

        Returns:
            bool: True if TSL-510, TSL-550 or TSL-710,
                  else False.
        """
        tsl_name = self.product_name
        self.logger.info(f"TSL name: {tsl_name}")
        return tsl_name in ("TSL-510", "TSL-550", "TSL-710")

    def get_spec_wavelength(self) -> None:
        """
        Gets minimum and maximum wavelengths supported by the connected TSL.

        Raises:
            InstrumentError: In case, could not get the spec min and max wavelengths from the TSL.
        """
        self.logger.info("Get TSL spec wavelength")
        error_code, self.spec_min_wav, self.spec_max_wav = self._instrument.Get_Spec_Wavelength(0, 0)

        self.logger.info(f"TSL spec wavelength: min_wav={self.spec_min_wav}, max_wav={self.spec_max_wav}")
        if error_code != 0:
            self.logger.warning("Error while getting TSL spec wavelength",
                           str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

    def get_scan_speed_table(self) -> list[float]:
        """
        **Note**
            This method works only with a "TSL-570" instrument.

        Returns scan scan_speed table of TSL-570:
        Example: [1,2,5,10,20,50,100,200]
                 All values in nm/sec units.

        Raises:
            InstrumentError: "DeviceError" when other TSL is connected.

        Returns:
            list[float]: Table of scan speeds allowed by the TSL-570.
        """
        self.logger.info("Get TSL speed table")
        error_code, table = self._instrument.Get_Sweep_Speed_table(None)
        self.scan_speed_table = []

        # This function only supports "TSL-570"
        # When other TSL connected, error_code return "DeviceError"
        if error_code == ExceptionCode.DeviceError:
            error_code = 0
        else:
            for item in table:
                self.scan_speed_table.append(item)

        if error_code != 0:
            self.logger.error("Error while getting TSL speed table",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("TSL speed table received.")
        return self.scan_speed_table

    def get_max_power(self) -> None:
        """
        **Note**
            This method works only with a "TSL-570" instrument.

        Returns the maximum output power that can be delivered by the connected TSL.

        Raises:
            InstrumentError: In case TSL doesn't return a value.
        """
        self.logger.info("Get TSL max power.")
        error_code, self.max_power = self._instrument.Get_APC_Limit_for_Sweep(self.spec_min_wav,
                                                                       self.spec_max_wav,
                                                                       0.0)
        if error_code == ExceptionCode.DeviceError:
            self.max_power = 999
            error_code = 0
        self.logger.info(f"TSL max power: {self.max_power}")

        if error_code != 0:
            self.logger.error("Error while getting TSL max power",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

    def get_power_logging_data(self, scan_speed, actual_step: float) -> list[float]:
        """
        Gets the power logging data from the TSL.

        Raises:
            InstrumentError: If getting the power logging data from the TSL fails.

        Returns:
            list[float]: List of power logging data.
        """
        self.logger.info("TSL get power logging data.")
        error_code, log_count, monitor = (
            self._instrument.Get_Logging_Data_Power_for_STS(scan_speed, actual_step, 0, None))
        if error_code not in [0, -2]:
            self.logger.error("Error while getting TSL power logging data, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"TSL power logging data acquired, data length={len(monitor)}")
        return monitor

    def set_power(self, power: float) -> None:
        """
        Sets the output power of the TSL.

        Parameters:
            power (float): The power value for the TSL to be set at.

        Raises:
            InstrumentError: If setting the output power is fails.
            InstrumentError: If the TSL is busy.
        """
        self.logger.info(f"Set TSL power: {power}")
        error_code = self._instrument.Set_APC_Power_dBm(power)

        if error_code != 0:
            self.logger.error(f"Error while setting TSL power", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

        error_code = self._instrument.TSL_Busy_Check(3000)

        if error_code != 0:
            self.logger.error(f"Error while setting TSL power", str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

    def set_wavelength(self, wavelength: float) -> None:
        """
        Sets the TSL at a specific wavelength.

        Parameters:
            wavelength (float): The wavelength value for the TSL to be set at.

        Raises:
            InstrumentError: If setting the wavelength is fails.
            InstrumentError: If the TSL is busy.
        """
        self.logger.info(f"Set TSL wavelength: {wavelength}")
        error_code = self._instrument.Set_Wavelength(wavelength)

        if error_code != 0:
            self.logger.error(f"Error while setting TSL wavelength",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

        error_code = self._instrument.TSL_Busy_Check(3000)

        if error_code != 0:
            self.logger.error(f"Error while setting TSL wavelength",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

    def set_scan_parameters(self,
                             start_wavelength: float,
                             stop_wavelength: float,
                             scan_step: float,
                             scan_speed: float) -> float:
        """
        Sets the TSL scan parameters.

        Parameters:
            start_wavelength (float): The starting wavelength for the scan.
            stop_wavelength (float): The stopping wavelength for the scan.
            scan_step (float): The step wavelength of a scan.
            scan_speed (float): The speed of a scan.

        Raises:
            InstrumentError: If setting the TSL scan parameters fails.
        """
        self.logger.info(f"Set TSL scan params: start_wavelength={start_wavelength}, "
                    f"stop_wavelength={stop_wavelength}, scan_step={scan_step}, scan_speed={scan_speed}")
        self.tsl_busy_check()

        error_code, actual_step = self._instrument.Set_Sweep_Parameter_for_STS(start_wavelength,
                                                                             stop_wavelength,
                                                                             scan_speed,
                                                                             scan_step,
                                                                             0)

        if error_code != 0:
            self.logger.error("Error while setting TSL scan params",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

        self.logger.info(f"TSL scan params set, actual_step={actual_step}")
        self.tsl_busy_check(5000)
        return actual_step

    def soft_trigger(self) -> None:
        """
        Issues a soft trigger to start the TSL scan.

        Raises:
            InstrumentError: In case TSL is not in Standby mode, or if TSL cannot start the scan.
        """
        self.logger.info("Issue soft trigger")
        error_code = self._instrument.Set_Software_Trigger()

        if error_code != 0:
            self.logger.error("Error while setting TSL soft trigger",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("Issue soft trigger done.")

    def start_scan(self) -> None:
        """
        Starts the TSL scan.
        Method to be used when TSL is not connected to STS.

        Raises:
            InstrumentError: In case TSL doesn't start the scan.
        """
        self.logger.info("TSL start scan")
        error_code = self._instrument.Sweep_Start()

        if error_code != 0:
            self.logger.error("Error while starting TSL scan",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("TSL start scan done.")

    def stop_scan(self, except_if_error: bool = True):
        """
        Stops the TSL scan.

        Parameters:
            except_if_error (bool | optional): Set True if raising exception is needed within this method.
            Else, i.e.,
            if this method is inserted within STS then set False
            so the exception will be raised from STS method.
            Default value: True.

        Raises:
            InstrumentError: In case of failure in stopping the TSL scan.
        """
        self.logger.info("TSL stop scan")
        error_code = self._instrument.Sweep_Stop()

        if error_code != 0 and except_if_error is True:
            self.logger.error("Error while stopping TSL scan",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("TSL stop scan done.")

    def tsl_busy_check(self, time_out: int = 3000) -> None:
        """
        Checks if the TSL is busy performing other operations.
        Default timeout = 3000 ms

        Raises:
            InstrumentError: In case, no response from TSL after timeout.
        """
        self.logger.info("TSL busy check")
        error_code = self._instrument.TSL_Busy_Check(time_out)

        if error_code != 0:
            self.logger.error("Error while TSL busy check",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("TSL busy check done.")

    def wait_for_scan_status(self,
                              waiting_time: int,
                              scan_status: int) -> None:
        """
        Wait until the TSL is set to a specified status prior the scanning process.


        Parameters:
            waiting_time (int): Waiting time (milliseconds) before setting a scan status.
            scan_status (int): Set the scan status of the TSL.
                                scan status values:
                                1: Standby
                                2: Running
                                3: Pause
                                4: Waiting for trigger
                                5: Return

        Raises:
            InstrumentError: In case TSL is not set to the specified scan status after timeout.
        """
        self.logger.info("TSL wait for scan status")
        _status = {
            1: self._instrument.Sweep_Status.Standby,
            2: self._instrument.Sweep_Status.Running,
            3: self._instrument.Sweep_Status.Pausing,
            4: self._instrument.Sweep_Status.WaitingforTrigger,
            5: self._instrument.Sweep_Status.Returning
        }
        error_code = self._instrument.Waiting_For_Sweep_Status(waiting_time, _status[scan_status])

        if error_code != 0:
            self.logger.error("Error while TSL wait for scan status",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("TSL wait for scan status done.")
