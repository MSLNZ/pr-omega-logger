"""
Start logging the Vaisala HMP110 sensor.
"""
import logging
import os
import re
import sqlite3
import sys
import time
import traceback
from datetime import datetime

import requests
from msl.equipment import Config

from omega_logger import DEFAULT_WAIT

try:
    logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)-5s] %(message)s')

    logger = logging.getLogger(__name__)
    logging.getLogger().handlers[0].formatter.default_msec_format = '%s.%03d'

    db_timeout = 10

    cfg = Config(sys.argv[1])
    vaisala = cfg.find(r'calibrations/vaisala')
    serial = vaisala.attrib['serial']

    db = cfg.database()
    records = db.records(manufacturer='Vaisala', serial=serial, flags=re.IGNORECASE)
    if not records:
        raise ValueError(f'No equipment record exists for '
                         f'manufacturer=Vaisala and serial={serial}')
    if len(records) > 1:
        raise ValueError(f'Multiple equipment record exists for '
                         f'manufacturer=Vaisala and serial={serial}')

    record = records[0]
    alias = record.alias
    url = record.connection.address
    timeout = record.connection.properties.get('timeout', 10)
    wait = cfg.value('wait', DEFAULT_WAIT)

    filename = f'{record.model}_{record.serial}.sqlite3'
    path = os.path.join(cfg.value('log_dir'), filename)

    db = sqlite3.connect(path, timeout=db_timeout)
    db.execute(
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
            reply = requests.get(url, timeout=timeout)
            reply.raise_for_status()
            json = reply.json()
            if json['error']:
                logger.error(f'{alias!r} Cannot read the modbus holding registers')
            else:
                now = datetime.now().replace(microsecond=0).isoformat(sep='T')
                t, h, d = json['temperature'], json['relative_humidity'], json['dewpoint']
                db = sqlite3.connect(path, timeout=db_timeout)
                db.execute('INSERT INTO data VALUES (NULL, ?, ?, ?, ?);', (now, t, h, d))
                db.commit()
                db.close()
                logger.info(f'{alias!r} T={t:.2f}\u00b0C H={h:.2f}% D={d:.2f}\u00b0C')
            time.sleep(max(0.0, wait - (time.time() - t0)))
        except KeyboardInterrupt:
            break
        except requests.RequestException as err:
            logger.error(f'{alias!r} {err}')
except:  # noqa: using bare 'except'
    traceback.print_exc(file=sys.stderr)
    input('Press <ENTER> to close ...')
