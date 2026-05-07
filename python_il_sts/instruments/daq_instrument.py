"""
DAQ Instrument.
"""

# Import the DAQ class from the DLL
from ..drivers.santec_wrapper import DAQ

# Import the instrument error strings
from ..utils import InstrumentError, instrument_error_strings

# Import the base instrument class.
from .base_instrument import BaseInstrument

# Import the program logger
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
            start_wavelength (float): Start wavelength (in nm) value of the scan.
            stop_wavelength (float): Stop wavelength (in nm) value of the scan.
            scan_speed (float): The scan speed (in nm/sec) value of the scan.
            tsl_actual_step (float): Step wavelength (in nm) value of the scan.

        Raises:
            InstrumentError: If setting the logging parameters to the DAQ device fails.
        """
        self.logger.info(f"Set DAQ logging params: start_wavelength={start_wavelength},"
                         f"stop_wavelength={stop_wavelength},scan_speed={scan_speed},"
                         f"tsl_actual_step={tsl_actual_step}")
        error_code = self._instrument.Set_Sampling_Parameter(start_wavelength,
                                                            stop_wavelength,
                                                            scan_speed,
                                                            tsl_actual_step)

        if error_code != 0:
            self.logger.error("Error while setting the logging params, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

    def start_sampling(self) -> None:
        """ Starts the DAQ sampling. """
        self.logger.info("Starting the sampling")
        error_code = self._instrument.Sampling_Start()

        if error_code != 0:
            self.logger.error("Error while starting the sampling, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

    def wait_for_sampling(self) -> None:
        """ Wait for the DAQ sampling to complete. """
        self.logger.info("Starting the wait for sampling")
        error_code = self._instrument.Waiting_for_sampling()

        if error_code != 0:
            self.logger.error("Error while waiting for the sampling, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info("Sampling wait completed")

    def get_raw_data(self) -> tuple[list[float], list[float]]:
        """
        Gets the raw sampling data from the DAQ device.

        Raises:
            InstrumentError: If getting the raw sampling data from the DAQ device fails.

        Returns:
            tuple[list[float], list[float]]: A tuple containing two lists:
                - The first list contains the TSL trigger data of a float type.
                - The second list contains the power monitor data of a float type.
        """
        self.logger.info("Retrieving the sampling raw data")
        error_code, trigger, monitor = self._instrument.Get_Sampling_Rawdata(
            None, None)

        if error_code != 0:
            self.logger.error("Error while getting the sampling raw data, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
        self.logger.info(f"The sampling raw data was retrieved, "
                         f"Data length: Trigger={len(trigger)}, Monitor={len(monitor)}")
        return trigger, monitor

    def stop_sampling(self) -> None:
        """ Stops the DAQ sampling. """
        self.logger.info("Stopping the sampling")
        error_code = self._instrument.Sampling_Stop()

        if error_code != 0:
            self.logger.error("Error while stopping the sampling, ",
                         str(error_code) + ": " + instrument_error_strings(error_code))
            raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))
