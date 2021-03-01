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
        json = requests.get(f'http://127.0.0.1:1875/now?corrected={c}').json()
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


def test_now_invalid_param():
    response = requests.get('http://127.0.0.1:1875/now?seral=56789')
    assert response.status_code == 400
    assert b"Invalid parameter: 'seral'<br/>Valid parameters are: alias, corrected, serial" == response.content

    response = requests.get('http://127.0.0.1:1875/now?apple=red')
    assert response.status_code == 400
    assert b"Invalid parameter: 'apple'<br/>Valid parameters are: alias, corrected, serial" == response.content


def test_aliases():
    json = requests.get('http://127.0.0.1:1875/aliases').json()
    assert len(json) == 2
    assert json['01234'] == 'b'
    assert json['56789'] == 'f'
