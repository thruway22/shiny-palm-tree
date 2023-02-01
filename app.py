import streamlit as st
import pandas as pd
from io import StringIO

def display_input_widgets(df, stride):
    locals()['col%s0' % stride], locals()['col%s1' % stride], locals()['col%s2' % stride] = form.columns(3)
    locals()['ticker%s' % stride] = locals()['col%s0' % stride].text_input('ticker%s' % stride, value=df.index[stride], label_visibility='collapsed')
    locals()['share%s' % stride] = locals()['col%s1' % stride].number_input('share%s' % stride, value=df['current_shares'][stride], min_value=0, step=1, format='%d', label_visibility='collapsed')
    locals()['target%s' % stride] = locals()['col%s2' % stride].number_input('target%s' % stride, value=df['target_weight'][stride], min_value=0.0, step=0.1, format='%.1f', label_visibility='collapsed')
    globals().update(locals()) 
    
def display_input_widgets2(stride):
    locals()['col%s0' % stride], locals()['col%s1' % stride], locals()['col%s2' % stride] = form.columns(3)
    locals()['ticker%s' % stride] = locals()['col%s0' % stride].text_input('ticker%s' % stride, label_visibility='collapsed')
    locals()['share%s' % stride] = locals()['col%s1' % stride].number_input('share%s' % stride, min_value=0, step=1, format='%d', label_visibility='collapsed')
    locals()['target%s' % stride] = locals()['col%s2' % stride].number_input('target%s' % stride, min_value=0.0, step=0.1, format='%.1f', label_visibility='collapsed')
    globals().update(locals())

st.title('NextTrade')
csv_file = st.file_uploader('upload a file', type='CSV')

if csv_file is None:
    #with st.expander('or input manually'):
    ticker_count = st.number_input('or choose number of stocks to input manually', value=0, min_value=0)
        
else:
    df = pd.read_csv(csv_file, names=['ticker', 'current_shares', 'target_weight'])
    df = df.set_index('ticker')
    form = st.form('read_ticker_form')
    cola, colb, colc = form.columns(3)
    cola.write('Ticker')
    colb.write('Current Shares (x)')
    colc.write('Target Weight (%)')
    for step in range(len(df)):
            display_input_widgets(df, step)
    submitted = form.form_submit_button("Submit")
        
if csv_file is None and ticker_count > 0:
    form = st.form('manual_ticker_form')
    cola, colb, colc = form.columns(3)
    cola.write('Ticker')
    colb.write('Current Shares (x)')
    colc.write('Target Weight (%)')
    for step in range(ticker_count):
        display_input_widgets2(step)
    submitted = form.form_submit_button("Submit")
   
    
    
       

    







