
"""
Instrument Manager.
"""

# Basic imports.
from typing import Dict

# Python IL STS imports.
from .get_instruments import GetInstruments
from ..instruments.base_instrument import BaseInstrument
from ..instruments.tsl_instrument import TslInstrument
from ..instruments.mpm_instrument import MpmInstrument
from ..instruments.daq_instrument import DaqInstrument
from ..drivers.santec_wrapper import (ConnectionType, GPIBType,
                                      Terminator, MainCommunication, DAQ)
from ..utils.error_handling import InstrumentError, instrument_error_strings

# Import program logger.
from ..logger import get_logger


# Initialize the Santec Main communication class.
main_communication = MainCommunication()

# Initialize the Santec DAQ class.
daq = DAQ()


class ConnectionManager(GetInstruments):
    """Main connection manager for instrument detection and connection."""

    def __init__(self, use_keysight_visa: bool = False):
        """Initializes the Connection Manager class."""
        super().__init__()
        self.logger = get_logger(self.__class__.__name__)
        self._instruments: Dict[str, str] = {}
        self._connected_instruments: Dict[str, BaseInstrument] = {}
        self._resources_listed: bool = False
        self._use_keysight_visa = use_keysight_visa
        self.logger.info("Initializing Instrument Manager...")

    def list_instruments(self):
        """
        Detects and displays all the Santec GPIB and USB instrument connections,
        as well as the DAQ devices.
        """
        self.logger.info("Listing instruments")
        instruments = self._list_instruments()
        if not instruments:
            return []

        self._instruments = {instr.name: instr.resource for instr in instruments}
        return list(self._instruments.keys())

    def connect(self, instrument_name: str) -> BaseInstrument | None:
        resource_name = self._instruments.get(instrument_name)
        if not resource_name:
            print(f"Instrument '{instrument_name}' not found.")
            return None

        if instrument_name in self._connected_instruments.keys():
            raise Exception(f"Instrument {instrument_name} is already connected.")

        instrument = None
        if "TSL" in instrument_name:
            instrument = self.connect_tsl(resource_name)
        elif "MPM" in instrument_name:
            instrument = self.connect_mpm(resource_name)
        elif "Dev" in instrument_name:
            instrument = self._connect_daq(resource_name)

        if instrument:
            self._connected_instruments[instrument_name] = instrument
            return instrument
        return None

    def _establish_connection(self,
                              instrument,
                              resource_name: str,
                              terminator: Terminator):

        if not resource_name:
            if "TCPIP" in resource_name:
                connection_type = ConnectionType.TCPIP
            else:
                raise Exception("Could not fetch resource name. "
                                "Please make the entered instrument resource name is of the correct format.")
        else:
            connection_type = self._get_connection_type(resource_name)

        if connection_type is ConnectionType.NULL:
            raise Exception("Connection type not found.")

        match connection_type:
            case ConnectionType.GPIB:
                self._gpib_connection(instrument, resource_name, terminator)
            case ConnectionType.USB:
                self._usb_connection(instrument, resource_name, terminator)
            case ConnectionType.TCPIP:
                self._tcpip_connection(instrument, resource_name, terminator)
            case ConnectionType.NULL:
                raise Exception(f"Invalid connection type: {connection_type}")

        print(f"Connected to {instrument.product_name}. Serial number: {instrument.serial_number}")
        return instrument

    def connect_tsl(self, resource_name) -> TslInstrument | None:
        terminator = Terminator.CR
        instrument = TslInstrument()
        return self._establish_connection(instrument, resource_name, terminator)

    def connect_mpm(self, resource_name) -> MpmInstrument | None:
        terminator = Terminator.LF
        instrument = MpmInstrument()
        return self._establish_connection(instrument, resource_name, terminator)

    def _connect_daq(self, device_name: str) -> DaqInstrument | None:
        """
        Establishes connection with a DAQ board.

        Raises:
            InstrumentError: If the connection fails with an error code.
        """
        self.logger.info("Connect DAQ device")
        instrument = DaqInstrument()
        instrument_instance = instrument.instrument
        instrument_instance.DeviceName = device_name
        device_response = None
        try:
            error_code, device_response = instrument_instance.Connect("")
            if error_code != 0:
                self.logger.critical("DAQ instrument connection error ",
                                str(error_code) + ": " + instrument_error_strings(error_code))
                raise InstrumentError(str(error_code) + ": " + instrument_error_strings(error_code))

            print(f"Connected to DAQ: {instrument.product_name}.")
            return instrument
        except InstrumentError as e:
            print(f"Error occurred: {e}")
        self.logger.info(f"Connected to DAQ device. device_answer: {device_response}")
        return None

    def _gpib_connection(self, instrument, resource_name, terminator):
        """Establishes a GPIB connection."""
        self.logger.info(f"Connecting to GPIB resource: {resource_name}")
        gpib_board, gpib_address, _ = resource_name.split("::")  # GPIB0::10::INSTR
        gpib_board = gpib_board[-1]

        instrument_instance = instrument.instrument
        instrument_instance.GPIBBoard = int(gpib_board)
        instrument_instance.GPIBAddress = int(gpib_address)
        instrument_instance.Terminator = terminator.value
        if self._use_keysight_visa:
            instrument_instance.GPIBConnectType = GPIBType.KeysightVisa.value
        else:
            instrument_instance.GPIBConnectType = GPIBType.NI4882.value

        try:
            error_code = instrument_instance.Connect(ConnectionType.GPIB.value)
            if error_code != 0:
                raise InstrumentError(
                    f"Failed to establish GPIB connection "
                    f"with GPIB{gpib_board}::{gpib_address}",
                    error_code,
                )
        except Exception as e:
            raise InstrumentError(
                f"Error connecting to GPIB{gpib_board}::{gpib_address}",
                str(e),
            )

    def _usb_connection(self, instrument, resource_name, terminator):
        """Establishes a USB connection."""
        self.logger.info(f"Connecting to USB resource: {resource_name}")
        usb_device_id = int(resource_name[-1])

        instrument_instance = instrument.instrument
        instrument_instance.DeviceID = usb_device_id
        instrument_instance.Terminator = terminator.value

        try:
            error_code = instrument_instance.Connect(ConnectionType.USB.value)
            if error_code != 0:
                raise InstrumentError(
                    f"Failed to establish USB connection "
                    f"with {resource_name}",
                    error_code,
                )
        except Exception as e:
            raise InstrumentError(
                f"Error connecting to USB: {resource_name}", str(e)
            )

    def _tcpip_connection(self, instrument, resource_name, terminator):
        """Establishes a TCPIP connection."""
        self.logger.info(f"Connecting to TCPIP resource: {resource_name}")
        _, ip_address, port_number, _ = resource_name.split("::")  # TCPIP0::192.168.10.101::5000::SOCKET

        instrument_instance = instrument.instrument
        instrument_instance.IPAddress = ip_address
        instrument_instance.Port = int(port_number)
        instrument_instance.TimeOut = 5000
        instrument_instance.Terminator = terminator.value

        try:
            error_code = instrument_instance.Connect(ConnectionType.TCPIP.value)
            if error_code != 0:
                raise InstrumentError(
                    f"Failed to establish LAN connection "
                    f"with {ip_address}::{port_number}",
                    error_code,
                )
            product_name = instrument_instance.Information.ProductName
            serial_number = instrument_instance.Information.SerialNumber
            instrument_name = f"{product_name}_{serial_number}_TCPIP"
            self._connected_instruments[instrument_name] = resource_name
        except Exception as e:
            raise InstrumentError(
                f"Error connecting to {ip_address}::{port_number}", str(e)
            )

    @staticmethod
    def _get_connection_type(instrument_name):
        """Determines the connection type based on the resource name."""
        instrument_name = instrument_name
        if "GPIB" in instrument_name:
            return ConnectionType.GPIB
        elif "USB" in instrument_name:
            return ConnectionType.USB
        elif "DEV" in instrument_name:
            return ConnectionType.DEV
        return ConnectionType.NULL