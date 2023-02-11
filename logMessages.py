import paho.mqtt.client as mqtt
import json
import os
import time
import subprocess
import ssl
from dotenv import load_dotenv

# This script connects to the MQ broker on the printer, subscribes to ALL topics, and then
# catalogs all messages for parsing with parsejson.py which will then parse all the files in each directory
# and create a diff file showing all the values used for each key in the messages.
# This is purely a tool to better understand all the communication via MQTT on the printer.

load_dotenv()

bambuIP = str(os.getenv("printerIP"))
bambuSerial = os.getenv("printerSerial")
printerName = os.getenv("printerName")
printerUser = os.getenv("printerUser")
printerPass = os.getenv("printerPass")
all_keys = set()
topics = {}

def wtfs(dpt, tdata):
    with open(dpt, "w") as f:
        f.write(tdata)
    return 0

def chkDir(dPath):
    if not os.path.exists(dPath):
        os.makedirs(dPath)
    return True

def on_connect(client, userdata, flags, rc):
    os.system('cls')
    print("Connected to " + printerName + " on IP " + bambuIP + " with result code "+str(rc))
    client.subscribe("#")

def on_message(client, userdata, msg):
    global last_message_time
    topic = msg.topic
    if time.time() - last_message_time >= 5:
        os.system('cls')
        print("Connected to " + printerName + " on IP " + bambuIP)
        elapsed_time = time.time() - start_time
        elapsed_time_str = time.strftime("%H:%M:%S", time.gmtime(elapsed_time))
        print(f"The process has been running for: {elapsed_time_str}")
        print(topics)
        print('--------------------------------------------------------------------------------------------')
        last_message_time = time.time()
    tstr = str(time.time())
    chkDir("./msgs/"+topic)
    data = json.loads(msg.payload.decode("utf-8"))
    if topic not in topics:
        topics[topic] = set(data.keys())
    else:
        topics[topic].update(data.keys())
    for tl in data.keys():
        tldir = "./msgs/" + topic + "/" + tl
        chkDir(tldir)
        wtfs(tldir + "/log." + tstr + ".json", msg.payload.decode("utf-8"))
        subpout = subprocess.Popen(['python', 'parsejson.py', tldir], stdout=subprocess.PIPE).communicate()[0]
        print(subpout.decode('utf-8').strip())
    with open("./msgs/topkeys.json", "w") as f:
        topics_dict = {topic: list(keys) for topic, keys in topics.items()}
        json.dump(topics_dict, f, indent=4)


start_time = time.time()
last_message_time = time.time()
client = mqtt.Client(userdata={"data": None})
client.tls_set(tls_version=ssl.PROTOCOL_TLS, ciphers=None, cert_reqs=ssl.CERT_NONE)
client.tls_insecure_set(True)
client.auto_reconnect = True
client.username_pw_set(printerUser, printerPass)
client.on_connect = on_connect
client.on_message = on_message
client.connect(bambuIP, port=8883, keepalive=60)
os.system('cls')
try:
    client.loop_forever()
except KeyboardInterrupt:
    print("Exiting due to keyboard interrupt.")
    client.disconnect()
