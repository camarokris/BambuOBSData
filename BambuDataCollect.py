import paho.mqtt.client as mqtt
import json
import os
import math
import datetime
import time
import http.client
import sys
import ssl
from dotenv import load_dotenv

load_dotenv()

bambuIP = str(os.getenv("printerIP"))
bambuSerial = os.getenv("printerSerial")
scenePath = os.getenv("scenePath").replace("\\","/")
printerName = os.getenv("printerName")
printerUser = os.getenv("printerUser")
printerPass = os.getenv("printerPass")
sbConn = os.getenv("SBhost") + ':' + os.getenv("SBPort")
mainScene = os.getenv("mainScene")
brbScene = os.getenv("brbScene")
esai = os.getenv("endStreamActionID")
esan = os.getenv("endStreamActionName")
gsai = os.getenv("getSceneActionID")
gsan = os.getenv("getSceneActionName")
msai = os.getenv("mainSceneActionID")
msan = os.getenv("mainSceneActionName")
bsai = os.getenv("brbSceneActionID")
bsan = os.getenv("brbSceneActionName")
esTimeout = int(os.getenv("endStreamTimeout"))
dPoints = ['layer_num','total_layer_num','bed_target_temper','bed_temper','chamber_temper','nozzle_target_temper','nozzle_temper','gcode_start_time','mc_percent','mc_remaining_time','spd_lvl','spd_mag','big_fan1_speed','big_fan2_speed','cooling_fan_speed']

endTimeCheck = ""
brbSceneActive = False

if scenePath.endswith("/"):
    scenePath = scenePath[:-1]

# setup connection to streamer.bot to control stream
# this requires that the HTTP Server is running in streamer.bot
# for more information on streamer.bot and the server go to
# https://wiki.streamer.bot/en/Servers-Clients/HTTP-Server

headers = {
    'Content-Type': 'application/json',
    'Accept': 'application/json'
}

def sbDoAction(id, name):
    payload = {
        "action": {
            "id": id,
            "name": name
        }
    }
    conn = http.client.HTTPConnection(sbConn)
    conn.request("POST", "/DoAction", json.dumps(payload), headers)
    res = conn.getresponse()
    # According to the documentation /DoAction only responds with a 204 status code.
    # We will check for a 204 and if anything else is returned we will call it an error
    if res.status == 204:
        return "Success: Got a 204 response"
    else:
        return f"Error: Got {res.status} response"

def obsGetScene():
    sbDoAction(gsai, gsan)
    time.sleep(0.5)
    with open(scenePath + '/currentScene.txt') as f:
        curScene = f.read()
    os.remove(scenePath + '/currentScene.txt')
    return curScene

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
    global endTimeCheck
    global brbSceneActive
    data = json.loads(msg.payload.decode("utf-8"))
    wtfs("BambuJsonDump.json", msg.payload.decode("utf-8"))
    if "print" in data:
        if "bed_temper" in data['print']:
            # We are going to loop to the dPoints list of nodes and publish that data to the corresponding
            # files on the file system for OBS to pickup and use
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
                    date_time_str = date_time.strftime('%b-%d %I:%M %p %Z')
                    now = datetime.datetime.now()
                    end_time = now + datetime.timedelta(minutes=int(data['print']['mc_remaining_time']))
                    end_time_str = end_time.strftime('%b-%d %I:%M %p %Z')
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
                elif "layer" in setting:
                    tdata = str(data['print'][setting])
                    wtfs(setting, tdata)
                else:
                    tdata = str(data['print'][setting]) + '%'
                    if "_mag" in setting:
                        wtfs("spd_percent", tdata + ' Speed')
                    elif "mc_percent" in setting:
                        wtfs(setting, tdata + ' Complete')
                    else:
                        wtfs(setting, tdata)
            # If the print is finished and the nozzle has cooled below 50 I am going to end the stream
            # This requires Streamer.bot to be connected to OBS via OBS WebSockets and for an action
            # to have been created in Streamer.bot that tells OBS to end the stream.
            if data['print']['gcode_state'] == "FINISH" and data['print']['nozzle_temper'] < 50:
                # Lets check if we set a timestamp
                if not endTimeCheck:
                    # Timestamp was not set. setting for future loop usage
                    endTimeCheck = time.time()
                else:
                    current_time = time.time()
                    difference = current_time - endTimeCheck
                    # Check if 10 minutes (600 seconds) has passed. If it has we assume that you are not changing prints
                    # and ending the stream.
                    if difference > esTimeout:
                        print("Print finished, ending stream")
                        # I manually obtained the ID for the action by running a curl GET on the /GetActions uri of the server
                        if msai:
                            print(sbDoAction(esai, esan))
                        # Since we are no longer streaming we will exit the script
                        sys.exit()
                    else:
                        # Here we will change the scene to the BRB scene if it has not been done already so you can change
                        # prints.
                        if bsai:
                            if brbSceneActive == False:
                                print(sbDoAction(bsai, bsan))
                                brbSceneActive = True
            else:
                # We are going to set endTimeCheck to blank and brbSceneActive to False if the conditions are not met
                # to keep the check variables clean except when conditions are met. So if during the 10 min period
                # you start another print it will clear the vars and not end the stream. We will also check to see
                # if the current scene is the main printing scene and if it is not we will switch scenes.
                endTimeCheck = ""
                brbSceneActive = False
                if gsai:
                    if obsGetScene() == brbScene:
                        print(sbDoAction(msai, msan))

client = mqtt.Client(userdata={"data": None})
client.tls_set(tls_version=ssl.PROTOCOL_TLS, ciphers=None, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.auto_reconnect = True
client.username_pw_set(printerUser, printerPass)
client.on_connect = on_connect
client.on_message = on_message
client.connect(bambuIP, port=8883, keepalive=60)
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Exiting due to keyboard interrupt.")
    client.disconnect()
