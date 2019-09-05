from django.shortcuts import render
import requests
import string
from django.views.decorators.csrf import csrf_exempt

# for time conversions
import datetime as dt
import pytz

# for keys import
import os
import pickle

######## SET VARIABLES #########

### retrieve keys from pickle file
module_dir = os.path.dirname(__file__)  # get current directory
file_path = os.path.join(module_dir, 'keys.txt')
file = open(file_path,"rb")
keys = pickle.load(file)


### global variable keys
dark_key = keys['dark_key']
mapbox_key = keys['mapbox_key']

def getMapData(location, dark = dark_key, mapbox = mapbox_key):
    inp = location.translate(str.maketrans('', '', string.punctuation))
    inp = inp.replace(' ','%20')
    ### Mapbox data
    map_url = 'https://api.mapbox.com/geocoding/v5/mapbox.places/' + inp + '.json?access_token={}'
    map_req = requests.get(map_url.format(mapbox)).json()
    map_results = map_req['features'][0]
    map_data = {
        'place_name': map_results['place_name'],
        'latitude': str(map_results['center'][0]),
        'longitude': str(map_results['center'][1])
    }
    return map_data


def getDarkData(map_input, dark = dark_key, mapbox = mapbox_key):
    dark_url = 'https://api.darksky.net/forecast/{0}/{1},{2}?units=si'
    dark_req = requests.get(dark_url.format(dark, map_input['longitude'], map_input['latitude'])).json()
    return dark_req

# in all weather retrieval functions, weather is the output from the getDarkData function
def getCurrent(weather):
    current = weather['currently']
    currently = {
        'summary': current['summary'],
        'icon': current['icon'],
        'temperature': round(current['temperature']),
        'feels_like': round(current['apparentTemperature']),
        'precipInt': str(current['precipIntensity']) + ' mm per hour',
    }
    return currently

def getSoon(weather):
    soon = weather['hourly']
    hourly = {
        'summary': soon['summary'],
    }
    return hourly

def getDay(weather, day):
    tmrw = weather['daily']['data'][day]
    daily = {
        'summary': tmrw['summary'],
        'icon': tmrw['icon'],
        'temperature_high': round(tmrw['temperatureHigh']),
        'temperature_low': round(tmrw['temperatureLow']),
        'precipInt': str(tmrw['precipIntensity']) + ' mm per hour'
    }
    return daily

def getAll(location, dark = dark_key, mapbox = mapbox_key):
    address = getMapData(location)
    weath = getDarkData(address)
    all = {
        'map_data': address,
        'currently': getCurrent(weather=weath),
        'minutely': getSoon(weather=weath),
        'daily': getTmrw(weather=weath),
    }



#### Create your views here. ####
@csrf_exempt
def result(request):
    if request.method=='POST':
        test = request.POST.get('kyle')
        day_input = request.POST.get('date')
        address = getMapData(test)
        weath = getDarkData(address)
        tz = pytz.timezone(weath['timezone'])
        this_day = dt.datetime.now(tz) + dt.timedelta(days=int(day_input))
        this_day = this_day.strftime('%A, %B %d')

        data = {
            'map_data': address,
            'currently': getCurrent(weather=weath),
            'hourly': getSoon(weather=weath),
            'daily': getDay(weather=weath, day = int(day_input)),
            'day': this_day,
            'days_ahead': int(day_input),
        }
        
        return render(request, 'weather_app/results.html', data)


@csrf_exempt
def home(request):
    return render(request, 'weather_app/home.html')
