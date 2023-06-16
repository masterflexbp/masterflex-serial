# Sample files to use the APIs
- `sample_enable.py`: Enables the Serial Communication application.
- `sample_set_speedp.py`: Sets the pump speed in the unit of percentage.
- `sample_start.py`: Starts the pump in dispense mode.

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