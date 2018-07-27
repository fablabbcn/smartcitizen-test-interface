import dash_core_components as dcc
import dash_html_components as html
from dash.dependencies import Input, Output

from app import app
from apps import beginTest, runTest

app.layout = html.Div([
    dcc.Location(id='url', refresh=False),
    html.Div(id='page-content'),
])


@app.callback(Output('page-content', 'children'),
              [Input('url', 'pathname')])
def display_page(pathname):
  if pathname == '/apps/beginTest':
    return beginTest.layout
  elif pathname == '/apps/runTest':
    return runTest.layout
  elif pathname == '/':
    return beginTest.layout
  else:
    return '404'

if __name__ == '__main__':

    # Run Dash Application
    app.run_server(debug=True, host='0.0.0.0', port=8082, processes = 4)