#!/usr/bin/env python

import sys
import json
import time
import serial

try:
    import mosquitto
except ImportError:
    import paho.mqtt.client as mosquitto

class MQTTClient(mosquitto.Mosquitto):
    def publish_utf8(self, topic, payload, *args, **kwargs):
        if isinstance(topic, unicode):
            topic = topic.encode('utf8', 'ignore')
        if isinstance(payload, unicode):
            payload = payload.encode('utf8', 'ignore')

        self.publish(topic, payload, *args, **kwargs)


class TMHZ19(object):
    REQ_READ_CONCENTRATION = "\xFF\x01\x86\x00\x00\x00\x00\x00\x79"

    class TCommunicationError(Exception):
        pass

    def __init__(self, port, timeout = 1):
        self.port = port
        self.timeout = timeout
        self.ser = serial.Serial(port, baudrate = 9600, timeout = self.timeout)

    def send_request(self, request):
        try:
            self.ser.write(request)
        except serial.SerialTimeoutException:
            raise self.TCommunicationError("timeout while sending request")

    def read_concentration(self):
        self.send_request(self.REQ_READ_CONCENTRATION)
        payload = self.read_response()
        return payload[1] * 256 + payload[2]

    def read_response(self):
        resp_len = 9
        resp = self.ser.read(resp_len)
        if len(resp) != resp_len:
            raise self.TCommunicationError("expected %d bytes, got %d" % (resp_len, len(resp)))

        payload = [ord(x) for x in resp[1:-1]]
        crc16 =((sum(payload) % 256) ^ 0xFF) + 1
        if crc16 != ord(resp[-1]):
            raise self.TCommunicationError("checksum error")

        return payload



class TMQTTMHZ19Sensor(object):
    def init_config(self, fname):
        self.config = json.load(open(fname))

        self.config.setdefault('mqtt_id', 'mh-z19')
        self.config.setdefault('name', 'MHZ19 sensor')
        self.config.setdefault('debug', False)
        self.config.setdefault('port', '/dev/ttyAPP2')
        self.config.setdefault('poll_interval', 10)
        if self.config['poll_interval'] < 6:
            raise RuntimeError("poll interval cannot be smaller than 6 seconds")

    def init_sensor(self):
        self.mhz19 = TMHZ19(self.config['port'])

    def init_mqtt(self):
        self.mqtt_client = MQTTClient()
        self.mqtt_client.connect('localhost')
        self.mqtt_client.loop_start()

        self.mqtt_client.publish_utf8("/devices/%s/meta/name" % self.config['mqtt_id'], self.config['name'], qos=1, retain=True)

        self.mqtt_client.publish_utf8("/devices/%s/controls/%s/meta/type" %
                                      (self.config['mqtt_id'], "co2"), "concentration", qos=1, retain=True)


    def set_channel_error(self, control_id, error):
        if self.error_cache.get(control_id) != error:
            self.mqtt_client.publish("/devices/%s/controls/%s/meta/error" %
                                     (self.config['mqtt_id'], control_id), error, qos=1, retain=1)
        self.error_cache[control_id] = error

    def publish_channel(self, control_id, value, decimal_places=1):
        self.set_channel_error(control_id, "")
        format = "%%.%df" % decimal_places
        value_str = format % value
        self.mqtt_client.publish_utf8("/devices/%s/controls/%s" %
                                      (self.config['mqtt_id'], control_id), value_str, qos=1, retain=True)

    def __init__(self, fname):
        self.fname = fname
        self.error_cache = {}

    def start(self):
        self.init_config(self.fname)
        self.init_sensor()
        self.init_mqtt()

        while True:
            try:
                co2_ppm = self.mhz19.read_concentration()
            except TMHZ19.TCommunicationError:
                self.set_channel_error('co2', "r")
            else:
                self.publish_channel('co2', co2_ppm)

            time.sleep(self.config['poll_interval'])

        return 0


def main():
    if len(sys.argv) != 2:
        print >>sys.stderr, "USAGE: %s <config file>"
        return 1

    sensor = TMQTTMHZ19Sensor(sys.argv[1])
    sensor.start()

    return 0


if __name__ == '__main__':
    main()
