import streamlit as st
import pandas as pd
import yfinance as yf
from collections import defaultdict
import plotly.express as px
import matplotlib.pyplot as plt
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
items_length = 0

if csv_file is None:
    ticker_count = st.number_input('or choose number of stocks to input manually', value=0, min_value=0)

form = st.form('input_form')

right, left = form.columns([3, 1])
contribution_amount = right.number_input('Contribution', min_value=0.0, step=0.1, format='%.1f')
#cash = middle.number_input('In-Account Cash', min_value=0.0, step=0.1, format='%.1f')
contribution_currency = left.selectbox('Currency', ccy_dict.keys(), index=list(ccy_dict).index('USD'))

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

allow_selling = form.checkbox('Allow selling of current shares', value=False)
allow_fractional = form.checkbox('Allow fractional shares', value=False)
excess_cash_handling = form.checkbox('Keep all excess cash in the first cash account', value=False)

submitted = form.form_submit_button("Submit")

if submitted:
    if items_length == 0:
        st.error('No tickers were entered')
        st.stop()
    
    sum_target = 0
    ticker_list = []
    for step in range(items_length):
        ticker = globals()['ticker%s' % step].upper()
        target = globals()['target%s' % step]
        
        if ticker == '':
            st.error('You cannot leave ticker empty')
            st.stop()

        if ticker.startswith('$'):
            try:
                currency_recognized = get_currency_rate(ticker[1:], True)
            except:
                st.error("Could not recognize currency '{}'".format(ticker))
                st.stop()
        else:
            try:
                ticker_recognized = yf.Ticker(ticker).fast_info['last_price']
            except:
                st.error("Could not recognize ticker '{}'".format(ticker))
                st.stop()        
           
        sum_target += target
        ticker_list.append(ticker)

    prohibit_duplicates = True # !important;  half-baked for later improvements
    if prohibit_duplicates and len(ticker_list) != len(set(ticker_list)):
        st.error('Duplicates are not allowed')
        st.stop()

    elif sum_target != 100:
        st.error('Sum of target weights must equal 100%')
        st.stop()

    else:
        st.success('Setting target weights successful!')
        
        with st.spinner('Getting ticker data from Yahoo! Finance...'):
            df = pd.DataFrame({'ticker': [], 'current_shares': [], 'target_weight': [], 'price': []})
            for step in range(items_length):
                ticker = globals()['ticker%s' % step]
                shares = globals()['share%s' % step]
                target = globals()['target%s' % step]

                if ticker.startswith('$'):
                    price = get_currency_rate(ticker[1:], True)
                    #cash = df['current_shares'][i] * price
                else:
                    price = yf.Ticker(ticker).history()['Close'][-1] * get_currency_rate(ticker)

                df = pd.concat([df, pd.DataFrame([{
                    'ticker': ticker, 'current_shares': shares, 'target_weight': target, 'price': price
                }])])

            df['ticker'] = df['ticker'].str.upper()
            df.set_index('ticker', inplace=True)    
            df['market_value'] = df['current_shares'] * df['price']
            df['pre_trade_weight'] = 100 * df['market_value'] / df['market_value'].sum()
          
        st.success('Getting financial data successful!')
    
        contribution_cash = contribution_amount * get_currency_rate(contribution_currency, True)
        account_cash_dict = defaultdict(list)
        account_cash = 0
        for i in range(len(df)):
            idx_name = df.iloc[i].name
            if idx_name.startswith('$'):
                col_loc = df.columns.get_loc('market_value')
                x = df.iat[i, col_loc]
                account_cash += x
                account_cash_dict[idx_name].append(x)
                df.iat[i, col_loc] = 0
        total_cash = contribution_cash + account_cash
        
        algo_list = []
        for i in range(len(df)): 
            value = (total_cash + df['market_value'].sum()) * (
                df.iat[i, df.columns.get_loc('target_weight')]/100
                ) - df.iat[i, df.columns.get_loc('market_value')]
            value = value if allow_selling else max(value, 0)
            algo_list.append(value)
        df['algo'] = algo_list
        
        df['allocated_value'] = total_cash * (df['algo'] / df['algo'].sum())
        df['possible_value'] = (df['allocated_value'] // df['price']) * df['price']

        if allow_fractional == False:
            excess_cash = df['allocated_value'].sum() - df['possible_value'].sum()
            excess_cash_weighted = {k: excess_cash * (sum(v)/account_cash) for (k, v) in account_cash_dict.items()}

            df['output_value'] = 0
            for i in df.index:
                if i not in excess_cash_weighted.keys():
                    df.at[i, 'output_value'] = df.at[i, 'possible_value'] 
                else:
                    df.at[i, 'output_value'] = df.at[i, 'possible_value'] + excess_cash_weighted[i]

            df['output_unit'] = df['output_value'] / df['price']

        else:
            df['output_value'] = df['allocated_value']
        
        df['output_unit'] = df['output_value'] / df['price'] 
        df['post_trade_weight'] = 100 * (df['market_value'] + df['output_value']) / (df['market_value'].sum() + df['output_value'].sum())

        if allow_fractional == False:

            cash_handling_dict = {
                'label': ['total_cash', 'trade_cash', 'excess_cash'],
                'value': [total_cash, total_cash - excess_cash, excess_cash]
            }

            st.plotly_chart(
                px.funnel(cash_handling_dict, x='value', y='label')
            )
        
            cash_handling_dict2 = {
                'level_a': ['total_cash', 'total_cash', 'total_cash'],
                'level_b': ['', 'trade_cash', 'excess_cash'],
                'values': [total_cash, total_cash - excess_cash, excess_cash]
            }

            st.plotly_chart(
                px.icicle(cash_handling_dict2, parents='level_a', names='level_b', values='values', color='day')#.update_traces(root_color="lightgrey")
            )

            st.write(
                '''Your total available cash to trade is **\${:.2f}**,
                but you can only trade **\${:.2f}** for complete (non-fractional) shares.
                With excess cash of **\${:.2f}**, how would you like to distribute it?'''.format(total_cash, total_cash - excess_cash, excess_cash)
            )



        # st.header('Plan:')

        # plan_df = df.copy()
        # plan_df = plan_df[['price', output_unit, output_value]]
        # plan_df.reset_index(inplace=True)
        # plan_df.rename(columns={
        #     'ticker': 'Ticker',
        #     'price': 'Market Price',
        #     output_unit: 'Trade Sahres',
        #     output_value: 'Trade Value',
        # }, inplace=True)
        # plan_df.index += 1
        
        st.table(df)
        # st.table(plan_df.style.format(precision=2, na_rep='', thousands=','))
        
        fig = px.bar(df, x=df.index, y=['pre_trade_weight', 'target_weight', 'post_trade_weight'], barmode='group')
        st.plotly_chart(fig, use_container_width=True)                 
            
   
    
    
       

    







