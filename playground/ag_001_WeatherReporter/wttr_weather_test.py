import requests

city = "London"
# The 'format=j1' tells the server to send structured data instead of a text-art picture
url = f"https://wttr.in/{city}?format=j1"

response = requests.get(url)
data = response.json()

# Access the first item in the list of current conditions
current = data['current_condition'][0]
print(f"Keys inside current_condition: {list(current.keys())}")
#