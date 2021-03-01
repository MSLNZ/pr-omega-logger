"""
Start the Dash app.
"""
import os
import sys
import socket
import logging
import tempfile
import traceback
from math import floor, ceil
from datetime import datetime

import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output, State
import plotly.graph_objs as go
from gevent.pywsgi import WSGIServer
from flask import request, jsonify, current_app
from msl.equipment import Config

from utils import (
    human_file_size,
    fromisoformat,
    initialize_webapp,
    find_report,
    find_reports,
    read_database,
    apply_calibration,
    HTMLTable,
    datetime_range_picker_kwargs,
)
from datetime_range_picker import DatetimeRangePicker

logging.basicConfig(
   level=logging.INFO,
   format='%(asctime)s [%(levelname)5s] %(message)s',
   datefmt='%Y-%m-%d %H:%M:%S',
)


def serve_layout():
    return html.Div([
        dcc.Dropdown(
            id='omega-dropdown',
            options=dropdown_options,
            multi=True,
            placeholder='Select the OMEGA logger(s)...',
        ),
        DatetimeRangePicker(
            id='datetime-range',
            **datetime_range_picker_kwargs(cfg)
        ),
        dcc.Tabs(
            id='tabs',
            value='temperature',
            children=[
                dcc.Tab(label='Current Readings', value='current-readings'),
                dcc.Tab(label='Temperature', value='temperature'),
                dcc.Tab(label='Humidity', value='humidity'),
                dcc.Tab(label='Dewpoint', value='dewpoint'),
            ],
            style={'display': 'inline-block'},
        ),
        html.Div(id='plot-viewer'),
        html.Div(id='current-readings-viewer'),
        dcc.Interval(
            id='current-readings-interval',
            interval=cfg.value('current_readings/interval', 10) * 1000,
        ),
    ])


try:
    path, serials = sys.argv[1:]
    cfg = Config(path)
    dropdown_options, calibrations, omegas = initialize_webapp(cfg, serials)
except:
    traceback.print_exc(file=sys.stderr)
    input('Press <ENTER> to close ...')
    sys.exit(1)

app = dash.Dash()
app.title = 'OMEGA iServers'
app.layout = serve_layout  # set app.layout to a function to serve a dynamic layout on every page load
app.server.config['JSONIFY_PRETTYPRINT_REGULAR'] = True


@app.server.route('/aliases')
def aliases():
    """Get the aliases of the OMEGA iServer's.

    Examples
    --------
    /aliases
        Return the aliases that are used. The keys are the serial numbers
        of each OMEGA iServer and the values are the aliases.
    """
    logging.info(f'[{request.remote_addr}] {request.full_path}')
    data = dict((value.serial, value.alias) for value in omegas.values())
    return jsonify(data)


@app.server.route('/now')
def now():
    """Get the current temperature, humidity and dewpoint values.

    Endpoint
    --------
    /now[?[serial=][alias=][corrected=true]]

    serial: the serial number of the OMEGA iServer to get the values from.

    alias: the alias of the OMEGA iServer to get the values from.
      If a serial number is also specified then it gets precedence over
      the alias.

    corrected: whether to apply the calibration equation. Default is true.

    Examples
    --------
    /now
        Return the corrected values from all OMEGA devices.
    /now?serial=12345
        Return the corrected values from the OMEGA device that
        has the serial number 12345.
    /now?alias=Mass2
        Return the corrected values from the OMEGA device that
        has the alias Mass2.
    /now?corrected=false
        Return the uncorrected values from all OMEGA devices.
    /now?serial=12345&corrected=false
        Return the uncorrected values from the OMEGA device that
        has the serial number 12345.
    /now?alias=Mass2&corrected=false
        Return the uncorrected values from the OMEGA device that
        has the alias Mass2.
    """
    if request.full_path.startswith('/now'):  # the dcc.Interval callback also calls this function
        logging.info(f'[{request.remote_addr}] {request.full_path}')

    apply_corr = request.args.get('corrected', 'true').lower() == 'true'
    requested = request.args.get('serial')
    if not requested:
        requested = request.args.get('alias')

    data = dict()
    for serial, omega in omegas.items():
        if requested and requested not in [serial, omega.alias]:
            continue

        nprobes = omega.connection.properties.get('nprobes', 1)
        nbytes = omega.connection.properties.get('nbytes')

        error = None
        try:
            cxn = omega.connect()
            thd = cxn.temperature_humidity_dewpoint(probe=1, nbytes=nbytes)
            if nprobes == 2:
                thd += cxn.temperature_humidity_dewpoint(probe=2, nbytes=nbytes)
            cxn.disconnect()
        except Exception as e:
            error = str(e)
            thd = [None] * (nprobes * 3)

        timestamp = datetime.now().replace(microsecond=0).isoformat()
        data[serial] = {
            'error': error,
            'alias': omega.alias,
            'timestamp': timestamp
        }
        if len(thd) == 3:
            data[serial].update({
                'temperature': thd[0], 'humidity': thd[1], 'dewpoint': thd[2]
            })
        else:
            data[serial].update({
                'temperature1': thd[0], 'humidity1': thd[1], 'dewpoint1': thd[2],
                'temperature2': thd[3], 'humidity2': thd[4], 'dewpoint2': thd[5]
            })

    if apply_corr:
        corrected = dict()
        for serial, values in data.items():
            for report in find_reports(calibrations, serial):
                values = apply_calibration(values, report)
            corrected[serial] = values
        return jsonify(corrected)
    return jsonify(data)


@app.server.route('/fetch')
def fetch():
    """Get temperature, humidity and/or dewpoint values between start and end datetimes for a specified OMEGA iServer.

    Endpoint
    --------
    /fetch[?[start=][end=][serial=][alias=][corrected=true][typ=]]

    start: start date and time as an ISO 8601 string (e.g. YYYY-MM-DDThh:mm:ss). Default is earliest record in database.

    end: end date and time as an ISO 8601 string. Default is now.

    serial: the serial number of the OMEGA iServer to get the values from. Default is all available iServers.

    alias: the alias of the OMEGA iServer to get the values from.
      If a serial number is also specified then it gets precedence over
      the alias.

    corrected: whether to apply the calibration equation. Default is true.

    typ: the type of data to retrieve (e.g. temperature, humidity, dewpoint). Default is all three.

    Examples
    --------
    /fetch?
        Return all available corrected values for temperature, humidity, and dewpoint since logging began,
        from all OMEGA devices.
    /fetch?serial=12345&start=2021-02-16T19:20:30
        Return the corrected temperature, humidity, and dewpoint values since 19:20:30 on the 16th Feb 2021
        from the OMEGA device that has the serial number 12345.
    /fetch?alias=Mass+2&start=2021-02-16T19:20:30
        Return the corrected temperature, humidity, and dewpoint values since 19:20:30 on the 16th Feb 2021
        from the OMEGA device that has the alias Mass 2.
    /fetch?serial=12345&corrected=false&start=2021-02-16T19:20:30&typ=temperature
        Return the uncorrected temperature values since 19:20:30 on the 16th Feb 2021
        from the OMEGA device that has the serial number 12345.
    /fetch?alias=Mass+2&corrected=false&start=2021-02-16T12:00:00&end=2021-02-17T16:00:00&typ=humidity
        Return the uncorrected humidity values between 12:00:00 on the 16th Feb 2021 and 16:00:00 on the 17th Feb 2021
        from the OMEGA device that has the alias Mass 2.
    """
    if request.full_path.startswith('/fetch'):
        logging.info(f'[{request.remote_addr}] {request.full_path}')

    start = request.args.get('start')
    start_timestamp = fromisoformat(start).isoformat(sep=' ') if start else None

    end = request.args.get('end')
    end_timestamp = fromisoformat(end).isoformat(sep=' ') if end else datetime.now().replace(microsecond=0).isoformat(sep=' ')

    apply_corr = request.args.get('corrected', 'true').lower() == 'true'

    typ = request.args.get('typ')
    types = [typ] if typ else ['temperature', 'humidity', 'dewpoint']

    requested = request.args.get('serial')
    if not requested:
        requested = request.args.get('alias')

    fetched = dict()
    for serial, omega in omegas.items():
        if requested and requested not in [serial, omega.alias]:
            continue

        logging.info(f'Fetching data for {serial} {omega.alias}')

        nprobes = omega.connection.properties.get('nprobes', 1)

        fetched[serial] = {
            'alias': omega.alias,
            'start': start_timestamp,
            'end': end_timestamp,
            'error': error,
        }
        for report in find_reports(calibrations, serial):
            c = report.component
            for typ in types:
                logging.info(f'Reading {typ} data for {omega.alias} {c}')
                data, message = read_database(report, typ, date1=start_timestamp, date2=end_timestamp, label=None)
                if apply_corr:
                    logging.info(f'Applying {typ} correction from Report {report.number}')
                    data = apply_calibration(data, report)
                if nprobes == 1:
                    fetched[serial].update({typ: data.tolist()})
                else:
                    fetched[serial].update({typ + report.probe: data.tolist()})

        logging.info("Finished fetch")

    return jsonify(fetched), 200


@app.server.route('/download')
def download():
    """Download a CSV file of the data in the plot.

    This route is not meant to be called directly. Clicking the
    Download link that is provided on the web page is the proper
    way to download the data in the plot as a CSV file.
    """
    filename = f'{request.remote_addr}.csv'
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.isfile(file_path):
        return 'You cannot download the data this way.<br/>' \
               'Please use the download link that is provided', 400

    def stream_then_remove_file():
        yield from file_handle
        file_handle.close()
        os.remove(file_path)

    file_handle = open(file_path, mode='rt')
    return current_app.response_class(
        stream_then_remove_file(),
        headers={
            'Content-Type': 'text/csv',
            'Content-Disposition': 'attachment',
        }
    )


@app.callback(
    Output('current-readings-interval', 'disabled'),
    [Input('tabs', 'value')])
def update_interval_state(tab):
    return tab != 'current-readings'


@app.callback(
    Output('plot-viewer', 'children'),
    [Input('tabs', 'value'),
     Input('omega-dropdown', 'value'),
     Input('datetime-range', 'start'),
     Input('datetime-range', 'end')])
def update_plot_viewer(tab, dropdown, start, end):
    if tab == 'current-readings' or not start or not end:
        return []

    plots = []
    labels = dropdown or []  # dropdown values could be None, but we still need an iterable
    start_date = fromisoformat(start)
    end_date = fromisoformat(end)
    y_range = [sys.maxsize, -sys.maxsize]
    table = HTMLTable()
    for label in labels:
        # find the latest CalibrationReport
        report = find_report(calibrations[label])

        # fetch the data
        data, message = read_database(report, tab, date1=start_date, date2=end_date, label=label)
        logging.info(f'[{request.remote_addr}] {message}')

        # apply the calibration equation
        if tab != 'dewpoint':
            data = apply_calibration(data, report)

        # add the data to the HTML table
        table.append(data, report, label)

        # if there is no data for the specified date range then calling
        # np.min or np.max will raise the following exception
        #   ValueError: zero-size array to reduction operation minimum which has no identity
        if data[tab].size > 0:
            y_range = [
                min(np.min(data[tab]), y_range[0]),
                max(np.max(data[tab]), y_range[1])
            ]

        plots.append(
            go.Scatter(
                x=data['timestamp'],
                y=data[tab],
                name=label,  # the name displayed in the legend
            )
        )

    # want the y_range values to be nice numbers like 20.1 not 20.0913136
    if y_range[0] == sys.maxsize:
        y_range = [0, 1]
    else:
        factor = 10.
        y_range = [floor(y_range[0]*factor)/factor, ceil(y_range[1]*factor)/factor]

    return [
        html.A(
            id='download-link',
            children='Download',
            download='omega-logger-data.csv',
            href='/download',
            target='_blank',
            title='Download the data in the plot as a CSV file',
        ),
        dcc.Graph(
            id='plot',
            figure={
                'data': plots,
                'layout': go.Layout(
                    title=tab.title(),
                    xaxis={'title': 'Timestamp', 'type': 'date'},
                    yaxis={
                        'title': tab.title() + (' [%]' if tab == 'humidity' else ' [&#176;C]'),
                        'range': y_range,
                    },
                    hovermode='closest',
                    legend=dict(orientation='v', x=1, y=1),
                    # height=500,
                    margin=go.layout.Margin(autoexpand=True, l=75, r=0, b=75, t=50, pad=10)
                ),
            }
        ),
        html.Table(
            className='summary-table',
            children=table.get(),
            style=dict(width='100%', border='2px solid black', textAlign='center'),
        ),
    ]


@app.callback(
    Output('download-link', 'the_returned_value_is_not_used'),
    [Input('download-link', 'n_clicks'),
     State('plot', 'figure')])
def create_csv_file_for_download(n_clicks, figure):
    if n_clicks is None:
        return

    filename = f'{request.remote_addr}.csv'
    temp_file = os.path.join(tempfile.gettempdir(), filename)

    data = figure['data']
    title = figure['layout']['title']['text']

    if not data:  # avoid getting -> ValueError: max() arg is an empty sequence
        n_rows = 0
        n_cols = 0
    else:
        n_rows = max(len(plot['x']) for plot in data)
        n_cols = 2 * len(data)

    csv_data = np.asarray([
        # the first row is the name from the plot legend and then an empty column
        [item for plot in data for item in (plot['name'], '')],

        # the second row is the description of the X and Y values
        [item for _ in data for item in ('Timestamp', title)]] +

        # the remaining rows are for the X and Y values
        [[''] * n_cols] * n_rows
    )

    for i, plot in enumerate(data):
        n = len(plot['x'])
        csv_data[2:n+2, 2*i] = plot['x']
        csv_data[2:n+2, 2*i+1] = plot['y']

    np.savetxt(temp_file, csv_data, fmt='%s', delimiter=',')
    size = human_file_size(os.path.getsize(temp_file))
    logging.info(f'[{request.remote_addr}] Requested a {size} csv file')


@app.callback(
    Output('current-readings-viewer', 'children'),
    [Input('tabs', 'value'),
     Input('current-readings-interval', 'n_intervals')])
def current_readings_viewer(tab, n_intervals):
    if tab != 'current-readings':
        return

    n = n_intervals or 0  # n_intervals is initially None
    n += 1
    logging.info(f'[{request.remote_addr}] Current Readings #{n}')

    children = []
    margin_right = cfg.value('current_readings/margin_right', '16px')
    for serial, data in now().json.items():
        b = f'{serial} - {data["alias"]} @ {data["timestamp"][11:]}'
        children.append(html.B(b))
        if data['error']:
            children.append(html.P(data['error']))
        else:
            p = []
            for key in sorted(data):
                if key in ['error', 'alias', 'timestamp']:
                    continue
                p.append(html.I(key+':', style={'color': 'grey'}))
                p.append(html.Span(f'{data[key]:.2f}', style={'margin-right': margin_right}))
            children.append(html.P(p))
    return html.Div(
        children=children,
        style={'fontSize': cfg.value('current_readings/font_size', '24px')}
    )


try:
    host = cfg.value('host', default=socket.gethostname())
    port = cfg.value('port', default=1875)
    with WSGIServer((host, port), application=app.server, log=None) as server:
        logging.info(f'Serving at http://{host}:{port}')
        server.serve_forever()
except KeyboardInterrupt:
    pass
except:
    traceback.print_exc(file=sys.stderr)
    input('Press <ENTER> to close ...')
