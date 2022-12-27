# Jeeves

A remote control for answering my building's doorbell.

<img src="https://user-images.githubusercontent.com/9959680/209721574-8dd10fd0-cae4-4840-8ed0-b17f029e811a.jpg" width="400" />
<img src="https://user-images.githubusercontent.com/9959680/209722515-7b1587a9-aeb9-4afe-b661-826bd59c348c.gif" width="400" />

Living in a flat in Berlin means that access into my building for deliveries/etc is through a main entry where first folks need to ring you through an intercom system to gain access to any of the apartments. A lot of times, this is disruptive for my workflow, my adhd, and my dog's anxiety to break my concentration by getting up to press the button for the building's door, then anxiously waiting the few minutes for the delivery person to knock on my _actual_ door since I feel incapable of sitting down and focusing again in this interim couple of minutes.

So, I decided to create a semi-automated + _soft electronics_ ✨ solution so I can unlock the building's front door from my desk.

When I hear the door buzzer, I can touch the pompom (which I've hidden a microcontroller inside and attached via conductive thread). This triggers the microcontroller inside to send a message over MQTT. The Pi Zero W is setup as both a MQTT broker (it receives messages & routes them to the clients subscribed to receive messages) and a MQTT client. The MQTT client running on the Pi is subscribed to messages published from the pompom. When the message is routed to this client from the broker, it triggers the servo to move and press the button. ✨

<img src="https://user-images.githubusercontent.com/9959680/209721698-8a0a2c11-41fd-4e58-8587-a01945da5d73.jpg" width="400" />
<img src="https://user-images.githubusercontent.com/9959680/209721576-eabd5d85-b4fe-4527-9847-78797531c121.jpg" width="400" />


## Materials

Note: many types of hardware/microcontrollers would be suitable for this application, I simply used what I already had available in my flat.

- [Pi Zero W](https://www.raspberrypi.com/products/raspberry-pi-zero-w/)
- [Adafruit QT PY ESP32-S2](https://www.adafruit.com/product/5325)
- Tower SG90 mini servo
- 3 M/F jumper cables
- [conductive thread](https://lightstitches.co.uk/product/conductive-thread-reel-250m/)
- yarn
- USB-C cable

## Pi Zero W Setup

The Pi Zero W serves as both MQTT broker and client. It assumes you have setup your pi already using the [pi imager](https://www.raspberrypi.com/software/).

### Setup MQTT Broker

For the broker, I'm using Mosquitto. I followed [this guide](https://randomnerdtutorials.com/how-to-install-mosquitto-broker-on-raspberry-pi/) and ran the following commands:

- Installation: `sudo apt install -y mosquitto mosquitto-clients`
- Make sure it runs on boot: `sudo systemctl enable mosquitto.service`
- Enable remote access with authorization:
  - `sudo mosquitto_passwd -c /etc/mosquitto/passwd YOUR_USERNAME`
  - Add additional usernames with `sudo mosquitto_passwd /etc/mosquitto/passwd OTHER_USERNAME`
  - Edit config file `sudo nano /etc/mosquitto/mosquitto.conf` and add the following lines:

      ```shell
      per_listener_settings true

      include_dir /etc/mosquitto/conf.d
      allow_anonymous false 
      listener 1883  
      password_file /etc/mosquitto/passwd
      ```

  - Restart mosquitto: `sudo systemctl restart mosquitto`
  - Get your broker's URL with `hostname -I` (necessary for setting up MQTT clients)
  - Test the broker setup by publishing a message by running the following from the terminal

    ```shell
    mosquitto_pub -t YOUR_TOPIC -m "YOUR MESSAGE -u USERNAME -P PASSWORD -d
    ```

    e.g.

    ```shell
    mosquitto_pub -t doorbell -m "ring ring buzz buzz" -u test -P test -d
    ```
    
    <img width="790" alt="Screen Shot 2022-12-27 at 9 13 41 PM" src="https://user-images.githubusercontent.com/9959680/209721816-11c22cbc-7c3d-4b83-9821-d27124eeed53.png">


### Setup MQTT client/servo code

The code for the client/servo is in [main.py](main.py)

- Install packages

    ```shell
    pip install RPi.GPIO
    pip install paho-mqtt
    ```

- Create `secrets.py` file and fill in with the info created in MQTT broker setup

   ```python
    USERNAME = 
    PASSWORD = 
    BROKER_URL =
   ```

- Setup the MQTT client to [run on boot](https://raspberrypi.stackexchange.com/questions/76804/trying-to-autorun-paho-mqtt-client-script-on-boot-up/95220#95220) with `systemd`
  - Create a file `/etc/systemd/system/mqttclient.service` with the contents:

    ```
    [Unit]
    Description=doorbell answerer
    After=network-online.target
    Wants=network-online.target
    After=mosquitto.service

    [Service]
    Type=simple
    User=pi
    ExecStart=/usr/bin/python /home/pi/jeeves/main.py
    Restart=on-failure
    RestartSec=5

    [Install]
    WantedBy=multi-user.target
    ```
  
  - Run `systemctl enable mqttclient`. This will cause your script to start next time the system boots (can trigger by running `sudo reboot`)
  - To start the service immediately, run `systemctl start mqttclient`.
  - Any output generated by the script will be collected by the system journal; you can view this by running `journalctl -u myqttclient.service`.
  - Or run `systemctl start mqttclient` to see if it's running or not.

## Adafruit QT PY ESP32-S2 Setup

The QT PY ESP32-S2 can be setup using Mu editor and circuitpython. Copy the [qt-py_esp32-s2/code.py](qt-py_esp32-s2/code.py) file to the QT Py and instal the necessary libraries. Pin A2 is used for capacitive touch.

- Create `secrets.py` file on the microcontroller

  ```python
  secrets = {
    'ssid' : 'your-ssid-here',
    'wifi_pw' : 'your-wifi-password-here',
    'user' : "your-client-username-here",
    'password': "your-client-pw-here",
    'broker': "your-broker-url-here",
    'port' : 1883
  }
  ```

## Braided USB-C cord + PomPom Assembly

- I used this [technique](https://www.studioknitsf.com/computer-cords-diy-yarn/) to wrap the cord with yarn.
- I used this [pompom maker](https://www.amazon.de/-/en/Clover-3129-Polypropylene-Stainless-Multi-Pack/dp/B07R187DT2/ref=sr_1_37?keywords=pompom+maker&qid=1672172901&sr=8-37) to wrap the yarn and conductive thread into a pompom and left the pompom tied a little looser so that i could insert the microcontroller into the center.
- I found that I needed to wrap the other pins with electrical tape to prevent the capacitive touch from being overactive even when I was not touch the pompom.
