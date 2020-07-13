# Before doing anything else need to set this environment variable to tell
# CircuitPython which board is present.
import os
os.environ["BLINKA_MCP2221"] = "1"

import os.path
import board
import busio
import adafruit_shtc3

import numpy as np
from astropy import units as u


# Can only be one instance of I2C bus with given pins so create it at module level
i2c = busio.I2C(board.SCL, board.SDA)


class DS18B20():

    def __init__(self, device_id):
        self._device_id = device_id
        self._path = os.path.join("/sys/bus/w1/devices", self._device_id, "w1_slave")
        if not os.path.exists(self._path):
            msg = f"No DS18B20 temperature sensor found at {self._path}, check device_id."
            raise ValueError(msg)

    @property
    def device_id(self):
        return self._device_id

    @property
    def temperature(self):
        with open(self._path) as virtual_file:
            raw_data = virtual_file.read()
        _, _, string_temp = raw_data.rpartition('=')
        return float(string_temp) * u.Celsius / 1000


class SHTC3():

    b = 18.678
    c = 257.14 * u.Celsius
    d = 234.5 * u.Celsius

    def __init__(self):
        self._shtc3 = adafruit_shtc3.SHTC3(i2c)

    @property
    def temperature(self):
        return self._shtc3.temperature * u.Celsius

    @property
    def humidity(self):
        return self._shtc3.relative_humidity * u.percent

    @property
    def measurements(self):
        temperature, humidity = self._shtc3.measurements
        temperature = temperature * u.Celsius
        humidity = humidity * u.percent
        dew_point = self._dew_point(temperature, humidity)
        return temperature, humidity, dew_point

    @property
    def dew_point(self):
        temperature, humidity = self._shtc3.measurements
        temperature = temperature * u.Celsius
        humidity = humidity * u.percent
        return self._dew_point(temperature, humidity)

    def _dew_point(self, temperature, humidity):
        gamma_m = self._gamma_m(temperature, humidity)
        return self.c * gamma_m / (self.b - gamma_m)

    def _gamma_m(self, temperature, humidity):
        h = humidity / (100 * u.percent)
        t = (self.b - (temperature / self.d)) * (temperature / (self.c + temperature))
        return np.log(h * np.exp(t))
