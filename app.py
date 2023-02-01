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
csv_file = st.file_uploader('Upload a file', type='CSV')

if csv_file is None:
    with st.expander('or manually input'):
        input_form = st.form('input_form')
        csv_string_placeholder = 'VTI,14,65\nBND,5,15\nKSA,3,20'
        csv_string = input_form.text_area('csv_string', height=150, placeholder=csv_string_placeholder, label_visibility='collapsed')
        input_form_submitted = input_form.form_submit_button("Submit")
        
else:
    df = pd.read_csv(csv_file, names=['ticker', 'current_shares', 'target_weight'])
    #df = df.set_index('ticker')
    st.table(df)
    







