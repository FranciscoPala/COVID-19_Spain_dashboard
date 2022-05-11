import streamlit as st
import pandas as pd
from 
import plotly.express as px


st.set_page_config(
    page_title='Covid-19 Dashboard Spain',
    layout = 'wide',
)

data = pd.read_csv('../data/covid_19_spain.csv', sep = ';')
age_series = get_sma7_by_age(data)
fig = px.line(
    age_series, 
    x="date", 
    y="dailyCases", 
    color='age',
    template = 'simple_white',
    width=1600,
    height=500,
    title = 'Daily Cases of Covid-19 by Age in Spain, 7-day Simple Moving Average')
