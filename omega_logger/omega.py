"""
Start logging a particular OMEGA iServer.
"""
import re
import sys
import logging
import traceback

from msl.equipment import Config


class AliasFormatter(logging.Formatter):

    def __init__(self, fmt, alias):
        """Inserts the alias of the equipment record into a logging message."""
        super(AliasFormatter, self).__init__(fmt=fmt)
        self.alias = alias

    def format(self, record):
        if self.alias and record.levelno > logging.INFO:
            record.msg = '[{}] {}'.format(self.alias, record.msg)
        return super(AliasFormatter, self).format(record)


try:
    path, serial = sys.argv[1:]
    cfg = Config(path)
    db = cfg.database()

    records = db.records(manufacturer='OMEGA', serial=serial, flags=re.IGNORECASE)
    if not records:
        raise ValueError('No equipment record exists for '
                         'manufacturer=OMEGA and serial={}'.format(serial))

    record = records[0]

    hdlr = logging.StreamHandler(sys.stdout)
    formatter = AliasFormatter('%(asctime)s [%(levelname)-5s] %(message)s', record.alias)
    hdlr.setFormatter(formatter)
    logging.root.addHandler(hdlr)
    logging.root.setLevel(logging.INFO)

    iserver = None
    while iserver is None:
        try:
            iserver = record.connect()
        except:
            pass

    nprobes = record.connection.properties.get('nprobes', 1)

    msg_format = None
    elements = cfg.findall('msg_format')
    for element in elements:
        if nprobes == int(element.attrib.get('nprobes', 1)):
            msg_format = element.text
            break

    iserver.start_logging(
        cfg.value('log_dir'),
        wait=cfg.value('wait', 60),
        nprobes=nprobes,
        nbytes=record.connection.properties.get('nbytes'),
        msg_format=msg_format,
    )
except KeyboardInterrupt:
    pass
except:
    traceback.print_exc(file=sys.stderr)
    input('Press <ENTER> to close ...')
