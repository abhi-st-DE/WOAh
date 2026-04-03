import os
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

api_key = os.getenv("OpenWeather_API_KEY")
if not api_key:
    raise ValueError("OpenWeather_API_KEY not found in your environment variable.")

def test_openweather_key(key):
    # We'll test using the Current Weather Data endpoint for a dummy city (London)
    city = "Haridwar"
    url = f"http://api.openweathermap.org/data/2.5/weather?q={city}&appid={key}"
    
    print("Sending test request to OpenWeather...")
    
    try:
        response = requests.get(url)
        
        # 200 means the request was successful and the key works
        if response.status_code == 200:
            print("\n✅ Success! Your API key is valid.")
            data = response.json()
            print(f"Current temperature in {city}: {data['main']['temp']} Kelvin")
            
        # 401 means the key is invalid or not activated
        elif response.status_code == 401:
            print("\n❌ Error 401: Unauthorized.")
            print("This means your key is invalid, OR you just generated it.")
            
        # Catch any other errors (like 404 Not Found, 429 Too Many Requests)
        else:
            print(f"\n⚠️ Unexpected Error {response.status_code}:")
            print(response.json())
            
    except requests.exceptions.RequestException as e:
        print(f"\n❌ Network error occurred: {e}")

# Run the test
test_openweather_key(api_key)