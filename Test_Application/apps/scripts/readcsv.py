import pandas as pd
from os.path import dirname, join

## Read the data initially to be able to have headers
def readcsv(filename, filepath):
	df = pd.read_csv(join(filepath, filename), verbose=True, skiprows=[1]).set_index('Time')
		  
	# prepare dataframe
	df.index = pd.to_datetime(df.index).tz_localize('UTC').tz_convert('UTC')
	df.sort_index(inplace=True)
	df.drop([i for i in df.columns if 'Unnamed' in i], axis=1, inplace=True)

	df = df.apply(pd.to_numeric)

	readings = df[df.index > '2001-01-01T00:00:01Z']

	return readings