"""
Web scraping utilities with async capabilities.
This fixture demonstrates async/await, context managers, and exception handling.
"""

import asyncio
import aiohttp
import requests
from typing import List, Dict, Optional, AsyncGenerator
from contextlib import asynccontextmanager
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse
import time
import logging


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ScrapingResult:
    """Data class to hold scraping results."""
    url: str
    status_code: int
    content: str
    headers: Dict[str, str]
    timestamp: float
    error: Optional[str] = None


class RateLimiter:
    """Simple rate limiter to control request frequency."""
    
    def __init__(self, max_requests: int, time_window: float):
        """
        Initialize rate limiter.
        
        Args:
            max_requests: Maximum number of requests allowed
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests = []
    
    async def acquire(self) -> None:
        """Acquire permission to make a request."""
        now = time.time()
        
        # Remove old requests outside the time window
        self.requests = [req_time for req_time in self.requests if now - req_time < self.time_window]
        
        # If we've hit the limit, wait
        if len(self.requests) >= self.max_requests:
            sleep_time = self.time_window - (now - self.requests[0])
            if sleep_time > 0:
                logger.info(f"Rate limit reached. Sleeping for {sleep_time:.2f} seconds")
                await asyncio.sleep(sleep_time)
        
        self.requests.append(now)


class WebScraper:
    """Asynchronous web scraper with rate limiting and error handling."""
    
    def __init__(self, max_concurrent: int = 10, rate_limit: int = 5, time_window: float = 1.0):
        """
        Initialize the web scraper.
        
        Args:
            max_concurrent: Maximum number of concurrent requests
            rate_limit: Maximum requests per time window
            time_window: Time window for rate limiting in seconds
        """
        self.max_concurrent = max_concurrent
        self.rate_limiter = RateLimiter(rate_limit, time_window)
        self.session = None
        self.results = []
    
    @asynccontextmanager
    async def get_session(self):
        """Context manager for aiohttp session."""
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)
        timeout = aiohttp.ClientTimeout(total=30)
        
        async with aiohttp.ClientSession(
            connector=connector,
            timeout=timeout,
            headers={'User-Agent': 'WebScraper/1.0'}
        ) as session:
            self.session = session
            try:
                yield session
            finally:
                self.session = None
    
    async def fetch_url(self, url: str) -> ScrapingResult:
        """
        Fetch a single URL with error handling and rate limiting.
        
        Args:
            url: URL to fetch
            
        Returns:
            ScrapingResult object with response data
        """
        await self.rate_limiter.acquire()
        
        try:
            async with self.session.get(url) as response:
                content = await response.text()
                result = ScrapingResult(
                    url=url,
                    status_code=response.status,
                    content=content,
                    headers=dict(response.headers),
                    timestamp=time.time()
                )
                logger.info(f"Successfully fetched {url} (status: {response.status})")
                return result
        
        except asyncio.TimeoutError:
            error_msg = f"Timeout error for {url}"
            logger.error(error_msg)
            return ScrapingResult(
                url=url,
                status_code=0,
                content="",
                headers={},
                timestamp=time.time(),
                error=error_msg
            )
        
        except aiohttp.ClientError as e:
            error_msg = f"Client error for {url}: {str(e)}"
            logger.error(error_msg)
            return ScrapingResult(
                url=url,
                status_code=0,
                content="",
                headers={},
                timestamp=time.time(),
                error=error_msg
            )
        
        except Exception as e:
            error_msg = f"Unexpected error for {url}: {str(e)}"
            logger.error(error_msg)
            return ScrapingResult(
                url=url,
                status_code=0,
                content="",
                headers={},
                timestamp=time.time(),
                error=error_msg
            )
    
    async def fetch_multiple(self, urls: List[str]) -> List[ScrapingResult]:
        """
        Fetch multiple URLs concurrently.
        
        Args:
            urls: List of URLs to fetch
            
        Returns:
            List of ScrapingResult objects
        """
        async with self.get_session():
            # Create semaphore to limit concurrent requests
            semaphore = asyncio.Semaphore(self.max_concurrent)
            
            async def fetch_with_semaphore(url: str) -> ScrapingResult:
                async with semaphore:
                    return await self.fetch_url(url)
            
            # Create tasks for all URLs
            tasks = [fetch_with_semaphore(url) for url in urls]
            
            # Execute all tasks and gather results
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Filter out exceptions and return valid results
            valid_results = []
            for result in results:
                if isinstance(result, ScrapingResult):
                    valid_results.append(result)
                    self.results.append(result)
                else:
                    logger.error(f"Task failed with exception: {result}")
            
            return valid_results
    
    def get_successful_results(self) -> List[ScrapingResult]:
        """Get only successful scraping results."""
        return [result for result in self.results if result.error is None and result.status_code == 200]
    
    def get_failed_results(self) -> List[ScrapingResult]:
        """Get only failed scraping results."""
        return [result for result in self.results if result.error is not None or result.status_code != 200]
    
    def clear_results(self) -> None:
        """Clear stored results."""
        self.results.clear()


def extract_links(html_content: str, base_url: str = "") -> List[str]:
    """
    Extract all links from HTML content.
    
    Args:
        html_content: HTML content to parse
        base_url: Base URL for resolving relative links
        
    Returns:
        List of extracted URLs
    """
    import re
    
    # Simple regex to find href attributes
    link_pattern = r'href=["\']([^"\']+)["\']'
    links = re.findall(link_pattern, html_content, re.IGNORECASE)
    
    # Convert relative URLs to absolute URLs
    absolute_links = []
    for link in links:
        if link.startswith('http'):
            absolute_links.append(link)
        elif base_url and not link.startswith('#'):
            absolute_links.append(urljoin(base_url, link))
    
    return list(set(absolute_links))  # Remove duplicates


async def scrape_sitemap(base_url: str, max_depth: int = 2) -> AsyncGenerator[ScrapingResult, None]:
    """
    Async generator to scrape a website following links up to max_depth.
    
    Args:
        base_url: Starting URL
        max_depth: Maximum depth to follow links
        
    Yields:
        ScrapingResult objects for each page scraped
    """
    scraper = WebScraper(max_concurrent=5, rate_limit=3)
    visited = set()
    to_visit = [(base_url, 0)]
    
    async with scraper.get_session():
        while to_visit:
            url, depth = to_visit.pop(0)
            
            if url in visited or depth > max_depth:
                continue
            
            visited.add(url)
            result = await scraper.fetch_url(url)
            yield result
            
            # Extract links from successful results
            if result.error is None and result.status_code == 200:
                links = extract_links(result.content, base_url)
                for link in links[:10]:  # Limit to first 10 links to avoid infinite loops
                    if link not in visited and urlparse(link).netloc == urlparse(base_url).netloc:
                        to_visit.append((link, depth + 1))


# Synchronous wrapper functions for backward compatibility
def fetch_url_sync(url: str, timeout: int = 30) -> Dict[str, any]:
    """
    Synchronous function to fetch a single URL.
    
    Args:
        url: URL to fetch
        timeout: Request timeout in seconds
        
    Returns:
        Dictionary with response data
    """
    try:
        response = requests.get(
            url,
            timeout=timeout,
            headers={'User-Agent': 'WebScraper/1.0'}
        )
        
        return {
            'url': url,
            'status_code': response.status_code,
            'content': response.text,
            'headers': dict(response.headers),
            'success': True,
            'error': None
        }
    
    except requests.RequestException as e:
        return {
            'url': url,
            'status_code': 0,
            'content': '',
            'headers': {},
            'success': False,
            'error': str(e)
        }


# Example usage
EXAMPLE_URLS = [
    "https://httpbin.org/json",
    "https://httpbin.org/xml",
    "https://httpbin.org/html",
    "https://httpbin.org/delay/1",
    "https://httpbin.org/status/200"
]