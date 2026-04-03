import os
import json
import requests
from pydantic import BaseModel, Field
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# inference from hugging face validation.
load_dotenv()
HF_TOKEN = os.getenv("HF_TOKEN") 
if not HF_TOKEN:
    raise ValueError("HF_TOKEN is not accessible from environment variables.")
client = InferenceClient(
    api_key=HF_TOKEN,
    model="moonshotai/Kimi-K2-Thinking"
)

def get_local_city() -> str:
    """Helper function to find the user's city via IP address if they don't provide one."""
    try:
        # Pings the IP API and asks for just the city name in text format
        response = requests.get("https://ipapi.co/city/", timeout=5)
        return response.text.strip()
    except:
        # If the IP locator fails, default to a major hub so the script doesn't crash
        return "Delhi"

def fetch_weather_wttr(city: str = "") -> dict:
    # 1. Handle the blank city problem FIRST
    if not city:
        city = get_local_city()
        print(f"[System] No city provided. Auto-detected location: {city}")

    # 2. Try the primary service (wttr.in) with a strict 3-second timeout
    try:
        print(f"[System] Attempting to fetch from the wttr.in for {city}...")
        # Wttr
        url = f"https://wttr.in/{city}?format=j1"

        response = requests.get(url, timeout=3)
        response.raise_for_status()

        data = response.json()
        current = data['current_condition'][0]

        return {
            "temp_C": current['temp_C'],
            "FeelsLikeC": current['FeelsLikeC'],
            "windspeedKmph": current['windspeedKmph'],
            "humidity": current['humidity'],
            "cloudcover": current['cloudcover'],
            "localObsDateTime": current['localObsDateTime']
        }
    
    # 3. If wttr.in times out or crashes, automatically fall back to OpenWeather
    except requests.exceptions.RequestException as e:
        print(f"[System] wttr.in failed! Falling back to OpenWeather... (Error: {e})")

        #OPENWEATHERAPI
        OpenWeatherApi = os.getenv("OpenWeather_API_KEY")
        if not OpenWeatherApi:
            return {"error": "OpenWeatherApi not found in env variables."}
        ow_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={OpenWeatherApi}&units=metric"

        try:
            ow_response = requests.get(ow_url, timeout=5)
            ow_data = ow_response.json()
            return {
                "source": "OpenWeather API",
                "city": city,
                "temp_C": ow_data['main']['temp'],
                "humidity": ow_data['main']['humidity']
            }
        except Exception as critical_error:
            # 4. If BOTH fail, return a clean error string for the LLM to read
            return {"error": "Both weather services are currently offline."}


class FetchWeatherWttrArgs(BaseModel):
    city: str = Field(
        default="",
        description="The city to get the temperature for, ONLY insert the name of the city here, if user DON'T provide city just DON'T pass anything inside."
    )

schema = {
    "type": "function",
    "function": {
        "name": "fetch_weather_wttr",
        "description": "Get the current weather and the temperature conditions.",
        "parameters": FetchWeatherWttrArgs.model_json_schema()
    }
}


class Agent:
    def __init__(self, client: InferenceClient, system: str = "", tools: list = None) -> None:
        self.client = client
        self.system = system
        self.messages: list = []
        self.tools = tools if tools is not None else []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})

        final_assistant_content = self.execute()

        if final_assistant_content:
            self.messages.append({"role": "assistant", "content": final_assistant_content})

        return final_assistant_content
    def execute(self):
        while True:
            completion = self.client.chat.completions.create(
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto" # Let the model decide when to call tools.
            )

            response_message = completion.choices[0].message

            if response_message.tool_calls:
                self.messages.append(response_message)
            # tools responses comes only after tool call, 
            # and if your agent don't has in his history it tool calls, it won't be able to respond.

                tool_outputs =[]
                for tool_call in response_message.tool_calls:
                    function_name = tool_call.function.name
                    function_args = json.loads(tool_call.function.arguments)

                    tool_output_content = f"Error: Tool '{function_name}' not found."

                    # Execute the tool
                    if function_name in globals() and callable(globals()[function_name]):
                        function_to_call = globals()[function_name]
                        executed_output = function_to_call(**function_args)
                        tool_output_content = str(executed_output) # Ensure output is a string.
                        print(f"Executing tool: {function_name} with args {function_args}, Output: {tool_output_content[:500]}...") # Debug print

                    tool_outputs.append(
                        {
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "name": function_name,
                            "content": tool_output_content,
                        }
                    )
                self.messages.extend(tool_outputs)
            else:
                return response_message.content

# Initialisation
system =  (
    " You are a helpful assistant that is capable of retrieving information about the weather of a city accurately "
    " You never try to change the factual information, of the weather, and stick to the information provided. "
    " If the city is not provided you don't provide any city to the tool and fetch whatever the tools provide. "
    " After fetching the information correctly you can beautifully curate the response to tell the user the weather. "
    " If user by mistake provides any country name in place of city name, you from your knowledge finds the weather ONLY for the capital of the country and not any other city. "
)

tools = [schema]

agent = Agent(client, system, tools)

response = agent("What is the weather in patliputra like now?")

print(f"final answer: {response}")

mess = agent.messages

print(f"agent messages are:", mess)