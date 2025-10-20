"""
DAQ Instrument.
"""

# Import DAQ class from the Santec DLL
from ..drivers.santec_wrapper import DAQ

# Importing instrument error strings
from ..utils import InstrumentError, instrument_error_strings

from .base_instrument import BaseInstrument

# Import program logger
from ..logger import get_logger


class DaqInstrument(BaseInstrument):
    """
    DAQ instrument class to control and command the DAQ device.
    """
    def __init__(self):
        super().__init__()
        self.logger = get_logger(__class__.__name__)
        self._instrument = DAQ()

    def set_logging_parameters(self,
                               start_wavelength: float,
                               stop_wavelength: float,
                               scan_speed: float,
                               tsl_actual_step: float) -> None:
        """
        Set DAQ logging parameters for DAQ sampling.

        Parameters:
            start_wavelength (float): Start wavelength value of the scan.
            stop_wavelength (float): Stop wavelength value of the scan.
            scan_speed (float): Speed value of the scan.
            tsl_actual_step (float): Step wavelength value of the scan.

        Raises:
            InstrumentError: If setting the logging parameters to the DAQ device fails.
        """
        self.logger.info(f"Set DAQ logging params: start_wavelength={start_wavelength}, stop_wavelength={stop_wavelength}, "
                    f"scan_speed={scan_speed}, tsl_actual_step={tsl_actual_step}")
        error_code = self._instrument.Set_Sampling_Parameter(start_wavelength,
                                                            stop_wavelength,
                                                            scan_speed,
                                                            tsl_actual_step)

        if error_code != 0:
            self.logger.error("Error while setting DAQ logging params, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"DAQ logging params set.")

    def sampling_start(self) -> None:
        """ Starts the DAQ sampling """
        self.logger.info("DAQ sampling start")
        error_code = self._instrument.Sampling_Start()
        if error_code != 0:
            self.logger.error("Error while DAQ sampling start, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("DAQ sampling started.")

    def sampling_wait(self) -> None:
        """ DAQ wait for sampling """
        self.logger.info("DAQ sampling wait")
        error_code = self._instrument.Waiting_for_sampling()
        if error_code != 0:
            self.logger.error("Error while DAQ sampling wait, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("DAQ sampling wait done.")

    def get_sampling_raw_data(self) -> tuple[list[float], list[float]]:
        """
        Gets the raw sampling data from the DAQ device.

        Raises:
            InstrumentError: If getting the raw sampling data from the DAQ device fails.

        Returns:
            tuple[list[float], list[float]]: A tuple containing two lists:
                - The first list contains the TSL trigger data of a float type.
                - The second list contains the power monitor data of a float type.
        """
        self.logger.info("DAQ get sampling raw data")
        error_code, trigger, monitor = self._instrument.Get_Sampling_Rawdata(
            None, None)
        if error_code != 0:
            self.logger.error("Error while getting DAQ sampling raw data, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"DAQ sampling raw data acquired, data length: trigger={len(trigger)}, monitor={len(monitor)}")
        return trigger, monitor
