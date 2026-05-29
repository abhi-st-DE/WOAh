import os
import json
import requests
from dotenv import load_dotenv
from pydantic import BaseModel, Field
from groq import Groq

# =====================================================================
# 1. Environment & Client Setup
# =====================================================================
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
FIRECRAWL_API_KEY = os.getenv("FIRECRAWL_API_KEY")

if not GROQ_API_KEY or not FIRECRAWL_API_KEY:
    raise ValueError("Missing Groq or Firecrawl API keys in your .env file")

# Groq uses the standard OpenAI-compatible client structure natively
client = Groq(api_key=GROQ_API_KEY)
MODEL = "llama-3.3-70b-versatile"  # Excellent model for tool calling

# =====================================================================
# 2. Tool Implementation
# =====================================================================
def search_and_scrape_web(query: str, limit: int = 2) -> str:
    """Searches the web via Firecrawl and scrapes the top results directly into Markdown."""
    print(f"\n[System] 🔍 Initiating Firecrawl search for: '{query}'...")
    url = "https://api.firecrawl.dev/v1/search"
    headers = {
        "Authorization": f"Bearer {FIRECRAWL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "query": query,
        "limit": limit,
        "scrapeOptions": {"formats": ["markdown"]}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        
        if not data.get("success") or not data.get("data"):
            return "No readable web results found."
            
        compiled_markdown = ""
        for result in data["data"]:
            title = result.get("title", "Unknown Title")
            source_url = result.get("url", "Unknown URL")
            markdown_content = result.get("markdown", "")
            
            # Expanded truncation safely leveraging llama-3.3's massive 128k context window
            if len(markdown_content) > 8000:
                markdown_content = markdown_content[:8000] + "\n...[Content Truncated for Context Length]..."
                
            compiled_markdown += f"\n\n### Source: {title}\nURL: {source_url}\n{'-'*40}\n{markdown_content}\n"
            
        return compiled_markdown
    except Exception as e:
        return f"Error executing Firecrawl search: {str(e)}"

# =====================================================================
# 3. Pydantic Schema & Tool Mapping
# =====================================================================
class FirecrawlSearchArgs(BaseModel):
    query: str = Field(
        ..., 
        description="The highly specific search query to look up on the web."
    )
    # 1. Replaced `default=2` with `...` to force it into the "required" JSON array
    # 2. Added a strict typing instruction to the description
    limit: int = Field(
        ..., 
        description="Number of results to scrape. Max 3. MUST be an integer number (e.g. 2), NOT a string."
    )

schema_firecrawl = {
    "type": "function",
    "function": {
        "name": "search_and_scrape_web",
        "description": "Searches the internet and scrapes the full markdown content of the top pages. Use this for up-to-date research.",
        "parameters": FirecrawlSearchArgs.model_json_schema()
    }
}

TOOL_SCHEMA_MAP = {
    "search_and_scrape_web": FirecrawlSearchArgs
}

# =====================================================================
# 4. Agent Class with Safe JSON / Tool Handling
# =====================================================================
class Agent:
    def __init__(self, client: Groq, system: str = "", tools: list = None) -> None:
        self.client = client
        self.system = system
        self.messages = []
        self.tools = tools if tools else []
        if self.system:
            self.messages.append({"role": "system", "content": system})

    def __call__(self, message=""):
        if message:
            self.messages.append({"role": "user", "content": message})
        return self.execute()

    def execute(self):
        while True:
            completion = self.client.chat.completions.create(
                model=MODEL,
                messages=self.messages,
                tools=self.tools,
                tool_choice="auto"
            )
            response_message = completion.choices[0].message

            if response_message.tool_calls:
                # Append the assistant's tool call request to history
                self.messages.append(response_message.model_dump(exclude_unset=True))
                
                tool_outputs = []
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    tool_output_content = f"Error: Tool '{func_name}' not found."

                    if func_name in globals() and callable(globals()[func_name]):
                        func_to_call = globals()[func_name]
                        try:
                            # Safely parse JSON args inside the try-catch block
                            raw_args = json.loads(tool_call.function.arguments)
                            
                            # Validate arguments using the Pydantic schema mapping
                            if func_name in TOOL_SCHEMA_MAP:
                                validated_args = TOOL_SCHEMA_MAP[func_name](**raw_args).model_dump()
                            else:
                                validated_args = raw_args
                                
                            executed_output = func_to_call(**validated_args)
                        except Exception as e:
                            executed_output = f"Error validating/executing arguments: {e}"
                            
                        tool_output_content = str(executed_output)
                        print(f"✅ Executed: {func_name} | Response length: {len(tool_output_content)}")

                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": tool_output_content,
                    })
                self.messages.extend(tool_outputs)
            else:
                self.messages.append({"role": "assistant", "content": response_message.content})
                return response_message.content

# =====================================================================
# 5. Initialization & Execution
# =====================================================================
if __name__ == "__main__":
    system_prompt = (
        "You are an elite Deep Web Researcher. When asked about a topic, you use your web scraping tool "
        "to pull live data. Analyze the sources carefully, ALWAYS cite the URLs using Markdown links, "
        "and synthesize a comprehensive, highly accurate report."
    )

    agent = Agent(client, system_prompt, [schema_firecrawl])
    
    query = "What are the latest developments in solid-state batteries from the last 30 days?"
    response = agent(query)
    
    print(f"\nFinal Answer:\n{response}")