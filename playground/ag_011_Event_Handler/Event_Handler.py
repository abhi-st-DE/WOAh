import os
import json
import datetime
from dotenv import load_dotenv
from google_auth import get_calendar_service
from pydantic import BaseModel, Field
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

def add_calendar_event(start_date_time: datetime.datetime, name: str, end_date_time: datetime.datetime = None) -> str:

    service = get_calendar_service()

     # --- Guard against missing or empty data ---
    if not name or name.strip() == "":
        return "Error: You have to give both the name and the time of the event. Please ask me again with those details."
    
    if not start_date_time:
        return "Error: You have to give both the name and the time of the event. Please provide a start time."
    # ---------------------------------------------

    if end_date_time is None:
        end_date_time = start_date_time + datetime.timedelta(hours=1)

    settings = service.settings().get(setting='timezone').execute()
    user_tz = settings['value']

    start_str = start_date_time.isoformat()
    end_str = end_date_time.isoformat()

    # 2. Build the body
    event_body = {
        'summary': name,
        'start': {
            'dateTime': start_str,
            'timeZone': user_tz,
            },
        'end': {
            'dateTime': end_str,
            'timeZone': user_tz,
            },
    }

    # 3. Execute
    event = service.events().insert(calendarId='primary', body=event_body).execute()
    return f"Event created: {event.get('htmlLink')}"


class AddCalendarEvent(BaseModel):
    start_date_time: datetime.datetime = Field(
        ...,
        description="Provide the date and time in a valid ISO format (e.g., '2026-04-04T10:00:00'). Do NOT include a timezone unless the user explicitly mentions one."
    )
    name: str = Field(
        ...,
        description="Provide the name of the event... (e.g. 'Coffee Chat')"
    )
    end_date_time: datetime.datetime = Field(
        None,
        description="If the user provides not end date time just provide None in place of end_date_time in add_calendar_function."
    )

schema_event = {
    "type": "function",
    "function": {
        "name": "add_calendar_event",
        "description": "Create a new event on the user's Google Calendar with a specific name, start time, and end time.",
        "parameters": AddCalendarEvent.model_json_schema() 
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
                    raw_args = json.loads(tool_call.function.arguments)

                    tool_output_content = f"Error: Tool '{function_name}' not found."

                    # Execute the tool
                    if function_name in globals() and callable(globals()[function_name]):
                        function_to_call = globals()[function_name]
                        try:
                            validated_args = AddCalendarEvent(**raw_args).model_dump()
                            executed_output = function_to_call(**validated_args)
                        except Exception as e:
                            executed_output = f"Error validating arguments: {e}"
                        tool_output_content = str(executed_output) # Ensure output is a string.
                        print(f"Executing tool: {function_name} with args {raw_args}, Output: {tool_output_content[:500]}...") # Debug print

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


# 1. Get the real current time
now = datetime.datetime.now().strftime("%A, %B %d, %Y %I:%M %p")

# 2. Inject it into the system prompt
system = (
    f"You are a helpful assistant that updates events on Google Calendar. "
    f"IMPORTANT: Today is {now}. "
    "MANDATORY: You must never guess or hallucinate a date or a name. "
    "If the user provides a start time but NO end time, assume the meeting is 1 hour long and call the tool immediately. "
    "Otherwise, if both name and start time are missing, you MUST ASK the user to provide the missing information."
    "ONLY respond to the user's actual prompt. Do not suggest or imagine extra dates or tasks that were not provided by the user." 
)

tools = [schema_event]

agent = Agent(client, system, tools)


# To test your actual agent!
response = agent("Set a leave on 1 May from 10:00 AM to 2 May 10 Am with a subject of Buddha Purnima leave.")
print(f"Agent response: {response}")

mess = agent.messages

print(f"agent messages are:", mess)