import datetime
import yfinance as yf
import dash
#import dash_core_components as dcc
from dash import dcc, html
#import dash_html_components as html
from dash.dependencies import Input, Output, State, ALL
from flask_caching import Cache
from typing import List
import pandas_datareader.data as web

app = dash.Dash()
app.title = "Stock Visualisation"

#Configure Cache

cache = Cache(app.server, config = {
	'CACHE_TYPE': 'simple',
	'CACHE_DEFAULT_TIMEOUT': 300 # Cache time out in seconds (5 minutes)
})

# Define dark mode colors
dark_background = '#2c2c2c'
dark_text = '#ffffff'
light_text = '#cccccc'
accent_color = '#1f77b4'
input_background = '#4a4a4a'
 
app.layout = html.Div(children=[
    html.H1("Stock Visualization Dashboard", style ={"color": dark_text}),

    html.Div([
    	html.Div([
    		html.H4("Please enter the stock name",style ={"color": light_text}),
    		dcc.Input(id='input', value='NVDA', type='text', maxLength = 5),
    	], style = {'diplay': 'inline-block', 'margin-right': '20px'}),

    	html.Div([
    		html.H4("Select Date Range", style ={"color": light_text}),
    		dcc.DatePickerRange(
				id = 'date-picker-range',
				start_date = datetime.datetime(2010,1,1),
				end_date = datetime.datetime.now(),
				display_format = 'MM-DD-YYYY',
				style = {'margin-left': '20px', "input_background":input_background}
			)
    	], style = {'diplay': 'inline-block'}),
    ]),

    html.Button('Add to Favorite', id='add-favorite-button', n_clicks = 0, style={'backgroundColor': accent_color, 'color': dark_text}),
    #html.Button('Remove from Favorite', id='remove-favorite-button', n_clicks = 0, style={'backgroundColor': accent_color, 'color': dark_text}),
    html.Div(id='company-name', style ={"color": dark_text}),
    html.Div(id="company-current-price", style ={"color": dark_text}),
    html.Div(id='company-industry', style ={"color": dark_text}),
    html.Div(id="company-dividend", style ={"color": dark_text}),
    html.Div(id="company-recommend", style = {'font-size': '20px', "color": dark_text}),
    html.Div(id="company-market-cap", style ={"color": dark_text}),
    html.Div(id="company-PE", style ={"color": dark_text}),
    html.Div(id='output-graph'),
    html.H2("Favorite Stocks", style ={"color": dark_text}),
    html.Ul(id = 'favorite-stocks-list', style ={"color": dark_text}),
    dcc.Store(id = 'favorites-store', data = [], storage_type = 'local')
],style = {'backgroundColor': dark_background, 'padding': '20px'})

# Define the callback to update the input field to uppercase
@app.callback(
    Output(component_id ='input', component_property ='value'),
    [Input(component_id = 'input', component_property ='value')]
)

def update_input_to_uppercase(input_value):
	if input_value:
		return input_value.upper()
	return input_value

# Function to format market cap
def format_market_cap(market_cap):
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

# Define a function to get stock data with caching 
@cache.memoize()
def get_stock_data(input_data, start, end):
	df = yf.download(input_data, start, end)
	return df.reset_index()

# callback Decorator 
@app.callback(
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
		
		#df = yf.download(input_data, start, end)
		df = get_stock_data(input_data, start, end)
		df_reset = df.reset_index()
		#df_reset.rename(columns={'DataFrame:            Date': 'Date'}, inplace=True)
		
		#print(df_reset.columns.tolist())
		print(f"DataFrame:\n {df_reset}")
		
		company_closing_price = df_reset['Close'].iloc[-1]

		ticker = yf.Ticker(input_data)
		company_info = ticker.info
		
		company_name = company_info["longName"]
		company_recent_price = company_info.get("currentPrice",company_closing_price )
		company_dividend = round(company_info.get("dividendYield",0)*100,2)
		company_recommend = company_info.get("recommendationKey", "No recommendation at this time ")
		company_industry = company_info.get("industry", "Others")
		company_market_cap = format_market_cap(company_info.get("marketCap", "N/A"))
		company_PE = company_info.get("trailingPE", "N/A") # got the case as PE have to be more than 40-60 to secure the paid dividend


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
		recommend_div = html.Div(f"Recommendation: {company_recommend.capitalize()}", style ={'color':color})
		market_cap_div = html.Div(f"Market Cap: {company_market_cap}")
		pe_div = html.Div(f"Price To Earnings Ratio(PE): {company_PE}")

		graph = dcc.Graph(id ="example", figure ={
            'data':[{'x':df_reset.Date, 'y':df_reset.Close, 'type':'line', 'name':input_data}],
            'layout':{
                'title':input_data,
                'plot_bgcolor': dark_background,
                'paper_bgcolor': dark_background,
                'font': {
                	'color': dark_text
                }
            }
        })

	except KeyError as e:
		company_name_div = html.Div(f"Invalid stock symbol entered.")

	except Exception as e:
		print(f"Error: {e}")
		company_name_div = html.Div(f"Error retrieving company name: {str(e)}")
		graph = html.Div("Error retrieving stock data.")

	return company_name_div, company_recent_price_div, company_industry_div, company_dividend_div, recommend_div, market_cap_div ,pe_div , graph

# Callback to add/remove a stock to favorites and update the Store
@app.callback(
	Output('favorites-store', 'data'),
	[Input('add-favorite-button', 'n_clicks'),
	Input({'type':'remove-button', 'index':ALL}, 'n_clicks')],
	[State('input', 'value'), State('favorites-store', 'data')]
)


def update_favorites(n_add_clicks, n_remove_clicks, input_value, favorites):
	ctx = dash.callback_context
	if not ctx.triggered:
		return favorites

	#Find the index of triggered button
	triggered_index = ctx.triggered[0]['prop_id'].split('.')[0]
	if 'add-favorite-button' in triggered_index and n_add_clicks > 0:
		if input_value and input_value not in favorites:
			favorites.append(input_value)
	else:
		index = eval(triggered_index)['index']
		favorites.remove(index)
	return favorites

# Callback to update the favorite stocks list display
@app.callback(
    Output('favorite-stocks-list', 'children'),
    [Input('favorites-store', 'data')]
)
def update_favorite_stocks_list(favorites):
    #return [html.Li(stock) for stock in favorites]
    return [html.Li([
    		stock, 
    		html.Button('X', id={'type':'remove-button', 'index':stock}, n_clicks = 0,
    					style={'backgroundColor': accent_color, 'color': dark_text, 'margin-left': '20px'})
    	]) for stock in favorites]

if __name__ == '__main__':
    app.run_server(debug = True)
