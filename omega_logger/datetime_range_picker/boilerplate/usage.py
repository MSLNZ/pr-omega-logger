from datetime import (
    datetime,
    timedelta,
)

import dash
import dash_html_components as html
from dash.dependencies import (
    Input,
    Output,
)

from datetime_range_picker import DatetimeRangePicker

app = dash.Dash(__name__)

app.layout = html.Div([
    html.Div(id='output'),
    DatetimeRangePicker(
        id='datetime-range',
        start=datetime.today() - timedelta(days=2),
        end=datetime.today(),
        min_date=datetime.today() - timedelta(days=3),
        max_date=datetime.today() + timedelta(days=3),
        date_format='Do MMM YYYY',  # https://www.tutorialspoint.com/momentjs/momentjs_format.htm
        time_format='h:mm:ss a',
        date_style={'color': '#514EA6', 'fontSize': '32px'},
        time_style={'color': '#027368', 'fontSize': '24px'},
        arrow={'width': '100px', 'height': '70px', 'color': '#025159'},
        class_name='datetime-range-left',
        text='Now',
    ),
])


@app.callback(
    Output('output', 'children'),
    [Input('datetime-range', 'start'),
     Input('datetime-range', 'end')])
def display_output(start, end):
    return [
        html.P(f'Start: {datetime.fromisoformat(start)}'),
        html.P(f'End: {datetime.fromisoformat(end)}')
    ]


if __name__ == '__main__':
    app.run_server(debug=True)
