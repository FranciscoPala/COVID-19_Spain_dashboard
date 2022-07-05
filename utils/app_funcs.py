import pandas as pd 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px
from scipy.signal import find_peaks


# GATHERING FUNCTIONS
######################

def get_data(): # added to class DataHandler
    """gathers data from the Spanish Ministry of Health and formats it 

    Returns:
        data(pd.DataFrame): gathered dataframe with some basic formatting
    """
    url = 'https://cnecovid.isciii.es/covid19/resources/casos_hosp_uci_def_sexo_edad_provres.csv'
    data = pd.read_csv(url, keep_default_na=False).convert_dtypes()
    data.fecha = pd.to_datetime(data.fecha)
    # renames
    col_rename = {
        'provincia_iso': 'province',
        'sexo':'sex',
        'grupo_edad':'age',
        'fecha':'date',
        'num_casos':'cases',
        'num_hosp':'hospitalizations',
        'num_uci':'icu',
        'num_def':'deaths',
    }
    data = data.rename(col_rename, axis = 'columns')
    # remap ages
    dict_remap = dict(zip(
        data.age.unique(), 
        ['0s', '10s', '20s', '30s', '40s', '50s', '60s', '70s', '80+', 'NC']))
    data.age = data.age.replace(dict_remap)
    # find first case
    min_date = data.groupby('date', as_index=False).sum().query("cases > 0").date.min()
    # keep only values gte min_date
    date_mask = data.date >= min_date
    data = data.loc[date_mask, :]
    return data


def map_province(covid_data, prov_data):
    """Maps the province to its autonomous community on covid dataset

    Args:
        covid_data (pd.DataFrame): covid data gathered by get_data()
        prov_data (pd.DataFrame): dataframe with province info
    Returns:
        pd.DataFrame: dataframe with the autonomousComunity variable
    """
    ccaa_map = prov_data.set_index('codigoProvincia').nombreCCAA
    covid_data['autonomousCommunity'] = covid_data.province.str.strip().replace(ccaa_map)
    return covid_data


# DATA PROCESSING FUNCTIONS
############################

def get_sma7_gby_date(data):
    """Takes the covid dataset and returns the daily 7-day moving average

    Args:
        data (pd.DataFrame): covid dataset returned by get_data()

    Returns:
        pd.DataFrame: sma7 of observed variables
    """
    by_date = data.groupby('date').agg(
        dailyCases = ('cases', sum),
        dailyHospitalizations = ('hospitalizations', sum),
        dailyICU = ('icu', sum),
        dailyDeaths = ('deaths', sum),
    ).sort_values('date').rolling(7).mean().fillna(0).astype(int).reset_index()
    return by_date


def get_sma7_gby_age_date(data):
    """groups by age and date and calculates the daile 7day-sma for each age group

    Args:
        data (pd.DataFrame): covid dataset returned by get_data()

    Returns:
        pd.DataFrame: sma7 by age and date of observed variables
    """
    # get daily data by age group
    by_age = data.groupby(['age', 'date']).agg(
        dailyCases = ('cases', sum),
        dailyHospitalizations = ('hospitalizations', sum),
        dailyICU = ('icu', sum),
        dailyDeaths = ('deaths', sum),
    ).sort_values(['age','date']).reset_index()
    # smooth to sma7
    by_age = by_age.set_index('date').groupby('age').rolling(7).mean()
    by_age = by_age.fillna(0).astype(int).reset_index()
    # also generate an 'all ages' age group for future plotting
    all_ages = by_age.groupby('date', as_index=False).sum()
    all_ages['age'] = 'All Ages'
    data_out = pd.concat([by_age, all_ages])
    return data_out


def get_waves(get_sma7_gby_date, data):
    """_summary_

    Args:
        get_sma7_gby_date (python function): gets the daily sma7 of observed variabels
        data (pd.DataFrame): covid dataset returned by get_data()

    Returns:
        pd.DataFrame: dataframe with the added "waves" column
    """
    # get daily totals
    daily_totals = get_sma7_gby_date(data)
    # get peak indices
    peaks, _ = find_peaks(
        x = daily_totals.dailyCases,
        width=20
        )
    # get peak dates
    peak_dates = daily_totals.iloc[peaks].date
    peaks_array = peak_dates.values
    # find valleys as minimum between peaks
    valleys = []
    for i in range(1,peaks_array.size):
        # subset dataset between peaks
        lower_bound = peaks_array[i-1]
        upper_bound = peaks_array[i]
        mask = daily_totals.date.between(lower_bound, upper_bound)
        # get index of the minumum
        valleys.append(daily_totals[mask].dailyCases.idxmin())
    # get dates from the indices list
    valley_dates = daily_totals.iloc[valleys].date.values
    # inserts required for pd.cut
    wave_dates = np.insert(valley_dates, 0, data.date.min())
    wave_dates = np.insert(wave_dates, wave_dates.size, data.date.max())
    # create the numerical variable wave 
    data['wave'] = pd.cut(
        data.date, 
        bins=wave_dates,
        right=True,
        include_lowest = True,
        labels = range(1, wave_dates.size)
        )
    return data


def get_wave_heatmap_data(data, variable):
    """groups the covid dataset by age group and wave and creates a contingency
    table representing all age-wave combinations normalized to wave totals

    Args:
        data (pd.DataFrame): covid dataset returned by get_data()
        variable (string): observed variable
            'cases' covid cases
            'hospitalizations': hospitalizations 
            'icu': ICU admissions
            'deaths': SMA-7 of the daths variable

    Returns:
        pandas.DataFrame: contingency table for the age group and wave variables
    """
    # gby age and wave
    totals_age_wave = data.groupby(['age', 'wave'], as_index = False).sum()
    # drop NC age
    mask = totals_age_wave.age != 'NC'
    totals_age_wave = totals_age_wave[mask]
    # get cases dataframe
    heatmap_age_wave = pd.crosstab(
        index = totals_age_wave.wave, 
        columns = totals_age_wave.age, 
        values = totals_age_wave[variable], 
        aggfunc=sum, 
        normalize = 'index'
        )
    return heatmap_age_wave


def get_age_heatmap_data(data, variable):
    """groups the covid dataset by age group and wave and creates a contingency
    table representing all age-wave combinations normalized to age totals

    Args:
        data (pd.DataFrame): covid dataset returned by get_data()
        variable (string): observed variable
            'cases' covid cases
            'hospitalizations': hospitalizations 
            'icu': ICU admissions
            'deaths': SMA-7 of the daths variable

    Returns:
        pandas.DataFrame: contingency table for the age group and wave variables
    """
    # gby age and wave
    totals_age_wave = data.groupby(['age', 'wave'], as_index = False).sum()
    # drop NC age
    mask = totals_age_wave.age != 'NC'
    totals_age_wave = totals_age_wave[mask]
    # get cases dataframe
    heatmap_age_wave = pd.crosstab(
        index = totals_age_wave.age, 
        columns = totals_age_wave.wave, 
        values = totals_age_wave[variable], 
        aggfunc=sum, 
        normalize = 'index'
        )
    return heatmap_age_wave


def get_hosp_ratio_data(data, pop):
    """

    Args:
        data (pd.DataFrame): covid dataset returned by get_data()
        pop (pd.Dataframe): population DataFrame

    Returns:
        _type_: _description_
    """
    # get totals
    totals_age_wave = data.groupby(['age', 'wave'], as_index = False).sum()
    total_pop = pop.groupby('age').population.sum().drop('total')
    # drop NC
    mask = totals_age_wave.age != 'NC'
    totals_age_wave = totals_age_wave[mask]
    # calculate crosstabs
    cases = pd.crosstab(totals_age_wave.wave, totals_age_wave.age, totals_age_wave.cases, aggfunc=sum)
    hosp = pd.crosstab(totals_age_wave.wave, totals_age_wave.age, totals_age_wave.hospitalizations, aggfunc=sum)
    # get ratios
    hosp_cases = hosp/cases
    hosp_total_pop = hosp/total_pop
    return hosp_cases, hosp_total_pop


def get_icu_ratio_data(data, pop):
    totals_age_wave = data.groupby(['age', 'wave'], as_index = False).sum()
    total_pop = pop.groupby('age').population.sum().drop('total')
    mask = totals_age_wave.age != 'NC'
    totals_age_wave = totals_age_wave[mask]
    icu = pd.crosstab(totals_age_wave.wave, totals_age_wave.age, totals_age_wave.icu, aggfunc=sum)
    hosp = pd.crosstab(totals_age_wave.wave, totals_age_wave.age, totals_age_wave.hospitalizations, aggfunc=sum)
    icu_hosp = icu/hosp
    icu_total_pop = icu/total_pop
    return icu_hosp, icu_total_pop


def get_deaths_ratio_data(data, pop):
    totals_age_wave = data.groupby(['age', 'wave'], as_index = False).sum()
    total_pop = pop.groupby('age').population.sum().drop('total')
    mask = totals_age_wave.age != 'NC'
    totals_age_wave = totals_age_wave[mask]
    deaths = pd.crosstab(totals_age_wave.wave, totals_age_wave.age, totals_age_wave.deaths, aggfunc=sum)
    icu = pd.crosstab(totals_age_wave.wave, totals_age_wave.age, totals_age_wave.icu, aggfunc=sum)
    deaths_icu = deaths/icu
    deaths_total_pop = deaths/total_pop
    return deaths_icu, deaths_total_pop


def get_age_totalpop_norm_heatmap_data(data, data_pop, variable):
    """returns contingency table for age-wave combinations normalize to the
    total Spanish population

    Args:
        data (pd.DataFrame): covid dataset returned by get_data()
        data_pop (pd.DataFrame): dataset with information on the spanish population
        variable (string): observed variable
            'cases' covid cases
            'hospitalizations': hospitalizations 
            'icu': ICU admissions
            'deaths': SMA-7 of the daths variable

    Returns:
        pandas.DataFrame: contingency table for the age group and wave variables
    """
    # gby age and wave
    totals_age_wave = data.groupby(['age', 'wave'], as_index = False).sum()
    # drop NC age
    mask = totals_age_wave.age != 'NC'
    totals_age_wave = totals_age_wave[mask]
    # crosstab
    heatmap_wave_age = pd.crosstab(
        index = totals_age_wave.wave, 
        columns = totals_age_wave.age, 
        values = totals_age_wave[variable], 
        aggfunc=sum,
        )
    # normalize to Spanish total pop by age group
    total_pop = data_pop.groupby('age').population.sum().drop('total')
    heatmap_wave_age = heatmap_wave_age/total_pop
    heatmap_wave_age = heatmap_wave_age.T
    return heatmap_wave_age


# PLOT FUNCTIONS
################

def plot_lineplot(data, variable):
    """plots a time-series line plot of the selected variable using plotly

    Args:
        data (pd.DataFrame): covid-data grouped by date and age
        variable (string): observed variable
            'cases': SMA-7 of the cases variable
            'hospitalizations': SMA-7 of the hospitalizations variable
            'icu': SMA-7 of the icu variable
            'daths': SMA-7 of the daths variable

    Returns:
        plotly.graph_objects.Figure: interactive plotly visualization
    """
    fig = px.line(
        data, 
        x="date",
        y=variable, 
        color='age',
        template = 'simple_white',
        width=1600,
        height=500,
        title = '7-day Simple Moving Average of {}'.format(variable.capitalize()))
    return fig


def plot_wave_heatmap(heatmap_data, barplot_data, variable):
    """plots a figure consisting of a heatmap and a barplot

    Args:
        heatmap_data (pandas.DataFrame): contingency table for the heatmap
        barplot_data (pd.DataFrame): wave totals 
        variable (string): observed variable

    Returns:
        matplotlib.Figure: figure consisting of a heatmap and a horizontal bar plot
    """
    size_unit=np.array([1.7*1.77, 1])
    fig, ax = plt.subplots(1, 2, figsize=7*size_unit, gridspec_kw={"width_ratios": (.6, .4)})
    fig.subplots_adjust(wspace=0, hspace=0)
    # heatmap
    sns.heatmap(
        data = heatmap_data, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[0],
        )
    # barplot
    sns.barplot(
        data = barplot_data, 
        x=variable, 
        y='wave', 
        orient = 'h', 
        color=sns.color_palette()[0], 
        ax=ax[1],
        alpha=0.8,
        )
    # despine barplot
    sns.despine(fig=fig, ax=ax[1], top=True, bottom=True, left=True, right=True)
    # Axes styling
    ax[0].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].set(
        ylabel=None,
        xlabel=None,
        yticklabels=[],
        xticklabels=[],
        xticks=[],
        )
    # show labels
    ax[1].bar_label(
        ax[1].containers[0],
        fmt='%.0f',
        padding=7,
        )
    # titles
    ax[0].set_title('{} by Age-Group as Percentage of Total Wave {}'.format(variable.capitalize(), variable.capitalize()))
    ax[1].set_title('Total {} by Wave'.format(variable.capitalize()))
    return fig


def plot_heatmap_age(heatmap_data, barplot_data, variable):
    """plots a figure consisting of a heatmap and a barplot

    Args:
        heatmap_data (pandas.DataFrame): contingency table for the heatmap
        barplot_data (pd.DataFrame): age totals 
        variable (string): observed variable

    Returns:
        matplotlib.Figure: figure consisting of a heatmap and a horizontal bar plot
    """
    size_unit=np.array([1.7*1.77, 1])
    fig, ax = plt.subplots(1, 2, figsize=7*size_unit, gridspec_kw={"width_ratios": (.6, .4)})
    fig.subplots_adjust(wspace=0, hspace=0)
    # heatmap
    sns.heatmap(
        data = heatmap_data, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[0],
        )
    # barplot
    sns.barplot(
        data = barplot_data, 
        x=variable, 
        y='age', 
        orient = 'h', 
        color=sns.color_palette()[0], 
        ax=ax[1],
        alpha=0.8,
        )
    # despine barplot
    sns.despine(fig=fig, ax=ax[1], top=True, bottom=True, left=True, right=True)
    # Axes styling
    ax[0].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].set(
        ylabel=None,
        xlabel=None,
        yticklabels=[],
        xticklabels=[],
        xticks=[],
        )
    # show labels
    ax[1].bar_label(
        ax[1].containers[0],
        fmt='%.0f',
        padding=7,
        )
    # titles
    ax[0].set_title('{} by Wave as Percentage of Total Age-Group {}'.format(variable.capitalize(), variable.capitalize()))
    ax[1].set_title('Total {} by Age Group'.format(variable.capitalize()))
    return fig


def plot_heatmap_pop(heatmap_data, pop_data):
    """plots a figure consisting of a heatmap and a barplot

    Args:
        heatmap_data (pandas.DataFrame): contingency table for the heatmap
        pop_data (pd.DataFrame): spanish population totals by age group 

    Returns:
        matplotlib.Figure: figure consisting of a heatmap and a horizontal bar plot
    """
    # figure and spacing
    size_unit=np.array([1.7*1.77, 1])
    fig, ax = plt.subplots(1, 2, figsize=7*size_unit, gridspec_kw={"width_ratios": (.6, .4)})
    fig.subplots_adjust(wspace=0, hspace=0)
    # heatmap
    sns.heatmap(
        data = heatmap_data, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[0],
        )
    # barplot
    sns.barplot(
        data = pop_data, 
        x='population', 
        y='age', 
        orient = 'h', 
        color=sns.color_palette()[0], 
        ax=ax[1],
        alpha=0.8,
        )
    # despine barplot
    sns.despine(fig=fig, ax=ax[1], top=True, bottom=True, left=True, right=True)
    # Axes styling
    ax[0].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].set(
        ylabel=None,
        xlabel=None,
        yticklabels=[],
        xticklabels=[],
        xticks=[],
        )
    # show labels
    ax[1].bar_label(
        ax[1].containers[0],
        fmt='%.0f',
        padding=7,
        )
    # titles
    ax[0].set_title('Cases by Wave as Percentage of Total Age-Group Population')
    ax[1].set_title('Total Population by Age Group')
    return fig



def plot_heatmap_ratios_hosp(heatmap_cases_norm, heatmap_pop_norm):
    """plots both crosstabs returned from get_hosp_ratio_data()

    Args:
        heatmap_cases_norm (pd.DataFrame): xtab of age-wave normalized to cases
        heatmap_pop_norm (pd.DataFrame): xtab of age-wave normalized to population

    Returns:
        matplotlib.Figure: figure consisting of two heatmaps
    """
    # figure and spacing
    size_unit=np.array([1.7*1.77, 1])
    fig, ax = plt.subplots(1, 2, figsize=7*size_unit, gridspec_kw={"width_ratios": (.5, .5)})
    fig.subplots_adjust(wspace=0, hspace=0)
    # heatmap normalized to cases
    sns.heatmap(
        data = heatmap_cases_norm.T 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[0],
        )
    # heatmap normalized to total population by age group
    sns.heatmap(
        data = heatmap_pop_norm.T, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[1],
        )
    # despine barplot
    # Axes styling
    ax[0].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].tick_params(axis=u'both', which=u'both',length=0)
    # titles
    ax[0].set_title('Hospitalizations by Wave as Percentage of Cases')
    ax[1].set_title('Hospitalizations by Wave as Percentage of Age-Group Population')
    return fig


def plot_heatmap_ratios_icu(heatmap_data1, heatmap_data2):
    # figure and spacing
    size_unit=np.array([1.7*1.77, 1])
    fig, ax = plt.subplots(1, 2, figsize=7*size_unit, gridspec_kw={"width_ratios": (.5, .5)})
    fig.subplots_adjust(wspace=0, hspace=0)
    # heatmap
    sns.heatmap(
        data = heatmap_data1.T, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[0],
        )
    # barplot
    sns.heatmap(
        data = heatmap_data2.T, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[1],
        )
    # despine barplot
    # Axes styling
    ax[0].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].tick_params(axis=u'both', which=u'both',length=0)

    # titles
    ax[0].set_title('ICU Admissions by Wave as Percentage of Hospitalizations')
    ax[1].set_title('ICU Admissions by Wave as Percentage of Age-Group Population')
    return fig


def plot_heatmap_ratios_deaths(heatmap_data1, heatmap_data2):
    # figure and spacing
    size_unit=np.array([1.7*1.77, 1])
    fig, ax = plt.subplots(1, 2, figsize=7*size_unit, gridspec_kw={"width_ratios": (.5, .5)})
    fig.subplots_adjust(wspace=0, hspace=0)
    # heatmap
    sns.heatmap(
        data = heatmap_data1.T, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[0],
        )
    # barplot
    sns.heatmap(
        data = heatmap_data2.T, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2%', 
        ax = ax[1],
        )
    # despine barplot
    # Axes styling
    ax[0].tick_params(axis=u'both', which=u'both',length=0)
    ax[1].tick_params(axis=u'both', which=u'both',length=0)

    # titles
    ax[0].set_title('Deaths by Wave as Percentage of ICU Admissions')
    ax[1].set_title('Deaths by Wave as Percentage of Age-Group Population')
    return fig