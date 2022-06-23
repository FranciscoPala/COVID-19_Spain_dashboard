import pathlib
import pandas as pd
from app_funcs import *



def DataHandler():

    def __init__(self, data_source, data_dir):
        self.data_source = data_source
        self.data_dir = data_dir
        self.processed_data_dir = data_dir / 'processed'
        self.last_date = None
        self.covid_data_path = None
        return None


    def update_covid_data(self):
        # read data from source url and format
        url = self.data_source
        data = pd.read_csv(url).convert_dtypes()
        # TODO add a format checker before running this
        data.fecha = pd.to_datetime(data.fecha)
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
        # define export path
        self.covid_data_path = self.data_dir / 'covid_19_spain.csv'
        data.to_csv(self.covid_data_path, sep = ';', index=False)
        # update last date attribute
        self.last_date = data.date.max()
        return 'finished gathering and formatting covid data'


    def compute_sma7_gby_date(self):
        data = pd.read_csv(self.covid_data_path, sep = ';')
        data_gby = data.groupby('date').agg(
            dailyCases = ('cases', sum),
            dailyHospitalizations = ('hospitalizations', sum),
            dailyICU = ('icu', sum),
            dailyDeaths = ('deaths', sum),
        ).sort_values('date').rolling(7).mean().fillna(0).astype(int).reset_index()
        # export
        out_path = self.processed_data_dir / 'sma7_gby_date.csv'
        data_gby.to_csv(out_path, index = False, sep = ';')
        return None


    def compute_sma7_bgy_age_date(self):
        data = pd.read_csv(self.covid_data_path, sep = ';')
        data_gby = data.groupby(['age', 'date']).agg(
            dailyCases = ('cases', sum),
            dailyHospitalizations = ('hospitalizations', sum),
            dailyICU = ('icu', sum),
            dailyDeaths = ('deaths', sum),
            ).sort_values(['age','date']).reset_index()
        # smooth to sma7
        data_gby = data_gby.set_index('date').groupby('age').rolling(7).mean()
        data_gby = data_gby.fillna(0).astype(int).reset_index()
        all_ages = data_gby.groupby('date', as_index=False).sum()
        all_ages['age'] = 'All Ages'
        data_out = pd.concat([data_gby, all_ages])
        out_path = self.processed_data_dir / 'sma7_gby_age_date.csv'
        data_out.to_csv(out_path, index = False, sep = ';')
        return None

    def compute_data_assets(self):
        self.compute_wave_variable()
        self.compute_sma7_gby_date()
        self.compute_sma7_bgy_age_date()

    


def VariableSection():


    def __init__(self, assets_dir, data_dir, section_name):
        """Initializes an instance of a section 

        Args:
            assets_dir (pathlib.Path): parent path for assets
            data_dir (pathlib.Path): parent path for data
            section_name (string): string with the variable to watch

        Returns:
            init_message (string): init message
        """
        self.assets_dir = assets_dir
        self.section_name = section_name
        self.data_dir = data_dir
        # create subdir for variable section in assets dir
        section_dir = self.assets_dir / self.section_name
        pathlib.Path(section_dir).mkdir(parents=True, exist_ok=True)
        init_message = 'created section directory at {}'.format(section_dir)
        return init_message


    def compute_assets(self, covid_csv_key):
        # connect to covid data time series csv
        covid_csv_path = self.data_path / covid_csv_key
        covid_data = pd.read_csv(covid_csv_path, sep = ';')
        #
        return None
