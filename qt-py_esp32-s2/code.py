import supervisor
import gc
import time
import board
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_minimqtt.adafruit_minimqtt import MMQTTException

import digitalio
import touchio

# Add a secrets.py to your filesystem that has a dictionary called secrets with "ssid" and
# "password" keys with your WiFi credentials. DO NOT share that file or commit it into Git or other
# source control.
# pylint: disable=no-name-in-module,wrong-import-order
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise

# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)

### Code ###
touch_A2 = touchio.TouchIn(board.A2)
touch_A2.threshold = 30000
is_touched = False


def shutdown():
    client.disconnect()


def reconnect():
    print("Restarting...")
    network_connect()
    client.reconnect()


def network_connect():
    try:
        print("Connecting to %s" % secrets["ssid"])
        wifi.radio.connect(secrets["ssid"], secrets["wifi_pw"])
        print("Connected to %s!" % secrets["ssid"])
        print("My IP address is", wifi.radio.ipv4_address)
    except ConnectionError as e:
        print("Connection Error:", e)


# Define callback methods which are called when events occur
# pylint: disable=unused-argument, redefined-outer-name
def connected(client, userdata, flags, rc):
    # This function will be called when the client is connected
    # successfully to the broker.
    print("Connected to broker!")


def disconnected(client, userdata, rc):
    print("Disconnected from broker!")


def mqtt_connect():
    global client

    # Set up a MiniMQTT Client
    client = MQTT.MQTT(
        broker=secrets["broker"],
        port=secrets["port"],
        username=secrets["user"],
        password=secrets["pw"],
        client_id=secrets["client_id"],
        socket_pool=pool,
        ssl_context=ssl.create_default_context(),
        keep_alive=120,
    )

    # Setup the callback methods above
    client.on_connect = connected
    client.on_disconnect = disconnected

    # Connect the client to the MQTT broker.
    print("Connecting to MQTT broker...")
    client.connect()


last_ping = 0
ping_interval = 120

# start execution
try:
    print("Connecting WIFI")
    network_connect()
    print("Connecting MQTT")
    mqtt_connect()
except KeyboardInterrupt:
    shutdown()
except Exception:
    shutdown()
    raise

while True:
    try:
        #print("mem start loop:", gc.mem_free())
        if (time.time() - last_ping) > ping_interval:
            print("ping broker")
            client.ping()
            last_ping = time.time()

        # print(touch_A2.raw_value)
        if touch_A2.value:
            print(touch_A2.value)
            print("touched!")

            # Send a new message
            print("Answering door...")
            client.publish("doorbell", "open me")
            print("Sent!")
            time.sleep(2)

        # Poll the message queue
        client.loop()

        gc.collect()
    except KeyboardInterrupt:
        client.disconnect()
        break
    except (ValueError, OSError, RuntimeError, MMQTTException) as e:
        print("ValueError, OSError, RuntimeError, MMQTTException: Failed to get data,retrying\n", e)
        reconnect()
        continue
    except Exception as e:
        print("Failed to get data, retrying\n", e)
        reconnect()
        continue
