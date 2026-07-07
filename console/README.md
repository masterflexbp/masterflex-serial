# Sample files to use the APIs
- `sample_enable.py`: Enables the Serial Communication application.
- `sample_set_speedp.py`: Sets the pump speed in the unit of percentage.
- `sample_start.py`: Starts the pump in dispense mode.
- `legacy/reglo_icc_sample.py`: Runs a sample command sequence for a legacy ISMATEC REGLO ICC pump.

# How to use the sample files
- Connect the Masterflex 07526-96 cable to the PC.
- Obtain the port number (refer to `Accessing the COM Port` section in the README.md in `masterflex-serial` folder)
- In command prompt, run the following command:
  ```
  python sample_enable.py COMx
  ``` 
  where `COMx` is the serial port number, and `x` is the actual number of the cable. 
  <br />
  <br />
- **NOTE:** Please run `sample_enable.py` prior to running `sample_set_speedp.py` and `sample_start.py` to enable Serial Communication. Failure to enable Serial Communication prior to running `sample_set_speedp.py` and/or `sample_start.py` will result in an error message. 

# How to use the legacy ISMATEC REGLO ICC sample
This sample connects to a legacy ISMATEC REGLO ICC pump [MFLX78001-80](https://www.vwr.com/us/en/product/NA5139092/masterflex-ismatec-reglo-independent-channel-control-icc-peristaltic-pumps-avantor?isCatNumSearch=true&searchedCatalogNumber=MFLX78001-80) and runs a fixed channel sequence. Channel 1 runs at 20 RPM for 5 seconds, channel 3 runs at 10 RPM for 10 seconds, then all channels are stopped.

Before running the sample:
- Confirm the pump is connected to the PC.
- Confirm the pump serial port, such as `COM8`.
- Confirm the pump address in `console\legacy\reglo_icc_sample.py`.
- Review the channel numbers, speeds, and run times in `console\legacy\reglo_icc_sample.py`.

Run this command from the `masterflex-serial` folder:
  ```
  python console\legacy\reglo_icc_sample.py COM8
  ```
  Replace `COM8` with the COM port assigned to the pump.
  <br />
  <br />
- **NOTE:** This legacy ICC sample uses 9600 baud and raw ICC ASCII commands. It does not require running `sample_enable.py` first.