import streamlit as st
import pandas as pd
from io import StringIO

def display_input_widgets(df, stride):
    locals()['col%s0' % stride], locals()['col%s1' % stride], locals()['col%s2' % stride] = form.columns(3)
    locals()['ticker%s' % stride] = locals()['col%s0' % stride].text_input('ticker%s' % stride, value=df.index[stride], label_visibility='collapsed')
    locals()['share%s' % stride] = locals()['col%s1' % stride].number_input('share%s' % stride, value=df['current_shares'][stride], min_value=0, step=1, format='%d', label_visibility='collapsed')
    locals()['target%s' % stride] = locals()['col%s2' % stride].number_input('target%s' % stride, value=df['target_weight'][stride], min_value=0.0, step=0.1, format='%.1f', label_visibility='collapsed')
    globals().update(locals())  

st.title('NextTrade')
uploaded_file = st.file_uploader('Choose a file', type='CSV')

with st.expander('or manually input'):
    csv_form = st.form('csv_form')
    if uploaded_file is None:
        csv_string_placeholder = 'VTI,14,65\nBND,5,15\nKSA,3,20'
        csv_string = csv_form.text_area('csv_string', height=150, placeholder=csv_string_placeholder, label_visibility='collapsed')
    else:
        df = pd.read_csv(uploaded_file, names=['ticker', 'current_shares', 'target_weight'])
        df = df.set_index('ticker')
        csv_string_value = df.to_csv(header=False)
        csv_string = csv_form.text_area('csv_string', height=150, value=csv_string_value, label_visibility='collapsed')
    csv_form_submitted = csv_form.form_submit_button("Submit")
    
if csv_form_submitted:
    #df = pd.read_csv(StringIO('VTI,14,65\nBND,5,15\nKSA,3,20'), sep=",", header=None)
    #st.table(df)
    
    form = st.form('ticker_form')
    cola, colb, colc = form.columns(3)
    cola.write('Ticker')
    colb.write('Current Shares (x)')
    colc.write('Target Weight (%)')
    for step in range(len(df)):
        display_input_widgets(df, step)
    submitted = form.form_submit_button("Submit")
    
    
    #ticker_count = st.number_input('Enter number', value=0)
    #if ticker_count > 0:
    #    form = st.form('input_form')
    #    cola, colb, colc = form.columns(3)
    #    cola.write('Ticker')
    #    colb.write('Current Shares (x)')
    #    colc.write('Target Weight (%)')
    #    for step in range(ticker_count):
    #        display_input_widgets(step)
    #    submitted = form.form_submit_button("Submit")'''

#placeholder = st.empty()
#with placeholder.container():
#    if submitted and uploaded_file is None:
 #       form2 = st.form('input_form2')
  #      for step in range(ticker_count):
   #             display_input_widgets(step) 
    #    form2.form_submit_button("Submit")
