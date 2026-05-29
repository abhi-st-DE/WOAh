import os
import json
import asyncio
import urllib.request
import xml.etree.ElementTree as ET

from bs4 import BeautifulSoup

# Make sure you have the correct imports from your crawl4ai version
from crawl4ai import AsyncWebCrawler, CrawlerRunConfig, CacheMode
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator
from crawl4ai.content_filter_strategy import PruningContentFilter

# Set your folder paths clearly
BASE_DIR = "/home/abhi/WOAh/playground/mcp/webcrawl/database"
os.makedirs(BASE_DIR, exist_ok=True)  # Ensure the folder exists!

KNOWLEDGE_BASE_FILE = os.path.join(BASE_DIR, "langchain_mcp_data.json")
STATE_FILE = os.path.join(BASE_DIR, "langchain_sync_state.json")


def get_sitemap_data(sitemap_url):
    """Fetches the sitemap and returns a dictionary of {url: last_modified_date}"""
    print(f"Fetching sitemap from {sitemap_url}...")
    req = urllib.request.Request(sitemap_url, headers={"User-Agent": "Mozilla/5.0"})

    try:
        with urllib.request.urlopen(req, timeout=10) as response:
            xml_data = response.read()
    except Exception as e:
        print(f"CRITICAL ERROR: Failed to fetch sitemap. {e}")
        return {}
    root = ET.fromstring(xml_data)
    sitemap_data = {}

    # Loop through all <url> blocks in the XML
    for url_tag in root.iter():
        if "url" in url_tag.tag:
            loc = None
            lastmod = None
            # Look inside the <url> block for loc and lastmod
            for child in url_tag:
                if "loc" in child.tag:
                    loc = child.text.strip()
                if "lastmod" in child.tag:
                    lastmod = child.text.strip()

            if loc and lastmod:
                sitemap_data[loc] = lastmod

    print(f"Found {len(sitemap_data)} URLs in the sitemap.")
    return sitemap_data


def get_urls_to_crawl(sitemap_data):
    """Compares the sitemap against our saved state file to find new/updated pages."""
    # Load previous state (if it exists)
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r", encoding="utf-8") as f:
            saved_state = json.load(f)
    else:
        saved_state = {}

    urls_to_crawl = []

    for url, lastmod in sitemap_data.items():
        # If the URL is brand new, OR the sitemap date is newer than our saved date
        if url not in saved_state or sitemap_data[url] > saved_state[url]:
            urls_to_crawl.append(url)

    return urls_to_crawl, saved_state


async def main():
    sitemap_url = "https://docs.langchain.com/sitemap.xml"

    # 1. Get raw sitemap data
    sitemap_data = get_sitemap_data(sitemap_url)

    # SAFETY CHECK: If sitemap download failed, abort completely so we don't delete our DB!
    if not sitemap_data:
        print("Sitemap is empty or failed to download. Aborting sync.")
        return

    # 2. Figure out what actually needs crawling
    urls_to_crawl, saved_state = get_urls_to_crawl(sitemap_data)

    # 3. Load existing knowledge base so we don't overwrite it
    if os.path.exists(KNOWLEDGE_BASE_FILE):
        with open(KNOWLEDGE_BASE_FILE, "r", encoding="utf-8") as f:
            mcp_knowledge_base = json.load(f)
    else:
        mcp_knowledge_base = {}

    # 4. GHOST DELETION
    # We do this BEFORE the early exit, so we catch deletions even if there are no new pages.
    urls_in_sitemap = set(sitemap_data.keys())
    urls_in_db = set(mcp_knowledge_base.keys())
    deleted_urls = urls_in_db - urls_in_sitemap

    db_was_modified = False  # Track if we make ANY changes (deletions or additions)

    for dead_url in deleted_urls:
        print(f"Removing deleted page from Knowledge Base: {dead_url}")
        del mcp_knowledge_base[dead_url]
        if dead_url in saved_state:
            del saved_state[dead_url]
        db_was_modified = True

    # 5. Early Exit Check
    if not urls_to_crawl:
        print("No new or updated pages to crawl.")
        # If we deleted ghosts, we still need to save the DB before exiting!
        if db_was_modified:
            print("Saving database after removing ghosts...")

            # Atomic save for Knowledge Base
            temp_kb_file = KNOWLEDGE_BASE_FILE + ".tmp"
            with open(temp_kb_file, "w", encoding="utf-8") as f:
                json.dump(mcp_knowledge_base, f, indent=4)
            os.replace(temp_kb_file, KNOWLEDGE_BASE_FILE)

            # Save State File
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(saved_state, f, indent=4)

            print("Ghost removal successfully saved to disk.")
        return

    print(f"Found {len(urls_to_crawl)} new or updated pages to crawl!")

    # 6. Configure the Crawler
    config = CrawlerRunConfig(
        css_selector="#content-area",
        cache_mode=CacheMode.BYPASS,
        # Put the markdown generator inside the config
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.3)
        ),
    )

    # 7. Run the Crawler fast
    async with AsyncWebCrawler() as crawler:
        results = await crawler.arun_many(
            urls=urls_to_crawl, config=config, concurrency_count=10
        )

        # 8. Process the results
        for res in results:
            url = res.url
            if res.success:
                print(f"Successfully parsed: {url}")
                # --- NEW TITLE EXTRACTION LOGIC ---
                page_title = "No title found"
                if res.html:
                    # Parse the raw HTML returned by Crawl4AI
                    soup = BeautifulSoup(res.html, "html.parser")
                    # Hunt specifically for the #page-title CSS selector
                    title_node = soup.select_one("#page-title")
                    
                    if title_node:
                        page_title = title_node.get_text(strip=True)
                    # Fallback to metadata just in case the page is formatted differently
                    elif res.metadata and res.metadata.get("title"):
                        page_title = res.metadata.get("title")
                # ----------------------------------
                
                url_slug = url.rstrip("/").split("/")[-1]

                # Save to knowledge base
                mcp_knowledge_base[url] = {
                    "title": page_title,
                    "slug": url_slug,
                    "content": res.markdown.fit_markdown,
                }

                # Update our sync state with the new date
                original_date = sitemap_data.get(url) or sitemap_data.get(
                    url.rstrip("/"), ""
                )
                saved_state[url] = original_date
            else:
                print(f"Failed to parse: {url}")

    # Instead of writing directly to KNOWLEDGE_BASE_FILE:
    temp_kb_file = KNOWLEDGE_BASE_FILE + ".tmp"
    with open(temp_kb_file, "w", encoding="utf-8") as f:
        json.dump(mcp_knowledge_base, f, indent=4)

    # Safely overwrite the old file with the new one
    os.replace(temp_kb_file, KNOWLEDGE_BASE_FILE)

    """
    # 9. Save the updated Knowledge Base
    with open(KNOWLEDGE_BASE_FILE, "w", encoding="utf-8") as f:
        json.dump(mcp_knowledge_base, f, indent=4)
    print(f"Knowledge base saved to {KNOWLEDGE_BASE_FILE}")
    """

    # 10. Save the new State File (so it skips these next week!)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(saved_state, f, indent=4)
    print(f"Sync state saved to {STATE_FILE}")


if __name__ == "__main__":
    # This is the correct way to trigger your async script
    asyncio.run(main())
