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
        # self.conn = sqlite3.connect(':memory:')
        print("Established database connection to a database\
                that resides in the memory!")

    def get_attack_count_by_country(self, country_list=None):
        if country_list is None:
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
            df_all = pd.read_sql_query("SELECT eventid, country_txt, iyear, longitude,latitude,"
                                       " success, nkill from attacks"
                                       " where iyear <= {}".format(year), self.conn)
        else:
            df_all = pd.read_sql_query("SELECT eventid, country_txt, iyear, longitude,latitude,success, "
                                       "nkill from attacks", self.conn)
        return df_all

    def get_data_for_scat(self, year=None):
        if year is None:
            df_all = pd.read_sql_query("SELECT eventid, country_txt, longitude,latitude, attacktype1_txt, iyear, "
                                       "imonth,iday, success from attacks", self.conn)
        else:
            df_all = pd.read_sql_query("SELECT eventid, country_txt, longitude,latitude, attacktype1_txt, iyear, "
                                       "imonth,iday, success from attacks where "
                                       "iyear <= {}".format(year), self.conn)
        return df_all

    def get_weapon_data(self, eventids=[]):
        if len(eventids) == 0:
            df_all = pd.read_sql_query("SELECT eventid, weaptype1_txt, COUNT(*) as count from "
                                       "attacks GROUP BY eventid,weaptype1_txt", self.conn)
        else:
            df_all = pd.read_sql_query(f"SELECT eventid, weaptype1_txt, COUNT(*) as count from "
                                       f"attacks WHERE eventid IN ({','.join(eventids)}) GROUP BY "
                                       f"eventid,weaptype1_txt", self.conn)
        return df_all

    # def get_data_for_bbox_for_ids(self, eventids=[]):
    #     if len(eventids) == 0:
    #         df_all = pd.read_sql_query("SELECT attacktype1_txt, COUNT(attacktype1_txt) as cnt, "
    #                                    "GROUP_CONCAT(DISTINCT location) loc, "
    #                                    "GROUP_CONCAT(DISTINCT targtype1_txt) targ  "
    #                                    " from attacks GROUP BY attacktype1_txt", self.conn)
    #     else:
    #         df_all = pd.read_sql_query(f"SELECT attacktype1_txt, COUNT(attacktype1_txt) as cnt"
    #                                    "GROUP_CONCAT(DISTINCT location) loc, "
    #                                    "GROUP_CONCAT(DISTINCT targtype1_txt) targ  "
    #                                    f" from attacks WHERE eventid IN ({','.join(eventids)}) GROUP BY "
    #                                    f" attacktype1_txt", self.conn)
    #     return df_all

    def get_data_for_bbox_for_ids(self, eventids=[]):
        if len(eventids) == 0:
            df_all = pd.read_sql_query("SELECT attacktype1_txt, COUNT(attacktype1_txt) as cnt, "
                                       "count(location) loc, "
                                       "count(targtype1_txt) targ  "
                                       " from attacks GROUP BY attacktype1_txt", self.conn)
        else:
            df_all = pd.read_sql_query(f"SELECT attacktype1_txt, COUNT(attacktype1_txt) as cnt, "
                                       "count(location) loc, "
                                       "count(targtype1_txt) targ  "
                                       f" from attacks WHERE eventid IN ({','.join(eventids)}) GROUP BY "
                                       f" attacktype1_txt", self.conn)
        return df_all

    def get_data_for_bbox(self, bbox):
        lat_max = bbox[0][1]
        lat_min = bbox[1][1]
        lon_max = bbox[1][0]
        lon_min = bbox[0][0]

        query = "SELECT weaptype1_txt, count(weaptype1_txt) cnt from attacks" \
                " where latitude >= {} and latitude <= {} " \
                "and longitude >= {} and longitude <= {} group by " \
                "weaptype1_txt".format(lat_min, lat_max, lon_min, lon_max)
        df_all = None
        try:
            df_all = pd.read_sql_query(query, self.conn)
        except Exception as ex:
            print(ex)
        return df_all

    def close_conn(self):
        self.conn.close()
