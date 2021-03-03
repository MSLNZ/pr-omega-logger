import os
from datetime import datetime, timedelta

import pytest
from msl.equipment import Config

from omega_logger import utils

resources = os.path.join(os.path.dirname(__file__), 'resources')

cfg = Config(os.path.join(resources, 'config.xml'))
cfg.find('log_dir').text = resources

serials = '01234,56789'


def test_fromisoformat():
    dt = utils.fromisoformat('2020-02-23')
    assert dt == datetime(2020, month=2, day=23)

    dt = utils.fromisoformat('2020-02-23 12:32:05')
    assert dt == datetime(2020, month=2, day=23, hour=12, minute=32, second=5)

    dt = utils.fromisoformat('2020-02-23T12:32:05')
    assert dt == datetime(2020, month=2, day=23, hour=12, minute=32, second=5)

    dt = utils.fromisoformat('2020-02-23T12')
    assert dt == datetime(2020, month=2, day=23, hour=12, minute=0, second=0)

    dt = utils.fromisoformat('2020-02-23T12:10')
    assert dt == datetime(2020, month=2, day=23, hour=12, minute=10, second=0)

    # these raise a ValueError
    for item in ['1614715543.374186', '2021', '2021-', '2021-0-0', '2021-01',
                 '01-01-2021', '2020.02.23', '2020-02-23T12-32-05',
                 '2020.02.23 12.32.05', '2020-02-23T12:', '2020-02-23T12:10:']:
        with pytest.raises(ValueError):
            utils.fromisoformat(item)
    for i in range(25):
        with pytest.raises(ValueError):
            utils.fromisoformat('x'*i)

    # these raise a TypeError
    for item in [None, 1614715543.374186, dict(), tuple(), set(), True, 2, 1+7j]:
        with pytest.raises(TypeError):
            utils.fromisoformat(item)


def test_initialize_webapp():
    dropdown_options, calibrations, omegas = utils.initialize_webapp(cfg, serials)

    assert len(dropdown_options) == 3
    assert dropdown_options[0] == {'label': 'b', 'value': 'b'}
    assert dropdown_options[1] == {'label': 'f - Probe 1', 'value': 'f - Probe 1'}
    assert dropdown_options[2] == {'label': 'f - Probe 2', 'value': 'f - Probe 2'}

    assert len(calibrations) == 3
    assert len(calibrations['b']) == 3
    assert len(calibrations['f - Probe 1']) == 2
    assert len(calibrations['f - Probe 2']) == 1

    assert len(omegas) == 2
    assert '01234' in omegas
    assert '56789' in omegas

    cal = calibrations['b'][0]
    assert cal.serial == '01234'
    assert os.path.basename(cal.dbase_file) == 'iTHX-W3-5_01234.sqlite3'
    assert cal.component == ''
    assert cal.probe == ''
    assert cal.date == utils.fromisoformat('2020-12-17')
    assert cal.number == 'H502'
    assert cal.start_date == utils.fromisoformat('2020-12-11')
    assert cal.end_date == utils.fromisoformat('2020-12-14')
    assert cal.coverage_factor == 2.0
    assert cal.confidence == '95%'
    assert cal.temperature['units'] == 'C'
    assert cal.temperature['min'] == 15.0
    assert cal.temperature['max'] == 25.0
    assert cal.temperature['coefficients'] == [0.07]
    assert cal.temperature['expanded_uncertainty'] == 0.12
    assert cal.humidity['units'] == '%rh'
    assert cal.humidity['min'] == 30.0
    assert cal.humidity['max'] == 80.0
    assert cal.humidity['coefficients'] == [-5.11, 2.44e-2, 5.39e-4]
    assert cal.humidity['expanded_uncertainty'] == 1.1

    cal = calibrations['b'][1]
    assert cal.serial == '01234'
    assert os.path.basename(cal.dbase_file) == 'iTHX-W3-5_01234.sqlite3'
    assert cal.component == ''
    assert cal.probe == ''
    assert cal.date == utils.fromisoformat('2018-07-21')
    assert cal.number == 'H386'
    assert cal.start_date == utils.fromisoformat('2018-06-08')
    assert cal.end_date == utils.fromisoformat('2018-06-11')
    assert cal.coverage_factor == 2.0
    assert cal.confidence == '95%'
    assert cal.temperature['units'] == 'C'
    assert cal.temperature['min'] == 18.0
    assert cal.temperature['max'] == 24.0
    assert cal.temperature['coefficients'] == [0.01]
    assert cal.temperature['expanded_uncertainty'] == 0.13
    assert cal.humidity['units'] == '%rh'
    assert cal.humidity['min'] == 30.0
    assert cal.humidity['max'] == 85.0
    assert cal.humidity['coefficients'] == [-9.5, 0.326, -5.05e-3, 3.21e-5]
    assert cal.humidity['expanded_uncertainty'] == 0.9

    cal = calibrations['b'][2]
    assert cal.serial == '01234'
    assert os.path.basename(cal.dbase_file) == 'iTHX-W3-5_01234.sqlite3'
    assert cal.component == ''
    assert cal.probe == ''
    assert cal.date == utils.fromisoformat('2016-02-22')
    assert cal.number == 'H322'
    assert cal.start_date == utils.fromisoformat('2016-01-20')
    assert cal.end_date == utils.fromisoformat('2016-01-22')
    assert cal.coverage_factor == 2.0
    assert cal.confidence == '95%'
    assert cal.temperature['units'] == 'C'
    assert cal.temperature['min'] == 17.0
    assert cal.temperature['max'] == 23.0
    assert cal.temperature['coefficients'] == [0.05]
    assert cal.temperature['expanded_uncertainty'] == 0.12
    assert cal.humidity['units'] == '%rh'
    assert cal.humidity['min'] == 30.0
    assert cal.humidity['max'] == 80.0
    assert cal.humidity['coefficients'] == [-3.44, 4.87e-2]
    assert cal.humidity['expanded_uncertainty'] == 0.8

    cal = calibrations['f - Probe 1'][0]
    assert cal.serial == '56789'
    assert os.path.basename(cal.dbase_file) == 'iTHX-W_56789.sqlite3'
    assert cal.component == 'Probe 1'
    assert cal.probe == '1'
    assert cal.date == utils.fromisoformat('2020-06-12')
    assert cal.number == 'H842'
    assert cal.start_date == utils.fromisoformat('2020-06-01')
    assert cal.end_date == utils.fromisoformat('2020-06-03')
    assert cal.coverage_factor == 2.0
    assert cal.confidence == '95%'
    assert cal.temperature['units'] == 'C'
    assert cal.temperature['min'] == 15.0
    assert cal.temperature['max'] == 25.0
    assert cal.temperature['coefficients'] == [0.002, 0.32]
    assert cal.temperature['expanded_uncertainty'] == 0.12
    assert cal.humidity['units'] == '%rh'
    assert cal.humidity['min'] == 30.0
    assert cal.humidity['max'] == 80.0
    assert cal.humidity['coefficients'] == [-8.3, 1.23, 3.56e-3]
    assert cal.humidity['expanded_uncertainty'] == 0.8

    cal = calibrations['f - Probe 1'][1]
    assert cal.serial == '56789'
    assert os.path.basename(cal.dbase_file) == 'iTHX-W_56789.sqlite3'
    assert cal.component == 'Probe 1'
    assert cal.probe == '1'
    assert cal.date == utils.fromisoformat('2018-07-21')
    assert cal.number == 'H388'
    assert cal.start_date == utils.fromisoformat('2018-06-08')
    assert cal.end_date == utils.fromisoformat('2018-06-11')
    assert cal.coverage_factor == 2.0
    assert cal.confidence == '95%'
    assert cal.temperature['units'] == 'C'
    assert cal.temperature['min'] == 18.0
    assert cal.temperature['max'] == 24.0
    assert cal.temperature['coefficients'] == [0.04, 0.13]
    assert cal.temperature['expanded_uncertainty'] == 0.13
    assert cal.humidity['units'] == '%rh'
    assert cal.humidity['min'] == 30.0
    assert cal.humidity['max'] == 85.0
    assert cal.humidity['coefficients'] == [-10.2, 0.393, -6.37e-3, 3.9e-5]
    assert cal.humidity['expanded_uncertainty'] == 1.0

    cal = calibrations['f - Probe 2'][0]
    assert cal.serial == '56789'
    assert os.path.basename(cal.dbase_file) == 'iTHX-W_56789.sqlite3'
    assert cal.component == 'Probe 2'
    assert cal.probe == '2'
    assert cal.date == utils.fromisoformat('2018-07-21')
    assert cal.number == 'H389'
    assert cal.start_date == utils.fromisoformat('2018-06-08')
    assert cal.end_date == utils.fromisoformat('2018-06-11')
    assert cal.coverage_factor == 2.0
    assert cal.confidence == '95%'
    assert cal.temperature['units'] == 'C'
    assert cal.temperature['min'] == 18.0
    assert cal.temperature['max'] == 24.0
    assert cal.temperature['coefficients'] == [0.1, 0.06, 0.01, 2.3e-4]
    assert cal.temperature['expanded_uncertainty'] == 0.14
    assert cal.humidity['units'] == '%rh'
    assert cal.humidity['min'] == 30.0
    assert cal.humidity['max'] == 85.0
    assert cal.humidity['coefficients'] == [4.2, 0.931, 0.00482]
    assert cal.humidity['expanded_uncertainty'] == 0.8

    dropdown_options, calibrations, omegas = utils.initialize_webapp(cfg, '01234')
    assert len(dropdown_options) == 1
    assert dropdown_options[0] == {'label': 'b', 'value': 'b'}
    assert len(calibrations) == 1
    assert len(calibrations['b']) == 3
    assert len(omegas) == 1
    assert '01234' in omegas

    dropdown_options, calibrations, omegas = utils.initialize_webapp(cfg, '56789')
    assert len(dropdown_options) == 2
    assert dropdown_options[0] == {'label': 'f - Probe 1', 'value': 'f - Probe 1'}
    assert dropdown_options[1] == {'label': 'f - Probe 2', 'value': 'f - Probe 2'}
    assert len(calibrations) == 2
    assert len(calibrations['f - Probe 1']) == 2
    assert len(calibrations['f - Probe 2']) == 1
    assert len(omegas) == 1
    assert '56789' in omegas


def test_initialize_webapp_config_minimal():
    # the 'config_minimal.xml' file does not contain any of the Optional XML elements
    cfg_min = Config(os.path.join(resources, 'config_minimal.xml'))
    dropdown_options, calibrations, omegas = utils.initialize_webapp(cfg_min, serials)

    assert len(dropdown_options) == 3
    assert dropdown_options[0] == {'label': 'b', 'value': 'b'}
    assert dropdown_options[1] == {'label': 'f - Probe 1', 'value': 'f - Probe 1'}
    assert dropdown_options[2] == {'label': 'f - Probe 2', 'value': 'f - Probe 2'}

    assert len(calibrations) == 3
    assert len(calibrations['b']) == 3
    assert len(calibrations['f - Probe 1']) == 2
    assert len(calibrations['f - Probe 2']) == 1

    assert len(omegas) == 2
    assert '01234' in omegas
    assert '56789' in omegas


def test_find_report():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    cal = calibrations['b']
    assert utils.find_report(cal).number == 'H502'
    assert utils.find_report(cal, '2018-08-22').number == 'H386'
    assert utils.find_report(cal, '2010-08-22').number == 'H322'
    assert utils.find_report(cal, '2021-08-22').number == 'H502'
    assert utils.find_report(cal, '2020-06-04').number == 'H502'
    assert utils.find_report(cal, datetime(2019, 4, 3)).number == 'H386'
    assert utils.find_report(cal, datetime(2019, 12, 30)).number == 'H502'
    assert utils.find_report(cal, datetime(2017, 1, 1)).number == 'H322'

    cal = calibrations['f - Probe 1']
    assert utils.find_report(cal).number == 'H842'
    assert utils.find_report(cal, '2018-08-22').number == 'H388'
    assert utils.find_report(cal, '2010-08-22').number == 'H388'
    assert utils.find_report(cal, '2021-08-22').number == 'H842'
    assert utils.find_report(cal, '2020-06-04').number == 'H842'
    assert utils.find_report(cal, datetime(2019, 4, 3)).number == 'H388'
    assert utils.find_report(cal, datetime(2019, 12, 30)).number == 'H842'
    assert utils.find_report(cal, datetime(2017, 1, 1)).number == 'H388'

    cal = calibrations['f - Probe 2']
    assert utils.find_report(cal).number == 'H389'
    assert utils.find_report(cal, '2018-08-22').number == 'H389'
    assert utils.find_report(cal, '2010-08-22').number == 'H389'
    assert utils.find_report(cal, '2021-08-22').number == 'H389'
    assert utils.find_report(cal, '2020-06-04').number == 'H389'
    assert utils.find_report(cal, datetime(2019, 4, 3)).number == 'H389'
    assert utils.find_report(cal, datetime(2019, 12, 30)).number == 'H389'
    assert utils.find_report(cal, datetime(2017, 1, 1)).number == 'H389'


def test_find_reports():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    reports = utils.find_reports(calibrations, '01234')
    assert len(reports) == 1
    assert reports[0].number == 'H502'
    assert reports[0] is utils.find_report(calibrations['b'])

    reports = utils.find_reports(calibrations, '01234', nearest='2018-06-10')
    assert len(reports) == 1
    assert reports[0].number == 'H386'
    assert reports[0] is utils.find_report(calibrations['b'], nearest=datetime(2018, 6, 10))

    reports = utils.find_reports(calibrations, '01234', nearest='2015-04-28')
    assert len(reports) == 1
    assert reports[0].number == 'H322'
    assert reports[0] is utils.find_report(calibrations['b'], nearest=datetime(2015, 4, 28))

    reports = utils.find_reports(calibrations, '56789')
    assert len(reports) == 2
    assert reports[0].number == 'H842'
    assert reports[1].number == 'H389'
    assert reports[0] is utils.find_report(calibrations['f - Probe 1'])
    assert reports[1] is utils.find_report(calibrations['f - Probe 2'])

    reports = utils.find_reports(calibrations, '56789', nearest='2017-01-01')
    assert len(reports) == 2
    assert reports[0].number == 'H388'
    assert reports[1].number == 'H389'
    assert reports[0] is utils.find_report(calibrations['f - Probe 1'], nearest='2017-01-01')
    assert reports[1] is utils.find_report(calibrations['f - Probe 2'], nearest='2017-01-01')

    reports = utils.find_reports(calibrations, 'abcdefg')
    assert len(reports) == 0


def test_read_database():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    report = calibrations['b'][0]
    data, _ = utils.read_database(report, 'temperature')
    assert data.dtype.names == ('timestamp', 'temperature')
    assert data[0][0] == '2015-01-01 20:29:27'
    assert data[0][1] == 18.5
    assert data[79][0] == '2021-06-28 21:16:48'
    assert data[79][1] == 16.7

    data, _ = utils.read_database(report, 'humidity', date1='2019-09-07')
    assert data.dtype.names == ('timestamp', 'humidity')
    assert data[0][0] == '2019-09-07 11:35:11'
    assert data[0][1] == 37.8
    assert data[22][0] == '2021-06-28 21:16:48'
    assert data[22][1] == 61.0

    data, _ = utils.read_database(report, 'humidity', date2=datetime(2017, 9, 17))
    assert data.dtype.names == ('timestamp', 'humidity')
    assert data[0][0] == '2015-01-01 20:29:27'
    assert data[0][1] == 68.2
    assert data[32][0] == '2017-08-18 14:42:31'
    assert data[32][1] == 76.2

    data, _ = utils.read_database(report, 'dewpoint', date1=datetime(2016, 8, 23), date2='2019-12-06 08:36:43')
    assert data.dtype.names == ('timestamp', 'dewpoint')
    assert data[0][0] == '2016-08-23 13:04:32'
    assert data[0][1] == 21.7
    assert data[40][0] == '2019-12-06 08:36:43'
    assert data[40][1] == 26.6

    report = calibrations['f - Probe 1'][0]
    data, _ = utils.read_database(report, 'temperature')
    assert data.dtype.names == ('timestamp', 'temperature')
    assert data[0][0] == '2015-01-01 23:56:47'
    assert data[0][1] == 15.3
    assert data[79][0] == '2021-06-28 18:53:48'
    assert data[79][1] == 16.9

    report = calibrations['f - Probe 2'][0]
    data, _ = utils.read_database(report, 'temperature', date1='2015-06-30')
    assert data.dtype.names == ('timestamp', 'temperature')
    assert data[0][0] == '2015-06-30 00:29:56'
    assert data[0][1] == 22.3
    assert data[73][0] == '2021-06-28 18:53:48'
    assert data[73][1] == 19.6

    report = calibrations['f - Probe 1'][1]
    data, _ = utils.read_database(report, 'humidity', date2=datetime(2020, 3, 1))
    assert data.dtype.names == ('timestamp', 'humidity')
    assert data[0][0] == '2015-01-01 23:56:47'
    assert data[0][1] == 76.1
    assert data[62][0] == '2020-02-04 05:52:17'
    assert data[62][1] == 48.2

    report = calibrations['f - Probe 2'][0]
    data, _ = utils.read_database(report, 'humidity', date1=datetime(2020, 1, 1), date2=datetime(2020, 2, 4))
    assert data.dtype.names == ('timestamp', 'humidity')
    assert len(data) == 1
    assert data[0][0] == '2020-01-05 15:09:59'
    assert data[0][1] == 60.4

    report = calibrations['f - Probe 1'][1]
    data, _ = utils.read_database(report, 'dewpoint', date1='2015-05-29', date2=datetime(2018, 8, 13))
    assert data.dtype.names == ('timestamp', 'dewpoint')
    assert data[0][0] == '2015-05-31 16:40:02'
    assert data[0][1] == 9.3
    assert data[38][0] == '2018-07-14 00:12:37'
    assert data[38][1] == 10.0

    report = calibrations['f - Probe 2'][0]
    data, _ = utils.read_database(report, 'dewpoint', date1='2021-05-20', date2=datetime(2030, 8, 13))
    assert data.dtype.names == ('timestamp', 'dewpoint')
    assert data[0][0] == '2021-05-29 06:24:31'
    assert data[0][1] == 17.0
    assert data[1][0] == '2021-06-28 18:53:48'
    assert data[1][1] == 10.6


def test_apply_calibration_1():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    report = utils.find_report(calibrations['f - Probe 1'])
    assert report.number == 'H842'
    data, _ = utils.read_database(report, 'temperature', date1='2018-11-11', date2='2019-06-09')
    uncalibrated = [
        ['2018-11-11 02:41:00', 22.3],
        ['2018-12-11 04:45:53', 27.9],
        ['2019-01-10 21:03:28', 34.4],
        ['2019-02-09 20:51:08', 23.0],
        ['2019-03-11 19:40:08', 20.5],
        ['2019-04-10 07:35:28', 21.3],
        ['2019-05-10 13:44:06', 29.3],
    ]
    for i in range(len(uncalibrated)):
        assert data[i][0] == uncalibrated[i][0]
        assert data[i][1] == uncalibrated[i][1]
    data2 = utils.apply_calibration(data, report)
    assert data2 is data  # calculation is done in-place
    calibrated = [
        ['2018-11-11 02:41:00', 22.3 + (0.002 + 0.32*22.3)],
        ['2018-12-11 04:45:53', 27.9 + (0.002 + 0.32*27.9)],
        ['2019-01-10 21:03:28', 34.4 + (0.002 + 0.32*34.4)],
        ['2019-02-09 20:51:08', 23.0 + (0.002 + 0.32*23.0)],
        ['2019-03-11 19:40:08', 20.5 + (0.002 + 0.32*20.5)],
        ['2019-04-10 07:35:28', 21.3 + (0.002 + 0.32*21.3)],
        ['2019-05-10 13:44:06', 29.3 + (0.002 + 0.32*29.3)],
    ]
    for i in range(len(uncalibrated)):
        assert data2[i][0] == calibrated[i][0]
        assert data2[i][1] == calibrated[i][1]


def test_apply_calibration_2():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    report = utils.find_report(calibrations['f - Probe 1'])
    assert report.number == 'H842'
    data, _ = utils.read_database(report, 'humidity', date1='2018-11-11', date2='2019-06-09')
    uncalibrated = [
        ['2018-11-11 02:41:00', 26.2],
        ['2018-12-11 04:45:53', 32.1],
        ['2019-01-10 21:03:28', 20.4],
        ['2019-02-09 20:51:08', 36.8],
        ['2019-03-11 19:40:08', 32.5],
        ['2019-04-10 07:35:28', 75.4],
        ['2019-05-10 13:44:06', 41.2],
    ]
    for i in range(len(uncalibrated)):
        assert data[i][0] == uncalibrated[i][0]
        assert data[i][1] == uncalibrated[i][1]
    data2 = utils.apply_calibration(data, report)
    assert data2 is data  # calculation is done in-place
    calibrated = [
        ['2018-11-11 02:41:00', 26.2 + (-8.3 + 1.23*26.2 + 3.56e-3*(26.2**2))],
        ['2018-12-11 04:45:53', 32.1 + (-8.3 + 1.23*32.1 + 3.56e-3*(32.1**2))],
        ['2019-01-10 21:03:28', 20.4 + (-8.3 + 1.23*20.4 + 3.56e-3*(20.4**2))],
        ['2019-02-09 20:51:08', 36.8 + (-8.3 + 1.23*36.8 + 3.56e-3*(36.8**2))],
        ['2019-03-11 19:40:08', 32.5 + (-8.3 + 1.23*32.5 + 3.56e-3*(32.5**2))],
        ['2019-04-10 07:35:28', 75.4 + (-8.3 + 1.23*75.4 + 3.56e-3*(75.4**2))],
        ['2019-05-10 13:44:06', 41.2 + (-8.3 + 1.23*41.2 + 3.56e-3*(41.2**2))],
    ]
    for i in range(len(uncalibrated)):
        assert data2[i][0] == calibrated[i][0]
        assert data2[i][1] == calibrated[i][1]


def test_apply_calibration_3():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    report = utils.find_report(calibrations['f - Probe 1'])
    assert report.number == 'H842'
    data, _ = utils.read_database(report, 'dewpoint', date1='2018-11-11', date2='2019-06-09')
    uncalibrated = [
        ['2018-11-11 02:41:00', 2.0],
        ['2018-12-11 04:45:53', 9.7],
        ['2019-01-10 21:03:28', 8.7],
        ['2019-02-09 20:51:08', 7.5],
        ['2019-03-11 19:40:08', 3.4],
        ['2019-04-10 07:35:28', 16.8],
        ['2019-05-10 13:44:06', 14.8],
    ]
    for i in range(len(uncalibrated)):
        assert data[i][0] == uncalibrated[i][0]
        assert data[i][1] == uncalibrated[i][1]
    data2 = utils.apply_calibration(data, report)
    assert data2 is data  # calculation is done in-place
    for i in range(len(uncalibrated)):
        assert data2[i][0] == uncalibrated[i][0]
        assert data2[i][1] == uncalibrated[i][1]


def test_apply_calibration_4():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    report = utils.find_report(calibrations['f - Probe 2'])
    assert report.number == 'H389'
    data, _ = utils.read_database(report, 'temperature', date1='2018-11-11', date2='2019-06-09')
    uncalibrated = [
        ['2018-11-11 02:41:00', 24.9],
        ['2018-12-11 04:45:53', 18.2],
        ['2019-01-10 21:03:28', 35.3],
        ['2019-02-09 20:51:08', 17.1],
        ['2019-03-11 19:40:08', 33.2],
        ['2019-04-10 07:35:28', 18.0],
        ['2019-05-10 13:44:06', 27.8],
    ]
    for i in range(len(uncalibrated)):
        assert data[i][0] == uncalibrated[i][0]
        assert data[i][1] == uncalibrated[i][1]
    data2 = utils.apply_calibration(data, report)
    assert data2 is data  # calculation is done in-place
    calibrated = [
        ['2018-11-11 02:41:00', 24.9 + (0.1 + 0.06*24.9 + 0.01*(24.9**2) + 2.3e-4*(24.9**3))],
        ['2018-12-11 04:45:53', 18.2 + (0.1 + 0.06*18.2 + 0.01*(18.2**2) + 2.3e-4*(18.2**3))],
        ['2019-01-10 21:03:28', 35.3 + (0.1 + 0.06*35.3 + 0.01*(35.3**2) + 2.3e-4*(35.3**3))],
        ['2019-02-09 20:51:08', 17.1 + (0.1 + 0.06*17.1 + 0.01*(17.1**2) + 2.3e-4*(17.1**3))],
        ['2019-03-11 19:40:08', 33.2 + (0.1 + 0.06*33.2 + 0.01*(33.2**2) + 2.3e-4*(33.2**3))],
        ['2019-04-10 07:35:28', 18.0 + (0.1 + 0.06*18.0 + 0.01*(18.0**2) + 2.3e-4*(18.0**3))],
        ['2019-05-10 13:44:06', 27.8 + (0.1 + 0.06*27.8 + 0.01*(27.8**2) + 2.3e-4*(27.8**3))],
    ]
    for i in range(len(uncalibrated)):
        assert data2[i][0] == calibrated[i][0]
        assert data2[i][1] == calibrated[i][1]


def test_apply_calibration_5():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    report = utils.find_report(calibrations['b'], nearest='2018-07-21')
    assert report.number == 'H386'
    data, _ = utils.read_database(report, 'temperature', date1='2020-11-30', date2='2021-05-29')
    uncalibrated = [
        ['2020-11-30 10:13:42', 18.2],
        ['2020-12-30 17:19:18', 33.6],
        ['2021-01-29 19:06:41', 30.4],
        ['2021-02-28 20:31:30', 34.7],
        ['2021-03-30 21:54:52', 16.5],
        ['2021-04-29 15:30:45', 26.2],
    ]
    for i in range(len(uncalibrated)):
        assert data[i][0] == uncalibrated[i][0]
        assert data[i][1] == uncalibrated[i][1]
    data2 = utils.apply_calibration(data, report)
    assert data2 is data  # calculation is done in-place
    calibrated = [
        ['2020-11-30 10:13:42', 18.2 + 0.01],
        ['2020-12-30 17:19:18', 33.6 + 0.01],
        ['2021-01-29 19:06:41', 30.4 + 0.01],
        ['2021-02-28 20:31:30', 34.7 + 0.01],
        ['2021-03-30 21:54:52', 16.5 + 0.01],
        ['2021-04-29 15:30:45', 26.2 + 0.01],
    ]
    for i in range(len(uncalibrated)):
        assert data2[i][0] == calibrated[i][0]
        assert data2[i][1] == calibrated[i][1]


def test_apply_calibration_6():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    data = {
        'error': None,
        'alias': 'something',
        'timestamp': '2020-11-30 10:13:42',
        'temperature': 26.2,
        'humidity': 59.4,
        'dewpoint': 17.6,
    }

    data_copy = data.copy()

    calibrated = {
        'error': None,
        'alias': 'something',
        'timestamp': '2020-11-30 10:13:42',
        'temperature': 26.2 + 0.01,
        'humidity': 59.4 + (-9.5 + 0.326*59.4 - 0.00505*(59.4**2) + 0.0000321*(59.4**3)),
        'dewpoint': 17.6,
    }

    report = utils.find_report(calibrations['b'], nearest='2018-07-21')
    assert report.number == 'H386'
    data2 = utils.apply_calibration(data, report)
    assert data2 is data  # calculation is done in-place
    assert data2['error'] is calibrated['error']
    assert data2['alias'] == calibrated['alias']
    assert data2['timestamp'] == calibrated['timestamp']
    assert abs(data2['temperature'] - calibrated['temperature']) < 1e-10
    assert abs(data2['humidity'] - calibrated['humidity']) < 1e-10
    assert data2['dewpoint'] == calibrated['dewpoint']

    for report in utils.find_reports(calibrations, '01234', nearest='2018-07-21'):
        data_copy = utils.apply_calibration(data_copy, report)
    assert data_copy['error'] is calibrated['error']
    assert data_copy['alias'] == calibrated['alias']
    assert data_copy['timestamp'] == calibrated['timestamp']
    assert abs(data_copy['temperature'] - calibrated['temperature']) < 1e-10
    assert abs(data_copy['humidity'] - calibrated['humidity']) < 1e-10
    assert data_copy['dewpoint'] == calibrated['dewpoint']


def test_apply_calibration_7():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    data = {
        'error': None,
        'alias': 'abcd',
        'timestamp': '2020-11-30 10:13:42',
        'temperature1': 26.2,
        'humidity1': 59.4,
        'dewpoint1': 17.6,
        'temperature2': 24.8,
        'humidity2': 45.7,
        'dewpoint2': 11.3,
    }

    data_copy = data.copy()
    data2_copy = data.copy()

    calibrated = {
        'error': None,
        'alias': 'abcd',
        'timestamp': '2020-11-30 10:13:42',
        'temperature1': 26.2 + (0.04 + 0.13*26.2),
        'humidity1': 59.4 + (-10.2 + 0.393*59.4 - 0.00637*(59.4**2) + 0.000039*(59.4**3)),
        'dewpoint1': 17.6,
        'temperature2': 24.8 + (0.1 + 0.06*24.8 + 0.01*(24.8**2) + 2.3e-4*(24.8**3)),
        'humidity2': 45.7 + (4.2 + 0.931*45.7 + 0.00482*(45.7**2)),
        'dewpoint2': 11.3,
    }

    report1 = utils.find_report(calibrations['f - Probe 1'], nearest='2018-07-21')
    assert report1.number == 'H388'
    data1 = utils.apply_calibration(data, report1)
    assert data1 is data  # calculation is done in-place

    # temperature1 and humidity1 had the calibration equation applied
    assert data1['error'] is calibrated['error']
    assert data1['alias'] == calibrated['alias']
    assert data1['timestamp'] == calibrated['timestamp']
    assert abs(data1['temperature1'] - calibrated['temperature1']) < 1e-10
    assert abs(data1['humidity1'] - calibrated['humidity1']) < 1e-10
    assert data1['dewpoint1'] == calibrated['dewpoint1']
    assert data1['temperature2'] == data['temperature2']
    assert data1['humidity2'] == data['humidity2']
    assert data1['dewpoint2'] == calibrated['dewpoint2']

    report2 = utils.find_report(calibrations['f - Probe 2'], nearest='2018-07-21')
    assert report2.number == 'H389'
    data2 = utils.apply_calibration(data1, report2)
    assert data2 is data  # calculation is done in-place
    assert data2 is data1  # calculation is done in-place

    # temperature2 and humidity2 had the calibration equation applied
    assert data2['error'] is calibrated['error']
    assert data2['alias'] == calibrated['alias']
    assert data2['timestamp'] == calibrated['timestamp']
    assert abs(data2['temperature1'] - calibrated['temperature1']) < 1e-10
    assert abs(data2['humidity1'] - calibrated['humidity1']) < 1e-10
    assert data2['dewpoint1'] == calibrated['dewpoint1']
    assert abs(data2['temperature2'] - calibrated['temperature2']) < 1e-10
    assert abs(data2['humidity2'] - calibrated['humidity2']) < 1e-10
    assert data2['dewpoint2'] == calibrated['dewpoint2']

    report1 = utils.find_report(calibrations['f - Probe 1'], nearest='2018-07-21')
    report2 = utils.find_report(calibrations['f - Probe 2'], nearest='2018-07-21')
    for r in [report1, report2]:
        data_copy = utils.apply_calibration(data_copy, r)
    assert data_copy['error'] is calibrated['error']
    assert data_copy['alias'] == calibrated['alias']
    assert data_copy['timestamp'] == calibrated['timestamp']
    assert abs(data_copy['temperature1'] - calibrated['temperature1']) < 1e-10
    assert abs(data_copy['humidity1'] - calibrated['humidity1']) < 1e-10
    assert data_copy['dewpoint1'] == calibrated['dewpoint1']
    assert abs(data_copy['temperature2'] - calibrated['temperature2']) < 1e-10
    assert abs(data_copy['humidity2'] - calibrated['humidity2']) < 1e-10
    assert data_copy['dewpoint2'] == calibrated['dewpoint2']

    for report in utils.find_reports(calibrations, '56789', nearest='2018-07-21'):
        data2_copy = utils.apply_calibration(data2_copy, report)
    assert data2_copy['error'] is calibrated['error']
    assert data2_copy['alias'] == calibrated['alias']
    assert data2_copy['timestamp'] == calibrated['timestamp']
    assert abs(data2_copy['temperature1'] - calibrated['temperature1']) < 1e-10
    assert abs(data2_copy['humidity1'] - calibrated['humidity1']) < 1e-10
    assert data2_copy['dewpoint1'] == calibrated['dewpoint1']
    assert abs(data2_copy['temperature2'] - calibrated['temperature2']) < 1e-10
    assert abs(data2_copy['humidity2'] - calibrated['humidity2']) < 1e-10
    assert data2_copy['dewpoint2'] == calibrated['dewpoint2']


def test_apply_calibration_8():
    _, calibrations, _ = utils.initialize_webapp(cfg, serials)

    data1 = {
        'error': 'yes',
        'alias': '',
        'timestamp': '2020-11-30 10:13:42',
        'temperature': None,
        'humidity': None,
        'dewpoint': None,
    }

    report = utils.find_report(calibrations['b'])
    data1_out = utils.apply_calibration(data1, report)
    assert data1_out['error'] == 'yes'
    assert len(data1_out['alias']) == 0
    assert data1_out['timestamp'] == '2020-11-30 10:13:42'
    assert data1_out['temperature'] is None
    assert data1_out['humidity'] is None
    assert data1_out['dewpoint'] is None

    data2 = {
        'error': 'abc123',
        'alias': 'xyZ',
        'timestamp': '2021-06-11 03:12:19',
        'temperature1': None,
        'humidity1': None,
        'dewpoint1': None,
        'temperature2': None,
        'humidity2': None,
        'dewpoint2': None,
    }

    report1 = utils.find_report(calibrations['f - Probe 1'])
    report2 = utils.find_report(calibrations['f - Probe 2'])
    data2_out = utils.apply_calibration(utils.apply_calibration(data2, report1), report2)
    assert data2_out['error'] == 'abc123'
    assert data2_out['alias'] == 'xyZ'
    assert data2_out['timestamp'] == '2021-06-11 03:12:19'
    assert data2_out['temperature1'] is None
    assert data2_out['humidity1'] is None
    assert data2_out['dewpoint1'] is None
    assert data2_out['temperature2'] is None
    assert data2_out['humidity2'] is None
    assert data2_out['dewpoint2'] is None

    data3 = {
        'error': 'abc123',
        'alias': 'j knmc k',
        'timestamp': '2021-06-11 03:12:19',
        'temperature1': None,
        'humidity1': None,
        'dewpoint1': None,
        'temperature2': None,
        'humidity2': None,
        'dewpoint2': None,
    }

    for report in utils.find_reports(calibrations, '56789'):
        data3 = utils.apply_calibration(data3, report)
    assert data3['error'] == 'abc123'
    assert data3['alias'] == 'j knmc k'
    assert data3['timestamp'] == '2021-06-11 03:12:19'
    assert data3['temperature1'] is None
    assert data3['humidity1'] is None
    assert data3['dewpoint1'] is None
    assert data3['temperature2'] is None
    assert data3['humidity2'] is None
    assert data3['dewpoint2'] is None

    data4 = {
        'error': 'yes',
        'alias': 'alias',
        'timestamp': '2020-11-30 10:13:42',
        'temperature': None,
        'humidity': None,
        'dewpoint': None,
    }
    for report in utils.find_reports(calibrations, '01234'):
        data4 = utils.apply_calibration(data4, report)
    assert data4['error'] == 'yes'
    assert data4['alias'] == 'alias'
    assert data4['timestamp'] == '2020-11-30 10:13:42'
    assert data4['temperature'] is None
    assert data4['humidity'] is None
    assert data4['dewpoint'] is None


def test_human_file_size():
    assert utils.human_file_size(0) == '0 B'
    assert utils.human_file_size(1) == '1 B'
    assert utils.human_file_size(2) == '2 B'
    assert utils.human_file_size(10) == '10 B'
    assert utils.human_file_size(210) == '210 B'
    assert utils.human_file_size(3210) == '3 kB'
    assert utils.human_file_size(43210) == '43 kB'
    assert utils.human_file_size(543210) == '543 kB'
    assert utils.human_file_size(6543210) == '7 MB'
    assert utils.human_file_size(76543210) == '77 MB'
    assert utils.human_file_size(876543210) == '877 MB'
    assert utils.human_file_size(9876543210) == '10 GB'


def test_datetime_range_picker_kwargs():
    today = datetime.today()
    kwargs = utils.datetime_range_picker_kwargs(cfg)

    start = today + timedelta(weeks=-1, days=-10)
    assert isinstance(kwargs['start'], datetime)
    assert kwargs['start'].year == start.year
    assert kwargs['start'].month == start.month
    assert kwargs['start'].day == start.day
    assert kwargs['start'].hour == 7
    assert kwargs['start'].minute == 0
    assert kwargs['start'].second == 22

    end = today + timedelta(weeks=1, days=1)
    assert isinstance(kwargs['end'], datetime)
    assert kwargs['end'].year == end.year
    assert kwargs['end'].month == end.month
    assert kwargs['end'].day == end.day
    assert kwargs['end'].hour == 0
    assert kwargs['end'].minute == 1
    assert kwargs['end'].second == 0

    max_date = today + timedelta(days=23)
    assert isinstance(kwargs['max_date'], datetime)
    assert kwargs['max_date'].year == max_date.year
    assert kwargs['max_date'].month == max_date.month
    assert kwargs['max_date'].day == max_date.day

    min_date = today + timedelta(weeks=-100, days=3)
    assert isinstance(kwargs['min_date'], datetime)
    assert kwargs['min_date'].year == min_date.year
    assert kwargs['min_date'].month == min_date.month
    assert kwargs['min_date'].day == min_date.day

    assert kwargs['date_format'] == 'D MMM YYYY'
    assert kwargs['time_format'] == 'h:mm:ss a'
    assert kwargs['date_style'] == {'color': '#514EA6', 'fontSize': '32px'}
    assert kwargs['time_style'] == {'color': '#027368', 'fontSize': '24px'}
    assert kwargs['arrow'] == {'width': '50px', 'height': '70px', 'color': '#025159'}
    assert kwargs['class_name'] == 'datetime-range-right'
    assert kwargs['text'] == 'Refresh'


def test_datetime_range_picker_kwargs_config_minimal():
    # the 'config_minimal.xml' file does not contain any of the Optional XML elements
    cfg_min = Config(os.path.join(resources, 'config_minimal.xml'))
    kwargs = utils.datetime_range_picker_kwargs(cfg_min)
    assert isinstance(kwargs, dict)
    assert not kwargs
