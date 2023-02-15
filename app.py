import streamlit as st
import pandas as pd
import yfinance as yf
from collections import defaultdict
import plotly.express as px
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from ccy_dict import ccy_dict

#####  #####  #####  #####  #####  #####  #####
#####  #####  #####  #####  #####  #####  #####

def display_input_widgets(stride, df=None):
    '''
    Displays the input widgets for user interaction.
    Default values are either empty/zeros for manual intraction,
    or obtained from passed dataframe with correct column order

    agrs:
        stride (int): stepper
        df (pd.dataframe): 
    '''
    
    ticker_value = '' if df is None else df.index[stride]
    shares_value = 0.0 if df is None else df.iloc[:, 0][stride].astype(float)
    target_value = 0.0 if df is None else df.iloc[:, 1][stride].astype(float)
    
    left, middle, right = form.columns(3)

    locals()['ticker%s' % stride] = left.text_input(
        'ticker%s' % stride, value=ticker_value, label_visibility='collapsed')

    locals()['share%s' % stride] = middle.number_input(
        'share%s' % stride, value=shares_value, min_value=0.0, step=0.1, format='%.1f',
        label_visibility='collapsed')

    locals()['target%s' % stride] = right.number_input(
        'target%s' % stride, value=target_value, min_value=0.0, step=0.1, format='%.1f',
        label_visibility='collapsed')
    
    globals().update(locals())

#####  #####  #####  #####  #####  #####  #####

def call_input_widgets(stride):

    ticker = globals()['ticker%s' % stride].upper()
    shares = globals()['share%s' % stride]
    target = globals()['target%s' % stride]

    return ticker, shares, target

#####  #####  #####  #####  #####  #####  #####
    
def get_currency_rate(**kwargs):
    '''
    Gets the currency exchnage rate
    '''

    if 'ticker' in kwargs:
        base = yf.Ticker(kwargs.get('ticker'))
        base_currency = '' if base.fast_info['currency'] == 'USD' else base.fast_info['currency']

    if 'currency' in kwargs:
        base_currency = kwargs.get('currency')

    rate = yf.Ticker('{}USD=X'.format(base_currency)).fast_info['last_price']
        
    return rate 

#####  #####  #####  #####  #####  #####  #####
#####  #####  #####  #####  #####  #####  #####

st.title('NextTrade')
csv_file = st.file_uploader('Upload a file', type='CSV', )

# initialize variables for error checks
widgets_length = 0
inputs_length = 0

# show option to enter inputs manually only if no file is uploaded
if csv_file is None:
    widgets_length = st.number_input('or choose number of stocks to input manually', value=0, min_value=0)

if csv_file is not None or widgets_length > 0:
    form = st.form('input_form')
    right, middle, left = form.columns(3)
    right.write('Ticker')
    middle.write('Current Shares (x)')
    left.write('Target Weight (%)')

    if csv_file is not None:
        inputs_df = pd.read_csv(csv_file, names=['ticker', 'current_shares', 'target_weight'], thousands=',')    
        inputs_df = inputs_df.fillna(0).set_index('ticker')
        inputs_length = len(inputs_df)
        for step in range(len(inputs_df)):
            try:
                display_input_widgets(step, inputs_df)
            except:
                submitted = form.form_submit_button('Submit', disabled=True)
                st.error('Something went wrong. Please check the uploaded file.')
                st.stop() 

    if widgets_length > 0:
        inputs_length = widgets_length
        for step in range(widgets_length):
            display_input_widgets(step) 

    right, left = form.columns([3, 1])
    contribution_amount = right.number_input('Contribution', min_value=0.0, step=0.1, format='%.1f')
    contribution_currency = left.selectbox('Currency', ccy_dict.keys(), index=list(ccy_dict).index('USD'))
    allow_selling = form.checkbox('Allow selling of current shares', value=False)
    allow_fractional = form.checkbox('Allow fractional shares', value=False)

    submitted = form.form_submit_button('Submit')

    if submitted:
        if inputs_length == 0:
            st.error('No tickers were entered')
            st.stop()
        
        target_sum = 0
        ticker_list = []
        important_currency_list = []
        for step in range(inputs_length):
            ticker, shares, target = call_input_widgets(step)
            
            if ticker == '':
                st.error('You cannot leave ticker empty')
                st.stop()

            if ticker.startswith('$') or ticker.startswith('!$'):
                if ticker.startswith('$'):
                    ticker_adj = ticker[1:]
                if ticker.startswith('!$'):
                    ticker_adj = ticker[2:]
                    important_currency_list.append(ticker_adj)
                try:
                    currency_recognized = get_currency_rate(currency=ticker_adj)
                except:
                    st.error("Could not recognize currency '{}'".format(ticker))
                    st.stop()
            else:
                try:
                    ticker_recognized = yf.Ticker(ticker).fast_info['last_price']
                except:
                    st.error("Could not recognize ticker '{}'".format(ticker))
                    st.stop()        
            
            target_sum += target
            ticker_list.append(ticker)

        prohibit_duplicates = True # !important;  half-baked needs improvements
        if prohibit_duplicates and len(ticker_list) != len(set(ticker_list)):
            st.error('Duplicates are not allowed')
            st.stop()

        elif target_sum != 100:
            st.error('Sum of target weights must equal 100%')
            st.stop()

        else:
            st.success('Setting target weights successful!')
            
            with st.spinner('Getting ticker data from Yahoo! Finance...'):
                df = pd.DataFrame({'ticker': [], 'current_shares': [], 'target_weight': [], 'price': [], 'account'= []})
                important_currency_checkbox = False
                for step in range(inputs_length):
                    ticker, shares, target = call_input_widgets(step)

                    if ticker.startswith('$'):
                        price = get_currency_rate(currency=ticker[1:])
                        account = ticker[1:]
                    elif ticker.startswith('!$'):
                        important_currency_checkbox = True
                        important_currency = ticker[1:]
                        ticker = important_currency # remove the '!'
                        price = get_currency_rate(currency=ticker[1:])
                        account = ticker[1:]
                    else:
                        engine = yf.Ticker(ticker)
                        price = engine.history()['Close'][-1] * get_currency_rate(ticker=ticker)
                        account = engine.fast_info['currency']

                    df = pd.concat([df, pd.DataFrame([{
                        'ticker': ticker, 'current_shares': shares, 'target_weight': target, 'price': price, 'account' = account 
                    }])])

                df = df.set_index('ticker')  
                df['market_value'] = df['current_shares'] * df['price']
                df['pre_trade_weight'] = 100 * df['market_value'] / df['market_value'].sum()
            
            st.success('Getting financial data successful!')
        
            contribution_cash = contribution_amount * get_currency_rate(currency=contribution_currency)
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
                # account_cash_dict_aux = account_cash_dict
                # if important_currency_checkbox:
                #     for k in account_cash_dict_aux.keys():
                #         account_cash_dict_aux[k] = [account_cash] if k == important_currency else [0]
                excess_cash_weighted = {k: excess_cash * (sum(v)/account_cash) for (k, v) in account_cash_dict.items()}
                if important_currency_checkbox:
                    for k in excess_cash_weighted.keys():
                        excess_cash_weighted[k] = [excess_cash] if k == important_currency else [0]
                df['output_value'] = 0
                for i in df.index:
                    if i not in account_cash_dict.keys(): # for tickers
                        df.at[i, 'output_value'] = df.at[i, 'possible_value']

                    else:
                        df.at[i, 'output_value'] = df.at[i, 'possible_value'] + excess_cash_weighted[i]

                    if not bool(account_cash_dict): # if empty
                        currency_injected = '$' + contribution_currency
                        df.loc[currency_injected] = 0
                        df.at[currency_injected, 'price'] = 1.0
                        df.at[currency_injected, 'market_value'] = excess_cash
                        df.at[currency_injected, 'output_value'] = excess_cash
                            
            else:
                excess_cash = 0
                df['output_value'] = df['allocated_value']

            df['output_unit'] = df['output_value'] / df['price']

            df['post_trade_weight'] = 100 * (df['market_value'] + df['output_value']) / (df['market_value'].sum() + df['output_value'].sum())
            
            labels_list = ['Contribution Cash']
            values_list = [contribution_cash]
            sources_list = [0]
            targets_list = []

            sources_length = len(sources_list) - 1 # left-section: account cash
            for k, v in account_cash_dict.items():
                labels_list.append(k)
                values_list.append(abs(sum(v)))
                sources_length += 1
                sources_list.append(sources_length)

            sources_length = len(sources_list) - 1 # left-section: selling
            for i in df[df['output_value'] < 0].index:
                labels_list.append(i)
                values_list.append(abs(df['output_value'][i]))
                sources_length += 1
                sources_list.append(sources_length)
            
            labels_list.append('Available Cash')
            values_list.append(0)

            sources_length = len(sources_list)
            sources_list.append(sources_length) # mid-section: available_cash 
            targets_list += (sources_length + 1) * [sources_length]

            targets_length = len(targets_list) - 1 # right_section: buying
            for i in df[df['output_value'] > 0].index:
                labels_list.append(i)
                values_list.append(abs(df['output_value'][i]))
                sources_list.append(sources_length)
                targets_length += 1
                targets_list.append(targets_length)

            flow_fig = go.Figure(data=[go.Sankey(
                valueformat = '$.2f',
                node = dict(
                    label=labels_list,
                    pad = 20,
                    thickness = 20,
                    #color = 'lightgrey',
                ),
                link = dict(
                    source = sources_list,
                    target = targets_list,
                    value = values_list,
                    color = '#F5F5F5'
            ))])

            flow_fig.update_layout(title_text='Cash Flow Diagram')
            flow_fig.update_xaxes(fixedrange=True)
            flow_fig.update_yaxes(fixedrange=True)
            st.plotly_chart(flow_fig, use_container_width=True, config= {'displayModeBar': False})

                    
            if allow_fractional == False:
                inflow_cash = total_cash + df[df['output_value'] < 0]['output_value'].abs().sum()
                st.write(
                    '''Your total available cash to trade is **\${:.2f}**,
                    but you can only trade **\${:.2f}** for complete (non-fractional) shares 
                    with excess cash of **\${:.2f}**.'''.format(inflow_cash, inflow_cash - excess_cash, excess_cash)
                )

            st.header('Plan:')

            plan_df = df[df['output_value'] != 0][['price', 'output_unit', 'output_value']].sort_values('output_value').reset_index().rename(columns={
                'ticker': 'Ticker',
                'price': 'Market Price',
                'output_unit': 'Trade Shares',
                'output_value': 'Trade Value'})
            plan_df.index += 1
            
            #st.table(df)
            st.table(plan_df.style.format(precision=2, na_rep='', thousands=','))
            
            dist_fig = px.bar(df, x=df.index, y=['pre_trade_weight', 'target_weight', 'post_trade_weight'], barmode='group')
            dist_fig.update_xaxes(tickangle=-45)
            dist_fig.update_layout(
                title='Weight Distribution',
                xaxis_title='Ticker',
                yaxis_title='Weight (%)',
                legend=dict(
                    title='',
                    orientation='h',
                    yanchor='bottom',
                    y=1.02,
                    xanchor='center',
                    x=0.5
            ))

            variable_names = ['Pre-Trade Weight', 'Target Weight', 'Post-Trade Weight']
            for idx, name in enumerate(variable_names):
                dist_fig.data[idx].name = name
                #dist_fig.data[idx].hovertemplate = name

            dist_fig.update_xaxes(fixedrange=True)
            dist_fig.update_yaxes(fixedrange=True)
            st.plotly_chart(dist_fig, use_container_width=True, config= {'displayModeBar': False})

            #fig = px.sunburst(df, path=['sex', 'day', 'time'], values='total_bill', color='day')
            
            # account_list = []
            # for i in df.index:
            #     if i.startswith('$'):
            #         account_list.append(i[1:])
            #     else:
            #         ticker = yf.Ticker(i)
            #         account_list.append(ticker.fast_info['currency'])
            # df['account'] = account_list
            left, right = st.columns(2)
            left.plotly_chart(
                px.sunburst(df.reset_index(), path=['account', 'ticker'], values='target_weight', color='account'),
                use_container_width=True, config= {'displayModeBar': False})
            right.plotly_chart(
                px.sunburst(df.reset_index(), path=['account', 'ticker'], values='post_trade_weight', color='account'),
                use_container_width=True, config= {'displayModeBar': False})   
                
    
        
        
        

        







