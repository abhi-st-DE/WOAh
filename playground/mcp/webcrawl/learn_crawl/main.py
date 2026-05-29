import base64
import json
from pathlib import Path
import asyncio
from typing import List
from crawl4ai import AsyncWebCrawler, BrowserConfig, CrawlerRunConfig, CacheMode
from crawl4ai.content_filter_strategy import PruningContentFilter, BM25ContentFilter
from crawl4ai.markdown_generation_strategy import DefaultMarkdownGenerator


CURRENT_DIR = Path(__file__).parent


async def demo_basic_crawl():
    """ Basic Web Crawling with Markdown Generation. """
    print("\n=== 1. Basic Web Crawling ===")
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun(
            url = "https://example.com"
        )
        for i, result in enumerate(results):
            print(f"Result {i + 1}:")
            print(f"Success: {result.success}")
            if result.success:
                print(f"Markdown length: {len(result.markdown.raw_markdown)} chars")
                print(f"First 100 characters: {result.markdown.raw_markdown[:100]}...")
            else:
                print(f"Failed to crawl the {url}.")

async def demo_parallel_crawl():
    "Crawl Multiple URLs in parallel."
    print(f"\n=== 2. Parallel Crawling===")
    urls = [
        "https://news.ycombinator.com/",
        "https://example.com/",
        "https://httpbin.org/html",
    ]
    async with AsyncWebCrawler() as crawler:
        results: List[CrawlResult] = await crawler.arun_many(
            urls=urls,
        )

        print(f"Crawled {len(results)} URLs in parallel:")
        for i, result in enumerate(results):
            print(
                f" {i+1}.{result.url} - {'Success' if result.success else 'Failed'}"
            )

async def basic_config():
    """ Basic Configuration """
    print(f"\n===Basic conf===")
    browser_conf = BrowserConfig(headless=True)
    #browser_conf = BrowserConfig(headless=False)
    run_conf = CrawlerRunConfig(
        cache_mode=CacheMode.BYPASS
    )

    async with AsyncWebCrawler(config=browser_conf) as crawler:
        result = await crawler.arun(
            url="https://example.com",
            config=run_conf
        )
        print(result.markdown)

async def BM25Filter_markdown():
    """ BM25 is a classical text ranking algorithm often used in search engines. 
    If you have a user query or rely on page metadata to derive a query, 
    BM25 can identify which text chunks best match that query.
    """
    print(f"\n=== BM25 filter algo for markdown, based on a specific query.")
    bm25_filter = BM25ContentFilter(
        user_query='data types in python',
        bm25_threshold=1.2
    )

    md_generator = DefaultMarkdownGenerator(content_filter=bm25_filter)

    config = CrawlerRunConfig(
        markdown_generator=md_generator
    )

    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun(
            url = "https://en.wikipedia.org/wiki/Python_(programming_language)",
            config=config
        )
        if result.success:
            print("Fit Markdown (BM25 query-based):")
            print(result.markdown.fit_markdown)
        else:
            print("Error:", result.error_message)

async def demo_fit_markdown():
    """ Generate focussed markdown with llm content filter. """
    print(f"\n=== 3. Fit Markdown with llm content filter===")
    
    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun(
            url = "https://en.wikipedia.org/wiki/Python_(programming_language)",
            config=CrawlerRunConfig(
                markdown_generator=DefaultMarkdownGenerator(
                    content_filter=PruningContentFilter()
                )
            ),
        )

        # Print stats and save the fit markdown
        print(f"Raw: {len(result.markdown.raw_markdown)} chars")
        print(f"Fit: {len(result.markdown.fit_markdown)} chars")

        """
        # optional to write to a file and check.
        
        # SAVE TO FILE the unfit or raw markdown
        #with open("python_raw.md", "w", encoding="utf-8") as f:
        #    f.write(result.markdown.raw_markdown)
        
        # SAVE TO FILE the fit markdown
        #with open("python_fit.md", "w", encoding="utf-8") as f:
        #    f.write(result.markdown.fit_markdown)
        """
        
async def demo_media_and_links():
    """ Extract media and links from all the pages. """
    print(f"\n=== 4 Media and links extraction===")

    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun(
            url="https://en.wikipedia.org/wiki/Main_page"
        )

        for i, result in enumerate(result):
            # Extract and save all images.
            images = result.media.get("images", [])
            print(f"Found {len(images)} images")

            # Extract and save all links internal and external.
            internal_links = result.links.get("internal", [])
            external_links = result.links.get("external", [])
            print(f"Found {len(internal_links)} no of internal links.")
            print(f"Found {len(external_links)} no of external links.")

            # Save everything to the files.
            with open("images.json", "w") as f:
                json.dump(images, f, indent=2)

            with open("links.json", "w") as f:
                json.dump(
                    {"internal": internal_links, "external": external_links},
                    f,
                    indent=2
                )

async def demo_screenshot_and_pdf():
    """ Create screenshot and pdf of a page. """
    print(f"\n=== 5. Screenshot and PDF of a page")
    
    async with AsyncWebCrawler() as crawler:
        result: List[CrawlResult] = await crawler.arun(
            #url
            url="https://en.wikipedia.org/wiki/Giant_anteater",
            config=CrawlerRunConfig(screenshot=True, scan_full_page=True, pdf=True, wait_for_images=True),
        )

        tmp_dir = CURRENT_DIR / "tmp"
        tmp_dir.mkdir(exist_ok=True)

        screenshot_path = tmp_dir / "example_screenshot.png"
        pdf_path = tmp_dir / "example.pdf"

        for i, result in enumerate(result):
            if result.screenshot:
                #Save the screenshot
                with open(screenshot_path, "wb") as f:
                    f.write(base64.b64decode(result.screenshot))
                print(f"Screenshot saved at {screenshot_path}")
            if result.pdf:
                #Save file Pdf.
                with open(pdf_path, "wb") as f:
                    f.write(result.pdf)
                print(f"Pdf saved at {pdf_path}") 

async def demo_css_structured_extraction_no_schema():
    """ Extract structured data using CSS selectors """
    print("\n=== 6 CSS structure extraction===")
    config = CrawlerRunConfig(
        css_selector="#content-area",
        cache_mode=CacheMode.BYPASS,
        markdown_generator=DefaultMarkdownGenerator(
            content_filter=PruningContentFilter(threshold=0.3)
        )
    )
    async with AsyncWebCrawler() as crawler:
        result = await crawler.arun(
            url="https://docs.langchain.com/langsmith/cron-jobs",
            config=config
        )
        print(result.markdown.fit_markdown)


async def main():
   #await demo_basic_crawl()
   #await demo_parallel_crawl()
   #await basic_config()
   #await demo_fit_markdown()
   #await BM25Filter_markdown()
   #await demo_media_and_links()
   #await demo_screenshot_and_pdf()
   await demo_css_structured_extraction_no_schema()
    

if __name__ == "__main__":
    asyncio.run(main())
