from mcp.server.fastmcp import FastMCP
from dotenv import load_dotenv
from bs4 import BeautifulSoup
import httpx
import json
import asyncio
import os

load_dotenv()

mcp = FastMCP("docs")

USER_AGENT = "docs-app/1.0"
SERPER_URL="https://google.serper.dev/search"

docs_url = {
    "langchain": "docs.langchain.com",
    "lang-graph": "docs.langchain.com/oss/python/langgraph/",
    "llama-index": "docs.llamaindex.ai/en/stable",
    "openai": "platform.openai.com/docs",
    "python": "docs.python.org",
    "javascript": "developer.mozilla.org/en-US/docs/Web/JavaScript",
    "typescript": "typescriptlang.org/docs",
    "rust": "doc.rust-lang.org",
    "go": "go.dev/doc",
    "java": "docs.oracle.com/en/java",
    "cpp": "cppreference.com",
    "csharp": "learn.microsoft.com/en-us/dotnet/csharp",
    "ruby": "ruby-doc.org",
    "php": "php.net/manual",
    "swift": "developer.apple.com/documentation/swift",
    "kotlin": "kotlinlang.org/docs",
    "dart": "dart.dev/guides",
    "scala": "docs.scala-lang.org",
    "elixir": "hexdocs.pm/elixir",
    "react": "react.dev",
    "vue": "vuejs.org/guide/introduction.html",
    "angular": "angular.dev",
    "svelte": "svelte.dev/docs",
    "nextjs": "nextjs.org/docs",
    "nuxtjs": "nuxt.com/docs",
    "tailwindcss": "tailwindcss.com/docs",
    "bootstrap": "getbootstrap.com/docs",
    "material-ui": "mui.com/material-ui/getting-started",
    "redux": "redux.js.org",
    "html": "developer.mozilla.org/en-US/docs/Web/HTML",
    "css": "developer.mozilla.org/en-US/docs/Web/CSS",
    "webpack": "webpack.js.org/concepts",
    "vite": "vitejs.dev/guide",
    "django": "docs.djangoproject.com",
    "flask": "flask.palletsprojects.com",
    "fastapi": "fastapi.tiangolo.com",
    "expressjs": "expressjs.com",
    "nestjs": "docs.nestjs.com",
    "springboot": "spring.io/projects/spring-boot",
    "rubyonrails": "guides.rubyonrails.org",
    "laravel": "laravel.com/docs",
    "aspnet": "learn.microsoft.com/en-us/aspnet/core",
    "phoenix": "hexdocs.pm/phoenix",
    "pytorch": "pytorch.org/docs/stable",
    "tensorflow": "tensorflow.org/api_docs",
    "keras": "keras.io",
    "scikit-learn": "scikit-learn.org/stable/user_guide.html",
    "pandas": "pandas.pydata.org/docs",
    "numpy": "numpy.org/doc",
    "huggingface": "huggingface.co/docs",
    "anthropic": "docs.anthropic.com",
    "jupyter": "docs.jupyter.org",
    "matplotlib": "matplotlib.org/stable/contents.html",
    "seaborn": "seaborn.pydata.org",
    "scipy": "docs.scipy.org/doc/scipy",
    "opencv": "docs.opencv.org",
    "postgresql": "postgresql.org/docs",
    "mysql": "dev.mysql.com/doc",
    "mongodb": "mongodb.com/docs",
    "redis": "redis.io/docs",
    "sqlite": "sqlite.org/docs.html",
    "elasticsearch": "elastic.co/guide/en/elasticsearch/reference/current",
    "cassandra": "cassandra.apache.org/doc/latest",
    "neo4j": "neo4j.com/docs",
    "firebase": "firebase.google.com/docs",
    "supabase": "supabase.com/docs",
    "docker": "docs.docker.com",
    "kubernetes": "kubernetes.io/docs",
    "terraform": "developer.hashicorp.com/terraform/docs",
    "aws": "docs.aws.amazon.com",
    "gcp": "cloud.google.com/docs",
    "azure": "learn.microsoft.com/en-us/azure",
    "github-actions": "docs.github.com/en/actions",
    "gitlab-ci": "docs.gitlab.com/ee/ci",
    "jenkins": "jenkins.io/doc",
    "ansible": "docs.ansible.com",
    "prometheus": "prometheus.io/docs/introduction/overview",
    "grafana": "grafana.com/docs",
    "nginx": "nginx.org/en/docs",
    "apache-http": "httpd.apache.org/docs",
    "linux-archwiki": "wiki.archlinux.org",
    "react-native": "reactnative.dev/docs/getting-started",
    "flutter": "docs.flutter.dev",
    "ios-developer": "developer.apple.com/documentation",
    "android-developer": "developer.android.com/docs",
    "expo": "docs.expo.dev",
    "git": "git-scm.com/doc",
    "graphql": "graphql.org/learn",
    "apollo-graphql": "apollographql.com/docs",
    "prisma": "prisma.io/docs",
    "socketio": "socket.io/docs",
    "rabbitmq": "rabbitmq.com/documentation.html",
    "kafka": "kafka.apache.org/documentation",
    "stripe": "docs.stripe.com",
    "twilio": "twilio.com/docs",
    "sendgrid": "docs.sendgrid.com",
    "auth0": "auth0.com/docs",
    "cypress": "docs.cypress.io",
    "playwright": "playwright.dev/docs/intro",
    "jest": "jestjs.io/docs/getting-started",
    "selenium": "selenium.dev/documentation",
    "linux-man-pages": "man7.org/linux/man-pages",
    # AI, LLMs, and Agent Frameworks
    "vllm": "docs.vllm.ai",
    "crewai": "docs.crewai.com",
    "autogen": "microsoft.github.io/autogen",
    "ollama": "github.com/ollama/ollama/tree/main/docs",
    "transformers": "huggingface.co/docs/transformers",
    
    # MLOps, Experiment Tracking, and ML UIs
    "mlflow": "mlflow.org/docs/latest",
    "wandb": "docs.wandb.ai",
    "ray": "docs.ray.io",
    "streamlit": "docs.streamlit.io",
    "gradio": "gradio.app/docs",
    "xgboost": "xgboost.readthedocs.io",

    # Vector Databases (Crucial for RAG/AI apps)
    "chroma": "docs.trychroma.com",
    "pinecone": "docs.pinecone.io",
    "milvus": "milvus.io/docs",
    "weaviate": "weaviate.io/developers/weaviate",
    "qdrant": "qdrant.tech/documentation",

    # Data Engineering, Big Data, and Fast Compute
    "spark": "spark.apache.org/docs/latest",
    "airflow": "airflow.apache.org/docs",
    "dbt": "docs.getdbt.com",
    "polars": "docs.pola.rs",
    "duckdb": "duckdb.org/docs",
    "databricks": "docs.databricks.com",
    "snowflake": "docs.snowflake.com",
    "superset": "superset.apache.org/docs/intro",

    # Modern Runtimes & Highly Popular Tools
    "bun": "bun.sh/docs",
    "deno": "docs.deno.com",
    "tauri": "v2.tauri.app",
    "godot": "docs.godotengine.org",

    # More AI, ML, & LLM Essentials
    "gemini": "ai.google.dev/gemini-api/docs",
    "cohere": "docs.cohere.com",
    "diffusers": "huggingface.co/docs/diffusers",
    "jax": "jax.readthedocs.io",
    "llama-cpp": "github.com/ggerganov/llama.cpp",

    # Core Data Engineering & Orchestration
    "prefect": "docs.prefect.io",
    "dagster": "docs.dagster.io",
    "dlt": "dlthub.com/docs",
    "flink": "nightlies.apache.org/flink/flink-docs-stable",
    "iceberg": "iceberg.apache.org/docs/latest",

    # Modern Web, UI & Frameworks
    "astro": "docs.astro.build",
    "remix": "remix.run/docs",
    "solidjs": "docs.solidjs.com",
    "storybook": "storybook.js.org/docs",

    # Modern Infrastructure, Cloud & Databases
    "cloudflare": "developers.cloudflare.com",
    "vercel": "vercel.com/docs",
    "pulumi": "pulumi.com/docs",
    "drizzle": "orm.drizzle.team/docs",
    "timescaledb": "docs.timescale.com"
}

async def search_web(query: str) -> dict | None:
    payload = json.dumps({"q": query, "num": 4})

    headers = {
        "X-API-KEY": os.getenv("SERPER_API_KEY"),
        "Content-Type": "application/json",        
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                SERPER_URL, headers=headers, data=payload, timeout=30.0
            )
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            return {"organic": []}



async def fetch_url(url: str):
    headers = {"User-Agent": USER_AGENT}
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(url,headers=headers, timeout=45.0)
            soup = BeautifulSoup(response.text, "html.parser")
            # Target ONLY the main content to avoid scraping sidebars/footers
            main_content = soup.find('main') or soup.find('article') or soup
            text = main_content.get_text(separator='\n', strip=True)
            return text[:9000]
        except Exception as e:
            return f"error fetching {url} is: {e}."

@mcp.tool()
async def get_docs(query: str, library: str):
    """
        Search the docs for a given query or library.
        If the library is known, it searches the specific site.
        Otherwise, it dynamically searches the web for the official docs.

        Args:
        query: The query to search for (e.g. "Chroma DB" etc)
        library: The library to search in (e.g. "langchain", "react", "fastapi, and many other.")

        Returns:
        Text from the docs
    """
    
    # 1. Check if we know the exact URL (The Fast/Accurate Path)
    if library in docs_url:
        search_query = f"site:{docs_url[library]} {query}"
        results = await search_web(search_query)
        
    # 2. If we don't know it, dynamically search for it! (The Flexible Path)
    else:
        # We drop the 'site:' operator and just ask for the official docs
        search_query = f"{library} official documentation {query}"
        results = await search_web(search_query)

    # 3. Fallback if the strict 'site:' search failed on a known library
    if library in docs_url and (not results or "organic" not in results or len(results["organic"]) == 0):
        fallback_query = f"{library} official documentation {query}"
        results = await search_web(fallback_query)

    # 4. If everything fails, gracefully exit
    if not results or "organic" not in results or len(results["organic"]) == 0:
        return f"No results found for '{query}' in {library} docs."

    # 5. Scrape the results (using the concurrent asyncio.gather method from before)
    urls = [result["link"] for result in results["organic"]]
    html_results = await asyncio.gather(*(fetch_url(url) for url in urls))
    
    final_text = "\n\n--- NEXT RESULT ---\n\n".join([res for res in html_results if res])
    return final_text if final_text else "Failed to extract text from the URLs."

if __name__ == "__main__":
    mcp.run(transport='stdio')