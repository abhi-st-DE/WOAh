import http.server
import socketserver
import json
import os
import re
import subprocess
import sys

PORT = 8000
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

AGENT_FILES = {
    "ag_001_WeatherReporter": "agent.py",
    "ag_010_MailMan": "MailMan.py",
    "ag_011_Event_Handler": "Event_Handler.py",
    "ag_100_DeepResearcher": "agent.py",
    "ag_101_PdfAuditor": "agent.py"
}

class AgentHandler(http.server.SimpleHTTPRequestHandler):
    
    def do_GET(self):
        # Serve index.html on root
        if self.path == '/':
            self.path = '/index.html'
        return super().do_GET()

    def do_POST(self):
        if self.path == '/run_agent':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            try:
                data = json.loads(post_data.decode('utf-8'))
                agent_id = data.get('agent_id')
                prompt = data.get('prompt', '').strip()
                
                if not agent_id or agent_id not in AGENT_FILES:
                    self.send_error_response("Invalid agent selection.")
                    return
                
                thinking, result = self.execute_agent(agent_id, prompt)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({
                    "thinking": thinking,
                    "result": result
                }).encode('utf-8'))
                
            except Exception as e:
                self.send_error_response(str(e))
                
        elif self.path == '/run_mcp':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            try:
                data = json.loads(post_data.decode('utf-8'))
                library = data.get('library', '').strip()
                query = data.get('query', '').strip()
                
                if not library or not query:
                    self.send_error_response("Missing library or query.")
                    return
                
                result = self.execute_mcp(library, query)
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"result": result}).encode('utf-8'))
                
            except Exception as e:
                self.send_error_response(str(e))
        else:
            self.send_error(404, "Endpoint not found.")

    def send_error_response(self, error_msg):
        self.send_response(400)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps({"error": error_msg}).encode('utf-8'))

    def execute_agent(self, agent_id, prompt):
        agent_dir = os.path.join(BASE_DIR, agent_id)
        original_file = os.path.join(agent_dir, AGENT_FILES[agent_id])
        temp_file = os.path.join(agent_dir, ".temp_run_agent.py")
        
        try:
            with open(original_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Escape prompt safely for triple quotes
            safe_prompt = prompt.replace('"""', '\\"\\"\\"')

            # Replace hardcoded invocation based on agent type
            if agent_id in ["ag_001_WeatherReporter", "ag_010_MailMan", "ag_011_Event_Handler"]:
                content = re.sub(r'response\s*=\s*agent\(.*?\)', f'response = agent("""{safe_prompt}""")', content, flags=re.DOTALL)
            else:
                content = re.sub(r'query\s*=\s*".*?"', f'query = """{safe_prompt}"""', content, flags=re.DOTALL)
                
            # For DeepResearcher / PdfAuditor, they are wrapped in asyncio.run or __name__ == "__main__"
            # It will still execute normally since we only replaced the `query` assignment.

            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Setup resilient offline PYTHONPATH fallback chaining
            site_packages = [
                os.path.join(agent_dir, ".venv/lib/python3.13/site-packages"),
                os.path.join(BASE_DIR, "ag_101_PdfAuditor/.venv/lib/python3.13/site-packages"),
                os.path.join(BASE_DIR, "mcp/webcrawl/learn_crawl/.venv/lib/python3.13/site-packages"),
                os.path.join(BASE_DIR, "ag_100_DeepResearcher/.venv/lib/python3.13/site-packages")
            ]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = ":".join(site_packages)
            
            # Subprocess execution
            process = subprocess.Popen(
                [sys.executable, ".temp_run_agent.py"],
                cwd=agent_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True
            )
            
            stdout, _ = process.communicate()
            
            # Split thinking and final result using known delimiters
            match = re.search(r'(final answer:|agent response:|final answer:?\n|final response:?\n)', stdout, re.IGNORECASE)
            if match:
                thinking = stdout[:match.start()].strip()
                result = stdout[match.end():].strip()
            else:
                thinking = stdout.strip()
                result = "[Agent did not produce a final result format. Check logs.]"
            
            return thinking, result

        except Exception as e:
            return f"Execution Wrapper Error: {str(e)}", ""
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

    def execute_mcp(self, library, query):
        mcp_dir = os.path.join(BASE_DIR, "mcp/documentation")
        temp_file = os.path.join(mcp_dir, ".temp_run_mcp.py")
        
        safe_library = library.replace('"""', '\\"\\"\\"')
        safe_query = query.replace('"""', '\\"\\"\\"')
        
        script_content = f"""
import asyncio
import sys
import io

# Force stdout to be utf-8 to avoid UnicodeEncodeError in pipes
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

from main import get_docs

async def run():
    try:
        result = await get_docs(query='''{safe_query}''', library='''{safe_library}''')
        print(result)
    except Exception as e:
        print(f"Error fetching docs: {{e}}")

if __name__ == "__main__":
    asyncio.run(run())
"""
        try:
            with open(temp_file, 'w', encoding='utf-8') as f:
                f.write(script_content)
                
            site_packages = [
                os.path.join(mcp_dir, ".venv/lib/python3.13/site-packages"),
                os.path.join(BASE_DIR, "ag_101_PdfAuditor/.venv/lib/python3.13/site-packages"),
                os.path.join(BASE_DIR, "mcp/webcrawl/learn_crawl/.venv/lib/python3.13/site-packages")
            ]
            
            env = os.environ.copy()
            env["PYTHONPATH"] = ":".join(site_packages)
            # Ensure python uses utf8 for stdout
            env["PYTHONIOENCODING"] = "utf-8"
            
            process = subprocess.Popen(
                [sys.executable, ".temp_run_mcp.py"],
                cwd=mcp_dir,
                env=env,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8'
            )
            
            stdout, _ = process.communicate()
            return stdout.strip()
            
        except Exception as e:
            return f"MCP Execution Error: {str(e)}"
        finally:
            if os.path.exists(temp_file):
                os.remove(temp_file)

if __name__ == "__main__":
    Handler = AgentHandler
    with socketserver.TCPServer(("", PORT), Handler) as httpd:
        print(f"🚀 Unified Agent Server running at http://localhost:{PORT}")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")
