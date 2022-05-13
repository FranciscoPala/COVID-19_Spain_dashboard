import pandas as pd 
import numpy as np
import seaborn as sns
import matplotlib.pyplot as plt
from scipy.signal import find_peaks

def get_data():
    # dather from ministry of health and convert dtypes
    url = 'https://cnecovid.isciii.es/covid19/resources/casos_hosp_uci_def_sexo_edad_provres.csv'
    data = pd.read_csv(url).convert_dtypes()
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
    # find first case
    min_date = data.groupby('date', as_index=False).sum().query("cases > 0").date.min()
    # keep only values gte min_date
    date_mask = data.date >= min_date
    data = data.loc[date_mask, :]
    return data

def get_sma7(data):
    by_date = data.groupby('date').agg(
        dailyCases = ('cases', sum),
        dailyHospitalizations = ('hospitalizations', sum),
        dailyICU = ('icu', sum),
        dailyDeaths = ('deaths', sum),
    ).sort_values('date').rolling(7).mean().fillna(0).astype(int).reset_index()
    return by_date


def get_sma7_by_age(data):
    by_age = data.groupby(['age', 'date']).agg(
        dailyCases = ('cases', sum),
        dailyHospitalizations = ('hospitalizations', sum),
        dailyICU = ('icu', sum),
        dailyDeaths = ('deaths', sum),
    ).sort_values(['age','date']).reset_index()
    # smooth to sma7
    by_age = by_age.set_index('date').groupby('age').rolling(7).mean()
    by_age = by_age.fillna(0).astype(int).reset_index()
    all_ages = by_age.groupby('date', as_index=False).sum()
    all_ages['age'] = 'All Ages'
    data_out = pd.concat([by_age, all_ages])
    return data_out


def get_waves(get_sma7, data):
    daily_totals = get_sma7(data)
    # get peak indices
    peaks, _ = find_peaks(
        x = daily_totals.dailyCases,
        width=20
        )
    peak_dates = daily_totals.iloc[peaks].date
    peaks_array = peak_dates.values
    valleys = []
    for i in range(1,peaks_array.size):
        lower_bound = peaks_array[i-1]
        upper_bound = peaks_array[i]
        mask = daily_totals.date.between(lower_bound, upper_bound)
        valleys.append(daily_totals[mask].dailyCases.idxmin())
    valley_dates = daily_totals.iloc[valleys].date.values
    wave_dates = np.insert(valley_dates, 0, data.date.min())
    wave_dates = np.insert(wave_dates, wave_dates.size, data.date.max())
    data['wave'] = pd.cut(
        data.date, 
        bins=wave_dates,
        right=True,
        include_lowest = True,
        labels = range(1, wave_dates.size)
        )
    return data

def get_wave_totals(data):
    totals_wave = data.groupby('wave', as_index=False).sum()
    return totals_wave


def get_heatmap_data(data, variable):
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


def plot_heatmap(heatmap_data, barplot_data, variable):
    size_unit=np.array([1.7*1.77, 1])
    fig, ax = plt.subplots(1, 2, figsize=7*size_unit, gridspec_kw={"width_ratios": (.6, .4)})
    fig.subplots_adjust(wspace=0, hspace=0)
    # heatmap
    sns.heatmap(
        data = heatmap_data, 
        annot=True, 
        linewidths=0.1, 
        cmap='Blues', 
        fmt='.2f', 
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
    ax[0].set_title('Distribution of Cases Within Wave by Age')
    ax[1].set_title('Total Cases by Wave (Thousands)')
    return fig