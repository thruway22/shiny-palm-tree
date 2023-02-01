import streamlit as st
import pandas as pd
from io import StringIO

def display_input_widgets(stride, values_df=None):
    
    ticker_value = '' if values_df is None else df.index[stride]
    shares_value = 0 if values_df is None else df['current_shares'][stride]
    target_value = 0.0 if values_df is None else df['target_weight'][stride]
    
    locals()['col%s0' % stride], locals()['col%s1' % stride], locals()['col%s2' % stride] = form.columns(3)
    locals()['ticker%s' % stride] = locals()['col%s0' % stride].text_input('ticker%s' % stride, value=ticker_value, label_visibility='collapsed')
    locals()['share%s' % stride] = locals()['col%s1' % stride].number_input('share%s' % stride, value=shares_value, min_value=0, step=1, format='%d', label_visibility='collapsed')
    locals()['target%s' % stride] = locals()['col%s2' % stride].number_input('target%s' % stride, value=target_value, min_value=0.0, step=0.1, format='%.1f', label_visibility='collapsed')
    
    globals().update(locals()) 

st.title('NextTrade')
csv_file = st.file_uploader('upload a file', type='CSV')
ticker_count = 0

if csv_file is None:
    #with st.expander('or input manually'):
    ticker_count = st.number_input('or choose number of stocks to input manually', value=0, min_value=0)

if csv_file is not None or ticker_count > 0:
    form = st.form('manual_ticker_form')
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
    submitted = form.form_submit_button("Submit")

    if submitted:
        sum_target = 0
        for step in range(items_length):
            sum_target += globals()['target%s' % step]

        if sum_target == 100:
            st.success('Setting target weights successful!')
            st.write('Number of stocks:', items_length, 'Sum of target weights:', sum_target)
        else:
            st.error('Sum of target weights must equal 100%')
            st.write('Number of stocks:', items_length, 'Sum of target weights:', sum_target)
            
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
            
            st.table(df)
   
    
    
       

    







