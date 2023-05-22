import alarm
import board
import time
import ssl
import socketpool
import wifi
import adafruit_minimqtt.adafruit_minimqtt as MQTT
from adafruit_minimqtt.adafruit_minimqtt import MMQTTException

# Must degrade to circuitpython 7.1.0 to use touchalarm

# Get wifi details and more from a secrets.py file
try:
    from secrets import secrets
except ImportError:
    print("WiFi secrets are kept in secrets.py, please add them there!")
    raise
    
# Create a socket pool
pool = socketpool.SocketPool(wifi.radio)


# Create an alarm that will trigger if pin is touched.
touch_alarm = alarm.touch.TouchAlarm(pin=board.A2)

# Print out which alarm woke us up, if any.
print(alarm.wake_alarm)

def network_connect():
    print("Connecting to %s"%secrets["ssid"])
    wifi.radio.connect(secrets["ssid"], secrets["wifi_pw"])
    print("Connected to %s!"%secrets["ssid"])
    print("My IP address is", wifi.radio.ipv4_address)

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
        keep_alive=60,
    )

    # Setup the callback methods above
    client.on_connect = connected
    client.on_disconnect = disconnected

    # Connect the client to the MQTT broker.
    print("Connecting to MQTT broker...")
    client.connect()

print("Connecting WIFI")
network_connect()
print("Connecting MQTT")
mqtt_connect()

# Send a new message
print("Answering door...")
if alarm.wake_alarm:
    client.publish("doorbell", "open me")
print("Sent!")
client.disconnect()
time.sleep(2)

# Exit the program, and then deep sleep until one of the alarms wakes us.
alarm.exit_and_deep_sleep_until_alarms(touch_alarm)
# Does not return, so we never get here.
