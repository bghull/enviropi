import asyncio

from atlas_i2c import atlas_i2c
from w1thermsensor import AsyncW1ThermSensor, Unit
import paho.mqtt.publish as publish

# TODO: split these into a proper config file
HOSTNAME = "192.168.1.104"
DS18B20 = {"id": "00000be11b73", "mqtt": "sensorpi/medium/T"}
EZO_PH = {"address": 99, "read_delay": 0.9, "mqtt": "sensorpi/medium/pH"}
EZO_EC = {"address": 100, "read_delay": 0.6, "mqtt": "sensorpi/medium/TDS"}
EZO_HUM = {"address": 111, "read_delay": 0.3, "mqtt": "sensorpi/air"}


def connect_ezo(sensor_cfg):
    sensor = atlas_i2c.AtlasI2C()
    sensor.set_i2c_address(sensor_cfg["address"])
    sensor.read_delay = sensor_cfg["read_delay"]
    sensor.mqtt = sensor_cfg["mqtt"]
    return sensor

def connect_onewire(sensor_cfg):
    try:
        sensor = AsyncW1ThermSensor(sensor_id=sensor_cfg["id"])
        sensor.mqtt = sensor_cfg["mqtt"]
        return sensor
    except Exception as exc:
        print(f"1W error: {exc}")
        return None

async def read_ezo(sensor):
    try:
        sensor.write("r")
        await asyncio.sleep(sensor.read_delay)
        response = sensor.read("r")
        if response.status_code == 1:
            data = response.data.decode("utf-8")
            publish.single(sensor.mqtt, payload=data, hostname=HOSTNAME)
    except Exception as err:
        print(f"Ezo error: {err}")

async def read_onewire(sensor):
    try:
        data = await sensor.get_temperature(Unit.DEGREES_F)
        publish.single(sensor.mqtt, payload=data, hostname=HOSTNAME)
    except Exception as err:
        print(f"Onewire error: {err}")

async def get_reading(sensor):
    if isinstance(sensor, atlas_i2c.AtlasI2C):
        try:
            sensor.write("r")
            await asyncio.sleep(sensor.read_delay)
            response = sensor.read("r")
            if response.status_code == 1:
                data = response.data.decode("utf-8")
        except OSError as err:
            print(f"OSError: {err}")
        except Exception as err:
            print(f"Other error: {err}")
    elif isinstance(sensor, AsyncW1ThermSensor):
        data = await sensor.get_temperature(Unit.DEGREES_F)
    publish.single(sensor.mqtt, payload=data, hostname=HOSTNAME)


async def main():
    ph = connect_ezo(EZO_PH)
    ec = connect_ezo(EZO_EC)
    hum = connect_ezo(EZO_HUM)
    ds18b20 = connect_onewire(DS18B20)
    tasks = [
        asyncio.create_task(read_ezo(ph)),
        asyncio.create_task(read_ezo(ec)),
        asyncio.create_task(read_ezo(hum)),
        asyncio.create_task(read_onewire(ds18b20)),
    ]
    await asyncio.gather(*tasks)


if __name__ == "__main__":
    import time

    start = time.time()
    asyncio.run(main())
    end = time.time()
    print(f"Execution time: {end-start}s")
