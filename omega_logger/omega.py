"""
Start logging a particular OMEGA iServer.
"""
import re
import sys
import logging
import traceback

from msl.equipment import Config

try:
    from validators import validator_map
except ModuleNotFoundError:
    pass

DEFAULT_WAIT = 60


class AliasFormatter(logging.Formatter):

    def __init__(self, fmt, alias):
        """Inserts the alias of the equipment record into a logging message."""
        super(AliasFormatter, self).__init__(fmt=fmt)
        self.alias = alias

    def format(self, rec):
        if self.alias and rec.levelno > logging.WARNING:
            rec.msg = f'[{self.alias}] {rec.msg}'
        return super(AliasFormatter, self).format(rec)


if __name__ == '__main__':
    try:
        path, serial = sys.argv[1:]
        cfg = Config(path)
        db = cfg.database()

        records = db.records(manufacturer='OMEGA', serial=serial, flags=re.IGNORECASE)
        if not records:
            raise ValueError(f'No equipment record exists for '
                             f'manufacturer=OMEGA and serial={serial}')
        if len(records) > 1:
            raise ValueError(f'Multiple equipment record exists for '
                             f'manufacturer=OMEGA and serial={serial}')

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
        for element in cfg.findall('msg_format'):
            if nprobes == int(element.attrib.get('nprobes', 1)):
                msg_format = element.text
                break

        validator_element = cfg.find('validator')
        if validator_element is None:
            validator = None
        else:
            name = validator_element.text
            kwargs = validator_element.attrib
            validator = validator_map[name](**kwargs)

        iserver.start_logging(
            cfg.value('log_dir'),
            wait=cfg.value('wait', DEFAULT_WAIT),
            nprobes=nprobes,
            nbytes=record.connection.properties.get('nbytes'),
            msg_format=msg_format,
            validator=None if validator is None else validator.validate,
        )

    except KeyboardInterrupt:
        pass
    except:
        traceback.print_exc(file=sys.stderr)
        input('Press <ENTER> to close ...')
