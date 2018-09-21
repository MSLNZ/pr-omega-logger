"""
Start logging a particular OMEGA iServer.
"""
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
    omega = record.connect()
except:
    traceback.print_exc(file=sys.stdout)
    input('Press <ENTER> to close ...')
else:
    omega.start_logging(
        cfg.value('log_dir'),
        wait=60.0,
        num_probes=record.connection.properties.get('nprobes', 1),
    )
