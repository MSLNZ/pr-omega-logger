# /// script
# requires-python = ">=3.14"
# dependencies = [
#   "msl-equipment@git+https://github.com/MSLNZ/msl-equipment.git",
# ]
# ///
import logging
import sqlite3
import sys
import time
import traceback
from datetime import datetime

from msl.equipment import Connection

# Delta Ohm, HD5017PTC, V1.225-s0.22
connection = Connection("Modbus::10.12.102.67", timeout=5)

try:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-5s] %(message)s')

    logger = logging.getLogger(__name__)
    logging.getLogger().handlers[0].formatter.default_msec_format = '%s.%03d'

    alias = "Cryogenic Radiometer"
    db_timeout = 10
    wait = 60
    path = r"C:\Users\light\OMEGA\HD50_HD5017PTC.sqlite3"

    db = sqlite3.connect(path, timeout=db_timeout)
    _ = db.execute(
        'CREATE TABLE IF NOT EXISTS data ('
        'pid INTEGER PRIMARY KEY AUTOINCREMENT, '
        'datetime DATETIME, '
        'temperature FLOAT, '
        'humidity FLOAT, '
        'dewpoint FLOAT);'
    )
    db.commit()
    db.close()

    logger.info(f'start logging to {path}')
    while True:
        try:
            t0 = time.time()
            with connection.connect() as device:
                humidity = device.read_input_registers(2).int16() * 0.1
                dew_point = device.read_input_registers(4).int16() * 0.1
                temperature = device.read_input_registers(64).int16() * 0.1

            now = datetime.now().replace(microsecond=0).isoformat(sep='T')
            db = sqlite3.connect(path, timeout=db_timeout)
            db.execute('INSERT INTO data VALUES (NULL, ?, ?, ?, ?);', (now, temperature, humidity, dew_point))
            db.commit()
            db.close()
            logger.info(f'{alias!r} T={temperature:.2f}\u00b0C H={humidity:.2f}% D={dew_point:.2f}\u00b0C')
            time.sleep(max(0.0, wait - (time.time() - t0)))
        except KeyboardInterrupt:
            break
        except Exception as err:
            logger.error(f'Senseca {err}')
except:  # noqa: using bare 'except'
    traceback.print_exc(file=sys.stderr)
    input('Press <ENTER> to close ...')
