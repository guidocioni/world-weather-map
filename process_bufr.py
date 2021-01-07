from pdbufr import read_bufr
import pandas as pd
from functools import reduce
import requests

def download_url(url, save_path, chunk_size=128):
    r = requests.get(url, stream=True)
    with open(save_path, 'wb') as fd:
        for chunk in r.iter_content(chunk_size=chunk_size):
            fd.write(chunk)

download_url('https://opendata.dwd.de/weather/weather_reports/synoptic/germany/Z__C_EDZW_latest_bda01%2Csynop_bufr_GER_999999_999999__MW_XXX.bin',
             './latest.bin')

# download_url('https://opendata.dwd.de/weather/weather_reports/synoptic/international/Z__C_EDZW_latest_bda01%2Csynop_bufr_999999_999999__MW_XXX.bin',
#              './latest.bin')

df_stations = read_bufr('./latest.bin',
          columns=('stationOrSiteName',
                   'latitude',
                   'longitude',
                   'heightOfStationGroundAboveMeanSeaLevel',
                   'year', 'month', 'day', 'hour', 'minute',
                   ))
df_stations = df_stations.drop_duplicates()
df_stations = df_stations.set_index('stationOrSiteName')
df_stations['date'] = df_stations.day.astype(int).astype(str) +"/"+\
df_stations.month.astype(int).astype(str)+"/"+\
df_stations.year.astype(int).astype(str)+" "+\
df_stations.hour.astype(int).astype(str)+":"+\
df_stations.minute.astype(int).astype(str)
df_stations['date'] = pd.to_datetime(df_stations['date'])
df_stations = df_stations.drop(columns=["minute", "hour", "year", "month", "day"])

df_kl = read_bufr('./latest.bin',
          columns=('stationOrSiteName',
                   'airTemperature',
                   'relativeHumidity',
                   'dewpointTemperature',
                   ),
              filters={'heightOfSensorAboveLocalGroundOrDeckOfMarinePlatform': 2})
df_kl = df_kl.drop_duplicates()
df_kl['airTemperature'] = df_kl['airTemperature'] - 273.15 
df_kl['dewpointTemperature'] = df_kl['dewpointTemperature'] - 273.15 
df_kl = df_kl.set_index('stationOrSiteName')
#
df_ps = read_bufr('./latest.bin',
          columns=('stationOrSiteName',
                   'pressureReducedToMeanSeaLevel',
                   ))
df_ps = df_ps.drop_duplicates()
df_ps['pressureReducedToMeanSeaLevel'] = df_ps['pressureReducedToMeanSeaLevel'] / 100.
df_ps = df_ps.set_index('stationOrSiteName')
#
df_wind = read_bufr('./latest.bin',
          columns=('stationOrSiteName',
                   'windSpeed', 'windDirection', 'maximumWindGustSpeed'
                   ),)

df_wind = df_wind.drop_duplicates()
df_wind['windSpeed'] = df_wind['windSpeed'] * 3.6
df_wind['maximumWindGustSpeed'] = df_wind['maximumWindGustSpeed'] * 3.6
df_wind = df_wind.set_index('stationOrSiteName')
#
df_prec = read_bufr('./latest.bin',
          columns=('stationOrSiteName',
                   'totalPrecipitationOrTotalWaterEquivalent'
                   ),
                   filters={'timePeriod': -10})

df_prec = df_prec.drop_duplicates().dropna(subset=['totalPrecipitationOrTotalWaterEquivalent'])
df_prec['totalPrecipitationOrTotalWaterEquivalent'] = df_prec['totalPrecipitationOrTotalWaterEquivalent'] * (.10 / 60.) # mm/h
df_prec = df_prec.set_index('stationOrSiteName')
#
df_snow = read_bufr('./latest.bin',
          columns=('stationOrSiteName',
                   'totalSnowDepth',
                   ))
df_snow = df_snow.drop_duplicates().dropna(subset=['totalSnowDepth'])
df_snow = df_snow.set_index('stationOrSiteName')
#
df_rad = read_bufr('./latest.bin',
          columns=('stationOrSiteName',
                   'globalSolarRadiationIntegratedOverPeriodSpecified',
                   ))
df_rad = df_rad.drop_duplicates().dropna(subset=['globalSolarRadiationIntegratedOverPeriodSpecified'])
df_rad['globalSolarRadiationIntegratedOverPeriodSpecified'] = df_rad['globalSolarRadiationIntegratedOverPeriodSpecified'] / 600 # W m-2 I hope
df_rad = df_rad.set_index('stationOrSiteName')
# final merging

data = [df_kl, df_ps, df_wind, df_prec, df_snow, df_rad, df_stations]
merged = reduce(lambda left, right: pd.merge(left, right, left_index=True, right_index=True, how='outer') , data)


merged.to_pickle('output.pkl')