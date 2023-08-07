*** I will be returning to this project in September and update any major changes then. Life has just been a bit difficult lately ***
# Bambu Lab 3D Printer Data Collector
### Made with OBS-Studio in mind for streaming

This was developed on Python 3.11.1 but should work within the Python 3 versions. 

You can see the data being used in action on https://twitch.tv/techdaddy

To use this data that is output you will want to use  the streamer.bot to middle man some of the functionality. Not having it will break the script as the script is set to connect to streamer.bots http server for scene information to automate stream scenes. If you comment out all but the payload line in the sbDoAction function in BambuDataCollect.py you can run this without that functionailty.

Make sure you have Python3 installed. You can check this from the command prompt by running `python3 --version` and that should return the current version you have installed. If you do not, you can install it from the MS Store on Windows or using your linux package manager of your choice. 

## Installation

1. Clone this repository, either by downloading the zip and unzipping or cloning it locally. If you are wanting to get data for more than one printer I would suggest downloading the zip and unzipping to one folder per printer. 
2. Rename `example.env` to `.env` 
3. In `.env` the scenePath is pointed to the local assets directory which contains pngs of the Bambu printer and a small temp box that is transparent. If you are going to have OBS read from another directory change the pach and use the fully qualified path. 
4. For the rest of the `.env` file you will need the IP address and Serial number of your printer. In Bambu Studio on your PC you can get the serial number by going to the Device section and clicking Update on the left. To get your IP address you can go to the printer, click the Nut icon and then click the network menu and you will see your IP. Enter those items into the `.env` file. Also if you are running multiple printers or would like to have a unique name displayed when connected make sure to update the `printerName` field in the `.env` file as well.
5. In order to avoid any confusion by installing libraries to your base install of Python, create a virtual environment. If you are running multiple instances you can create one virtual environment to use with all of them or create one in each instance. To create a virtual environment run `python -m venv BambuVenv`. you may need to install python3-venv in linux from your package manager. 
6. Now that you have created your virtual environment lets activate it (make sure you are in the parent directory that BambuVenv exists in):
    Windows Command Prompt: `BamabuVenv\Scripts\activate.bat`
    Windows Powershell: `.\BambuVenv\Scripts\activate.ps1`
    Linux: `source BambuVenv/bin/activate`
7. In your command prompt (for linux or windows) you should now see the current working directory name prepended by (BambuVenv). Go ahead and run `pip install -r requirements.txt` this will download and install the required Python libraries to run this process within the virtual environment.
8. If you are not already in the directory where BambuDataCollect.py is located in your command promp/terminal make sure to change to that directory
9. run the script with the following command `python BambuDataCollect.py` as long as you configured the `.env` file correctly you should see some text part of which will say 'result code 0' which means that it is working as expected. 
10. The script will continually update the text files in the `scenePath` directory location until you close the command prompt/terminal or hit Ctrl+C
11. If you terminated the script with Ctrl+c and are done either close the terminal or make sure to type `deactivate` in order to exit the python virtual environment. 

## Output File Explanation

In the `.env` file you put the path where you want the output files to go to be used with OBS. Here is a list of those files and what they contain.

- aux_fan_speed.txt
  - Contains the fan speed rounded to the nearest 10% in the format of `xx%`
- BambuJsonDump.json.txt
  - The full json dump of all the information the printer regularly sends out. This is written to on every update so if you want to look at it I would copy it out then open it up so it does not cause any issues with the file write. 
- bed_target_temp_c.txt
  - The Bed target temp in Celsius 
- bed_target_temp_f.txt
  - The Bed target temp in Fahrenheit
- bed_temp_c.txt
  - The current Bed temp in Celsius
- bed_temp_f.txt
  - The current Bed temp in Fahrenheit
- chamber_fan_speed.txt
  - Contains the fan speed rounded to the nearest 10% in the format of `xx%`
- chamber_temp_c.txt
  - The current Chamber temp in Celsius
- chamber_temp_f.txt
  - The current Chamber temp in Fahrenheit
- gcode_end_time_estimated.txt
  - The estimated time the print will finish in the format of `YYYY-MM-DD HH:mm:ss UTC`
- gcode_start_time.txt
  - The time the print started in the format of `YYYY-MM-DD HH:mm:ss UTC`
- mc_percent.txt
  - The completion percentage
- mc_remaining_time.txt
  - The remaining time in the format of `HH:mm Remains`
- nozzle_target_temp_c.txt
  - The Nozzle target temp in Celsius 
- nozzle_target_temp_f.txt
  - The Nozzle target temp in  Fahrenheit
- nozzle_temp_c.txt
  - The current Nozzle temp in Celsius
- nozzle_temp_f.txt
  - The current Nozzle temp in Fahrenheit
- part_cooling_fan_speed.txt
  - Contains the fan speed rounded to the nearest 10% in the format of `xx%`
- spd_lvl.txt
  - The speed setting (Silent, Standard, Sport, Ludacris)
- spd_percent.txt
  - The percentage of speed compared to standard in the format of `xxx%` 


## OBS Setup
 To get your camera feed available in OBS follow the instructions here https://wiki.bambulab.com/en/software/bambu-studio/virtual-camera
 
You can then use `Text(GDI+)` objects in your OBS scene to pull the data from the files. when you create your `Text(GDI+)` object you will check the "Read from file" check box and then choose the file you want to read from. OBS will update the data from that file on screen everytime it changes. 

I included X1CFront.png in the assets folder so you can have a visual representation of the printer on stream and use the temp.png as temperature frames for the different readings. 


## Data Gathering

For those interested you can run logMessage.py to get a log of EVERY message that passes through the printers MQTT broker. 
It will write every message to a file in the msgs directory and then use the parsejson.py script to parse every file in a directory and catalog ONLY the differences for each node. 
I used it to find the data that is logged to files today. 


