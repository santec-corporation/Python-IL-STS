"""
DAQ Device Class.

@organization: Santec Holdings Corp.
"""

from ..drivers.santec_wrapper import DAQ

# Importing instrument error strings
from python_il_sts.utils.error_handling_class import InstrumentError, instrument_error_strings

# Import program logger
from python_il_sts.logger import get_logger
logger = get_logger("DAQ Device Class.")


class DaqDevice:
    """
    DAQ device class to control and command the DAQ device.

    Attributes:
        __daq (DAQ): The DAQ class from the namespace Santec.
        _device_name (str): The name of the DAQ device.

    Parameters:
        device_name (str): The name of the DAQ device.

    Raises:
        None
    """
    def __init__(self,
                 device_name: str):
        logger.info("Initializing Daq Instrument class.")
        self.__daq = DAQ()
        self._device_name = device_name
        logger.info(f"Daq Device details, Device Name: {device_name}")

    def connect(self) -> None:
        """
        Establishes connection with a DAQ board.

        Raises:
            InstrumentError: If the connection fails with an error code.
        """
        logger.info("Connect DAQ device")
        self.__daq.DeviceName = str(self._device_name)
        device_answer = None
        try:
            errorcode, device_answer = self.__daq.Connect("")
            if errorcode != 0:
                logger.critical("DAQ instrument connection error ",
                                str(errorcode) + ": " + instrument_error_strings(errorcode))
                raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        except InstrumentError as e:
            print(f"Error occurred: {e}")
        logger.info(f"Connected to DAQ device. device_answer: {device_answer}")

    def set_logging_parameters(self,
                               start_wavelength: float,
                               stop_wavelength: float,
                               sweep_speed: float,
                               tsl_actual_step: float) -> None:
        """
        Set DAQ logging parameters for DAQ sampling.

        Parameters:
            start_wavelength (float): Start wavelength value of the sweep.
            stop_wavelength (float): Stop wavelength value of the sweep.
            sweep_speed (float): Speed value of the sweep.
            tsl_actual_step (float): Step wavelength value of the sweep.

        Raises:
            InstrumentError: If setting the logging parameters to the DAQ device fails.
        """
        logger.info(f"Set DAQ logging params: start_wavelength={start_wavelength}, stop_wavelength={stop_wavelength}, "
                    f"sweep_speed={sweep_speed}, tsl_actual_step={tsl_actual_step}")
        errorcode = self.__daq.Set_Sampling_Parameter(start_wavelength,
                                                      stop_wavelength,
                                                      sweep_speed,
                                                      tsl_actual_step)

        if errorcode != 0:
            logger.error("Error while setting DAQ logging params, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"DAQ logging params set.")

    def sampling_start(self) -> None:
        """ Starts the DAQ sampling """
        logger.info("DAQ sampling start")
        errorcode = self.__daq.Sampling_Start()
        if errorcode != 0:
            logger.error("Error while DAQ sampling start, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("DAQ sampling started.")

    def sampling_wait(self) -> None:
        """ DAQ wait for sampling """
        logger.info("DAQ sampling wait")
        errorcode = self.__daq.Waiting_for_sampling()
        if errorcode != 0:
            logger.error("Error while DAQ sampling wait, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info("DAQ sampling wait done.")

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
        logger.info("DAQ get sampling raw data")
        errorcode, trigger, monitor = self.__daq.Get_Sampling_Rawdata(
            None, None)
        if errorcode != 0:
            logger.error("Error while getting DAQ sampling raw data, ",
                         str(errorcode) + ": " + instrument_error_strings(errorcode))
            raise InstrumentError(str(errorcode) + ": " + instrument_error_strings(errorcode))
        logger.info(f"DAQ sampling raw data acquired, data length: trigger={len(trigger)}, monitor={len(monitor)}")
        return trigger, monitor

    def disconnect(self) -> None:
        """
        Disconnects the connection from the DAQ device.

        Raises:
              RuntimeError: If disconnecting the DAQ device fails.
        """
        try:
            self.__daq.DisConnect()
            logger.info("DAQ connection disconnected.")
        except RuntimeError as e:
            logger.error(f"Error while disconnecting the DAQ connection, {e}")
