import sqlite3
import dash
import pandas as pd

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True


server = app.server


class TerroristData:

    def __init__(self):
        self.conn = sqlite3.connect('terroristdb.db')
        print("Opened database successfully")

        # connect a database connection to the
        # database that resides in the memory
        #self.conn = sqlite3.connect(':memory:')
        print("Established database connection to a database\
                that resides in the memory!")

    def get_attack_count_by_country(self, country_list=None):
        if country_list == None:
            df_cty = pd.read_sql_query("SELECT country_txt, count() from attacks group by country", self.conn)
        else:
            df_cty = pd.read_sql_query("SELECT country_txt, count() from attacks where "
                                       " country in {} "
                                       "group by country".format(country_list), self.conn)
        return df_cty

    def get_country(self):
        df_cty = pd.read_sql_query("SELECT DISTINCT	country_txt from attacks order by country_txt asc", self.conn)
        return df_cty

    def get_years(self):
        df_year = pd.read_sql_query("SELECT iyear  from attacks", self.conn)
        return df_year

    def get_lat_long(self, year=None):
        if year is not None:
            df_all = pd.read_sql_query("SELECT country_txt, iyear, longitude,latitude from attacks"
                                       " where iyear <= {}".format(year), self.conn)
        else:
            df_all = pd.read_sql_query("SELECT country_txt, iyear, longitude,latitude from attacks", self.conn)
        return df_all

    def get_data_for_scat(self, year=None):
        if year is None:
            df_all = pd.read_sql_query("SELECT country_txt, longitude,latitude, attacktype1_txt, iyear, "
                                       "imonth,iday from attacks", self.conn)
        else:
            df_all = pd.read_sql_query("SELECT country_txt, longitude,latitude, attacktype1_txt, iyear, "
                                       "imonth,iday from attacks where "
                                       "iyear <= {}".format(year), self.conn)

        return df_all

    def close_conn(self):
        self.conn.close()


