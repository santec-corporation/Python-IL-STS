# -*- coding: utf-8 -*-

"""
Created on Wed 05 17:17:26 2024

@author: chentir
@organization: santec holdings corp.
"""

# Importing high-level santec package and its modules
from src.santec import TslInstrument, MpmInstrument, GetAddress

# Initializing get instrument address class
device_address = GetAddress()


def main():
    """ Main method of this project """

    tsl: TslInstrument
    mpm: MpmInstrument

    device_address.initialize_instrument_addresses()
    tsl_address = device_address.get_tsl_address()
    mpm_address = device_address.get_mpm_address()

    # Only connect to the devices that the user wants to connect
    tsl = TslInstrument(instrument=tsl_address)
    tsl.connect()

    mpm = MpmInstrument(instrument=mpm_address)
    mpm.connect()

    # TSL Query / Write example
    # Write to TSL
    status = tsl.write('POW 5')       # Sets TSL output power to 5
    print(status)               # Prints 0 if write was successful

    # Query TSL
    status, response = tsl.query('POW?')        # Gets TSL output power
    print(status)             # Prints status 0 if a query was successful
    print(response)           # Prints query response

    # MPM Query / Write example
    # Write to MPM
    status = mpm.write('AVG 5')    # Sets MPM averaging time to 5
    print(status)  # Prints 0 if write was successful

    # Query MPM
    status, response = mpm.query('AVG?')  # Gets MPM averaging time
    print(status)  # Prints status 0 if a query was successful
    print(response)  # Prints query response


if __name__ == '__main__':
    main()
