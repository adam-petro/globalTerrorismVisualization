import sqlalchemy as db
import pandas as pd

## Create database
engine = db.create_engine('sqlite:///terroristdb.db')
conn = engine.connect()
metadata = db.MetaData()
#attacks = db.Table('attacks', metadata, autoload=True, autoload_with=engine)

# write data
filepath = './dataset/globalterrorismdb_0221dist.csv'
df = pd.read_csv(filepath, delimiter=';', on_bad_lines='skip', low_memory=False)

# TODO: do any pre-processing here
##############
##CODE HERE
df['latitude'] = df['latitude'].str.replace(',', '.')
df['longitude'] = df['longitude'].str.replace(',', '.')
df['latitude'] = pd.to_numeric(df['latitude'])
df['longitude'] = pd.to_numeric(df['longitude'])
df = df.replace({'Vehicle (not to include vehicle-borne explosives, i.e., car or truck bombs)': 'Vehicle'})
##############

# Write to sql Lite
df.to_sql('attacks', con=engine, if_exists='replace')

