import json
import urllib.request
import urllib.parse
import sys

def get_current_weather(city):
    """
    Fetches the current weather for a given city using wttr.in.
    """
    try:
        # Encode the city name for the URL
        encoded_city = urllib.parse.quote(city)
        url = f"https://wttr.in/{encoded_city}?format=j1"
        
        # Create a request with a User-Agent to avoid being blocked
        req = urllib.request.Request(
            url, 
            headers={'User-Agent': 'Mozilla/5.0'}
        )
        
        with urllib.request.urlopen(req) as response:
            if response.status != 200:
                return json.dumps({"error": f"Failed to fetch weather data. Status code: {response.status}"})
            
            data = json.loads(response.read().decode('utf-8'))
            
            # Extract current condition
            current_condition = data['current_condition'][0]
            
            result = {
                "city": city,
                "temperature_C": current_condition['temp_C'],
                "weather_desc": current_condition['weatherDesc'][0]['value'],
                "humidity": current_condition['humidity'],
                "wind_speed_kmph": current_condition['windspeedKmph'],
                "observation_time": current_condition['observation_time']
            }
            
            return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        return json.dumps({"error": str(e)})

# Simple test block (not executed when imported)
if __name__ == "__main__":
    if len(sys.argv) > 1:
        print(get_current_weather(sys.argv[1]))
    else:
        print(get_current_weather("Beijing"))
