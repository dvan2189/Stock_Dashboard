import datetime
import yfinance as yf
import dash
from dash import dcc, html
from dash.dependencies import Input, Output, State, ALL
from flask_caching import Cache

class StockDashboard:
    def __init__(self):
        self.app = dash.Dash()
        self.app.title = "Stock Visualisation"
        self.configure_cache()
        self.setup_layout()
        self.setup_callback()

    # Configure Cache
    def configure_cache(self):
        self.cache = Cache(self.app.server, config={
            'CACHE_TYPE': 'simple',
            'CACHE_DEFAULT_TIMEOUT': 300  # Cache time out in seconds (5 minutes)
        })

    def setup_layout(self):
        # Define dark mode colors
        dark_background = '#2c2c2c'
        dark_text = '#ffffff'
        light_text = '#cccccc'
        accent_color = '#1f77b4'
        input_background = '#4a4a4a'

        self.app.layout = html.Div(children=[
            html.H1("Stock Visualization Dashboard", style={"color": dark_text}),

            html.Div([
                html.Div([
                    html.H4("Please enter the stock name", style={"color": light_text}),
                    dcc.Input(id='input', value='NVDA', type='text', maxLength=5),
                ], style={'display': 'inline-block', 'margin-right': '20px'}),

                html.Div([
                    html.H4("Select Date Range", style={"color": light_text}),
                    dcc.DatePickerRange(
                        id='date-picker-range',
                        start_date=datetime.datetime(2010, 1, 1),
                        end_date=datetime.datetime.now(),
                        display_format='MM-DD-YYYY',
                        style={'margin-left': '20px', 'backgroundColor': input_background}
                    )
                ], style={'display': 'inline-block'}),
            ]),

            html.Button('Add to Favorite', id='add-favorite-button', n_clicks=0, style={'backgroundColor': accent_color, 'color': dark_text}),
            html.Div(id='company-name', style={"color": dark_text}),
            html.Div(id="company-current-price", style={"color": dark_text}),
            html.Div(id='company-industry', style={"color": dark_text}),
            html.Div(id="company-dividend", style={"color": dark_text}),
            html.Div(id="company-recommend", style={'font-size': '20px', "color": dark_text}),
            html.Div(id="company-market-cap", style={"color": dark_text}),
            html.Div(id="company-PE", style={"color": dark_text}),
            html.Div(id='output-graph'),
            html.H2("Favorite Stocks", style={"color": dark_text}),
            html.Ul(id='favorite-stocks-list', style={"color": dark_text}),
            dcc.Store(id='favorites-store', data=[], storage_type='local')
        ], style={'backgroundColor': dark_background, 'padding': '20px'})

    def setup_callback(self):
        # Define the callback to update the input field to uppercase
        @self.app.callback(
            Output(component_id='input', component_property='value'),
            [Input(component_id='input', component_property='value')]
        )
        def update_input_to_uppercase(input_value):
            if input_value:
                return input_value.upper()
            return input_value

        # Callback Decorator
        @self.app.callback(
            [Output(component_id='company-name', component_property='children'),
             Output(component_id='company-current-price', component_property='children'),
             Output(component_id='company-industry', component_property='children'),
             Output(component_id='company-dividend', component_property='children'),
             Output(component_id='company-recommend', component_property='children'),
             Output(component_id='company-market-cap', component_property='children'),
             Output(component_id='company-PE', component_property='children'),
             Output(component_id='output-graph', component_property='children')],
            [Input(component_id='input', component_property='value'),
             Input(component_id='date-picker-range', component_property='start_date'),
             Input(component_id='date-picker-range', component_property='end_date')]
        )
        def update_graph(input_data, start_date, end_date):
            input_data = input_data.upper()[:5]

            start = datetime.datetime.strptime(start_date.split('T')[0], '%Y-%m-%d')
            end = datetime.datetime.strptime(end_date.split('T')[0], '%Y-%m-%d')

            try:
                #df = self.get_stock_data(input_data, start, end)
                df = yf.download(input_data, start, end)
                df_reset = df.reset_index()

                company_closing_price = df_reset['Close'].iloc[-1]

                ticker = yf.Ticker(input_data)
                company_info = ticker.info

                company_name = company_info["longName"]
                company_recent_price = company_info.get("currentPrice", company_closing_price)
                company_dividend = round(company_info.get("dividendYield", 0) * 100, 2)
                company_recommend = company_info.get("recommendationKey", "No recommendation at this time ")
                company_industry = company_info.get("industry", "Others")
                company_market_cap = self.format_market_cap(company_info.get("marketCap", "N/A"))
                company_PE = company_info.get("trailingPE", "N/A")

                currency = company_info["financialCurrency"]

                if company_recommend == "buy":
                    color = "blue"
                elif company_recommend == "hold":
                    color = "orange"
                elif company_recommend == "sell":
                    color = "red"
                else:
                    color = 'grey'

                company_name_div = html.Div(f"Company Name: {company_name}")
                company_recent_price_div = html.Div(f"Recently Price: ${company_recent_price} {currency}")
                company_industry_div = html.Div(f"Industry: {company_industry}")
                company_dividend_div = html.Div(f"Dividend: {company_dividend}%")
                recommend_div = html.Div(f"Recommendation: {company_recommend.capitalize()}", style={'color': color})
                market_cap_div = html.Div(f"Market Cap: {company_market_cap}")
                pe_div = html.Div(f"Price To Earnings Ratio(PE): {company_PE}")

                graph = dcc.Graph(id="example", figure={
                    'data': [{'x': df_reset.Date, 'y': df_reset.Close, 'type': 'line', 'name': input_data}],
                    'layout': {
                        'title': input_data,
                        'plot_bgcolor': '#2c2c2c',
                        'paper_bgcolor': '#2c2c2c',
                        'font': {
                            'color': '#ffffff'
                        }
                    }
                })

            except KeyError as e:
                company_name_div = html.Div(f"Invalid stock symbol entered.")
                company_recent_price_div = company_industry_div = company_dividend_div = recommend_div = market_cap_div = pe_div = html.Div("")

                graph = html.Div("")

            except Exception as e:
                print(f"Error: {e}")
                company_name_div = html.Div(f"Error retrieving company name: {str(e)}")
                graph = html.Div("Error retrieving stock data.")
                company_recent_price_div = company_industry_div = company_dividend_div = recommend_div = market_cap_div = pe_div = html.Div("")

            return company_name_div, company_recent_price_div, company_industry_div, company_dividend_div, recommend_div, market_cap_div, pe_div, graph

        # Callback to add/remove a stock to favorites and update the Store
        @self.app.callback(
            Output('favorites-store', 'data'),
            [Input('add-favorite-button', 'n_clicks'),
             Input({'type': 'remove-button', 'index': ALL}, 'n_clicks')],
            [State('input', 'value'), State('favorites-store', 'data')]
        )
        def update_favorites(n_add_clicks, n_remove_clicks_list, input_value, favorites):
            if favorites is None:
                favorites = []

            ctx = dash.callback_context

            if not ctx.triggered:
                return favorites

            trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

            if 'add-favorite-button' in trigger_id and n_add_clicks > 0:
                if input_value and input_value not in favorites:
                    favorites.append(input_value)
            else:
                triggered_index = eval(trigger_id)['index']
                if triggered_index in favorites:
                    favorites.remove(triggered_index)

            return favorites

        # Callback to update the favorite stocks list display
        @self.app.callback(
            Output('favorite-stocks-list', 'children'),
            [Input('favorites-store', 'data')]
        )
        def update_favorite_stocks_list(favorites):
            return [html.Li([
                f"{stock} ",
                html.Button('X', id={'type': 'remove-button', 'index': stock}, n_clicks=0, style={'color': 'red', 'backgroundColor': 'transparent', 'border': 'none', 'cursor': 'pointer', 'margin-left': '5px'})
            ]) for stock in favorites]

    # Function to get stock data with caching
    '''
    @self.cache.memoize()
    def get_stock_data(self, input_data, start, end):
        df = yf.download(input_data, start, end)
        return df.reset_index()
    '''

    # Function to format market cap
    def format_market_cap(self, market_cap):
        if market_cap is None:
            return "N/A"
        elif market_cap >= 1e12:
            return f"${market_cap / 1e12:.2f}T"
        elif market_cap >= 1e9:
            return f"${market_cap / 1e9:.2f}B"
        elif market_cap >= 1e6:
            return f"${market_cap / 1e6:.2f}M"
        else:
            return f"${market_cap:.2f}"

    def run(self):
        self.app.run_server(debug=True)

if __name__ == '__main__':
    dashboard = StockDashboard()
    dashboard.run()
