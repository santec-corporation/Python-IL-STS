## Detailed README

[![en](https://img.shields.io/badge/lang-en-blue.svg)](https://github.com/santec-corporation/Python-IL-STS/blob/main/docs/README.md)
[![jp](https://img.shields.io/badge/lang-jp-red.svg)](https://github.com/santec-corporation/Python-IL-STS/blob/main/docs/README.jp.md)

> [!IMPORTANT]    
> ⚠️ Crucial information below.
> Precautions before running the script
> - Make sure that the TSL LD diode is switched ON and warm up during 30min.
> - It is recommended to perform a zeroing of the MPM before running an STS operation. 


## Core Scripts Overview
- [get_address.py](/./src/santec/get_address.py): Detects connected instruments via GPIB and USB.
- [tsl_instrument_class.py](/./src/santec/tsl_instrument_class.py): Manages TSL instrument functionality.
- [mpm_instrument_class.py](/./src/santec/mpm_instrument_class.py): Handles MPM instrument operations.
- [daq_device_class.py](/./src/santec/daq_device_class.py): Interacts with DAQ devices.
- [sts_process.py](/./src/santec/sts_process.py): Processes data from the Swept Test System.
- [error_handling_class.py](/./src/santec/error_handling_class.py): Manages errors related to Instrument DLL and STS Process DLL.
- [file_saving.py](/./src/santec/file_saving.py): Records operational data for the Swept Test System.

---

## LAN Configuration

#### 1. Open the `main.py` file.

#### 2. Replace the below code in the `connection()` function,

```python
def connection():
    tsl: TslInstrument
    mpm: MpmInstrument
    daq: SpuDevice
    
    device_address = GetAddress()
    device_address.initialize_instruments(is_tsl_mpm=False)

    tsl = TslInstrument(interface="LAN", ip_address="192.168.1.161")  # Replace with your TSL IP address
    tsl.connect()

    mpm = MpmInstrument(interface="LAN", ip_address="192.168.1.162")  # Replace with your MPM IP address
    mpm.connect()
    
    if "220" in mpm.idn():
        return tsl, mpm, None

    daq_address = device_address.get_daq_address()
    daq = SpuDevice(device_name=daq_address)
    daq.connect()

    return tsl, mpm, daq
```

#### 3. Follow the steps from here, [Initialize the System](https://github.com/santec-corporation/Santec_IL_STS/blob/main/docs/README.md#1-initialize-the-system).


---

## How to Run the Script

Verify the instrument connections before running the script, <br>
- [Front Connections](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/connection_front.png)
- [Rear Connections](https://github.com/santec-corporation/Santec_IL_STS/blob/stable/docs/connection_rear.png)

#### 1. Initialize the System
Run the `main.py` script to launch the measurement interface. 

#### 2. Instrument Selection
A list of connected instruments will be displayed.\
Select the following:\
Light Source,\
Power Meter,\
DAQ Board.

#### 3. Reference Data Configuration
- The program will search for previously saved reference data.
- If no data is found, input the following sweep parameters: \
Start and stop wavelengths,\
Sweep speed,\
Sweep resolution (step size),\
Output power,\
MPM optical channels to measure,\
Optical dynamic ranges.

#### 4. Utilizing Existing Data
If recorded reference data is available, the script will prompt you to upload the sweep parameters and associated data.

#### 5. Optical Channel Connection
- Follow the prompts to connect each selected optical channel.
- Begin measuring reference data.

**Note**: Use a patch cord to connect the TSL directly to each optical port.

#### 6. Connecting the Device Under Test (DUT)
- Connect the DUT.
- Enter the number of measurement repetitions.
- Press ENTER to start the measurement.

#### 7. Measurement Results
- The script will display the Insertion Loss results.
- You can choose to conduct a second measurement if needed.
- If no further measurements are required, the script will save the reference and DUT data.
- The instruments will be disconnected automatically.

---

## Sweep Configuration Parameters

**File type** [JSON](https://www.json.org/json-en.html) <br>
**File name** **last_scan_params.json**

### Example
  ```json
  {
      "selected_chans": [
          ["0", "1"],
          ["0", "2"]
      ],
      "selected_ranges": [
          1,
          2
      ],
      "start_wavelength": 1500.0,
      "stop_wavelength": 1600.0,
      "sweep_step": 0.1,
      "sweep_speed": 50.0,
      "power": 0.0,
      "actual_step": 0.1
  }
  ```
### Customization Tips
**Channel Selection**<br>
Adjust the **selected_chans** array to include any channels necessary for your analysis.
Each combination allows you to compare different configurations.

**Range Selection**<br>
Modify **selected_ranges** to select specific ranges, according to your experimental design.
Ensure the indices match your available range options.

**Wavelength Settings**<br>
Change **start_wavelength** and **stop_wavelength** to define the spectral range of interest for your measurements.

**Sweep Parameters**<br>

**Step Size**<br>
Tweak **sweep_step** for finer or coarser sampling; smaller steps yield more detailed data.

**Speed**<br>
Adjust **sweep_speed** based on how quickly you need results versus the precision required.

**Power Adjustment**<br>
Set the power parameter based on your equipment's requirements and desired sensitivity during measurements.

**Actual Step**<br>
The step size between two TSL triggers. This value is obtained after setting the TSL sweep parameters, refer to `set_sweep_parameters` of the `tsl_instrument_class`.

---

## About Santec Swept Test System

### What is STS IL PDL?
  The Swept Test System is the photonic solution by Santec Corporation,
  to perform Wavelength-Dependent Loss characterization of passive optical devices.
  It consists of:
  - A light source: Santec’s Tunable Semiconductor Laser, also known as TSL
  - A power meter: Santec’s Multi-port Power Meter, also known as MPM
   

### For more information on the Swept Test System [CLICK HERE](https://inst.santec.com/products/componenttesting/sts)