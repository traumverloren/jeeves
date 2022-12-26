#!/usr/bin/python

import secrets
import paho.mqtt.client as mqtt
import RPi.GPIO as GPIO
import time

# Set GPIO numbering mode
GPIO.setmode(GPIO.BOARD)

# Set pin 11 as an output, and set servo1 as pin 11 as PWM
GPIO.setup(11,GPIO.OUT)
servo = GPIO.PWM(11,50) # Note 11 is pin, 50 = 50Hz pulse

angle = 120

# Start PWM running, with value of 0 (pulse off)
servo.start(0)

def press_button():
    # Turn to 120 degrees
    servo.ChangeDutyCycle(2+(angle/18))
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)
    time.sleep(1)

    #turn back to 0 degrees
    print ("Turning back to 0 degrees")
    servo.ChangeDutyCycle(2)
    time.sleep(0.5)
    servo.ChangeDutyCycle(0)

def shutdown():
    #Clean things up at the end
    servo.stop()
    GPIO.cleanup()

# The callback for when the client receives a CONNACK response from the server.
def on_connect(client, userdata, flags, rc):
    print("Connected with result code "+str(rc))

    # Subscribing in on_connect() means that if we lose the connection and
    # reconnect then subscriptions will be renewed.
    client.subscribe("doorbell")

# The callback for when a PUBLISH message is received from the server.
def on_message(client, userdata, msg):
    print(msg.topic+" "+str(msg.payload))
    if msg.topic == "doorbell":
        press_button()

try:
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message
    client.username_pw_set(secrets.USERNAME, secrets.PASSWORD)
    client.connect(secrets.BROKER, 1883, 60)

    while True:
        client.loop_forever()
except KeyboardInterrupt:
    shutdown()
except Exception as e:
    raise
finally:
    print("shutting down")
    GPIO.cleanup()
