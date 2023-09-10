#get weather data from a given string location
import requests
from geopy.geocoders import Nominatim

#get lat and long from a US ONLY city based on city name
def get_latlong(loc):
    geolocator = Nominatim(user_agent="<username>")
    location = geolocator.geocode(loc)
    return (location.latitude, location.longitude)

#return noaa api information about the city
def get_location_info(location):
    response = requests.get(f'https://api.weather.gov/points/{location[0]},{location[1]}')
    data = response.json()
    forecast_link = data['properties']['forecast']
    hours_forecast_link = data['properties']['forecastHourly']
    location_info = [data['properties']['relativeLocation']['properties']['city'], data['properties']['relativeLocation']['properties']['state']]
    return [forecast_link, hours_forecast_link, location_info]

#return data from noaa api dealing with the two-part daily forecast
def get_forecast_data(fl):
    response = requests.get(fl)
    data = response.json()
    periods = []
    for i in data['properties']['periods']:
        periods.append(i)
    return periods

def parse_forecast_data(periods):
    for p in periods:
        print(f'{p["name"]}')
        print(f'Temperature: {p["temperature"]} °F')
        if(p['probabilityOfPrecipitation']['value'] != None):
            print(f'Precip Probability: {p["probabilityOfPrecipitation"]["value"]}%')
        print(f'Dewpoint: {(p["dewpoint"]["value"] * (9/5)) + 32} °F')
        print(f'Humidity: {p["relativeHumidity"]["value"]}%')
        print(f'Wind Speed: {p["windSpeed"]}')
        print(f'Wind Direction: {p["windDirection"]}')
        print(f'Icon Link: {p["icon"][:-11]}size=large')
        print(f'Short Desc: {p["shortForecast"]}')
        print(f'Detailed Forecast: {p["detailedForecast"]}')
        print('-------------')

location = get_latlong('Schenetady, NY')
location_info = get_location_info(location)
forecast_data = get_forecast_data(location_info[0])
parse_forecast_data(forecast_data)
