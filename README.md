
<p align="right"> <a href="https://www.santec.com/en/" target="_blank" rel="noreferrer"> <img src="https://www.santec.com/dcms_media/image/common_logo01.png" alt="santec" 
  width="250" height="45"/> </a> </p>

<h1 align="left"> Santec IL STS </h1>

Program to measure Insertion Loss. <br> <br>

[![en](https://img.shields.io/badge/lang-en-blue.svg)](https://github.com/santec-corporation/Python-IL-STS/blob/main/README.md)
[![jp](https://img.shields.io/badge/lang-jp-red.svg)](https://github.com/santec-corporation/Python-IL-STS/blob/main/README.jp.md)

## Overview

The **Santec_IL_STS** is designed to configure and operate the Santec Swept Test System (STS). <br>
This tool facilitates the measurement of Insertion Loss (IL) using Santec's TSL and MPM series instruments.

--- 

## Key Features

- Configure the instruments (Light source: TSL series, Power meter: MPM series, DAQ board)
- Perform wavelength scans
- Record reference and measurement scan power
- Calculate and save Insertion Loss (IL) data
- Re-use previous scan parameters and reference data

---

## Getting Started

### System Requirements

**Python:** 3.12+

**Platform:** Windows 10
- **Drivers:** 
  - NI-488.2: [Version 20](https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#345631)
  - NI-DAQmx: [Version 20](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#346240)
  - NI-VISA: [Version 20](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html#346210)

**Platform:** Windows 11
- **Drivers:** 
  - NI-488.2: [2024 Q3](https://www.ni.com/en/support/downloads/drivers/download.ni-488-2.html#544048) (Latest)
  - NI-DAQmx: [2024 Q4](https://www.ni.com/en/support/downloads/drivers/download.ni-daq-mx.html#549669) (Latest)
  - NI-VISA: [2024 Q4](https://www.ni.com/en/support/downloads/drivers/download.ni-visa.html#548367) (Latest)

**Santec DLLs:** Installed via Santec Swept Test System (IL/PDL) software.
- Download the latest version of the STS IL/PDL software [here](https://downloads.santec.com/downloads).
- .NET: Framework 4.5.2+ (as required by Santec DLLs)

> ⚠️ PySantec relies on Santec’s .NET Framework DLLs and therefore does not support Linux or macOS. <br>
> Importing the package on non‑Windows platforms raises an error.


### Dependencies

- [pythonnet](https://pythonnet.github.io/) : Also known as `clr`, for .NET interoperability
- [pyvisa](https://pyvisa.readthedocs.io/en/latest/index.html) : For controlling measurement devices
- [nidaqmx](https://nidaqmx-python.readthedocs.io/en/latest/) : API for NI DAQ driver interaction


### Supported Instruments
The Swept Test System IL PDL Software is designed to function with:
- _TSL-510, TSL-550, TSL-570, TSL-710 and TSL-770 laser series_
- _MPM-210, MPM-210H and MPM-220 power meter series_


### Supported Instrument Connections
- **TSL-510, TSL-550, TSL-710**  
  **Supported Interfaces**: GPIB

- **TSL-570, TSL-770**  
  **Supported Interfaces**: GPIB, USB, or LAN

- **MPM-210, MPM-210H and MPM-220**  
  **Supported Interfaces**: GPIB or LAN

---

## Installation and Execution

### Python Installation

**Download and Install Python:**
Version 3.12+ recommended.
   - Go to the [Python Downloads](https://www.python.org/downloads/) page.
   - Download the latest version.
   - Follow the installation instructions for your operating system.

### Cloning the Repository

To clone the repository, use the following command in your terminal:

```bash
git clone https://github.com/santec-corporation/Python-IL-STS.git
```

### Downloading the Latest Release,
You can download the latest release directly from the [Releases](https://github.com/santec-corporation/Python-IL-STS/releases) page.

### Executing the Program
1. Navigate to the Project Directory,
   ```bash
    cd Python_IL_STS
   ```
   
2. Install the dependencies, 
   ```bash
    pip install -r docs/requirements.txt
   ```

3. Run the Program,
   ```bash
    python main.py
   ```

Optional steps,

4. Log to the screen, call the `log_to_screen()` method in `main.py`.

### Upgrading Dependencies

- **Upgrade pythonnet:**
  ```bash
  pip install --upgrade pythonnet
  ```

- **Upgrade pyvisa:**
  ```bash
  pip install --upgrade pyvisa
  ```
  
- **Upgrade nidaqmx:**
  ```bash
  pip install --upgrade nidaqmx
  ```

<br/>
