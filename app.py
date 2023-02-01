import streamlit as st
import pandas as pd
import yfinance as yf
import plotly.express as px
from ccy_dict import ccy_dict

def display_input_widgets(stride, values_df=None):
    
    ticker_value = '' if values_df is None else df.index[stride]
    shares_value = 0.0 if values_df is None else df['current_shares'][stride].astype(float)
    target_value = 0.0 if values_df is None else df['target_weight'][stride].astype(float)
    
    locals()['col%s0' % stride], locals()['col%s1' % stride], locals()['col%s2' % stride] = form.columns(3)
    locals()['ticker%s' % stride] = locals()['col%s0' % stride].text_input('ticker%s' % stride, value=ticker_value, label_visibility='collapsed')
    locals()['share%s' % stride] = locals()['col%s1' % stride].number_input('share%s' % stride, value=shares_value, min_value=0.0, step=0.1, format='%.1f', label_visibility='collapsed')
    locals()['target%s' % stride] = locals()['col%s2' % stride].number_input('target%s' % stride, value=target_value, min_value=0.0, step=0.1, format='%.1f', label_visibility='collapsed')
    
    globals().update(locals())
    
def get_currency_rate(input, bypass=False):
    
    if bypass == False:
        base = yf.Ticker(input)
        base_currency = '' if base.fast_info['currency'] == 'USD' else base.fast_info['currency']
    else:
        base_currency = input
        
    rate = yf.Ticker('{}USD=X'.format(base_currency)).fast_info['last_price']
        
    return rate 

st.title('NextTrade')
csv_file = st.file_uploader('upload a file', type='CSV')
ticker_count = 0

if csv_file is None:
    ticker_count = st.number_input('or choose number of stocks to input manually', value=0, min_value=0)

form = st.form('manual_ticker_form')
cola, colb, colc = form.columns(3)
contribution = cola.number_input('Contribution', min_value=0.0, step=0.1, format='%.1f')
cash = colb.number_input('In-Account Cash', min_value=0.0, step=0.1, format='%.1f')
currency = colc.selectbox('Currency', ccy_dict.keys(), index=list(ccy_dict).index('USD'))
if csv_file is not None or ticker_count > 0:
    cola, colb, colc = form.columns(3)
    cola.write('Ticker')
    colb.write('Current Shares (x)')
    colc.write('Target Weight (%)')
    if csv_file is not None:
        df = pd.read_csv(csv_file, names=['ticker', 'current_shares', 'target_weight'])
        df = df.set_index('ticker')
        items_length = len(df)
        for step in range(len(df)):
            display_input_widgets(step, df)
    if ticker_count > 0:
        items_length = ticker_count
        for step in range(ticker_count):
            display_input_widgets(step) 

allow_selling = form.checkbox('Allow selling of current shares to rebalance', value=False)
allow_fractional = form.checkbox('Allow fractional shares', value=False)

submitted = form.form_submit_button("Submit")

if submitted:
    sum_target = 0
    for step in range(items_length):
        sum_target += globals()['target%s' % step]

    if sum_target != 100:
        st.error('Sum of target weights must equal 100%')

    else:
        st.success('Setting target weights successful!')

        tickers_list = []
        shares_list = []
        targets_list = []
        for step in range(items_length):
            tickers_list.append(globals()['ticker%s' % step])
            shares_list.append(globals()['share%s' % step])
            targets_list.append(globals()['target%s' % step])
        df = pd.DataFrame({
            'ticker': tickers_list,
            'current_shares': shares_list,
            'target_weight': targets_list
        }).set_index('ticker')

        cash = cash * get_currency_rate(currency, True)
        contribution = contribution * get_currency_rate(currency, True)
        
        prices_list = []
        with st.spinner('Getting ticker data from Yahoo! Finance...'):
            for i in df.index:
                    prices_list.append(
                        yf.Ticker(i).history()['Close'][-1] * get_currency_rate(i))
                    
        st.success('Getting financial data successful!')
        
        df['price'] = prices_list
        df['market_value'] = df['current_shares'] * df['price']
        df['pre_trade_weight'] = 100 * df['market_value'] / (df['market_value'].sum() + cash)
        
        algo_list = []
        for i in df.index:
            value = (contribution + cash + df['market_value'].sum()) * (df['target_weight'][i]/100) - df['market_value'][i]
            value = value if allow_selling == True else max(value, 0)
            algo_list.append(value)
        df['algo'] = algo_list
        
        df['allocated_value'] = (contribution + cash) * (df['algo'] / df['algo'].sum())
        df['allocated_unit'] = df['allocated_value'] / df['price']
        df['possible_unit'] = df['allocated_value'] // df['price']
        df['possible_value'] = df['possible_unit'] * df['price']
        
        if allow_fractional == True:
            output_value = 'allocated_value'
            output_unit = 'allocated_unit'
        else:
            output_value = 'possible_value'
            output_unit = 'possible_unit'
            
        df['post_trade_weight'] = 100 * (df['market_value'] + df[output_value]) / (df['market_value'].sum() + df[output_value].sum())
        
        st.header('Plan:')
        
        plan_df = pd.DataFrame({
            'Ticker': [], 'Market Price':[], 'Trade Shares':[], 'Trade Value':[]
        })
        
        for i, j in zip(df[df['possible_unit'] != 0].index, range(len(df))):
            plan_df.loc[j] = [i, df['price'][i], df[output_unit][i], df[output_value][i]]
        
        plan_df.index += 1
        st.table(plan_df.style.format(precision=2, na_rep='', thousands=','))
        
        fig = px.histogram(df, x=df.index, y=['pre_trade_weight', 'target_weight', 'post_trade_weight'],
                           barmode='group')
        st.plotly_chart(fig, use_container_width=True)
                    
            
   
    
    
       

    







