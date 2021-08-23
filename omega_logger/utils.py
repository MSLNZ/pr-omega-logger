import os
import re
import sqlite3
from math import log, floor
from time import perf_counter
from datetime import datetime, timedelta

import numpy as np
import dash_html_components as html
from msl.equipment.resources.omega.ithx import iTHX


def datetime_range_picker_kwargs(cfg):
    """Parse the configuration file for the DatetimeRangerPicker kwargs.

    Parameters
    ----------
    cfg : :class:`msl.equipment.config.Config`
        The configuration-file object.

    Returns
    -------
    :class:`dict`
        The keyword arguments.
    """
    kwargs = dict()
    datetime_range_picker = cfg.find('datetime_range_picker')
    if not datetime_range_picker:
        return kwargs

    for element in datetime_range_picker:
        text = element.text.strip()
        if text:
            kwargs[element.tag] = text
        else:
            kwargs[element.tag] = dict()
            for sub_element in element:
                kwargs[element.tag][sub_element.tag] = sub_element.text

    today = datetime.today()
    for key in ['start', 'end', 'max_date', 'min_date']:
        if key in kwargs:
            value = kwargs[key]
            dt = timedelta(
                weeks=int(value.get('weeks', 0)),
                days=int(value.get('days', 0))
            )
            new_date = today + dt
            kwargs[key] = new_date.replace(
                hour=int(value.get('hour', 0)),
                minute=int(value.get('minute', 0)),
                second=int(value.get('second', 0))
            )

    return kwargs


def human_file_size(size):
    """Return the human-readable size of a file.

    For example, 123456789 becomes '123 MB'.

    Parameters
    ----------
    size : :class:`int`
        The file size.

    Returns
    -------
    :class:`str`
        The file size that is human readable.
    """
    thresh = 1000.  # use 1024 instead?
    n = floor(log(size) / log(thresh)) if size > 0 else 0
    prefix = size / (thresh ** n)
    suffix = ['B', 'kB', 'MB', 'GB', 'TB'][n]
    return f'{prefix:.0f} {suffix}'


def fromisoformat(date_string):
    """Construct a datetime object from an ISO 8601 string.

    Parameters
    ----------
    date_string : :class:`str`
        The string representation of the date and time.

    Returns
    -------
    :class:`datetime.datetime`
        The datetime object.
    """
    try:
        # datetime.fromisoformat is available in Python 3.7+
        return datetime.fromisoformat(date_string)
    except AttributeError:
        dstr = date_string[0:10]
        tstr = date_string[11:]
        date = datetime.strptime(dstr, '%Y-%m-%d')
        if not tstr:
            return date

        # Parses times of the form HH[:MM[:SS]]
        hour, minute, second = 0, 0, 0
        time_split = tuple(map(int, tstr.split(':')))
        if len(time_split) == 1:
            hour = time_split[0]
        elif len(time_split) == 2:
            hour, minute = time_split
        elif len(time_split) == 3:
            hour, minute, second = time_split

        return datetime(date.year, month=date.month, day=date.day,
                        hour=hour, minute=minute, second=second)


def initialize_webapp(cfg, serials):
    """Initialize the web application.

    Parameters
    ----------
    cfg : :class:`msl.equipment.config.Config`
        The configuration-file object.
    serials : :class:`str`
        A comma-separated string of OMEGA serial numbers to log.

    Returns
    -------
    :class:`list`
        The dropdown options.
    :class:`dict`
        The keys are the labels and the values are :class:`.CalibrationReport`\\s.
    :class:`dict`
        The keys are the serial numbers and the values are the
        :class:`msl.equipment.record_types.EquipmentRecord`\\s
        of the OMEGA iServer's.
    """
    dropdown_options = list()
    calibrations = dict()
    omegas = dict()

    serials = serials.split(',')
    log_dir = cfg.value('log_dir')
    cal_elements = cfg.find('calibrations') or []
    records = cfg.database().records(manufacturer='OMEGA')
    for record in sorted(records, key=lambda r: r.alias):
        if record.serial not in serials:
            continue
        dbase_file = os.path.join(log_dir, record.model + '_' + record.serial + '.sqlite3')
        for element in cal_elements:
            if element.attrib.get('serial') == record.serial:
                reports = [CalibrationReport(record.serial, dbase_file, report)
                           for report in element.findall('report')]
                components = sorted(set(r.component for r in reports))
                for component in components:
                    label = record.alias
                    if ';' in label:
                        # a semi-colon is reserved for requesting multiple
                        # iServers in a URL query parameter
                        raise ValueError(f'The alias {label!r} cannot contain a semi-colon')
                    if component:
                        label += f' - {component}'
                        calibrations[label] = [r for r in reports if r.component == component]
                    else:
                        calibrations[label] = reports
                    dropdown_options.append({
                        'label': label,
                        'value': label,
                    })
                    omegas[record.serial] = record

    return dropdown_options, calibrations, omegas


class CalibrationReport(object):

    def __init__(self, serial, dbase_file, report):
        """Create a calibration record.

        Parameters
        ----------
        serial : :class:`str`
            The serial number of an OMEGA iServer.
        dbase_file : :class:`str`
            The path to the database file.
        report : :class:`xml.etree.Element`
            An element from the configuration file.
        """
        self.serial = serial
        self.dbase_file = dbase_file
        self.component = report.attrib.get('component', '')
        if self.component:
            self.probe = re.search(r'(\d)', self.component).group(0)
        else:
            self.probe = ''
        self.date = fromisoformat(report.attrib['date'])
        self.number = report.attrib['number']
        self.start_date = fromisoformat(report.find('start_date').text)
        self.end_date = fromisoformat(report.find('end_date').text)
        self.coverage_factor = float(report.find('coverage_factor').text)
        self.confidence = report.find('confidence').text
        for name in ['temperature', 'humidity']:
            e = report.find(name)
            d = {
                'units': e.attrib['units'],
                'min': float(e.attrib['min']),
                'max': float(e.attrib['max']),
                'coefficients': [
                    float(val) for val in re.split(r'[;,]', e.find('coefficients').text)
                ],
                'expanded_uncertainty': float(e.find('expanded_uncertainty').text),
            }
            setattr(self, name, d)


class HTMLTable(object):

    def __init__(self):
        """Create the HTML table for the webapp."""
        self._table = [
            html.Tr([
                html.Th('OMEGA logger'),
                html.Th('Report No.'),
                html.Th('Description'),
                html.Th('Average'),
                html.Th('Stdev'),
                html.Th('Median'),
                html.Th('Max'),
                html.Th('Min'),
                html.Th('# Points')]
            )]

    def append(self, data, report, label):
        """Append a row to the table.

        Parameters
        ----------
        data : :class:`numpy.ndarray`
            The data.
        report : :class:`.CalibrationReport`
            The report.
        label : :class:`str`
            The label to insert in the first column of the table.
        """
        tab = data.dtype.names[1]
        values = data[tab]
        report_number = '<uncorrected>' if tab == 'dewpoint' else report.number
        nrows = len(self._table)
        if values.size > 0:

            # if the max or min values are outside of the range that was used
            # in the calibration report then change the colour of the row
            style, mx, mn = None, np.max(values), np.min(values)
            if tab != 'dewpoint':
                r = getattr(report, tab)
                if mx > r['max'] or mn < r['min']:
                    style = dict(backgroundColor='#FF0000')

            self._table.append(
                html.Tr([
                    html.Td(label, style=style),
                    html.Td(report_number, style=style),
                    html.Td(tab.title() if not style else tab.title() + ' [value out of range]', style=style),
                    html.Td(f'{np.average(values):.1f}', style=style),
                    html.Td(f'{np.std(values):.1f}', style=style),
                    html.Td(f'{np.median(values):.1f}', style=style),
                    html.Td(f'{mx:.1f}', style=style),
                    html.Td(f'{mn:.1f}', style=style),
                    html.Td(f'{values.size}', style=style),
                ], style=dict(backgroundColor='#F2F2F2' if nrows % 2 else '#FFFFFF'))
            )
        else:
            self._table.append(
                html.Tr([
                    html.Td(label),
                    html.Td(report_number),
                    html.Td(tab.title()),
                    html.Td(''),
                    html.Td(''),
                    html.Td(''),
                    html.Td(''),
                    html.Td(''),
                    html.Td('0'),
                ], style=dict(backgroundColor='#F2F2F2' if nrows % 2 else '#FFFFFF'))
            )

    def get(self):
        """Returns the HTML table."""
        return self._table


def find_reports(calibrations, serial, nearest=None):
    """Find all calibration reports for the OMEGA devices
    with a particular serial number that are closest to a
    specified date.

    Parameters
    ----------
    calibrations : :class:`dict`
        All :class:`.CalibrationReport`\\s.
    serial : :class:`str`
        The serial number of the OMEGA iServer to find.
    nearest : :class:`str` or :class:`datetime.datetime`, optional
        The date to compare each report to. If not specified then
        uses the current time. If a string then in the ISO 8601
        format.

    Returns
    -------
    :class:`list` of :class:`.CalibrationReport`
        The calibration reports.
    """
    return [find_report(reports, nearest=nearest)
            for reports in calibrations.values()
            if reports and reports[0].serial == serial]


def find_report(reports, nearest=None):
    """Find the report that is nearest to the specified date.

    Parameters
    ----------
    reports : :class:`list` of :class:`.CalibrationReport`
        The calibrations reports.
    nearest : :class:`str` or :class:`datetime.datetime`, optional
        The date to compare each report to. If not specified then
        uses the current time. If a string then in the ISO 8601
        format.

    Returns
    -------
    :class:`.CalibrationReport`
        The calibration report.
    """
    if nearest is None:
        nearest = datetime.now()
    elif isinstance(nearest, str):
        nearest = fromisoformat(nearest)
    deltas = [abs(nearest - r.start_date) for r in reports]
    return reports[deltas.index(min(deltas))]


def read_database(report, typ, date1=None, date2=None, label=''):
    """Read data from a database.

    Parameters
    ----------
    report : :class:`.CalibrationReport`
        The calibration report.
    typ : :class:`str`
        The type of data to retrieve (one of temperature, humidity, dewpoint).
    date1 : :class:`datetime.datetime` or :class:`str`, optional
        Include all records that have a timestamp > `date1`. If :class:`str` then in
        ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` format.
    date2 : :class:`datetime.datetime` or :class:`str`, optional
        Include all records that have a timestamp < `date2`. If :class:`str` then in
        ``yyyy-mm-dd`` or ``yyyy-mm-dd HH:MM:SS`` format.
    label : :class:`str`, optional
        The value is used to construct the message that is returned. If you do not
        care about the returned message then you can ignore this argument.

    Returns
    -------
    :class:`numpy.ndarray`
        The data from the database.
    :class:`str`
        A message that describes how many records were fetch, what field was selected
        from the database and how long the process took.
    """
    select = ('timestamp', typ + report.probe)
    t0 = perf_counter()
    values = iTHX.data(report.dbase_file, date1=date1, date2=date2, as_datetime=False, select=select)
    dt = perf_counter() - t0
    data = np.asarray(values, dtype=[('timestamp', 'U19'), (typ, float)])
    message = f'Fetched {data.size} {select[1]!r} records for {label!r} in {dt:.3f} seconds'
    return data, message


def apply_calibration(data, report):
    """Apply the calibration equation to the data.

    Parameters
    ----------
    data : :class:`dict` or :class:`numpy.ndarray`
        The data to apply the calibration to.
    report : :class:`.CalibrationReport`
        The calibration report that contains the calibration equation.

    Returns
    -------
    :class:`dict` or :class:`numpy.ndarray`
        The data with the calibration applied.
    """
    def apply(array, t_or_h):
        coefficients = getattr(report, t_or_h)['coefficients']
        x = array[t_or_h]
        dx = np.full(x.size, coefficients[0])
        for n, c in enumerate(coefficients[1:], start=1):
            dx += c * (x ** n)
        x += dx
        return array

    if isinstance(data, dict):
        for key, value in data.items():
            if key == 'error' and value is not None:
                return data
            if report.component and (report.component[-1] != key[-1]):
                continue
            typ = key.rstrip('12')
            if typ == 'temperature' or typ == 'humidity':
                arr = np.array([value], dtype=[(typ, float)])
                data[key] = apply(arr, typ)[0][0]
    else:
        name = data.dtype.names[1]
        if name == 'dewpoint':
            return data
        data = apply(data, name)

    return data


def database_info(log_dir, omegas):
    """Get the information about all databases.

    Parameters
    ----------
    log_dir : :class:`str`
        The directory where the databases are located.
    omegas : :class:`dict`
        The keys are the serial numbers and the values are the
        :class:`msl.equipment.record_types.EquipmentRecord`\\s
        of the OMEGA iServer's.

    Returns
    -------
    :class:`dict`
        The information about all databases.
    """
    info = {}
    _regex = re.compile(r'_(?P<serial>\d+).sqlite3$')
    for filename in os.listdir(log_dir):
        match = _regex.search(filename)
        if not match:
            continue
        file = os.path.join(log_dir, filename)
        with sqlite3.connect(file) as db:
            cursor = db.cursor()
            cursor.execute("PRAGMA table_info('data');")
            fields = [f[1] for f in cursor.fetchall()]
            cursor.execute('SELECT MIN(timestamp),MAX(timestamp),COUNT(timestamp) FROM data;')
            min_date, max_date, count = cursor.fetchone()
            info[match['serial']] = {
                'alias': omegas[match['serial']].alias,
                'fields': fields,
                'file_size': human_file_size(os.stat(file).st_size),
                'max_date': max_date,
                'min_date': min_date,
                'num_records': count,
            }

    return info
