import paho.mqtt.client as mqtt
import json
import os
import math
import datetime
from dotenv import load_dotenv

load_dotenv()

bambuIP = str(os.getenv("printerIP"))
bambuSerial = os.getenv("printerSerial")
scenePath = os.getenv("scenePath").replace("\\","/")
printerName = os.getenv("printerName")
dPoints = ['bed_target_temper','bed_temper','chamber_temper','nozzle_target_temper','nozzle_temper','gcode_start_time','mc_percent','mc_remaining_time','spd_lvl','spd_mag','big_fan1_speed','big_fan2_speed','cooling_fan_speed']

if scenePath.endswith("/"):
    scenePath = scenePath[:-1]

def wtfs(dpt, tdata):
    dpath = scenePath + '/' + dpt + '.txt'
    with open(dpath, "w") as f:
        f.write(tdata)
    return 0

def rtnt(n):
    rounded = math.floor(n / 10) * 10
    if n - rounded >= 5:
        return rounded + 10
    else:
        return rounded

def on_connect(client, userdata, flags, rc):
    print("Connected to " + printerName + " on IP " + bambuIP + " with result code "+str(rc))
    print("Sending data to " + os.path.abspath(scenePath))
    client.subscribe("device/" + bambuSerial + "/report")

def on_message(client, userdata, msg):
    data = json.loads(msg.payload.decode("utf-8"))
    wtfs("BambuJsonDump.json", msg.payload.decode("utf-8"))
    if "print" in data:
        if "bed_temper" in data['print']:
            for setting in dPoints:
                if "fan" in setting:
                    fspd = rtnt(round((100/15)*int(data['print'][setting])))
                    tdata = str(fspd) + '%'
                    if "fan1" in setting:
                        wtfs("aux_fan_speed", tdata)
                    elif "fan2" in setting:
                        wtfs("chamber_fan_speed", tdata)
                    elif "fan_" in setting:
                        wtfs("part_cooling_fan_speed", tdata)
                elif "temper" in setting:
                    tc = setting[:-2]+'_c'
                    tf = setting[:-2] + '_f'
                    tcdata = str(int(data['print'][setting]))
                    tfdata = str(int((data['print'][setting] * 9/5) + 32))
                    wtfs(tc, tcdata)
                    wtfs(tf, tfdata)
                elif "start_" in setting:
                    date_time = datetime.datetime.fromtimestamp(int(data['print'][setting]))
                    date_time_str = date_time.strftime('%Y-%m-%d %H:%M:%S %Z')
                    end_time = date_time + datetime.timedelta(minutes=data['print']['mc_remaining_time'])
                    end_time_str = end_time.strftime('%Y-%m-%d %H:%M:%S %Z')
                    wtfs(setting, date_time_str)
                    wtfs('gcode_end_time_estimated', end_time_str)
                elif "remaining_" in setting:
                    minrem = data['print'][setting]
                    hours, remainder = divmod(minrem, 60)
                    tdata = "{}:{:02d} Remains".format(hours, remainder)
                    wtfs(setting, tdata)
                elif "_lvl" in setting:
                    if data['print'][setting] == 1:
                        tdata = "Silent"
                    elif data['print'][setting] == 2:
                        tdata = "Standard"
                    elif data['print'][setting] == 3:
                        tdata = "Sport"
                    elif data['print'][setting] == 4:
                        tdata = "Ludacris"
                    wtfs(setting, tdata)
                else:
                    tdata = str(data['print'][setting]) + '%'
                    if "_mag" in setting:
                        wtfs("spd_percent", tdata + ' Speed')
                    elif "mc_percent" in setting:
                        wtfs(setting, tdata + ' Complete')
                    else:
                        wtfs(setting, tdata)

client = mqtt.Client(userdata={"data": None})
client.on_connect = on_connect
client.on_message = on_message
client.connect(bambuIP, port=1883, keepalive=60)
client.loop_forever()

