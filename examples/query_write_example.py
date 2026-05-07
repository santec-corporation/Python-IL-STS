"""
Python IL STS - Query / Write example.
"""

# Import the basic modules from python_il_sts
from python_il_sts import ConnectionManager, TslInstrument, MpmInstrument


def tsl():
    tsl_resource = ""
    tsl_instrument: TslInstrument

    connection_manager = ConnectionManager()
    instrument_list = connection_manager.list_instruments()

    print("List of Instruments: ", instrument_list)

    for dev in instrument_list:
        if "TSL" in dev:
            tsl_resource = dev

    if tsl_resource == "":
        raise Exception("TSL instrument not connected. Please connect the TSL.")

    tsl_instrument = connection_manager.connect_tsl(tsl_resource)

    # Write to TSL
    tsl_instrument.write('POW 5')

    # Query TSL
    status, response = tsl_instrument.query('POW?')        # Gets TSL output power
    print(status)             # Prints status 0 if a query was successful
    print(response)           # Prints query response


def mpm():
    mpm_resource = ""
    mpm_instrument: MpmInstrument

    connection_manager = ConnectionManager()
    instrument_list = connection_manager.list_instruments()

    print("List of Instruments: ", instrument_list)

    for dev in instrument_list:
        if "MPM" in dev:
            mpm_resource = dev

    if mpm_resource == "":
        raise Exception("MPM instrument not connected. Please connect the MPM.")

    mpm_instrument = connection_manager.connect_mpm(mpm_resource)

    # Write to MPM
    mpm_instrument.write('AVG 5')

    # Query MPM
    status, response = mpm_instrument.query('AVG?')  # Gets MPM averaging time
    print(status)  # Prints status 0 if a query was successful
    print(response)  # Prints query response


if __name__ == '__main__':
    tsl()
    mpm()
