# SPDX-FileCopyrightText: 2021 ladyada for Adafruit Industries
# SPDX-License-Identifier: MIT

import time
import ssl
import socketpool
import board
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
import neopixel
import digitalio
import touchio

OFF = (0, 0, 0)
RED = (255, 0, 0)
WHITE = (50, 50, 50)
GREEN = (0, 255, 0)

# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

### Code ###

# Remove these two lines on boards without board.NEOPIXEL_POWER.
np_power = digitalio.DigitalInOut(board.NEOPIXEL_POWER)
np_power.switch_to_output(value=False)
np = neopixel.NeoPixel(board.NEOPIXEL, 1)
np_power.value = True
np[0] = RED

touch_A2 = touchio.TouchIn(board.A2) 
touch_A2.threshold = 20000

print("Connecting to %s" % secrets["ssid"])
wifi.radio.connect(secrets["ssid"], secrets["wifi_pw"])
print("Connected to %s!" % secrets["ssid"])
print("My IP address is", wifi.radio.ipv4_address)

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

is_touched = False

# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Connected to broker!")


def disconnected(client, userdata, rc):
    print("Disconnected from broker!")

# Set up a MiniMQTT Client
mqtt_client = MQTT.MQTT(
    broker=secrets["broker"],
    port=secrets["port"],
    username=secrets["user"],
    password=secrets["pw"],
    socket_pool=pool,
    ssl_context=ssl.create_default_context(),
)

# Setup the callback methods above
mqtt_client.on_connect = connected
mqtt_client.on_disconnect = disconnected

# Connect the client to the MQTT broker.
print("Connecting to MQTT broker...")
mqtt_client.connect()

np[0] = GREEN
time.sleep(1)
np[0] = OFF


while True:
    # Poll the message queue
    mqtt_client.loop()

    if touch_A2.value:
        print("touched!")
        np[0] = WHITE 
        
        # Send a new message
        print("Answering door...")
        mqtt_client.publish("doorbell", "open me")
        print("Sent!")

        time.sleep(2)
        np[0] = OFF
