import os

tg_token : str = os.getenv('TG_TOKEN') # type: ignore
ha_token : str = os.getenv('HA_TOKEN') # type: ignore

HOST = 'http://192.168.1.89:8123'