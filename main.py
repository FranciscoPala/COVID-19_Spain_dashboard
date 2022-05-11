import streamlit as st
import pandas as pd
import pathlib
from utils.funcs import *
import plotly.express as px

cwd = pathlib.Path.cwd()

st.set_page_config(
    page_title='Covid-19 Dashboard Spain',
    layout = 'wide',
)

data = pd.read_csv(cwd / 'data/covid_19_spain.csv', sep = ';')

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

st.plotly_chart(fig, use_container_width=True)

fig = px.line(
    age_series, 
    x="date", 
    y="dailyHospitalizations", 
    color='age',
    template = 'simple_white',
    width=1600,
    height=500,
    title = 'Daily Hospitalizations of Covid-19 by Age in Spain, 7-day Simple Moving Average')

st.plotly_chart(fig, use_container_width=True)

fig = px.line(
    age_series, 
    x="date", 
    y="dailyICU", 
    color='age',
    template = 'simple_white',
    width=1600,
    height=500,
    title = 'Daily ICU Admissions of Covid-19 by Age in Spain, 7-day Simple Moving Average')

st.plotly_chart(fig, use_container_width=True)

fig = px.line(
    age_series, 
    x="date", 
    y="dailyDeaths", 
    color='age',
    template = 'simple_white',
    width=1600,
    height=500,
    title = 'Daily Deaths of Covid-19 by Age in Spain, 7-day Simple Moving Average')

st.plotly_chart(fig, use_container_width=True)