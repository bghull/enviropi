<p align="center">
  <strong>An automated environmental sensing platform built on Node-RED and Python 3</strong><br><br>
  Mobile-friendly | Easy-to-read | Real-time and historical | Still-frame and timelapse images | Easily extended to other sensors
</p>

# Purpose and Goals

This project began as a simple wireless temperature reporting station for my outdoor vermicompost bin (which was itself another experiment undertaken during Covid-19). _Eisenia foetida_ "red wriggler" composting worms are sensitive to the light, temperature, humidity, and chemical conditions of the soil they inhabit, and I was looking for an excuse to dive deeper into physical computing and hobby electronics anyway. This entire build was supposed to consist entirely of one Arduino Uno and a DS18B20 temperature sensor or two...

Along the way I've borrowed all the best ideas from other nerds doing similar work in other communities, from saltwater reef aquariums like [reefpi](https://learn.adafruit.com/reef-pi-installation-and-configuration), to NFT hydroculture builds like [HydroPWNics](https://hackaday.io/project/2964-hydropwnics/details), to the citizen-scientists at [the Cave Pearl project](https://thecavepearlproject.org/2015/03/01/using-ds18b20-sensors-to-make-a-diy-thermistor-string-pt-1-the-build/). Huge thanks to them all.

# System Diagram

Each device gathers data (in the form of sensor values or image files) and sends them to a central server over MQTT, BLE, and/or scp. The central server performs all data formatting/storage/retrieval, in addition to image manipulation and hosting of the Node-RED dashboard. After a successful database write, the new values are passed to the various UI widgets on the dashboard including status indicators and historical charts. 

New sensor readings or image snapshots can be requested via buttons on the dashboard, which sends commands from the central server to the relevant device. Off-the-shelf "smart plugs" switch mains-voltage devices based on user-defined targets, e.g. a humidifier to keep relative humidity within range.

The flow tabs in Node-RED are structured along the same lines as this diagram: "Inputs" corresponds to the Devices tab, "Broker" to the Database and Images tabs, and "UI" to the Dashboard tab.

<img src="https://github.com/bghull/enviropi/blob/main/screenshots/diagram.png">

# Hardware
- *brokerpi*: Raspberry Pi 4 2GB
  - MQTT broker and central server for entire system 
  - Hosts Node-RED which handles all database I/O, image manipulation, and web interface
- *sensorpi*: Raspberry Pi Zero W (first gen)
  - Reads all sensors (mounted to Atlas Scientific Tentacle T3 or wired straight into GPIO):
    - Atlas Scientific EZO-pH via I2C (pH)
    - Atlas Scientific EZO-EC via I2C (electrical conductivity)
    - D18B20 via one-wire bus (temperature)
    - Atlas Scientific EZO-HUM via I2C (temperature, relative humidity)
  - Formats all data and transmits to *brokerpi* via `paho-mqtt`
- *camerapi*: Raspberry Pi Zero W (first gen)
  - Captures regular snapshots (RPi cam v2.1 via `raspistill`)
  - Transmits images to *brokerpi* via `scp` for processing/displaying
- Ruuvitag BLE open-source sensor package (temperature, relative humidity, air pressure)
- TP-Link Kasa smart plugs (basically used as relays with an IP address. Easy API-driven switching of mains-voltage devices. Entirely optional.)

# Node-RED flows (JSON)
## Devices

Handles all device inputs, including data formatting and structuring of payload variables for INSERT operation.

<img src="https://github.com/bghull/enviropi/blob/main/screenshots/devices.png">

- For simplicity downstream, all sensor readings received within a 2s window are joined into one payload and written into the SQL database as a single row. This design allows me to consistently update all dashboard elements at one time with a single row.

## Database

Handles all database input/output, including debugging and scrubbing of bad values (e.g. from faulty sensors).

<img src="https://github.com/bghull/enviropi/blob/main/screenshots/database.png">

- Currently uses SQLite3, eventually targeting InfluxDB for use with Grafana interface. (While a timeseries database seems ideal for this kind of work, I'm not convinced my low polling rate (5 mins) justifies the implementation time-cost.)

## Dashboard

Handles all elements of the web dashboard, including all user views and some controller functionality.

<p align="justify">
<img align="left" src="https://github.com/bghull/enviropi/blob/main/screenshots/dashboard.png" height="600">  <img align="right" src="https://github.com/bghull/enviropi/blob/main/screenshots/main_screen.png" height="600">
</p>
<br clear="right"/>

- Digital "LEDs" provide at-a-glance information on environment and sensor state.
- "Last Update" timestamp and last-known value printouts provide peace of mind that the system is running as intended.
- Charts of each environment variable provide more detailed history.

- Manual controls abstract away the device-to-device communication, allowing for new sensor reads, new camera images, and switching of smart plugs with the click of a button.

## Images

Handles all image manipulation. Contains two entirely independent workflows:

1. Visually printing a date and time on every new image received before displaying on dashboard.
2. Compiling those images into timelapse mp4's per user-configured settings.

### 1. Timestamp incoming images:
  
<img src="https://github.com/bghull/enviropi/blob/main/screenshots/timestamping.png">

- Monitor folder for new incoming image files.
- Stamp image with a human-readable time format (pulled from filename).
- Save image to local storage and display on Node-RED dashboard.
  
### 2. Create new timelapse:

<img src="https://github.com/bghull/enviropi/blob/main/screenshots/timelapse.png">

- Read user-specified start/end dates as well as target mp4 total runtime, which are then passed to **timelapse.py**.
  - The shorter the duration or higher the image count, the faster time passes in the timelapse.
- Build and execute a structured `ffmpeg` command via Python, and make the output mp4 available to dashboard dropdown menu.

Dashboard control:

<img src="https://github.com/bghull/enviropi/blob/main/screenshots/timelapse_controls.png" height="500">

# Python scripts
**read_async.py** (on *sensorpi*)
- Polls all sensors, calculates derived values, and formats data
  - Uses asyncio to minimize wait time, as each EZO sensor requires a variable processing delay between write and read commands.
- Publishes values to *brokerpi* via MQTT

**picture.py** (on *camerapi*)
- Snaps photo via `raspistill` and sends to *brokerpi* via `scp`
- Command line arguments allow for easy adjustments to account for changing camera position/orientation/lighting

**timelapse.py** (on *brokerpi*)
- Calls ffmpeg with various command line arguments to create timelapse mp4's


# Setup
Currently undocumented: Python requirements.txt files, `ssh-keygen` & `ssh-copy-id` between devices, crontab configs, static IP address config (DHCP on wireless router).