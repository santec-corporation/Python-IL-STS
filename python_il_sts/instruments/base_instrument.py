
"""
Base Instrument.
"""

import inspect

from ..logger import get_logger
from ..drivers.santec_wrapper import TSL, MPM


class BaseInstrument:
    def __init__(self):
        self._instrument = None
        self.logger = get_logger(__class__.__name__)

    @property
    def instrument(self):
        return self._instrument

    @property
    def information(self):
        if self._instrument:
            return self._instrument.Information
        raise Exception("Instrument is not connected.")

    def _check_restricted_method(self):
        """Check if the method is restricted to certain instrument types."""
        if not isinstance(self._instrument, (TSL, MPM)):
            stack = inspect.stack()
            caller_frame = stack[1].function
            error_string = (
                f"{self._instrument.__class__.__name__} "
                f"is not allowed to use method '{caller_frame}'."
            )
            self.logger.error(error_string)
            raise PermissionError(error_string)

    @property
    def __status(self) -> str:
        """Returns the current instrument status string."""
        return self._status

    @__status.setter
    def __status(self, value):
        """Set the current instrument status."""
        self.logger.debug(f"Setting instrument status: {value}")
        self._status = value

    def query(self, command: str) -> str:
        """Send a query command to the instrument
        and return the status and response."""
        """This method is restricted to TSL and MPM instruments."""
        self._check_restricted_method()
        command = command.upper()
        self.logger.debug("Query command: %s", command)

        try:
            status, response = self._instrument.Echo(command, "")
            self.__status = status
            self.logger.debug(f"Query Status: {status}. Response: {response}.")
            return response

        except Exception as e:
            error_string = f"Error while querying command {command}: {e}"
            self.logger.error(error_string)
            raise RuntimeError(error_string)

    def write(self, command: str) -> None:
        """Send a write command to the instrument and return the status."""
        """This method is restricted to TSL and MPM instruments."""
        self._check_restricted_method()
        command = command.upper()
        self.logger.debug("Write command: %s", command)

        try:
            status = self._instrument.Write(command)
            self.__status = status
            self.logger.debug(f"Write Status: {status}.")

        except Exception as e:
            error_string = f"Error while writing command {command}: {e}"
            self.logger.error(error_string)
            raise RuntimeError(error_string)

    def read(self) -> str:
        """Read data from the instrument and return the status and response."""
        """This method is restricted to TSL and MPM instruments."""
        self._check_restricted_method()
        self.logger.debug("Read command.")

        try:
            status, response = self._instrument.Read("")
            self.__status = status
            self.logger.debug(f"Read Status: {status}. Response: {response}.")
            return response

        except Exception as e:
            error_string = f"Error while reading instrument: {e}"
            self.logger.error(error_string)
            raise RuntimeError(error_string)

    @property
    def idn(self):
        """Return the identification string of the instrument."""
        idn = self.query("*IDN?")
        self.logger.debug(f"IDN string: {idn}")
        return idn

    @property
    def product_name(self):
        """Return the product name of the instrument."""
        product_name = self._instrument.Information.ProductName
        self.logger.debug(f"Product name: {product_name}")
        return product_name

    @property
    def serial_number(self):
        """Return the serial number of the instrument."""
        serial_number = self._instrument.Information.SerialNumber
        self.logger.debug(f"Serial number: {serial_number}")
        return serial_number

    @property
    def firmware_version(self):
        """Return the firmware version of the instrument."""
        firmware_version = self._instrument.Information.FWversion
        self.logger.debug(f"Firmware version: {firmware_version}")
        return firmware_version

    def disconnect(self) -> None:
        """
        Disconnects the instrument.
        """
        try:
            self._instrument.DisConnect()
            self.logger.info("Instrument disconnected.")
        except RuntimeError as e:
            self.logger.error(f"Error while disconnecting, {e}")

