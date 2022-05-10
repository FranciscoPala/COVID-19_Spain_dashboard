import pandas as pd 
import numpy as np
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


def get_daily_sma7(data, by=['date']):
    # groupby date
    by_date = data.groupby(by, as_index=False).agg(
        dailyCases = ('cases', sum),
        dailyHospitalizations = ('hospitalizations', sum),
        dailyICU = ('icu', sum),
        dailyDeaths = ('deaths', sum),
    ).sort_values('date')
    # smooth to sma7
    cols = ['dailyCases', 'dailyHospitalizations', 'dailyICU', 'dailyDeaths']
    by_date.loc[:,cols] = by_date.loc[:,cols].rolling(7).mean().fillna(by_date.loc[:,cols])
    by_date.loc[:,cols] = by_date.loc[:,cols].astype(int)
    return by_date


def get_waves(get_daily_sma7, data):
    daily_totals = get_daily_sma7(data)
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