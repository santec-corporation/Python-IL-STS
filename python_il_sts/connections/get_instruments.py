"""
Get Instrument Addresses.

Connection modes: GPIB, LAN and USB.
"""

import pyvisa
import nidaqmx
from dataclasses import dataclass

from ..drivers.santec_wrapper import MainCommunication

# Import program logger
from ..logger import get_logger

_resource_manager = pyvisa.ResourceManager()  # Initializing pyvisa resource manager class
_resources = _resource_manager.list_resources()  # Getting a list of all detected instruments
_system = nidaqmx.system.System.local()  # Getting a list of all detected DAQ devices


@dataclass
class Instrument:
    idn: str = ""
    name: str = ""
    resource: str = ""


class GetInstruments:
    """
    A class to get the GPIB or USB addresses of TSL, MPM and DAQ instruments/devices.
    """

    def __init__(self):
        self.logger = get_logger(__class__.__name__)

    def _list_instruments(self) -> list:
        """
        Detects GPIB and USB instruments and returns a list of Instrument objects.

        Returns:
            list: A list of detected Instrument objects.
        """
        instruments = []
        self.list_gpib_resources(instruments)
        self.list_usb_resources(instruments)
        self.list_daq_devices(instruments)
        self.sort_devices(instruments)

        self.logger.info(f"Current instruments: {instruments}")

        return instruments

    def list_gpib_resources(self, instruments: list) -> None:
        """
        Detects GPIB resources and appends them to the provided instruments list.

        Parameters:
            instruments (list): The list where detected GPIB resources will be stored.
        """
        self.logger.info("Getting GPIB resources")
        resource_tools = [i for i in _resources if 'GPIB' in i]
        self.logger.info(f"Available GPIB resources: {resource_tools}")

        for resource in resource_tools:
            self.initialize_gpib_resource(resource, instruments)

    def initialize_gpib_resource(self, resource: str, instruments: list) -> None:
        """
        Opens a GPIB resource and appends it to the instrument list if it
        is identified as a SANTEC instrument.

        Parameters:
            resource (str): The resource string to be opened.
            instruments (list): The list where the found SANTEC instrument will be stored.
        """
        try:
            self.logger.debug(f"Opening resource: {resource}")
            instrument = _resource_manager.open_resource(resource)
            idn = instrument.query("*IDN?")
            self.logger.info(f"Opened instrument: {idn}")

            idn_split = idn.split(',')
            if 'santec' in idn_split[0].lower():
                name = f"{idn_split[1]}_{idn_split[2]}_GPIB"
                instr = Instrument(idn=idn, name=name, resource=resource)
                instruments.append(instr)
            instrument.close()

        except RuntimeError as err:
            self.logger.info(f"Error while opening resource: {resource}, {err}")


    def list_usb_resources(self, instruments: list) -> None:
        """
        Detects USB resources and appends them to the provided instruments list.

        Parameters:
            instruments (list): The list where detected USB resources will be stored.
        """
        self.logger.info("Getting USB resources")
        main_communication = MainCommunication()
        usb_resources = list(main_communication.Get_USB_Resouce())
        self.logger.info(f"Available USB resources: {usb_resources}")

        for i, value in enumerate(usb_resources):
            usb_id = f"USB{i}"
            idn = value.strip("'").split('_')
            name = f"{idn[0]}_{idn[1]}_USB"
            instr = Instrument(idn=idn, name=name, resource=usb_id)
            instruments.append(instr)

    def list_daq_devices(self, instruments: list) -> str | None:
        """
        Prompts the user to select a DAQ device from the available devices
        and stores its ip_address.

        Parameters:
            instruments (list): The list containing information about the detected instruments.
        """
        self.logger.info("Listing DAQ devices.")
        daq_devices = _system.devices
        self.logger.info(f"Current DAQ devices: {daq_devices}")

        if daq_devices:
            for dev in daq_devices:
                name = f"{dev.name}_{dev.product_num}"
                instr = Instrument(idn=dev.product_type, name=name, resource=dev.name)
                instruments.append(instr)

    @staticmethod
    def sort_devices(instruments: list) -> None:
        """
        Sorts the instrument list by the type of instrument (TSL vs. MPM)
        and prints the sorted list of detected instruments.

        Parameters:
            instruments (list): The list containing detected instruments.
        """
        instruments.sort(key=lambda x: x.idn.startswith('SANTEC,MPM'))
