# Quick test for your search_web function
import asyncio
import os
from main import search_web # Assuming your server file is named main.py

async def test_search():
    query = "site:python.langchain.com/docs Chroma DB"
    results = await search_web(query)
    print(f"Results: {results}")

if __name__ == "__main__":
    asyncio.run(test_search())
