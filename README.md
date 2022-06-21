# Covid-19 Dashboard for Spain
## Deployment
### AWS
1. The app was deployed via AWS ECS by building the Docker image and pushing it to AWS ECR. The EC2 Cluster consisted of one t2.medium instance and a single task was defined taking up all the EC2 instance CPU and Memory.
### Locally 
2. To deploy the app locally navigate to a directory on your local machine and run
```
git clone https://github.com/FranciscoPala/COVID-19_Spain_dashboard.git
cd COVID-19_Spain_dashboard
pip install -r requirements.txt
streamlit run app.py
```
## Overview
I decided to start working on this project on the summer of 2021, when the 5th wave was peaking and restrictions were being imposed on some Spanish regions. I found a [dataset](https://cnecovid.isciii.es/covid19/) published by the Spanish Ministry of Health. Which included **daily** **cases**, **hospitalizations**, **ICU admissions** and **deaths** disaggregated by **province** and **sex**.  
### Home section
1. Visualization of the datasets. And information on how the variables have been generated
1. A button to update the datasets
### Cases Section
1. An interactive line plot of the 7-day simple moving average. Total and by age.
2. A heatmap with the distribution by age group for each wave of the total cases and a horizontal bar plot of the total cases by wave.
3. A heatmap with the distribution by wave for each age group of the total cases and a horizontal bar plot of the total cases by age group.
4. A heatmap of **Cases as % of Total Age Group Population** by wave and a horizontal bar plot of the **total population**
### Hospitalization Section
1. The same first 3 plots as in the cases section for the hospitalization variable
1. A heatmap of **Hospitalizations as % of Total Cases** by wave and a heatmap of **Hospitalizations as % of Total Age Group Population**
### ICU Admissions Section
1. The same first 3 plots as in the cases section for the ICU admissions variable
1. A heatmap of **ICU Admissions as % of Hospitalizations** by wave and age group and a heatmap of **ICU Admissions as % of Total Age Group Population**
### Deaths Section 
1. The same first 3 plots as in the cases section for the deaths variable
1. A heatmap of **Deaths as % of ICU Admissions** by wave and age group a heatmap of **Deaths as % of Total Age Group Population**
