import datetime
import yfinance as yf
import dash
#import dash_core_components as dcc
from dash import dcc, html
#import dash_html_components as html
from dash.dependencies import Input, Output
import pandas_datareader.data as web

app = dash.Dash()
app.title = "Stock Visualisation"
 
app.layout = html.Div(children=[
    html.H1("Stock Visualization Dashboard"),
    html.H4("Please enter the stock name"),
    dcc.Input(id='input', value='NVDA', type='text', maxLength = 5),
    html.Div(id='company-name'),
    html.Div(id="company-current-price"),
    html.Div(id='company-industry'),
    html.Div(id="company-dividend"),
    html.Div(id="company-recommend", style = {'font-size': '20px'}),
    html.Div(id='output-graph')
],style = {'background': '#F3F4E0'})

# Define the callback to update the input field to uppercase
@app.callback(
    Output(component_id ='input', component_property ='value'),
    [Input(component_id = 'input', component_property ='value')]
)

def update_input_to_uppercase(input_value):
	if input_value:
		return input_value.upper()
	return input_value

# callback Decorator 
@app.callback(
	[Output(component_id='company-name', component_property='children'),
	Output(component_id='company-current-price', component_property='children'),
	Output(component_id='company-industry', component_property='children'),
	Output(component_id='company-dividend', component_property='children'),
	Output(component_id='company-recommend', component_property='children'),
	Output(component_id='output-graph', component_property='children')],
	[Input(component_id='input', component_property='value')]
)


def update_graph(input_data):

	input_data = input_data.upper()[:5]

	start = datetime.datetime(2010, 1, 1)
	end = datetime.datetime.now()


	try:
		
		df = yf.download(input_data, start, end)
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
		#company_dividend  = round(company_info["dividendYield"]*100,2)
		company_recommend = company_info.get("recommendationKey", "No recommendation at this time ")
		company_industry = company_info.get("industry", "Others")

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

		graph = dcc.Graph(id ="example", figure ={
            'data':[{'x':df_reset.Date, 'y':df_reset.Close, 'type':'line', 'name':input_data}],
            'layout':{
                'title':input_data,
                'plot_bgcolor': '#E0EAF4',
                'font': {
                	'color': 'black'
                }
            }
        })
		
	except Exception as e:
		print(f"Error: {e}")
		company_name_div = html.Div(f"Error retrieving company name: {str(e)}")
		graph = html.Div("Error retrieving stock data.")

	return company_name_div, company_recent_price_div, company_industry_div, company_dividend_div, recommend_div, graph

if __name__ == '__main__':
    app.run_server(debug = True)
