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

#TODO: do any filter here
##############
##CODE HERE
##############

# Write to sql Lite
df.to_sql('attacks', con=engine)

