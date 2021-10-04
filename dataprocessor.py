import sqlite3
import dash
import pandas as pd

app = dash.Dash(__name__)
server = app.server


class TerroristData:

    def __init__(self):
        self.conn = sqlite3.connect('terroristdb.db')
        print("Opened database successfully")

        # connect a database connection to the
        # database that resides in the memory
        conn = sqlite3.connect(':memory:')
        print("Established database connection to a database\
                that resides in the memory!")

    def get_attact_count_by_country(self, country_list=None):
        if country_list == None:
            df_cty = pd.read_sql_query("SELECT country_txt, count() from attacks group by country", self.conn)
        else:
            df_cty = pd.read_sql_query("SELECT country_txt, count() from attacks where "
                                       " country in {} "
                                       "group by country".format(country_list), self.conn)
        return df_cty

    def close_conn(self):
        self.conn.close()


td = TerroristData()
df = td.get_attact_count_by_country()
print(df.head())



