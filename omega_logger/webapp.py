"""
Start the Dash app.
"""
#import io
import os
import re
import sys
import time
import socket
import logging
import traceback
from math import floor, ceil
from datetime import datetime

#import flask
import numpy as np
import dash
import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output
import plotly.graph_objs as go
from gevent.pywsgi import WSGIServer

from msl.equipment import Config
from msl.equipment.resources.omega.ithx import iTHX

logging.basicConfig(
    level=logging.INFO,
    format='                 [%(asctime)s] "%(message)s"',
    datefmt='%Y-%m-%d %H:%M:%S',
)


class CalibrationReport(object):

    def __init__(self, serial, report):
        self.serial = serial
        self.date = datetime.strptime(report.attrib['date'], '%Y-%m-%d')
        self.number = report.attrib['number']
        self.start_date = datetime.strptime(report.find('start_date').text, '%Y-%m-%d')
        self.end_date = datetime.strptime(report.find('end_date').text, '%Y-%m-%d')
        self.coverage_factor = float(report.find('coverage_factor').text)
        self.confidence = report.find('confidence').text
        for name in ['temperature', 'humidity']:
            e = report.find(name)
            d = {
                'units': e.attrib['units'],
                'min': float(e.attrib['min']),
                'max': float(e.attrib['max']),
                'coefficients': [float(val) for val in re.split(r'[;,]', e.find('coefficients').text)],
                'expanded_uncertainty': float(e.find('expanded_uncertainty').text),
            }
            setattr(self, name, d)

    def __str__(self):
        return '<CalibrationReport serial={} component={!r} number={!r}>'\
            .format(self.serial, self.component, self.number)


# get the info about the OMEGA loggers
dropdown_options = list()
calibrations = dict()
cfg = Config(sys.argv[1])
omegas = cfg.database().records(manufacturer='OMEGA')
for omega in sorted(omegas, key=lambda r: r.alias):
    dropdown_options.append({
        'label': omega.alias + ' - ' + omega.serial,
        'value': omega.model + '_' + omega.serial + '.sqlite3'
    })
    element = cfg.root.find('.//omega[@serial="%s"]' % omega.serial)
    calibrations[omega.serial] = [CalibrationReport(omega.serial, report) for report in element.findall('report')]


os.chdir(cfg.value('log_dir'))


def fetch_data(path, start, stop):
    t0 = time.time()
    values = iTHX.data(path, date1=start, date2=stop, as_datetime=False)
    message = 'Fetched %d records in %.3f seconds' % (len(values), time.time() - t0)
    dtype = [('timestamp', 'U19'), ('temperature', float), ('humidity', float), ('dewpoint', float)]
    data = np.asarray(values, dtype=dtype)
    return data, message


def div_timestamp(prefix):
    now = datetime.now()
    return html.Div([
        html.Div(
            dcc.DatePickerSingle(
                id=prefix+'-date',
                date=now.strftime('%Y-%m-%d'),
                display_format='YYYY-MM-DD',
            ),
            title=prefix.title() + ': Date',
            style={'display': 'inline-block'},
        ),
        html.Div(
            dcc.Dropdown(
                id=prefix+'-hour',
                options=[{'label': '%02d' % i, 'value': '%02d' % i} for i in range(24)],
                value='00' if prefix == 'from' else '%02d' % now.hour,
                clearable=False,
            ),
            title=prefix.title() + ': Hour',
            style={'display': 'inline-block', 'vertical-align': 'middle', 'paddingLeft': '0.2%'},
        ),
        html.Div(
            dcc.Dropdown(
                id=prefix+'-minute',
                options=[{'label': '%02d' % i, 'value': '%02d' % i} for i in range(60)],
                value='00' if prefix == 'from' else '%02d' % now.minute,
                clearable=False,
            ),
            title=prefix.title() + ': Minute',
            style={'display': 'inline-block', 'vertical-align': 'middle', 'paddingLeft': '0.2%'},
        ),
        html.Div(
            dcc.Dropdown(
                id=prefix+'-second',
                options=[{'label': '%02d' % i, 'value': '%02d' % i} for i in range(60)],
                value='00',
                clearable=False,
            ),
            title=prefix.title() + ': Second',
            style={'display': 'inline-block', 'vertical-align': 'middle', 'paddingLeft': '0.2%'},
        ),
        html.Div(
            html.Button('Now', id='now-button', title='Set the To timestamp to now'),
            style={'display': 'inline-block', 'vertical-align': 'middle', 'paddingLeft': '0.2%'},
        ) if prefix == 'to' else None
    ])


def serve_layout():
    return html.Div([
        dcc.Dropdown(
            id='omega-dropdown',
            options=dropdown_options,
            multi=True,
            placeholder='Select the OMEGA logger(s)...',
        ),
        html.Div([
            html.Div(div_timestamp('from'), style={'display': 'inline-block', 'width': '50%'}),
            html.Div(div_timestamp('to'), style={'display': 'inline-block', 'width': '50%'}),
        ]),
        dcc.Tabs(
            id='tabs',
            value='temperature',
            children=[
                dcc.Tab(
                    label='Temperature',
                    value='temperature'
                ),
                dcc.Tab(
                    label='Humidity',
                    value='humidity'
                ),
                dcc.Tab(
                    label='Dewpoint',
                    value='dewpoint'
                )
            ],
            style={'display': 'inline-block'},
        ),
        html.A(
            'Download',
            id='download-link',
            download='omega-data.csv',
            href='',
            target='_blank',
            title='Download the data in the plot\n'
                  '* Not supported in Internet Explorer\n'
                  '* Chrome limit is #points < 78,000 (i.e., a < 2MB CSV file)'
        ),
        html.Div(id='plot-viewer'),
    ])


# create the application
app = dash.Dash()
app.title = 'OMEGA Loggers'
app.layout = serve_layout  # set app.layout to a function to serve a dynamic layout on every page load


@app.callback(Output('download-link', 'href'), [Input('plot-viewer', 'children')])
def update_download_link(children):
    data = children[0]['props']['figure']['data']
    title = children[0]['props']['figure']['layout']['title']['text']
    if not data:
        csv_string = ''
    else:
        nrows = max(len(plot['x']) for plot in data)
        ncols = 2 * len(data)

        csv_data = np.asarray(
            [[item for plot in data for item in (plot['name'], '')],
             [item for _ in data for item in ('Timestamp', title)]] +
            [[''] * ncols] * nrows
        )

        for i, plot in enumerate(data):
            n = len(plot['x'])
            csv_data[2:n+2, 2*i] = plot['x']
            csv_data[2:n+2, 2*i+1] = plot['y']

        # use '%0A' instead of '\n' if using the flask.send_file method
        csv_string = '\n'.join(','.join(row) for row in csv_data)

    logging.info('size(csv_string)={} MB'.format(len(csv_string)/1e6))

    return 'data:text/csv;charset=utf-8,' + csv_string
    #return '/data/download?value={}'.format(csv_string)


#@app.server.route('/data/download')
#def download_csv():
#    value = flask.request.args.get('value')
#    mem = io.BytesIO()
#    mem.write(value.encode())
#    mem.seek(0)
#    return flask.send_file(
#        mem,
#        mimetype='text/csv',
#        attachment_filename='omega_logger-data.csv',
#        as_attachment=True,
#    )


@app.callback(
    Output('plot-viewer', 'children'),
    [Input('tabs', 'value'),
     Input('omega-dropdown', 'value'),
     Input('from-date', 'date'),
     Input('from-hour', 'value'),
     Input('from-minute', 'value'),
     Input('from-second', 'value'),
     Input('to-date', 'date'),
     Input('to-hour', 'value'),
     Input('to-minute', 'value'),
     Input('to-second', 'value'),])
def value_changed(*args):
    tab = args[0]
    sqlite_databases = args[1]
    date1 = '{} {}:{}:{}'.format(*args[2:6])
    date2 = '{} {}:{}:{}'.format(*args[6:])
    plots = []
    y_range = [sys.maxsize, -sys.maxsize]
    table = [html.Tr([html.Th('OMEGA logger'), html.Th('Report No.'), html.Th('Description'), html.Th('Average'),
                      html.Th('Stdev'), html.Th('Median'), html.Th('Max'), html.Th('Min'), html.Th('# Points')])]
    if sqlite_databases:
        row = 0
        for db in sqlite_databases:
            name = [item['label'] for item in dropdown_options if item['value'] == db][0]
            data, message = fetch_data(db, date1, date2)
            logging.info('{} -> {}'.format(db, message))

            # get the results from the latest Calibration Report
            serial = name.split('-')[1].strip()
            report = None
            for r in calibrations[serial]:
                if report is None or r.start_date > report.start_date:
                    report = r

            # apply the calibration correction
            for item in ('temperature', 'humidity'):
                coefficients = getattr(report, item)['coefficients']
                correction = coefficients[0] * np.ones(data[item].size)
                for n, c in enumerate(coefficients[1:], start=1):
                    correction += c * data[item]**n
                data[item] += correction

            for item in ('temperature', 'humidity', 'dewpoint'):
                report_number = '<uncorrected>' if item == 'dewpoint' else report.number
                row += 1
                if data[item].size > 0:

                    # if the max or min values are outside of the range that was used
                    # in the calibration report then change the color of the row
                    style, mx, mn = None, np.max(data[item]), np.min(data[item])
                    if item != 'dewpoint':
                        obj = getattr(report, item)
                        if mx > obj['max'] or mn < obj['min']:
                            style = dict(backgroundColor='#FF0000')

                    table.append(
                        html.Tr([
                            html.Td(name, style=style),
                            html.Td(report_number, style=style),
                            html.Td(item.title() if not style else item.title() + ' [value out of range]', style=style),
                            html.Td('{:.1f}'.format(np.average(data[item])), style=style),
                            html.Td('{:.1f}'.format(np.std(data[item])), style=style),
                            html.Td('{:.1f}'.format(np.median(data[item])), style=style),
                            html.Td('{:.1f}'.format(mx), style=style),
                            html.Td('{:.1f}'.format(mn), style=style),
                            html.Td('{}'.format(data[item].size), style=style),
                        ], style=dict(backgroundColor='#F2F2F2' if row % 2 else '#FFFFFF'))
                    )
                else:
                    table.append(
                        html.Tr([
                            html.Td(name),
                            html.Td(report_number),
                            html.Td(item.title()),
                            html.Td(''),
                            html.Td(''),
                            html.Td(''),
                            html.Td(''),
                            html.Td(''),
                            html.Td('0'),
                        ], style=dict(backgroundColor='#F2F2F2' if row % 2 else '#FFFFFF'))
                    )

        plots.append(
            go.Scatter(
                x=data['timestamp'],
                y=data[tab],
                name=name,  # the name displayed in the legend
            )
        )

        # if there is no data for the specified date range then calling
        # np.min or np.max will raise the following exception
        #   ValueError: zero-size array to reduction operation minimum which has no identity
        if data[tab].size > 0:
            y_range = [
                min(np.min(data[tab]), y_range[0]),
                max(np.max(data[tab]), y_range[1])
            ]

    # want the y_range values to be nice numbers like 20.1 not 20.0913136
    if y_range[0] == sys.maxsize:
        y_range = [0, 1]
    else:
        factor = 10.
        y_range = [floor(y_range[0]*factor)/factor, ceil(y_range[1]*factor)/factor]

    return [
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
            children=table,
            style=dict(width='100%', border='2px solid black', textAlign='center'),
        ),
    ]


@app.callback(Output('to-second', 'value'), [Input('now-button', 'n_clicks')])
def now_second(n_clicks):
    return datetime.now().strftime('%S')


@app.callback(Output('to-minute', 'value'), [Input('now-button', 'n_clicks')])
def now_minute(n_clicks):
    return datetime.now().strftime('%M')


@app.callback(Output('to-hour', 'value'), [Input('now-button', 'n_clicks')])
def now_hour(n_clicks):
    return datetime.now().strftime('%H')


@app.callback(Output('to-date', 'date'), [Input('now-button', 'n_clicks')])
def now_date(n_clicks):
    return datetime.now().strftime('%Y-%m-%d')


host = cfg.value('host', default=socket.gethostname())
port = cfg.value('port', default=1875)

try:
    http_server = WSGIServer((host, port), app.server)
except:
    traceback.print_exc(file=sys.stdout)
    input('Press <ENTER> to close ...')
else:
    logging.info('Serving at http://{}:{}'.format(host, port))
    try:
        http_server.serve_forever()
    except Exception:
        traceback.print_exc(file=sys.stderr)
        input('Press <ENTER> to close ...')
    except KeyboardInterrupt:
        pass
