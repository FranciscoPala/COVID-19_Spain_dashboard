# Covid-19 Dashboard for Spain
## Overview
I decided to start working on this project on the summer of 2021, when the 5th wave was peaking and restrictions were being imposed on some Spanish regions. I found a [dataset](https://cnecovid.isciii.es/covid19/) published by the Spanish Ministry of Health. Which included **daily** **cases**, **hospitalizations**, **ICU admissions** and **deaths** disaggregated by **province** and **sex**.  
The app is deployed in **streamlit**, and it consists of several pages:
- An **Overview** section where the two main datasets used in visualizations are printed with a button to update to the most recent data.
- A **Cases** section with 3 different plots:
  - An interactive line plot of the 7-day simple moving average. Total and by age.
  - A heatmap with the distribution by age group for each wave of the total cases and a horizontal bar plot of the total cases by wave.
  - A heatmap with the distribution by wave for each age group of the total cases and a horizontal bar plot of the total cases by age group.
- A section like the above for each **Hospitalizations**, **ICU Admissions** and **Deaths**.
- A **Ratios** section containing:
  - A heatmap of **Cases as % of Total Age Group Population** by wave and a horizontal bar plot of the **total population**
  - A heatmap of **Hospitalizations as % of Total Cases** by wave and a heatmap of **Hospitalizations as % of Total Age Group Population**
  - A heatmap of **ICU Admissions as % of Hospitalizations** by wave and age group and a heatmap of **ICU Admissions as % of Total Age Group Population**
  - A heatmap of **Deaths as % of ICU Admissions** by wave and age group a heatmap of **Deaths as % of Total Age Group Population**
- A **Predictions** section containing the daily prediction of total cases for the next two weeks using ARIMA.