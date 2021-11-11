import sqlite3
import dash
import pandas as pd

app = dash.Dash(__name__)
app.config.suppress_callback_exceptions = True


server = app.server


class TerroristData:

    def __init__(self):
        self.conn = sqlite3.connect('terroristdb.db', check_same_thread=False)
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
            df_all = pd.read_sql_query("SELECT eventid, country_txt, iyear, longitude,latitude, success, nkill, weaptype1_txt from attacks"
                                       " where iyear <= {}".format(year), self.conn)
        else:
            df_all = pd.read_sql_query("SELECT eventid, country_txt, iyear, longitude,latitude,success, nkill, weaptype1_txt from attacks", self.conn)
        return df_all

    def get_data_for_scat(self, year=None):
        if year is None:
            df_all = pd.read_sql_query("SELECT eventid, country_txt, longitude,latitude, attacktype1_txt, iyear, "
                                       "imonth,iday, success, weaptype1_txt from attacks", self.conn)
        else:
            df_all = pd.read_sql_query("SELECT eventid, country_txt, longitude,latitude, attacktype1_txt, iyear, "
                                       "imonth,iday, success, weaptype1_txt from attacks where "
                                       "iyear <= {}".format(year), self.conn)
        return df_all

    def get_weapon_data(self, eventids=[]):
        if len(eventids)==0:
            df_all = pd.read_sql_query("SELECT eventid, weaptype1_txt, iyear, success, country_txt as count from attacks", self.conn)
        else:
            df_all = pd.read_sql_query(f"SELECT eventid, weaptype1_txt, iyear, success, country_txt as count from attacks WHERE eventid IN ({','.join(eventids)})", self.conn)
        return df_all

    def get_groups_data(self, eventids=[], year_begin=None, year_end=None):
        # filter out NaNs and unknown groups
        if len(eventids) == 0:
            df_all = pd.read_sql_query("SELECT eventid, iyear, gname, nkill from attacks WHERE nkill is not null and gname != 'Unknown'", self.conn)
        else:
            df_all = pd.read_sql_query(f"SELECT eventid, iyear, gname, nkill from attacks WHERE eventid IN ({','.join(eventids)}) and nkill is not null and gname != 'Unknown'", self.conn) 
        return df_all
    
    def get_terrorist_groups(self):
        df_tg = pd.read_sql_query("SELECT DISTINCT	gname from attacks order by gname asc", self.conn)
        return df_tg
    
    # def get_target_nationalities(self, eventids=[]):
        # df_tg_natlty = natlty1_txt


    def get_top_groups_sorted(self):
        df_all = pd.read_sql_query("SELECT gname, COUNT(*) as count from attacks WHERE nkill is not null and gname != 'Unknown' GROUP BY gname ORDER BY count DESC", self.conn)
        return df_all

    def close_conn(self):
        self.conn.close()


