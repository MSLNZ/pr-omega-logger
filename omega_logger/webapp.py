"""
Start the Dash app.
"""
import os
import re
import sys
import socket
import tempfile
import traceback
from math import floor, ceil
from datetime import datetime
from difflib import get_close_matches
from concurrent.futures import ThreadPoolExecutor

import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
import plotly.graph_objs as go
from gevent.pywsgi import WSGIServer
from msl.equipment import Config
from dash.dependencies import (
    Input,
    Output,
    State,
)
from flask import (
    request,
    jsonify,
    current_app,
    render_template,
    make_response,
    has_request_context,
)

from utils import (
    fromisoformat,
    initialize_webapp,
    find_report,
    find_reports,
    read_database,
    apply_calibration,
    HTMLTable,
    datetime_range_picker_kwargs,
)
from omega_logger import __version__
from datetime_range_picker import DatetimeRangePicker


def serve_layout():
    return html.Div([
        html.A(
            id='api-help-link',
            children='?',
            href=f'{request.url_root}help' if has_request_context() else '',
            target='_blank',
            title='View the API documentation',
            style={
                'color': '#fff',
                'background-color': '#f15A29',
                'width': 16,
                'height': 16,
                'display': 'inline-block',
                'border-radius': '100%',
                'font-size': 16,
                'text-align': 'center',
                'text-decoration': 'none',
                'box-shadow': 'inset -2px -2px 1px 0px rgba(0,0,0,0.25)',
                'margin-left': '98%',
                'margin-bottom': 4,
            }
        ),
        dcc.Dropdown(
            id='omega-dropdown',
            options=dropdown_options,
            multi=True,
            placeholder='Select the OMEGA iServer(s)...',
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


def read_raw(omega):
    """Read the raw temperature, humidity and dewpoint values from an OMEGA iServer.

    Parameters
    ----------
    omega : :class:`msl.equipment.record_types.EquipmentRecord`
        The Equipment Record of an OMEGA iServer.

    Returns
    -------
    :class:`str`
        The serial number of the OMEGA iServer.
    :class:`dict`
        The data.
    """
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
    data = {
        'error': error,
        'alias': omega.alias,
        'timestamp': timestamp,
        'report_number': None,
    }
    if len(thd) == 3:
        data.update({
            'temperature': thd[0], 'humidity': thd[1], 'dewpoint': thd[2]
        })
    else:
        data.update({
            'temperature1': thd[0], 'humidity1': thd[1], 'dewpoint1': thd[2],
            'temperature2': thd[3], 'humidity2': thd[4], 'dewpoint2': thd[5]
        })

    return omega.serial, data


@app.server.route('/<string:path1>/')
@app.server.route('/<string:path1>/<path:path2>/')
def page_not_found(**ignore):
    """Return page not found for all undefined routes."""
    return make_response(
        render_template('page_not_found.html', url_root=request.url_root),
        404
    )


@app.server.route('/aliases/')
def aliases():
    """<p>Get the aliases of the OMEGA iServers.</p>

    <h4>Returns</h4>
    <p>The keys are the serial numbers of each iServer and
    the values are the aliases.</p>

    <p><i>Example:</i></p>
    <div class="highlight-console"><div class="highlight"><span class="go">
<pre>{
  "12345": "Photometric bench",
  "6789": "Mass2"
}</pre></span></div></div>
    """
    data = dict((value.serial, value.alias) for value in omegas.values())
    return jsonify(data)


@app.server.route('/now/')
def now():
    """<p>Get the current temperature, humidity and dewpoint of the
    requested OMEGA iServer(s).</p>

    <h3>Parameters</h3>
    <ul>
      <li>
        <b>serial</b> : string (optional)
        <p>The serial number(s) of the OMEGA iServer(s) to get the data from.
        If requesting data from multiple iServers then the serial numbers must
        be separated by a semi-colon.</p>
      </li>
      <li>
        <b>alias</b> : string (optional)
        <p>The alias(es) of the OMEGA iServer(s) to get the data from.
        If requesting data from multiple iServers then the aliases must
        be separated by a semi-colon.</p>
      </li>
      <li>
        <b>corrected</b> : integer or boolean (optional)
        <p>Whether to apply the calibration equation to the data.
        Default is <i>true</i>.</p>
      </li>
    </ul>

    <p><i>Examples:</i></p>
    <ul>
      <li>
        <b>/now</b>
        <p>Return the corrected data from all OMEGA iServers.</p>
      </li>
      <li>
        <b>/now?corrected=false</b>
        <p>Return the uncorrected data from all OMEGA iServers.</p>
      </li>
      <li>
        <b>/now?serial=12345</b>
        <p>Return the corrected data from the OMEGA iServer that
        has the serial number <i>12345</i>.</p>
      </li>
      <li>
        <b>/now?alias=Mass2</b>
        <p>Return the corrected data from the OMEGA iServer that
        has the alias <i>Mass2</i>.</p>
      </li>
      <li>
        <b>/now?alias=Photometric+bench</b>
        <p>Return the corrected data from the OMEGA iServer that
        has the alias <i>Photometric bench</i>.</p>
      </li>
      <li>
        <b>/now?serial=12345&corrected=0</b>
        <p>Return the uncorrected data from the OMEGA iServer that
        has the serial number <i>12345</i>.</p>
      </li>
      <li>
        <b>/now?alias=Photometric+bench&corrected=false</b>
        <p>Return the uncorrected data from the OMEGA iServer that
        has the alias <i>Photometric bench</i>.</p>
      </li>
      <li>
        <b>/now?serial=12345;6789</b>
        <p>Return the corrected data from the OMEGA iServer that
        has the serial number <i>12345</i> and from the OMEGA iServer
        that has the serial number <i>6789</i>.</p>
      </li>
      <li>
        <b>/now?serial=12345&alias=Mass2&corrected=0</b>
        <p>Return the uncorrected data from the OMEGA iServer that
        has the serial number <i>12345</i> and from the OMEGA iServer
        that has the alias <i>Mass2</i>.</p>
      </li>
    </ul>

    <h4>Returns</h4>
    <p>The keys are the serial numbers of the requested
    iServers and the value depends on whether the iServer
    has 1 or 2 probes and whether an error occurred requesting
    the data.</p>
    <p><i>Example:</i></p>
    <div class="highlight-console"><div class="highlight"><span class="go">
<pre>{
  "12345": {
    "alias": "Photometric bench",
    "dewpoint": 9.6,
    "error": null,
    "humidity": 51.3,
    "report_number": null,
    "temperature": 20.0,
    "timestamp": "2021-08-16T13:36:34"
},
  "6789": {
    "alias": "Mass2",
    "dewpoint1": null,
    "dewpoint2": null,
    "error": "Timeout occurred after 10.0 seconds",
    "humidity1": null,
    "humidity2": null,
    "report_number": null,
    "temperature1": null,
    "temperature2": null,
    "timestamp": "2021-08-16T13:36:44"
  }
}</pre></span></div></div>
    """
    allowed_params = ('alias', 'corrected', 'serial')
    for k, v in request.args.items():
        if k not in allowed_params:
            allowed = ', '.join(allowed_params)
            return f'Invalid parameter: {k!r}<br/>' \
                   f'Valid parameters are: {allowed}', 400

    apply_corr = request.args.get('corrected', 'true').lower() in ['true', '1']

    requested = set()
    for name in ('serial', 'alias'):
        value = request.args.get(name)
        if value:
            for element in value.split(';'):
                if element:
                    requested.add(element)

    records = []
    for serial, omega in omegas.items():
        if requested and not requested.intersection({serial, omega.alias}):
            continue
        records.append(omega)

    with ThreadPoolExecutor() as executor:
        futures = [executor.submit(read_raw, record) for record in records]
        data = dict(f.result() for f in futures)

    if apply_corr:
        corrected = dict()
        for serial, values in data.items():
            reports = find_reports(calibrations, serial)
            for report in reports:
                values = apply_calibration(values, report)
            corrected[serial] = values
            corrected[serial]['report_number'] = ';'.join(r.number for r in reports)
        return jsonify(corrected)
    return jsonify(data)


@app.server.route('/fetch/')
def fetch():
    """<p>Fetch the temperature, humidity and/or dewpoint values from the database
    between start and end dates for the requested OMEGA iServer(s).</p>

    <h3>Parameters</h3>
    <ul>
      <li>
        <b>start</b> : string (optional)
        <p>Start date and time as an ISO 8601 string (e.g., YYYY-MM-DD or YYYY-MM-DDThh:mm:ss).
        Default is the earliest record in the database.</p>
      </li>
      <li>
        <b>end</b> : string (optional)
        <p>End date and time as an ISO 8601 string. Default is now.</p>
      </li>
      <li>
        <b>type</b> : string (optional)
        <p>The type of data to retrieve (e.g., temperature, humidity, dewpoint).
        Default is all three. Include multiple types by using a <b>+</b> sign,
        a comma or a semi-colon as the separator.</p>
      </li>
      <li>
        <b>serial</b> : string (optional)
        <p>The serial number(s) of the OMEGA iServer(s) to get the data from.
        If requesting data from multiple iServers then the serial numbers must
        be separated by a semi-colon.</p>
      </li>
      <li>
        <b>alias</b> : string (optional)
        <p>The alias(es) of the OMEGA iServer(s) to get the data from.
        If requesting data from multiple iServers then the aliases must
        be separated by a semi-colon.</p>
      </li>
      <li>
        <b>corrected</b> : integer or boolean (optional)
        <p>Whether to apply the calibration equation to the data.
        Default is <i>true</i>.</p>
      </li>
    </ul>

    <p><i>Examples:</i></p>
    <ul>
      <li>
        <b>/fetch</b>
        <p>Return all available corrected values for temperature, humidity,
        and dewpoint since logging began, from all OMEGA iServers.</p>
      </li>
      <li>
        <b>/fetch?serial=12345&start=2021-02-16T19:20:30</b>
        <p>Return the corrected temperature, humidity, and dewpoint values
        since <i>19:20:30 on the 16th Feb 2021</i> from the OMEGA iServer
        that has the serial number <i>12345</i>.</p>
      </li>
      <li>
        <b>/fetch?alias=Mass2&start=2021-02-16T19:20:30</b>
        <p>Return the corrected temperature, humidity, and dewpoint values
        since <i>19:20:30 on the 16th Feb 2021</i> from the OMEGA iServer
        that has the alias <i>Mass2</i>.</p>
      </li>
      <li>
        <b>/fetch?serial=12345&corrected=0&start=2021-02-16T09:20:30&type=temperature</b>
        <p>Return the uncorrected temperature values since <i>09:20:30 on the 16th Feb 2021</i>
        from the OMEGA iServer that has the serial number <i>12345</i>.</p>
      </li>
      <li>
        <b>/fetch?alias=Mass2&start=2021-02-16&end=2021-02-17&type=temperature+humidity</b>
        <p>Return the corrected temperature and humidity values between <i>16th Feb 2021</i>
        and <i>17th Feb 2021</i> from the OMEGA iServer that has the alias <i>Mass2</i>.</p>
      </li>
    </ui>
    """
    allowed_params = ['start', 'end', 'serial', 'alias', 'corrected', 'type']
    for k, v in request.args.items():
        if k not in allowed_params:
            allowed = ', '.join(allowed_params)
            return f'Invalid parameter: {k!r}<br/>' \
                   f'Valid parameters are: {allowed}', 400

    timestamps = {}
    for kwg in ['start', 'end']:
        time_arg = request.args.get(kwg)
        try:
            timestamps[kwg] = fromisoformat(time_arg).isoformat(sep=' ')
        except TypeError:
            if kwg == 'start':
                timestamps[kwg] = None
            else:
                timestamps[kwg] = datetime.now().replace(microsecond=0).isoformat(sep=' ')
        except ValueError:
            return f'The value for {kwg!r} must be an ISO 8601 string ' \
                   f'(e.g., YYYY-MM-DD or YYYY-MM-DDThh:mm:ss).<br/>'\
                   f'Received {time_arg!r}', 400

    apply_corr = request.args.get('corrected', 'true').lower() in ['true', '1']

    known_types = ['temperature', 'humidity', 'dewpoint']
    types = []

    error = ''
    type_vals = request.args.get('type')
    if type_vals is not None:  # parse types to check they're spelled correctly (or find close match)
        for t in re.split(r'[\s,;]', type_vals):
            if not t:
                continue
            match = get_close_matches(t, known_types, cutoff=0.5)
            if match:
                types.append(match[0])
            else:
                error += t + ","

    if not types:
        types = known_types
    if error:
        error = f"Unknown type value(s) received: {error}".strip(",")
    else:
        error = None  # maintain consistency with other methods

    requested = set()
    for name in ('serial', 'alias'):
        value = request.args.get(name)
        if value:
            for element in value.split(';'):
                if element:
                    requested.add(element)

    fetched = dict()
    for serial, omega in omegas.items():
        if requested and not requested.intersection({serial, omega.alias}):
            continue

        reports = find_reports(calibrations, serial)
        nprobes = omega.connection.properties.get('nprobes', 1)

        fetched[serial] = {
            'alias': omega.alias,
            'start': timestamps['start'],
            'end': timestamps['end'],
            'error': error,
            'report_number': None if not apply_corr else ';'.join(r.number for r in reports),
        }
        for report in reports:
            for typ in types:
                data, message = read_database(report, typ, date1=timestamps['start'], date2=timestamps['end'])
                if apply_corr:
                    data = apply_calibration(data, report)
                if nprobes == 1:
                    fetched[serial].update({typ: data.tolist()})
                else:
                    fetched[serial].update({typ + report.probe: data.tolist()})

    return jsonify(fetched), 200


@app.server.route('/help/')
def api_help():
    """Display the help for each API endpoint."""
    docs = [{'name': route.__name__, 'value': route.__doc__} for route in [aliases, now, fetch]]
    return render_template('help.html', docs=docs, version=__version__, url_root=request.url_root)


@app.server.route('/download/')
def download():
    """Download a CSV file of the data in the plot.

    This route is not meant to be called directly. Clicking the
    Download link that is provided on the web page is the proper
    way to download the data in the plot as a CSV file.
    """
    filename = f'{request.remote_addr}.csv'
    file_path = os.path.join(tempfile.gettempdir(), filename)
    if not os.path.isfile(file_path):
        return make_response(
            render_template('direct_download.html', url_root=request.url_root),
            400
        )

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


@app.callback(
    Output('current-readings-viewer', 'children'),
    [Input('tabs', 'value'),
     Input('current-readings-interval', 'n_intervals')])
def current_readings_viewer(tab, n_intervals):
    if tab != 'current-readings':
        return

    n = n_intervals or 0  # n_intervals is initially None
    n += 1

    children = []
    margin_right = cfg.value('current_readings/margin_right', '16px')
    for serial, data in now().json.items():
        b = f'{serial} [{data["report_number"]}] - {data["alias"]} @ {data["timestamp"][11:]}'
        children.append(html.B(b))
        if data['error']:
            children.append(html.P(data['error']))
        elif 'temperature2' in data.keys():
            for sensor in ['1', '2']:
                p = []
                for key in 'temperature' + sensor, 'humidity' + sensor, 'dewpoint' + sensor:
                    p.append(html.Span(key + ':', style={'color': 'grey'}))
                    p.append(html.Span(f'{data[key]:.2f}', style={'margin-right': margin_right}))
                children.append(html.P(p))
        else:
            p = []
            for key in sorted(data):
                if key in ['error', 'alias', 'timestamp', 'report_number']:
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
    log = None if cfg.value('disable_request_logging') else 'default'
    with WSGIServer((host, port), application=app.server, log=log) as server:
        print(f'Serving at http://{host}:{port}')
        server.serve_forever()
except KeyboardInterrupt:
    pass
except:
    traceback.print_exc(file=sys.stderr)
    input('Press <ENTER> to close ...')
