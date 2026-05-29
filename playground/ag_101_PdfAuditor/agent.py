import os
import json
import logging
import asyncio
import tiktoken
from pathlib import Path
from dotenv import load_dotenv
from pydantic import BaseModel, Field, ValidationError
from openai import AsyncOpenAI
from chunkr_ai import Chunkr

# =====================================================================
# 1. Production Configuration & Logging
# =====================================================================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("DocumentAgent")

load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
CHUNKR_API_KEY = os.getenv("CHUNKR_API_KEY")
SAFE_DIR = Path(os.getenv("SAFE_DOC_DIR", "./documents")).resolve()

# Create safe directory if it doesn't exist
SAFE_DIR.mkdir(parents=True, exist_ok=True)

if not GROQ_API_KEY or not CHUNKR_API_KEY:
    raise ValueError("CRITICAL: Missing Groq or Chunkr API keys in environment.")

client = AsyncOpenAI(api_key=GROQ_API_KEY, base_url="https://api.groq.com/openai/v1")
MODEL = "llama-3.3-70b-versatile"
TOKENIZER = tiktoken.get_encoding("cl100k_base")

# Hard limits
MAX_ITERATIONS = 5
MAX_FILE_SIZE_BYTES = 20 * 1024 * 1024  # 20 MB
MAX_CONTEXT_TOKENS = 6000
ALLOWED_EXTENSIONS = {'.pdf', '.docx', '.xlsx', '.png', '.jpg', '.jpeg'}

# =====================================================================
# 2. Hardened Tool Implementation
# =====================================================================
def _sync_chunkr_upload(file_path: str) -> str:
    """Synchronous core for Chunkr SDK to be run in a thread pool."""
    chunkr_client = Chunkr()
    task = chunkr_client.upload(file_path)
    
    extracted_text = ""
    total_characters = 0
    
    # Metadata preservation & Basic OCR validation check
    for chunk in task.output.chunks:
        # Assuming chunk object contains a page or id attribute; fallback to sequential if not
        chunk_id = getattr(chunk, 'page_number', getattr(chunk, 'id', 'Unknown'))
        extracted_text += f"\n--- [Source Element: {chunk_id}] ---\n"
        
        for segment in chunk.segments:
            extracted_text += f"{segment.content}\n"
            total_characters += len(segment.content)
            
    if total_characters < 50 and Path(file_path).stat().st_size > 100000:
        logger.warning(f"Low OCR yield for {file_path}. Document may be image-heavy or require different parsing.")
        extracted_text += "\n[SYSTEM WARNING: Low text yield detected. Content may be incomplete.]\n"
        
    return extracted_text

async def process_pdf_document(file_path: str) -> str:
    """Validates, sandboxes, and processes a document asynchronously with retries."""
    target_path = Path(file_path).resolve()

    # 1. Sandboxing & Existence Validation
    if not target_path.is_relative_to(SAFE_DIR):
        logger.error(f"Security violation attempted: {target_path}")
        return "Error: Access denied. File path must be within the designated secure directory."
    
    if not target_path.exists() or not target_path.is_file():
        return f"Error: File '{target_path.name}' does not exist."

    # 2. File Type & Size Validation
    if target_path.suffix.lower() not in ALLOWED_EXTENSIONS:
        return f"Error: Unsupported file type. Allowed: {ALLOWED_EXTENSIONS}"
    
    file_size = target_path.stat().st_size
    if file_size > MAX_FILE_SIZE_BYTES:
        return f"Error: File exceeds maximum allowed size of {MAX_FILE_SIZE_BYTES / (1024*1024):.1f}MB."

    logger.info(f"Processing '{target_path.name}' ({file_size / 1024:.1f} KB)")

    # 3. Retry Handling & Async Execution (Prevent event-loop blocking)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Run the synchronous Chunkr SDK in a thread to unblock asyncio
            extracted_text = await asyncio.to_thread(_sync_chunkr_upload, str(target_path))
            
            # 4. Token-Aware Truncation
            tokens = TOKENIZER.encode(extracted_text)
            if len(tokens) > MAX_CONTEXT_TOKENS:
                logger.warning(f"Document exceeds context limits ({len(tokens)} tokens). Truncating.")
                truncated_tokens = tokens[:MAX_CONTEXT_TOKENS]
                extracted_text = TOKENIZER.decode(truncated_tokens)
                extracted_text += "\n\n[SYSTEM WARNING: Document truncated at token limit.]"

            return extracted_text
            
        except Exception as e:
            logger.warning(f"Chunkr processing attempt {attempt + 1} failed: {e}")
            if attempt == max_retries - 1:
                logger.error(f"Chunkr processing failed definitively after {max_retries} attempts.")
                return f"Error: Remote processing failed. {str(e)}"
            await asyncio.sleep(2 ** attempt)  # Exponential backoff

# =====================================================================
# 3. Schemas & Tool Registry
# =====================================================================
class ProcessPdfArgs(BaseModel):
    file_path: str = Field(..., description=f"Filename relative to {SAFE_DIR}. Do not use absolute paths.")

schema_chunkr = {
    "type": "function",
    "function": {
        "name": "process_pdf_document",
        "description": "Reads a validated document and returns exact layout/text with metadata.",
        "parameters": ProcessPdfArgs.model_json_schema()
    }
}

TOOL_SCHEMA_MAP = {"process_pdf_document": ProcessPdfArgs}
AVAILABLE_TOOLS = {"process_pdf_document": process_pdf_document}

# =====================================================================
# 4. Asynchronous Agent 
# =====================================================================
class AsyncAgent:
    def __init__(self, client: AsyncOpenAI, system: str = "", tools: list = None) -> None:
        self.client = client
        self.system = system
        self.messages = [{"role": "system", "content": system}] if system else []
        self.tools = tools or []

    def _prune_context(self):
        """Prevents context explosion by keeping system prompt and recent messages."""
        # Simple rolling window: Keep System prompt (0), and last 10 messages
        if len(self.messages) > 12:
            logger.info("Context window growing large. Pruning older messages.")
            self.messages = [self.messages[0]] + self.messages[-10:]

    async def execute(self, prompt: str):
        self.messages.append({"role": "user", "content": prompt})
        
        # 1. Capped Loop for Infinite Recursion Protection
        for iteration in range(MAX_ITERATIONS):
            self._prune_context()
            
            try:
                # 2. Temperature set for consistent reasoning
                completion = await self.client.chat.completions.create(
                    model=MODEL,
                    messages=self.messages,
                    tools=self.tools,
                    tool_choice="auto",
                    temperature=0.2 
                )
                response_message = completion.choices[0].message
            except Exception as e:
                logger.error(f"API Completion failed: {e}")
                yield f"\n[System Error: Failed to contact LLM API: {e}]"
                return

            if response_message.tool_calls:
                self.messages.append(response_message.model_dump(exclude_unset=True))
                
                tool_outputs = []
                for tool_call in response_message.tool_calls:
                    func_name = tool_call.function.name
                    logger.info(f"LLM requested tool execution: {func_name}")
                    
                    if func_name not in AVAILABLE_TOOLS:
                        tool_outputs.append({
                            "tool_call_id": tool_call.id,
                            "role": "tool",
                            "content": f"Error: '{func_name}' is not an authorized tool.",
                        })
                        continue

                    # 3. Typed Exception Handling
                    try:
                        raw_args = json.loads(tool_call.function.arguments)
                        
                        # Remap to safe dir to force sandboxing
                        if 'file_path' in raw_args:
                            raw_args['file_path'] = str(SAFE_DIR / Path(raw_args['file_path']).name)

                        validated_args = TOOL_SCHEMA_MAP[func_name](**raw_args).model_dump()
                        
                        # Yield status to user before long-running async task
                        yield f"\n> ⏳ Executing `{func_name}` for {Path(validated_args['file_path']).name}...\n"
                        
                        executed_output = await AVAILABLE_TOOLS[func_name](**validated_args)
                        
                    except json.JSONDecodeError as e:
                        executed_output = f"Error: Invalid JSON payload from model - {e}"
                        logger.error(executed_output)
                    except ValidationError as e:
                        executed_output = f"Error: Schema validation failed - {e}"
                        logger.error(executed_output)
                    except Exception as e:
                        executed_output = f"Error: Unexpected tool failure - {e}"
                        logger.exception("Tool execution exception")

                    tool_outputs.append({
                        "tool_call_id": tool_call.id,
                        "role": "tool",
                        "content": str(executed_output),
                    })
                    
                self.messages.extend(tool_outputs)
            else:
                # 4. Streaming final output
                self.messages.append({"role": "assistant", "content": response_message.content})
                
                yield "\nFinal Response:\n"
                yield response_message.content
                return
                
        yield "\n[System Warning: Maximum iterations reached. Task terminated to prevent infinite loop.]"

# =====================================================================
# 5. Initialization
# =====================================================================
async def main():
    system_prompt = (
        "You are an elite Document Auditor. "
        "Structure findings in JSON or strictly formatted Markdown lists. "
        "Reference [Source Element: X] when citing facts."
    )
    
    agent = AsyncAgent(client, system_prompt, [schema_chunkr])
    query = "Please read 'REGNFORM1.pdf' and tell me my Application Number, Name, Date of Birth and Address."
    
    print(f"\n[System] Asking Agent: '{query}'")
    
    # Iterate over the async generator to receive real-time updates and streaming text
    async for partial_response in agent.execute(query):
        print(partial_response, end="", flush=True)
    print("\n")

if __name__ == "__main__":
    asyncio.run(main())