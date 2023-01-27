import os
import socket
import sys
import threading
from math import isnan
from subprocess import PIPE
from subprocess import Popen
from subprocess import check_output

import pytest
import requests

proc = None

# the expected corrected values
temperature = 21.0 + 0.07
humidity = 41.0 + (-5.11 + 2.44e-2 * 41.0 + 5.39e-4 * (41.0 ** 2))
temperature1 = 21.0 + (0.002 + 0.32 * 21.0)
humidity1 = 41.0 + (-8.3 + 1.23 * 41.0 + 3.56e-3 * (41.0 ** 2))
temperature2 = 22.0 + (0.1 + 0.06 * 22.0 + 0.01 * (22.0 ** 2) + 2.3e-4 * (22.0 ** 3))
humidity2 = 42.0 + (4.2 + 0.931 * 42.0 + 0.00482 * (42.0 ** 2))


def on_new_client(client_socket, client_address):
    while True:
        data = client_socket.recv(32)
        if not data:
            break

        d = data.decode().rstrip()
        if d == '*SRTC':  # temperature probe 1
            client_socket.sendall(b'021.0\r')
        elif d == '*SRTC2':  # temperature probe 2
            client_socket.sendall(b'022.0\r')
        elif d == '*SRH':  # humidity probe 1
            client_socket.sendall(b'041.0\r')
        elif d == '*SRH2':  # humidity probe 2
            client_socket.sendall(b'042.0\r')
        elif d in ['*SRD', '*SRDC']:  # dewpoint probe 1
            client_socket.sendall(b'011.0\r')
        elif d == '*SRDC2':  # dewpoint probe 2
            client_socket.sendall(b'012.0\r')
        elif d == '*SRB':  # temperature and humidity (not valid for 2 probe devices)
            client_socket.sendall(b'021.0\r,041.0\r')
        else:
            client_socket.sendall(b'unhandled request\r')
            break
    client_socket.close()


def simulate_omega_iserver():
    clients = []
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 1876))
        s.listen(5)
        while True:
            t = threading.Thread(target=on_new_client, args=s.accept(), daemon=True)
            t.start()
            clients.append(t)


def setup_module():
    global proc

    # start the OMEGA simulator
    thread = threading.Thread(target=simulate_omega_iserver, daemon=True)
    thread.start()

    # start the webapp
    cwd = os.path.join(os.path.dirname(__file__), os.pardir, 'omega_logger')
    cfg = os.path.join(os.path.dirname(__file__), 'resources', 'config.xml')
    cmd = [sys.executable, '-m', 'webapp', cfg, '01234,56789,abcde,fghij']
    proc = Popen(cmd, stderr=PIPE, cwd=cwd)

    # wait for the webapp and the OMEGA simulator to start
    while True:
        out = check_output(['netstat', '-an'])
        if out.find(b':1875 ') > 0 and out.find(b':1876 ') > 0:
            break


def teardown_module():
    if proc is not None:
        proc.terminate()


def get(route, params=None):
    if route.startswith('/fetch'):
        # in version 0.4, the default start time for the /fetch route change from
        # "the beginning" to "1 hour ago", so specify a start time that is older than
        # the oldest timestamp in the testing databases
        if params is None:
            params = {}
        if isinstance(params, dict) and 'start' not in params:
            params['start'] = '2015-01-01'
    return requests.get('http://127.0.0.1:1875' + route, params=params, timeout=10)


@pytest.mark.parametrize('route', ['/fetch', '/fetch/'])
def test_fetch(route):
    json = get(route).json()
    assert len(json) == 4
    assert '01234' in json
    assert '56789' in json
    assert 'abcde' in json
    assert 'fghij' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2015-01-01T00:00:00'
    assert json['01234']['report_number'] == 'H502'

    assert json['01234']['temperature'][0] == ['2015-01-01T20:29:27', 18.57]
    assert json['01234']['humidity'][0] == ['2015-01-01T20:29:27', 67.26109836]
    assert json['01234']['dewpoint'][0] == ['2015-01-01T20:29:27', 12.5]

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2015-01-01T00:00:00'
    assert json['56789']['report_number'] == 'H842;H389'

    assert json['56789']['temperature1'][0] == ['2015-01-01T23:56:47', 20.198]
    assert json['56789']['humidity1'][0] == ['2015-01-01T23:56:47', 182.0197076]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01T23:56:47', 11.1]

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['start'] == '2015-01-01T00:00:00'
    assert json['abcde']['report_number'] == '<uncalibrated>'

    assert json['abcde']['temperature'][0][0] == '2022-07-31T08:12:00'
    assert json['abcde']['humidity'][0][0] == '2022-07-31T08:12:00'
    for item in ('temperature', 'humidity'):
        for _, value in json['abcde'][item]:
            assert isnan(value)
    assert json['abcde']['dewpoint'] == [
        ['2022-07-31T08:12:00', 8.6],
        ['2022-07-31T08:13:00', 8.5],
        ['2022-07-31T08:14:00', 8.5],
        ['2022-07-31T08:15:00', 8.6]
    ]

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['start'] == '2015-01-01T00:00:00'
    assert json['fghij']['report_number'] == '<uncalibrated>;<uncalibrated>'

    assert json['fghij']['temperature1'][0][0] == '2022-07-31T08:12:00'
    assert json['fghij']['humidity1'][0][0] == '2022-07-31T08:12:00'
    assert json['fghij']['temperature2'][0][0] == '2022-07-31T08:12:00'
    assert json['fghij']['humidity2'][0][0] == '2022-07-31T08:12:00'
    for item in ('temperature1', 'temperature2', 'humidity1', 'humidity2'):
        for _, value in json['fghij'][item]:
            assert isnan(value)
    assert json['fghij']['dewpoint1'] == [
        ['2022-07-31T08:12:00', 8.6],
        ['2022-07-31T08:13:00', 8.5],
        ['2022-07-31T08:14:00', 8.5],
        ['2022-07-31T08:15:00', 8.6]
    ]
    assert json['fghij']['dewpoint2'] == [
        ['2022-07-31T08:12:00', 8.5],
        ['2022-07-31T08:13:00', 8.6],
        ['2022-07-31T08:14:00', 8.6],
        ['2022-07-31T08:15:00', 8.5]
    ]


def test_fetch_invalid_params():
    response = get('/fetch?woofwoof')
    assert response.status_code == 400
    assert response.text == "Invalid parameter(s): woofwoof<br/>" \
                            "Valid parameters are: alias, corrected, end, serial, start, type"

    response = get('/fetch', params='woofwoof')
    assert response.status_code == 400
    assert response.text == "Invalid parameter(s): woofwoof<br/>" \
                            "Valid parameters are: alias, corrected, end, serial, start, type"

    response = get('/fetch', params={'ball': 'yellow', 'play': 'fetch'})
    assert response.status_code == 400
    assert response.text == "Invalid parameter(s): ball, play<br/>" \
                            "Valid parameters are: alias, corrected, end, serial, start, type"


@pytest.mark.parametrize('corrected', ['1', 'true', 'True', 1, True])
def test_fetch_corrected(corrected):
    json = get('/fetch', params={'corrected': corrected}).json()
    assert len(json) == 4
    assert '01234' in json
    assert '56789' in json
    assert 'abcde' in json
    assert 'fghij' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2015-01-01T00:00:00'
    assert json['01234']['report_number'] == 'H502'

    assert json['01234']['temperature'][0] == ['2015-01-01T20:29:27', 18.57]
    assert json['01234']['humidity'][0] == ['2015-01-01T20:29:27', 67.26109836]
    assert json['01234']['dewpoint'][0] == ['2015-01-01T20:29:27', 12.5]

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2015-01-01T00:00:00'
    assert json['56789']['report_number'] == 'H842;H389'

    assert json['56789']['temperature1'][0] == ['2015-01-01T23:56:47', 20.198]
    assert json['56789']['humidity1'][0] == ['2015-01-01T23:56:47', 182.0197076]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01T23:56:47', 11.1]

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['start'] == '2015-01-01T00:00:00'
    assert json['abcde']['report_number'] == '<uncalibrated>'

    assert json['abcde']['temperature'][0][0] == '2022-07-31T08:12:00'
    assert json['abcde']['humidity'][0][0] == '2022-07-31T08:12:00'
    for item in ('temperature', 'humidity'):
        for _, value in json['abcde'][item]:
            assert isnan(value)
    assert json['abcde']['dewpoint'] == [
        ['2022-07-31T08:12:00', 8.6],
        ['2022-07-31T08:13:00', 8.5],
        ['2022-07-31T08:14:00', 8.5],
        ['2022-07-31T08:15:00', 8.6]
    ]

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['start'] == '2015-01-01T00:00:00'
    assert json['fghij']['report_number'] == '<uncalibrated>;<uncalibrated>'

    assert json['fghij']['temperature1'][0][0] == '2022-07-31T08:12:00'
    assert json['fghij']['humidity1'][0][0] == '2022-07-31T08:12:00'
    assert json['fghij']['temperature2'][0][0] == '2022-07-31T08:12:00'
    assert json['fghij']['humidity2'][0][0] == '2022-07-31T08:12:00'
    for item in ('temperature1', 'temperature2', 'humidity1', 'humidity2'):
        for _, value in json['fghij'][item]:
            assert isnan(value)
    assert json['fghij']['dewpoint1'] == [
        ['2022-07-31T08:12:00', 8.6],
        ['2022-07-31T08:13:00', 8.5],
        ['2022-07-31T08:14:00', 8.5],
        ['2022-07-31T08:15:00', 8.6]
    ]
    assert json['fghij']['dewpoint2'] == [
        ['2022-07-31T08:12:00', 8.5],
        ['2022-07-31T08:13:00', 8.6],
        ['2022-07-31T08:14:00', 8.6],
        ['2022-07-31T08:15:00', 8.5]
    ]


@pytest.mark.parametrize(
    'corrected',
    ['0', 'false', 'FALSE', 'not_true_or_1', 0, False]
)
def test_fetch_uncorrected(corrected):
    json = get('/fetch', params={'corrected': corrected}).json()
    assert len(json) == 4
    assert '01234' in json
    assert '56789' in json
    assert 'abcde' in json
    assert 'fghij' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2015-01-01T00:00:00'
    assert json['01234']['report_number'] is None
    # Raw data in json: [1, "2015-01-01T20:29:27", 18.5, 68.2, 12.5],
    assert json['01234']['temperature'][0] == ['2015-01-01T20:29:27', 18.5]
    assert json['01234']['humidity'][0] == ['2015-01-01T20:29:27', 68.2]
    assert json['01234']['dewpoint'][0] == ['2015-01-01T20:29:27', 12.5]

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2015-01-01T00:00:00'
    assert json['56789']['report_number'] is None
    # Raw data in json: [1, "2015-01-01T23:56:47", 15.3, 76.1, 11.1, 24.5, 24.0, 2.6],
    assert json['56789']['temperature1'][0] == ['2015-01-01T23:56:47', 15.3]
    assert json['56789']['humidity1'][0] == ['2015-01-01T23:56:47', 76.1]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01T23:56:47', 11.1]

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['start'] == '2015-01-01T00:00:00'
    assert json['abcde']['report_number'] is None

    assert json['abcde']['temperature'] == [
        ['2022-07-31T08:12:00', 20.0],
        ['2022-07-31T08:13:00', 19.9],
        ['2022-07-31T08:14:00', 19.9],
        ['2022-07-31T08:15:00', 20.0]
    ]
    assert json['abcde']['humidity'] == [
        ['2022-07-31T08:12:00', 48.1],
        ['2022-07-31T08:13:00', 48.0],
        ['2022-07-31T08:14:00', 47.9],
        ['2022-07-31T08:15:00', 47.8]
    ]
    assert json['abcde']['dewpoint'] == [
        ['2022-07-31T08:12:00', 8.6],
        ['2022-07-31T08:13:00', 8.5],
        ['2022-07-31T08:14:00', 8.5],
        ['2022-07-31T08:15:00', 8.6]
    ]

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['start'] == '2015-01-01T00:00:00'
    assert json['fghij']['report_number'] is None

    assert json['fghij']['temperature1'] == [
        ['2022-07-31T08:12:00', 20.0],
        ['2022-07-31T08:13:00', 19.9],
        ['2022-07-31T08:14:00', 19.9],
        ['2022-07-31T08:15:00', 20.0]
    ]
    assert json['fghij']['humidity1'] == [
        ['2022-07-31T08:12:00', 48.1],
        ['2022-07-31T08:13:00', 48.0],
        ['2022-07-31T08:14:00', 47.9],
        ['2022-07-31T08:15:00', 47.8]
    ]
    assert json['fghij']['dewpoint1'] == [
        ['2022-07-31T08:12:00', 8.6],
        ['2022-07-31T08:13:00', 8.5],
        ['2022-07-31T08:14:00', 8.5],
        ['2022-07-31T08:15:00', 8.6]
    ]
    assert json['fghij']['temperature2'] == [
        ['2022-07-31T08:12:00', 19.9],
        ['2022-07-31T08:13:00', 20.0],
        ['2022-07-31T08:14:00', 20.0],
        ['2022-07-31T08:15:00', 19.9]
    ]
    assert json['fghij']['humidity2'] == [
        ['2022-07-31T08:12:00', 47.9],
        ['2022-07-31T08:13:00', 48.1],
        ['2022-07-31T08:14:00', 47.8],
        ['2022-07-31T08:15:00', 47.9]
    ]
    assert json['fghij']['dewpoint2'] == [
        ['2022-07-31T08:12:00', 8.5],
        ['2022-07-31T08:13:00', 8.6],
        ['2022-07-31T08:14:00', 8.6],
        ['2022-07-31T08:15:00', 8.5]
    ]


def test_fetch_uncorrected_start():
    json = get('/fetch', params={'corrected': 'false', 'start': '2021-01-01T12:00:00'}).json()
    assert len(json) == 4

    assert '01234' in json
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2021-01-01T12:00:00'
    assert json['01234']['report_number'] is None

    # Raw data in json: [75, "2021-01-29T19:06:41", 30.4, 44.7, 17.0]
    assert json['01234']['temperature'][0][1] == 30.4
    assert json['01234']['humidity'][0][1] == 44.7
    assert json['01234']['dewpoint'][0][1] == 17.0

    assert '56789' in json
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2021-01-01T12:00:00'
    assert json['56789']['report_number'] is None

    # Raw data in json: [75, "2021-01-29T19:19:50", 27.7, 41.5, 13.4, 25.3, 46.1, 12.8],
    assert json['56789']['temperature1'][0][1] == 27.7
    assert json['56789']['humidity1'][0][1] == 41.5
    assert json['56789']['dewpoint1'][0][1] == 13.4
    assert json['56789']['temperature2'][0][1] == 25.3
    assert json['56789']['humidity2'][0][1] == 46.1
    assert json['56789']['dewpoint2'][0][1] == 12.8

    json = get('/fetch', params={'corrected': 'false', 'start': '2022-07-31T08:15:00'}).json()
    assert len(json) == 4
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2022-07-31T08:15:00'
    assert json['01234']['report_number'] is None
    assert json['01234']['temperature'] == []
    assert json['01234']['humidity'] == []
    assert json['01234']['dewpoint'] == []

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2022-07-31T08:15:00'
    assert json['56789']['report_number'] is None
    assert json['56789']['temperature1'] == []
    assert json['56789']['humidity1'] == []
    assert json['56789']['dewpoint1'] == []
    assert json['56789']['temperature2'] == []
    assert json['56789']['humidity2'] == []
    assert json['56789']['dewpoint2'] == []

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['start'] == '2022-07-31T08:15:00'
    assert json['abcde']['report_number'] is None
    assert json['abcde']['temperature'] == [['2022-07-31T08:15:00', 20.0]]
    assert json['abcde']['humidity'] == [['2022-07-31T08:15:00', 47.8]]
    assert json['abcde']['dewpoint'] == [['2022-07-31T08:15:00', 8.6]]

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['start'] == '2022-07-31T08:15:00'
    assert json['fghij']['report_number'] is None
    assert json['fghij']['temperature1'] == [['2022-07-31T08:15:00', 20.0]]
    assert json['fghij']['humidity1'] == [['2022-07-31T08:15:00', 47.8]]
    assert json['fghij']['dewpoint1'] == [['2022-07-31T08:15:00', 8.6]]
    assert json['fghij']['temperature2'] == [['2022-07-31T08:15:00', 19.9]]
    assert json['fghij']['humidity2'] == [['2022-07-31T08:15:00', 47.9]]
    assert json['fghij']['dewpoint2'] == [['2022-07-31T08:15:00', 8.5]]


def test_fetch_serial_end_1():
    json = get('/fetch', params={'serial': '01234', 'end': '2021-02-02'}).json()
    assert len(json) == 1
    assert '01234' in json
    assert '56789' not in json
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2015-01-01T00:00:00'
    assert json['01234']['end'] == '2021-02-02T00:00:00'
    assert json['01234']['report_number'] == 'H502'
    assert len(json['01234']['temperature']) == len(json['01234']['humidity']) == len(json['01234']['dewpoint']) == 75
    assert json['01234']['temperature'][-1] == ['2021-01-29T19:06:41', 30.47]
    assert json['01234']['humidity'][-1] == ['2021-01-29T19:06:41', 41.757650510000005]
    assert json['01234']['dewpoint'][-1] == ['2021-01-29T19:06:41', 17.0]


def test_fetch_serial_end_2():
    json = get('/fetch', params={'serial': 56789, 'end': '2016-01-01'}).json()
    assert len(json) == 1
    assert '01234' not in json
    assert '56789' in json
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2015-01-01T00:00:00'
    assert json['56789']['end'] == '2016-01-01T00:00:00'
    assert json['56789']['report_number'] == 'H842;H389'

    assert len(json['56789']['temperature1']) == 13
    assert len(json['56789']['temperature2']) == 13
    assert len(json['56789']['humidity1']) == 13

    assert json['56789']['temperature1'][-1] == ['2015-12-27T00:45:37', 24.026]
    assert json['56789']['humidity1'][-1] == ['2015-12-27T00:45:37', 174.0113344]
    assert json['56789']['dewpoint1'][-1] == ['2015-12-27T00:45:37', 13.3]
    assert json['56789']['humidity1'][0] == ['2015-01-01T23:56:47', 182.0197076]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01T23:56:47', 11.1]
    assert json['56789']['temperature2'][-1] == ['2015-12-27T00:45:37', 49.42193]
    assert json['56789']['humidity2'][-1] == ['2015-12-27T00:45:37', 159.090145]
    assert json['56789']['dewpoint2'][-1] == ['2015-12-27T00:45:37', 24.6]


@pytest.mark.parametrize('params', [{'start': 'yesterday'}, {'end': '2020.08.10'}])
def test_fetch_invalid_timepoints(params):
    response = get('/fetch', params=params)
    key, value = next(iter(params.items()))
    assert response.status_code == 400
    assert response.text == f'The value for {key!r} must be an ISO 8601 string ' \
                            f'(e.g., yyyy-mm-dd or yyyy-mm-ddTHH:MM:SS).<br/>' \
                            f'Received {value!r}'


def test_fetch_serial_and_alias():
    json = get('/fetch', params={'serial': 56789, 'alias': 'b'}).json()
    assert len(json) == 2
    assert '01234' in json
    assert '56789' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2015-01-01T00:00:00'
    assert json['01234']['report_number'] == 'H502'
    assert json['01234']['temperature'][0] == ['2015-01-01T20:29:27', 18.57]
    assert json['01234']['humidity'][0] == ['2015-01-01T20:29:27', 67.26109836]
    assert json['01234']['dewpoint'][0] == ['2015-01-01T20:29:27', 12.5]

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2015-01-01T00:00:00'
    assert json['56789']['report_number'] == 'H842;H389'
    assert json['56789']['temperature1'][0] == ['2015-01-01T23:56:47', 20.198]
    assert json['56789']['humidity1'][0] == ['2015-01-01T23:56:47', 182.0197076]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01T23:56:47', 11.1]

    # Incorrect spelling of serial
    response = get('/fetch', params={'start': '2021-01-01T12:00:00', 'seral': '01234'})
    assert response.status_code == 400
    assert response.text == "Invalid parameter(s): seral<br/>" \
                            "Valid parameters are: alias, corrected, end, serial, start, type"

    # Unknown serial number
    json = get('/fetch', params={'start': '2021-01-01T12:00:00', 'serial': '9876543210'}).json()
    assert json == {}

    # Incorrect spelling of alias
    response = get('/fetch', params={'start': '2021-01-01T12:00:00', 'alis': '01234'})
    assert response.status_code == 400
    assert response.text == "Invalid parameter(s): alis<br/>" \
                            "Valid parameters are: alias, corrected, end, serial, start, type"

    # Unknown alias
    json = get('/fetch', params={'start': '2021-01-01T12:00:00', 'alias': '007'}).json()
    assert json == {}

    # Unknown serial number but known alias
    json = get('/fetch', params={'serial': 'muesli', 'alias': 'b'}).json()
    assert len(json) == 1
    assert '01234' in json
    assert '56789' not in json
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2015-01-01T00:00:00'
    assert json['01234']['report_number'] == 'H502'
    assert json['01234']['temperature'][0] == ['2015-01-01T20:29:27', 18.57]
    assert json['01234']['humidity'][0] == ['2015-01-01T20:29:27', 67.26109836]
    assert json['01234']['dewpoint'][0] == ['2015-01-01T20:29:27', 12.5]


def test_fetch_type():
    json = get('/fetch', params={'type': 'temperature'}).json()
    assert len(json) == 4
    assert '01234' in json
    assert '56789' in json
    assert 'abcde' in json
    assert 'fghij' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2015-01-01T00:00:00'
    assert json['01234']['report_number'] == 'H502'

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2015-01-01T00:00:00'
    assert json['56789']['report_number'] == 'H842;H389'

    assert json['01234']['temperature'][0] == ['2015-01-01T20:29:27', 18.57]
    assert 'humidity' not in json['01234']
    assert 'dewpoint' not in json['01234']

    assert json['56789']['temperature1'][0] == ['2015-01-01T23:56:47', 20.198]
    assert json['56789']['temperature2'][0] == ['2015-01-01T23:56:47', 35.45490875]
    assert 'humidity1' not in json['56789']
    assert 'humidity2' not in json['56789']
    assert 'dewpoint1' not in json['56789']
    assert 'dewpoint2' not in json['56789']

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['start'] == '2015-01-01T00:00:00'
    assert json['abcde']['report_number'] == '<uncalibrated>'
    for _, value in json['abcde']['temperature']:
        assert isnan(value)
    assert 'humidity' not in json['abcde']
    assert 'dewpoint' not in json['abcde']

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['start'] == '2015-01-01T00:00:00'
    assert json['fghij']['report_number'] == '<uncalibrated>;<uncalibrated>'
    for item in ('temperature1', 'temperature2'):
        for _, value in json['fghij'][item]:
            assert isnan(value)
    assert 'humidity1' not in json['fghij']
    assert 'humidity2' not in json['fghij']
    assert 'dewpoint1' not in json['fghij']
    assert 'dewpoint2' not in json['fghij']

    json = get('/fetch', params={'type': 'humidity', 'corrected': 'False'}).json()
    assert len(json) == 4
    assert '01234' in json
    assert '56789' in json
    assert 'abcde' in json
    assert 'fghij' in json

    assert 'temperature' not in json['01234']
    assert 'dewpoint' not in json['01234']
    assert json['01234']['report_number'] is None
    assert json['56789']['report_number'] is None

    assert json['01234']['humidity'][0] == ['2015-01-01T20:29:27', 68.2]
    assert json['56789']['humidity1'][0] == ['2015-01-01T23:56:47', 76.1]
    assert json['56789']['humidity2'][0] == ['2015-01-01T23:56:47', 24.0]

    # Checking matches to incorrect spelling (but close)
    json = get('/fetch', params={'type': 'temp, hum'}).json()
    assert len(json) == 4
    assert json['01234']['error'] is None
    assert json['01234']['temperature'] is not None
    assert json['01234']['humidity'] is not None
    assert 'dewpoint' not in json['01234']

    json = get('/fetch', params={'type': 'dew'}).json()
    assert len(json) == 4
    assert json['01234']['error'] is None
    assert 'temperature' not in json['01234']
    assert 'humidity' not in json['01234']
    assert json['01234']['dewpoint'] is not None

    json = get('/fetch', params={'type': 'temp, dew'}).json()
    assert json['01234']['error'] is None
    assert json['01234']['temperature'] is not None
    assert json['01234']['dewpoint'] is not None
    assert 'humidity' not in json['01234']

    # No correct or close type values -- returns all data
    json = get('/fetch', params={'type': 'dp'}).json()
    assert 'Unknown type value(s) received: dp' in json['01234']['error']
    assert 'Unknown type value(s) received: dp' in json['56789']['error']
    assert json['01234']['temperature'] is not None
    assert json['01234']['humidity'] is not None
    assert json['01234']['dewpoint'] is not None

    json = get('/fetch', params={'type': 'omega'}).json()
    assert 'Unknown type value(s) received' in json['01234']['error']
    assert json['01234']['temperature'] is not None
    assert json['01234']['humidity'] is not None
    assert json['01234']['dewpoint'] is not None


@pytest.mark.parametrize('route', ['/now', '/now/'])
def test_now(route):
    json = get(route).json()
    assert len(json) == 4

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['temperature'] == 21.0
    assert json['abcde']['humidity'] == 41.0
    assert json['abcde']['dewpoint'] == 11.0
    assert json['abcde']['report_number'] == '<uncalibrated>'

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['temperature1'] == 21.0
    assert json['fghij']['humidity1'] == 41.0
    assert json['fghij']['dewpoint1'] == 11.0
    assert json['fghij']['temperature2'] == 22.0
    assert json['fghij']['humidity2'] == 42.0
    assert json['fghij']['dewpoint2'] == 12.0
    assert json['fghij']['report_number'] == '<uncalibrated>;<uncalibrated>'


@pytest.mark.parametrize('corrected', ['1', 'true', 'TRUE', 1, True])
def test_now_corrected(corrected):
    json = get('/now', params={'corrected': corrected}).json()
    assert len(json) == 4

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['temperature'] == 21.0
    assert json['abcde']['humidity'] == 41.0
    assert json['abcde']['dewpoint'] == 11.0
    assert json['abcde']['report_number'] == '<uncalibrated>'

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['temperature1'] == 21.0
    assert json['fghij']['humidity1'] == 41.0
    assert json['fghij']['dewpoint1'] == 11.0
    assert json['fghij']['temperature2'] == 22.0
    assert json['fghij']['humidity2'] == 42.0
    assert json['fghij']['dewpoint2'] == 12.0
    assert json['fghij']['report_number'] == '<uncalibrated>;<uncalibrated>'


@pytest.mark.parametrize(
    'corrected',
    ['0', 'false', 'FALSE', 'not_true_or_1', 0, False]
)
def test_now_uncorrected(corrected):
    json = get('/now', params={'corrected': corrected}).json()
    assert len(json) == 4

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == 21.0
    assert json['01234']['humidity'] == 41.0
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] is None

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == 21.0
    assert json['56789']['humidity1'] == 41.0
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == 22.0
    assert json['56789']['humidity2'] == 42.0
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] is None

    assert json['abcde']['error'] is None
    assert json['abcde']['alias'] == 'g'
    assert json['abcde']['temperature'] == 21.0
    assert json['abcde']['humidity'] == 41.0
    assert json['abcde']['dewpoint'] == 11.0
    assert json['abcde']['report_number'] is None

    assert json['fghij']['error'] is None
    assert json['fghij']['alias'] == 'h'
    assert json['fghij']['temperature1'] == 21.0
    assert json['fghij']['humidity1'] == 41.0
    assert json['fghij']['dewpoint1'] == 11.0
    assert json['fghij']['temperature2'] == 22.0
    assert json['fghij']['humidity2'] == 42.0
    assert json['fghij']['dewpoint2'] == 12.0
    assert json['fghij']['report_number'] is None


def test_now_serial():
    json = get('/now', params={'serial': '01234'}).json()
    assert len(json) == 1
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'
    assert '56789' not in json

    json = get('/now', params={'serial': '56789'}).json()
    assert len(json) == 1
    assert '01234' not in json
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'

    json = get('/now', params={'serial': '01234;56789;'}).json()
    assert len(json) == 2
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'


def test_now_serial_unknown():
    json = get('/now', params={'serial': 'unknown'}).json()
    assert len(json) == 0
    assert isinstance(json, dict)

    json = get('/now', params={'serial': 'unknown;;56789'}).json()
    assert len(json) == 1
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'


def test_now_alias():
    json = get('/now', params={'alias': 'b'}).json()
    assert len(json) == 1
    assert '56789' not in json
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'

    json = get('/now', params={'alias': 'f'}).json()
    assert len(json) == 1
    assert '01234' not in json
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'

    json = get('/now', params={'alias': 'b;f'}).json()
    assert len(json) == 2
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'


def test_now_alias_unknown():
    json = get('/now', params={'alias': 'unknown'}).json()
    assert len(json) == 0
    assert isinstance(json, dict)

    json = get('/now', params={'alias': 'b;unknown'}).json()
    assert len(json) == 1
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'


def test_now_serial_and_alias():
    json = get('/now', params={'serial': '56789', 'alias': 'b'}).json()
    assert len(json) == 2
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['01234']['report_number'] == 'H502'
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] == 'H842;H389'


def test_now_serial_uncorrected():
    json = get('/now', params={'serial': 56789, 'corrected': False}).json()
    assert len(json) == 1
    assert '01234' not in json
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == 21.0
    assert json['56789']['humidity1'] == 41.0
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == 22.0
    assert json['56789']['humidity2'] == 42.0
    assert json['56789']['dewpoint2'] == 12.0
    assert json['56789']['report_number'] is None


@pytest.mark.parametrize('key', ['aliases', 'serials', 'seral'])
def test_now_invalid_param(key):
    response = get('/now', params={key: '56789'})
    assert response.status_code == 400
    assert response.text == f'Invalid parameter(s): {key}<br/>' \
                            f'Valid parameters are: alias, corrected, serial'


@pytest.mark.parametrize('route', ['/aliases', '/aliases/'])
def test_aliases(route):
    json = get(route).json()
    assert len(json) == 4
    assert json['01234'] == 'b'
    assert json['56789'] == 'f'
    assert json['abcde'] == 'g'
    assert json['fghij'] == 'h'


@pytest.mark.parametrize('route', ['/help', '/help/'])
def test_help(route):
    response = get(route)
    assert '<title>API Help | OMEGA iServers</title>' in response.text


@pytest.mark.parametrize('route', ['/download', '/download/'])
def test_download(route):
    response = get(route)
    assert response.status_code == 400
    assert '<p>You cannot directly access the <b>/download</b> route.</p>' in response.text


@pytest.mark.parametrize(
    'route',
    ['/alias', '/new', '/fetc',
     '/a', '/a/',
     '/a/b', '/a/b/',
     '/a/b/c', '/a/b/c/',
     '/a/b/c/d', '/a/b/c/d/',
     '/a/b/c/d/e', '/a/b/c/d/e/']
)
def test_page_not_found(route):
    response = get(route)
    assert response.status_code == 404
    assert '<title>Page not found | OMEGA iServers</title>' in response.text


@pytest.mark.parametrize('route', ['/databases', '/databases/'])
def test_databases(route):
    json = get(route).json()
    assert len(json) == 4
    assert json['01234'] == {
        'alias': 'b',
        'fields': ['pid', 'datetime', 'temperature', 'humidity', 'dewpoint'],
        'file_size': '12 kB',
        'max_date': '2021-06-28T21:16:48',
        'min_date': '2015-01-01T20:29:27',
        'num_records': 80,
    }
    assert json['56789'] == {
        'alias': 'f',
        'fields': ['pid', 'datetime', 'temperature1', 'humidity1', 'dewpoint1', 'temperature2', 'humidity2', 'dewpoint2'],
        'file_size': '20 kB',
        'max_date': '2021-06-28T18:53:48',
        'min_date': '2015-01-01T23:56:47',
        'num_records': 80,
    }
    assert json['abcde'] == {
        'alias': 'g',
        'fields': ['pid', 'datetime', 'temperature', 'humidity', 'dewpoint'],
        'file_size': '12 kB',
        'max_date': '2022-07-31T08:15:00',
        'min_date': '2022-07-31T08:12:00',
        'num_records': 4,
    }
    assert json['fghij'] == {
        'alias': 'h',
        'fields': ['pid', 'datetime', 'temperature1', 'humidity1', 'dewpoint1', 'temperature2', 'humidity2', 'dewpoint2'],
        'file_size': '12 kB',
        'max_date': '2022-07-31T08:15:00',
        'min_date': '2022-07-31T08:12:00',
        'num_records': 4,
    }


@pytest.mark.parametrize(
    ('route', 'params'),
    [('/reports', {}),
     ('/reports', {'serial': '01234', 'alias': 'f'}),
     ('/reports', {'serial': '56789', 'alias': 'b'}),
     ('/reports', {'serial': '01234;56789', 'alias': 'ignored'}),
     ('/reports', {'serial': 'ignored', 'alias': 'b;f'}),
     ('/reports', {'date': 'all'}),
     ('/reports/', {})]
)
def test_reports_all(route, params):
    json = get(route, params=params).json()
    if params and 'date' not in params:
        assert len(json) == 2
        assert len(json['01234']) == 3
        assert len(json['56789']) == 3
    else:
        assert len(json) == 4
        assert len(json['01234']) == 3
        assert len(json['56789']) == 3
        assert len(json['abcde']) == 1
        assert len(json['fghij']) == 2

    report = json['01234'][0]
    assert report['alias'] == 'b'
    assert report['component'] == ''
    assert report['confidence'] == '95%'
    assert report['coverage_factor'] == 2.0
    assert report['date'] == '2020-12-17'
    assert report['end_date'] == '2020-12-14'
    assert report['humidity'] == {
        'coefficients': [-5.11, 2.44e-2, 5.39e-4],
        'expanded_uncertainty': 1.1,
        'max': 80.0,
        'min': 30.0,
        'unit': '%rh'
    }
    assert report['number'] == 'H502'
    assert report['serial'] == '01234'
    assert report['start_date'] == '2020-12-11'
    assert report['temperature'] == {
        'coefficients': [0.07],
        'expanded_uncertainty': 0.12,
        'max': 25.0,
        'min': 15.0,
        'unit': 'C'
    }

    report = json['01234'][1]
    assert report['alias'] == 'b'
    assert report['component'] == ''
    assert report['confidence'] == '95%'
    assert report['coverage_factor'] == 2.0
    assert report['date'] == '2018-07-21'
    assert report['end_date'] == '2018-06-11'
    assert report['humidity'] == {
        'coefficients': [-9.5, 0.326, -0.00505, 0.0000321],
        'expanded_uncertainty': 0.9,
        'max': 85.0,
        'min': 30.0,
        'unit': '%rh'
    }
    assert report['number'] == 'H386'
    assert report['serial'] == '01234'
    assert report['start_date'] == '2018-06-08'
    assert report['temperature'] == {
        'coefficients': [0.01],
        'expanded_uncertainty': 0.13,
        'max': 24.0,
        'min': 18.0,
        'unit': 'C'
    }

    report = json['01234'][2]
    assert report['alias'] == 'b'
    assert report['component'] == ''
    assert report['confidence'] == '95%'
    assert report['coverage_factor'] == 2.0
    assert report['date'] == '2016-02-22'
    assert report['end_date'] == '2016-01-22'
    assert report['humidity'] == {
        'coefficients': [-3.44, 0.0487],
        'expanded_uncertainty': 0.8,
        'max': 80.0,
        'min': 30.0,
        'unit': '%rh'
    }
    assert report['number'] == 'H322'
    assert report['serial'] == '01234'
    assert report['start_date'] == '2016-01-20'
    assert report['temperature'] == {
        'coefficients': [0.05],
        'expanded_uncertainty': 0.12,
        'max': 23.0,
        'min': 17.0,
        'unit': 'C'
    }

    report = json['56789'][0]
    assert report['alias'] == 'f'
    assert report['component'] == 'Probe 1'
    assert report['confidence'] == '95%'
    assert report['coverage_factor'] == 2.0
    assert report['date'] == '2020-06-12'
    assert report['end_date'] == '2020-06-03'
    assert report['humidity'] == {
        'coefficients': [-8.3, 1.23, 3.56e-3],
        'expanded_uncertainty': 0.8,
        'max': 80.0,
        'min': 30.0,
        'unit': '%rh'
    }
    assert report['number'] == 'H842'
    assert report['serial'] == '56789'
    assert report['start_date'] == '2020-06-01'
    assert report['temperature'] == {
        'coefficients': [0.002, 0.32],
        'expanded_uncertainty': 0.12,
        'max': 25.0,
        'min': 15.0,
        'unit': 'C'
    }

    report = json['56789'][1]
    assert report['alias'] == 'f'
    assert report['component'] == 'Probe 1'
    assert report['confidence'] == '95%'
    assert report['coverage_factor'] == 2.0
    assert report['date'] == '2018-07-21'
    assert report['end_date'] == '2018-06-11'
    assert report['humidity'] == {
        'coefficients': [-10.2, 0.393, -0.00637, 0.000039],
        'expanded_uncertainty': 1.0,
        'max': 85.0,
        'min': 30.0,
        'unit': '%rh'
    }
    assert report['number'] == 'H388'
    assert report['serial'] == '56789'
    assert report['start_date'] == '2018-06-08'
    assert report['temperature'] == {
        'coefficients': [0.04, 0.13],
        'expanded_uncertainty': 0.13,
        'max': 24.0,
        'min': 18.0,
        'unit': 'C'
    }

    report = json['56789'][2]
    assert report['alias'] == 'f'
    assert report['component'] == 'Probe 2'
    assert report['confidence'] == '95%'
    assert report['coverage_factor'] == 2.0
    assert report['date'] == '2018-07-21'
    assert report['end_date'] == '2018-06-11'
    assert report['humidity'] == {
        'coefficients': [4.2, 0.931, 0.00482],
        'expanded_uncertainty': 0.8,
        'max': 85.0,
        'min': 30.0,
        'unit': '%rh'
    }
    assert report['number'] == 'H389'
    assert report['serial'] == '56789'
    assert report['start_date'] == '2018-06-08'
    assert report['temperature'] == {
        'coefficients': [0.1, 0.06, 0.01, 2.3e-4],
        'expanded_uncertainty': 0.14,
        'max': 24.0,
        'min': 18.0,
        'unit': 'C'
    }

    if not params:
        assert json['abcde'] == [{}]
        assert json['fghij'] == [{}, {}]


@pytest.mark.parametrize(
    ('route', 'params'),
    [('/reports', {'serial': '01234'}),
     ('/reports', {'serial': '01234;ignore'}),
     ('/reports', {'alias': 'b'}),
     ('/reports', {'alias': 'ignore;b;banana'}),
     ('/reports/', {'serial': '01234'})]
)
def test_reports_all_one_iserver(route, params):
    json = get(route, params=params).json()
    assert len(json) == 1
    assert len(json['01234']) == 3

    assert [r['date'] for r in json['01234']] == ['2020-12-17', '2018-07-21', '2016-02-22']
    assert [r['number'] for r in json['01234']] == ['H502', 'H386', 'H322']


@pytest.mark.parametrize('route', ['/reports', '/reports/'])
def test_reports_latest(route):
    json = get(route, params={'date': 'latest'}).json()
    assert len(json) == 4
    assert len(json['01234']) == 1
    assert len(json['56789']) == 2
    assert len(json['abcde']) == 1
    assert len(json['fghij']) == 2

    report = json['01234'][0]
    assert report['alias'] == 'b'
    assert report['component'] == ''
    assert report['date'] == '2020-12-17'
    assert report['number'] == 'H502'

    report = json['56789'][0]
    assert report['alias'] == 'f'
    assert report['component'] == 'Probe 1'
    assert report['date'] == '2020-06-12'
    assert report['number'] == 'H842'

    report = json['56789'][1]
    assert report['alias'] == 'f'
    assert report['component'] == 'Probe 2'
    assert report['date'] == '2018-07-21'
    assert report['number'] == 'H389'

    assert json['abcde'] == [{}]
    assert json['fghij'] == [{}, {}]


@pytest.mark.parametrize('route', ['/reports', '/reports/'])
def test_reports_date(route):
    json = get(route, params={'date': '2017-01-23'}).json()
    assert len(json) == 4
    assert len(json['01234']) == 1
    assert len(json['56789']) == 2
    assert len(json['abcde']) == 1
    assert len(json['fghij']) == 2

    report = json['01234'][0]
    assert report['alias'] == 'b'
    assert report['component'] == ''
    assert report['date'] == '2016-02-22'
    assert report['number'] == 'H322'

    report = json['56789'][0]
    assert report['alias'] == 'f'
    assert report['component'] == 'Probe 1'
    assert report['date'] == '2018-07-21'
    assert report['number'] == 'H388'

    report = json['56789'][1]
    assert report['alias'] == 'f'
    assert report['component'] == 'Probe 2'
    assert report['date'] == '2018-07-21'
    assert report['number'] == 'H389'

    assert json['abcde'] == [{}]
    assert json['fghij'] == [{}, {}]


@pytest.mark.parametrize('route', ['/reports', '/reports/'])
def test_reports_one_latest(route):
    json = get(route, params={'alias': 'b', 'date': 'latest'}).json()
    assert len(json) == 1
    assert len(json['01234']) == 1

    report = json['01234'][0]
    assert report['alias'] == 'b'
    assert report['component'] == ''
    assert report['date'] == '2020-12-17'
    assert report['number'] == 'H502'


@pytest.mark.parametrize(
    ('route', 'date'),
    [('/reports', '2020'),
     ('/reports', '2020-08.23'),
     ('/reports', '2020.08.23'),
     ('/reports', '20201823'),
     ('/reports', '2020-18-23'),
     ('/reports', 'invalid'),
     ('/reports/', '2020')]
)
def test_reports_invalid_date(route, date):
    response = get(route, params={'date': date})
    assert response.status_code == 400
    assert response.text.startswith(f'Invalid ISO 8601 date format: {date!r}<br/>')


@pytest.mark.parametrize('route', ['/reports', '/reports/'])
def test_reports_no_results(route):
    json = get(route, params={'alias': 'invalid'}).json()
    assert json == {}


@pytest.mark.parametrize('route', ['/connections', '/connections/'])
def test_connections(route):
    json = get(route).json()
    assert json == {
        'b': {
            'address': 'TCP::127.0.0.1::1876',
            'backend': 'MSL',
            'interface': 'SOCKET',
            'manufacturer': 'OMEGA',
            'model': 'iTHX-W3-5',
            'properties': {
                'termination': "b'\\r'",
                'timeout': 5
            },
            'serial': '01234'
        },
        'f': {
            'address': 'TCP::127.0.0.1::1876',
            'backend': 'MSL',
            'interface': 'SOCKET',
            'manufacturer': 'OMEGA',
            'model': 'iTHX-W',
            'properties': {
                'termination': "b'\\r'",
                'timeout': 5,
                'nprobes': 2
            },
            'serial': '56789'
        },
        'g': {
            'address': 'TCP::127.0.0.1::1876',
            'backend': 'MSL',
            'interface': 'SOCKET',
            'manufacturer': 'OMEGA',
            'model': 'iTHX-W3',
            'properties': {
                'termination': "b'\\r'",
                'timeout': 5
            },
            'serial': 'abcde'
        },
        'h': {
            'address': 'TCP::127.0.0.1::1876',
            'backend': 'MSL',
            'interface': 'SOCKET',
            'manufacturer': 'OMEGA',
            'model': 'iTHX-W',
            'properties': {
                'termination': "b'\\r'",
                'timeout': 5,
                'nprobes': 2
            },
            'serial': 'fghij'
        }
    }
