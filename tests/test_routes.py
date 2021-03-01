import os
import sys
import socket
import threading
from subprocess import Popen, PIPE, check_output

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


def setup_module(module):
    global proc

    # start the OMEGA simulator
    thread = threading.Thread(target=simulate_omega_iserver, daemon=True)
    thread.start()

    # start the webapp
    cwd = os.path.join(os.path.dirname(__file__), os.pardir, 'omega_logger')
    cfg = os.path.join(os.path.dirname(__file__), 'resources', 'config.xml')
    cmd = [sys.executable, '-m', 'webapp', cfg, '01234,56789']
    proc = Popen(cmd, stderr=PIPE, cwd=cwd)

    # wait for the webapp and the OMEGA simulator to start
    while True:
        out = check_output(['netstat', '-an'])
        if out.find(b':1875 ') > 0 and out.find(b':1876 ') > 0:
            break


def teardown_module(module):
    if proc is not None:
        proc.terminate()


def test_now():

    json = requests.get('http://127.0.0.1:1875/now').json()
    assert len(json) == 2
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['temperature1'] == temperature1
    assert json['56789']['humidity1'] == humidity1
    assert json['56789']['dewpoint1'] == 11.0
    assert json['56789']['temperature2'] == temperature2
    assert json['56789']['humidity2'] == humidity2
    assert json['56789']['dewpoint2'] == 12.0


def test_now_uncorrected():
    for c in ['false', 'False', 'not_equal_to_true']:
        json = requests.get('http://127.0.0.1:1875/now?corrected={}'.format(c)).json()
        assert len(json) == 2
        assert json['01234']['error'] is None
        assert json['01234']['alias'] == 'b'
        assert json['01234']['temperature'] == 21.0
        assert json['01234']['humidity'] == 41.0
        assert json['01234']['dewpoint'] == 11.0
        assert json['56789']['error'] is None
        assert json['56789']['alias'] == 'f'
        assert json['56789']['temperature1'] == 21.0
        assert json['56789']['humidity1'] == 41.0
        assert json['56789']['dewpoint1'] == 11.0
        assert json['56789']['temperature2'] == 22.0
        assert json['56789']['humidity2'] == 42.0
        assert json['56789']['dewpoint2'] == 12.0


def test_now_serial():
    json = requests.get('http://127.0.0.1:1875/now?serial=01234').json()
    assert len(json) == 1
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0
    assert '56789' not in json

    json = requests.get('http://127.0.0.1:1875/now?serial=56789').json()
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


def test_now_alias():
    json = requests.get('http://127.0.0.1:1875/now?alias=b').json()
    assert len(json) == 1
    assert '56789' not in json
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['temperature'] == temperature
    assert json['01234']['humidity'] == humidity
    assert json['01234']['dewpoint'] == 11.0

    json = requests.get('http://127.0.0.1:1875/now?alias=f').json()
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


def test_now_serial_and_alias():
    # the serial number gets precedence over the alias
    json = requests.get('http://127.0.0.1:1875/now?serial=56789&alias=b').json()
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


def test_now_serial_uncorrected():
    json = requests.get('http://127.0.0.1:1875/now?serial=56789&corrected=false').json()
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


def test_fetch():
    json = requests.get('http://127.0.0.1:1875/fetch').json()
    assert len(json) == 2
    assert '01234' in json
    assert '56789' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] is None

    assert json['01234']['temperature'][0] == ['2015-01-01 20:29:27', 18.57]
    assert json['01234']['humidity'][0] == ['2015-01-01 20:29:27', 67.26109836]
    assert json['01234']['dewpoint'][0] == ['2015-01-01 20:29:27', 12.5]

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] is None

    assert json['56789']['temperature1'][0] == ['2015-01-01 23:56:47', 20.198]
    assert json['56789']['humidity1'][0] == ['2015-01-01 23:56:47', 182.0197076] # that's a funky corrected value!
    assert json['56789']['dewpoint1'][0] == ['2015-01-01 23:56:47', 11.1]

    json = requests.get('http://127.0.0.1:1875/fetch?woofwoof')
    assert json.status_code == 400
    assert 'Unknown arguments' in json.text


def test_fetch_uncorrected():
    json = requests.get('http://127.0.0.1:1875/fetch?corrected=False').json()
    assert len(json) == 2
    assert '01234' in json
    assert '56789' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] is None
    # Raw data in json: ["2015-01-01 20:29:27", 18.5, 68.2, 12.5],
    assert json['01234']['temperature'][0] == ['2015-01-01 20:29:27', 18.5]
    assert json['01234']['humidity'][0] == ['2015-01-01 20:29:27', 68.2]
    assert json['01234']['dewpoint'][0] == ['2015-01-01 20:29:27', 12.5]

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] is None
    # Raw data in json: ["2015-01-01 23:56:47", 15.3, 76.1, 11.1, 24.5, 24.0, 2.6],
    assert json['56789']['temperature1'][0] == ['2015-01-01 23:56:47', 15.3]
    assert json['56789']['humidity1'][0] == ['2015-01-01 23:56:47', 76.1]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01 23:56:47', 11.1]


def test_fetch_serial_end():
    json = requests.get('http://127.0.0.1:1875/fetch?serial=01234&end=2021-02-02').json()
    assert len(json) == 1
    assert '01234' in json
    assert '56789' not in json
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] is None
    assert json['01234']['end'] == '2021-02-02 00:00:00'
    assert len(json['01234']['temperature']) == len(json['01234']['humidity']) == len(json['01234']['dewpoint']) == 75
    assert json['01234']['temperature'][-1] == ['2021-01-29 19:06:41', 30.47]
    assert json['01234']['humidity'][-1] == ['2021-01-29 19:06:41', 41.757650510000005]
    assert json['01234']['dewpoint'][-1] == ['2021-01-29 19:06:41', 17.0]

    json = requests.get('http://127.0.0.1:1875/fetch?serial=56789&end=2016-01-01').json()
    assert len(json) == 1
    assert '01234' not in json
    assert '56789' in json
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] is None
    assert json['56789']['end'] == '2016-01-01 00:00:00'

    assert len(json['56789']['temperature1']) == len(json['56789']['temperature2']) == len(json['56789']['humidity1']) == 13

    assert json['56789']['temperature1'][-1] == ['2015-12-27 00:45:37', 24.026]
    assert json['56789']['humidity1'][-1] == ['2015-12-27 00:45:37', 174.0113344]
    assert json['56789']['dewpoint1'][-1] == ['2015-12-27 00:45:37', 13.3]
    assert json['56789']['humidity1'][0] == ['2015-01-01 23:56:47', 182.0197076]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01 23:56:47', 11.1]
    assert json['56789']['temperature2'][-1] == ['2015-12-27 00:45:37', 49.42193]
    assert json['56789']['humidity2'][-1] == ['2015-12-27 00:45:37', 159.090145]
    assert json['56789']['dewpoint2'][-1] == ['2015-12-27 00:45:37', 24.6]


def test_fetch_uncorrected_start():
    json = requests.get('http://127.0.0.1:1875/fetch?corrected=false&start=2021-01-01T12:00:00').json()
    assert len(json) == 2

    assert '01234' in json
    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] == '2021-01-01 12:00:00'

    # Raw data in json: ["2021-01-29 19:06:41", 30.4, 44.7, 17.0]
    assert json['01234']['temperature'][0][1] == 30.4
    assert json['01234']['humidity'][0][1] == 44.7
    assert json['01234']['dewpoint'][0][1] == 17.0

    assert '56789' in json
    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] == '2021-01-01 12:00:00'

    # Raw data in json: ["2021-01-29 19:19:50", 27.7, 41.5, 13.4, 25.3, 46.1, 12.8],
    assert json['56789']['temperature1'][0][1] == 27.7
    assert json['56789']['humidity1'][0][1] == 41.5
    assert json['56789']['dewpoint1'][0][1] == 13.4
    assert json['56789']['temperature2'][0][1] == 25.3
    assert json['56789']['humidity2'][0][1] == 46.1
    assert json['56789']['dewpoint2'][0][1] == 12.8


def test_fetch_serial_and_alias():
    # the serial number gets precedence over the alias
    json = requests.get('http://127.0.0.1:1875/fetch?serial=56789&alias=b').json()
    assert len(json) == 1
    assert '01234' not in json
    assert '56789' in json

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] is None

    assert json['56789']['temperature1'][0] == ['2015-01-01 23:56:47', 20.198]
    assert json['56789']['humidity1'][0] == ['2015-01-01 23:56:47', 182.0197076]
    assert json['56789']['dewpoint1'][0] == ['2015-01-01 23:56:47', 11.1]

    # Incorrect spelling of serial
    json = requests.get('http://127.0.0.1:1875/fetch?start=2021-01-01T12:00:00&seral=01234')
    assert json.status_code == 400
    assert 'Unknown arguments' in json.text

    # Unknown serial number
    json = requests.get('http://127.0.0.1:1875/fetch?start=2021-01-01T12:00:00&serial=9876543210').json()
    assert json == {}

    # Incorrect spelling of alias
    json = requests.get('http://127.0.0.1:1875/fetch?start=2021-01-01T12:00:00&alis=01234')
    assert json.status_code == 400
    assert 'Unknown arguments' in json.text

    # Unknown alias
    json = requests.get('http://127.0.0.1:1875/fetch?start=2021-01-01T12:00:00&alias=007').json()
    assert json == {}

    # Unknown serial number but known alias - note that this also returns an empty json object
    json = requests.get('http://127.0.0.1:1875/fetch?serial=muesli&alias=b').json()
    assert json == {}


def test_fetch_type():
    json = requests.get('http://127.0.0.1:1875/fetch?type=temperature').json()
    assert len(json) == 2
    assert '01234' in json
    assert '56789' in json

    assert json['01234']['error'] is None
    assert json['01234']['alias'] == 'b'
    assert json['01234']['start'] is None

    assert json['56789']['error'] is None
    assert json['56789']['alias'] == 'f'
    assert json['56789']['start'] is None

    assert json['01234']['temperature'][0] == ['2015-01-01 20:29:27', 18.57]
    assert 'humidity' not in json
    assert 'dewpoint' not in json

    assert json['56789']['temperature1'][0] == ['2015-01-01 23:56:47', 20.198]
    assert json['56789']['temperature2'][0] == ['2015-01-01 23:56:47', 35.45490875]

    json = requests.get('http://127.0.0.1:1875/fetch?type=humidity&corrected=False').json()
    assert len(json) == 2
    assert '01234' in json
    assert '56789' in json

    assert 'temperature' not in json
    assert 'dewpoint' not in json

    assert json['01234']['humidity'][0] == ['2015-01-01 20:29:27', 68.2]
    assert json['56789']['humidity1'][0] == ['2015-01-01 23:56:47', 76.1]
    assert json['56789']['humidity2'][0] == ['2015-01-01 23:56:47', 24.0]

    # One incorrectly spelled, other fine
    json = requests.get('http://127.0.0.1:1875/fetch?type=temperature+humi').json()
    assert len(json) == 2
    assert 'Unknown type value(s) received: humi' in json['01234']['error']

    # No correct type values (returns all data)
    json = requests.get('http://127.0.0.1:1875/fetch?type=dew').json()
    assert 'Unknown type value(s) received: dew' in json['56789']['error']
    assert json['01234']['temperature'] is not None

    json = requests.get('http://127.0.0.1:1875/fetch?type=temp+dew').json()
    assert 'Unknown type value(s) received: temp,dew' in json['01234']['error']
    assert json['01234']['temperature'] is not None


def test_aliases():
    json = requests.get('http://127.0.0.1:1875/aliases').json()
    assert len(json) == 2
    assert json['01234'] == 'b'
    assert json['56789'] == 'f'
