import requests
import json
import os
import sys
import pandas as pd

class MNWApi():
    def __init__(self):
        self.api_url = "https://api.meteonetwork.it/v3"
        
        if 'MNW_TOKEN' in os.environ:
            self.token = os.environ['MNW_TOKEN']
        else:
            print('Requiring new token')
            self.token = self.get_token()
            os.environ['MNW_TOKEN'] = self.token
        if 'MNW_BULK_TOKEN' in os.environ:
            self.bulk_token = os.environ['MNW_BULK_TOKEN']
        else:
            print('Requiring new bulk token')
            self.bulk_token = self.get_token(bulk=True)
            os.environ['MNW_BULK_TOKEN'] = self.token
        
        self.headers = {'Authorization': "Bearer %s" % self.token}
        self.bulk_headers = {'Authorization': "Bearer %s" % self.bulk_token}

    def get_token(self, bulk=False):
        url =  "%s/login" % self.api_url
        data = {
            'email': os.environ['MNW_MAIL'],
            'password': os.environ['MNW_PASSWORD']
        }
        if bulk:
            data['bulk'] = True
            data['company'] = 'Private interest, no commercial purpose'
            data['description'] = 'Hobby, making visualisation and analysis of data'
            data['contribution'] = 'service'
        
        response = requests.request("POST", url, data=data)
        js = json.loads(response.text)
        
        if "access_token" in js:
            return js["access_token"]
        else:
            sys.exit('Error in getting token: %s' % response.text) 

    def get_realtime_station(self, station_code, data_quality=True):
        '''Get realtime data from a single station. 
        Need station_code as input'''
        url = "%s/data-realtime/%s" % (self.api_url, station_code)
        data = {
            'data_quality': data_quality
        }
        response = requests.request("GET", url, headers=self.headers, params=data)
        
        return pd.read_json(response.text)
    
    def get_realtime_stations(self, country=None, region=None,
                             lat=None, lon=None, range_km=None, data_quality=True):
        '''Get realtime data for all stations.
        One can specify country, region (IT) or a center lat, lon and a range (in km)
        to search stations in this area.'''
        url = "%s/data-realtime" % self.api_url
        data = {
            'data_quality': data_quality
        }
        if country:
            data['country'] = country
        if region:
            data['region'] = region
        if lat:
            data['lat'] = lat
        if lon:
            data['lon'] = lon
        if range_km:
            data['range'] = range_km
            
        response = requests.request("GET", url, headers=self.bulk_headers, params=data)
        
        return pd.read_json(response.text)

    def get_daily_station(self, station_code, observation_date="today", data_quality=True):
        '''Get daily data from a single station. 
        Need station_code and observation_date (YYYY-MM-DD) as input'''
        url = "%s/data-daily/%s" % (self.api_url, station_code)
        data = {
            'data_quality': data_quality,
            'observation_date': observation_date
        }
        response = requests.request("GET", url, headers=self.headers, params=data)
        
        return pd.read_json(response.text)

    def get_daily_stations(self, observation_date="today", country=None, region=None,
                             lat=None, lon=None, range_km=None, data_quality=True):
        '''Get daily data for all stations.
        One can specify country, region (IT) or a center lat, lon and a range (in km)
        to search stations in this area.'''
        url = "%s/data-daily" % self.api_url
        data = {
            'data_quality': data_quality,
            'observation_date': observation_date
        }
        if country:
            data['country'] = country
        if region:
            data['region'] = region
        if lat:
            data['lat'] = lat
        if lon:
            data['lon'] = lon
        if range_km:
            data['range'] = range_km
            
        response = requests.request("GET", url, headers=self.bulk_headers, params=data)
        
        return pd.read_json(response.text)
    
    def get_stations_meta(self, country=None, region=None,
                             lat=None, lon=None, range_km=None, data_quality=True):
        '''Get station attributes.'''
        url = "%s/stations" % self.api_url
        data = {
            'data_quality': data_quality
        }
        if country:
            data['country'] = country
        if region:
            data['region'] = region
        if lat:
            data['lat'] = lat
        if lon:
            data['lon'] = lon
        if range_km:
            data['range'] = range_km
            
        response = requests.request("GET", url, headers=self.bulk_headers, params=data)
        
        return pd.read_json(response.text)
    
    def get_archive_station(self, station_code, observation_date="today", data_quality=True):
        '''Get archived data from a single station. 
        Need station_code and observation_date (YYYY-MM-DD) as input'''
        url = "%s/data-archive/%s" % (self.api_url, station_code)
        data = {
            'data_quality': data_quality,
            'observation_date':observation_date
        }
        response = requests.request("GET", url, headers=self.bulk_headers, params=data)
        
        return pd.read_json(response.text)