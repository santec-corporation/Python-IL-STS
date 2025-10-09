

from python_il_sts.connections.connection_manager import ConnectionManager

connect = ConnectionManager()

print(connect.list_instruments())

tsl = connect.connect('TSL-570_22071071_GPIB')
print(tsl.firmware_version)