"""
Start logging a particular OMEGA iServer.
"""
import os
import sys
import logging
import traceback

from msl.equipment import Config

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)-5s] %(message)s',
)

try:
    cfg = Config(sys.argv[1])
    record = cfg.database().records(manufacturer='OMEGA', serial=sys.argv[2])[0]

    iserver = None
    while iserver is None:
        try:
            iserver = record.connect()
        except:
            pass

    iserver.start_logging(
        cfg.value('log_dir'),
        wait=60.0,
        nprobes=record.connection.properties.get('nprobes', 1),
    )
except KeyboardInterrupt:
    pass
except:
    traceback.print_exc(file=sys.stdout)
    input('Press <ENTER> to close ...')
