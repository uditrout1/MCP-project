"""
Crawler Engine module.
This module provides the core functionality for crawling web applications.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union, Set
import logging
import time
import re
import urllib.parse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
from bs4 import BeautifulSoup
from playwright.sync_api import sync_playwright

logger = logging.getLogger(__name__)


class CrawlerEngine(ABC):
    """
    Abstract base class for web crawler engines.
    
    This class defines the interface for different crawler implementations.
    """
    
    @abstractmethod
    def start(self, url: str):
        """
        Start crawling from a URL.
        
        Args:
            url: The starting URL
        """
        pass
    
    @abstractmethod
    def navigate(self, url: str):
        """
        Navigate to a specific URL.
        
        Args:
            url: The URL to navigate to
        """
        pass
    
    @abstractmethod
    def get_page_content(self) -> str:
        """
        Get the content of the current page.
        
        Returns:
            str: The page content as HTML
        """
        pass
    
    @abstractmethod
    def get_links(self) -> List[str]:
        """
        Get all links on the current page.
        
        Returns:
            List[str]: List of URLs
        """
        pass
    
    @abstractmethod
    def click(self, selector: str) -> bool:
        """
        Click on an element.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def fill(self, selector: str, value: str) -> bool:
        """
        Fill a form field.
        
        Args:
            selector: CSS selector for the field
            value: Value to fill
            
        Returns:
            bool: True if successful, False otherwise
        """
        pass
    
    @abstractmethod
    def wait_for(self, selector: str, timeout: int = 30) -> bool:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in seconds
            
        Returns:
            bool: True if the element appeared, False if timed out
        """
        pass
    
    @abstractmethod
    def close(self):
        """Close the crawler and release resources."""
        pass


class SeleniumEngine(CrawlerEngine):
    """
    Crawler engine using Selenium.
    """
    
    def __init__(self, headless: bool = True, user_agent: str = None):
        """
        Initialize the Selenium crawler engine.
        
        Args:
            headless: Whether to run in headless mode
            user_agent: User agent string to use
        """
        self.headless = headless
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.driver = None
        self.visited_urls = set()
    
    def _setup_driver(self):
        """Set up the Selenium WebDriver."""
        options = Options()
        if self.headless:
            options.add_argument("--headless")
        
        options.add_argument(f"user-agent={self.user_agent}")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        
        self.driver = webdriver.Chrome(options=options)
    
    def start(self, url: str):
        """
        Start crawling from a URL.
        
        Args:
            url: The starting URL
        """
        if self.driver is None:
            self._setup_driver()
        
        self.navigate(url)
    
    def navigate(self, url: str):
        """
        Navigate to a specific URL.
        
        Args:
            url: The URL to navigate to
        """
        if self.driver is None:
            self._setup_driver()
        
        try:
            self.driver.get(url)
            self.visited_urls.add(url)
            logger.info(f"Navigated to {url}")
            return True
        except WebDriverException as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    def get_page_content(self) -> str:
        """
        Get the content of the current page.
        
        Returns:
            str: The page content as HTML
        """
        if self.driver is None:
            return ""
        
        return self.driver.page_source
    
    def get_links(self) -> List[str]:
        """
        Get all links on the current page.
        
        Returns:
            List[str]: List of URLs
        """
        if self.driver is None:
            return []
        
        links = []
        elements = self.driver.find_elements(By.TAG_NAME, "a")
        
        for element in elements:
            href = element.get_attribute("href")
            if href and href.startswith("http"):
                links.append(href)
        
        return links
    
    def click(self, selector: str) -> bool:
        """
        Click on an element.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.driver is None:
            return False
        
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.click()
            return True
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    def fill(self, selector: str, value: str) -> bool:
        """
        Fill a form field.
        
        Args:
            selector: CSS selector for the field
            value: Value to fill
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.driver is None:
            return False
        
        try:
            element = self.driver.find_element(By.CSS_SELECTOR, selector)
            element.clear()
            element.send_keys(value)
            return True
        except Exception as e:
            logger.error(f"Error filling field {selector}: {e}")
            return False
    
    def wait_for(self, selector: str, timeout: int = 30) -> bool:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in seconds
            
        Returns:
            bool: True if the element appeared, False if timed out
        """
        if self.driver is None:
            return False
        
        try:
            wait = WebDriverWait(self.driver, timeout)
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, selector)))
            return True
        except TimeoutException:
            logger.warning(f"Timeout waiting for element {selector}")
            return False
    
    def close(self):
        """Close the crawler and release resources."""
        if self.driver is not None:
            self.driver.quit()
            self.driver = None


class PlaywrightEngine(CrawlerEngine):
    """
    Crawler engine using Playwright.
    """
    
    def __init__(self, headless: bool = True, user_agent: str = None):
        """
        Initialize the Playwright crawler engine.
        
        Args:
            headless: Whether to run in headless mode
            user_agent: User agent string to use
        """
        self.headless = headless
        self.user_agent = user_agent or "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        self.playwright = None
        self.browser = None
        self.page = None
        self.visited_urls = set()
    
    def _setup_browser(self):
        """Set up the Playwright browser."""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.headless
        )
        self.page = self.browser.new_page(
            user_agent=self.user_agent
        )
    
    def start(self, url: str):
        """
        Start crawling from a URL.
        
        Args:
            url: The starting URL
        """
        if self.page is None:
            self._setup_browser()
        
        self.navigate(url)
    
    def navigate(self, url: str):
        """
        Navigate to a specific URL.
        
        Args:
            url: The URL to navigate to
        """
        if self.page is None:
            self._setup_browser()
        
        try:
            self.page.goto(url)
            self.visited_urls.add(url)
            logger.info(f"Navigated to {url}")
            return True
        except Exception as e:
            logger.error(f"Error navigating to {url}: {e}")
            return False
    
    def get_page_content(self) -> str:
        """
        Get the content of the current page.
        
        Returns:
            str: The page content as HTML
        """
        if self.page is None:
            return ""
        
        return self.page.content()
    
    def get_links(self) -> List[str]:
        """
        Get all links on the current page.
        
        Returns:
            List[str]: List of URLs
        """
        if self.page is None:
            return []
        
        return self.page.eval_on_selector_all("a[href]", """
            elements => elements.map(element => element.href)
                .filter(href => href.startsWith('http'))
        """)
    
    def click(self, selector: str) -> bool:
        """
        Click on an element.
        
        Args:
            selector: CSS selector for the element
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.page is None:
            return False
        
        try:
            self.page.click(selector)
            return True
        except Exception as e:
            logger.error(f"Error clicking element {selector}: {e}")
            return False
    
    def fill(self, selector: str, value: str) -> bool:
        """
        Fill a form field.
        
        Args:
            selector: CSS selector for the field
            value: Value to fill
            
        Returns:
            bool: True if successful, False otherwise
        """
        if self.page is None:
            return False
        
        try:
            self.page.fill(selector, value)
            return True
        except Exception as e:
            logger.error(f"Error filling field {selector}: {e}")
            return False
    
    def wait_for(self, selector: str, timeout: int = 30000) -> bool:
        """
        Wait for an element to appear.
        
        Args:
            selector: CSS selector for the element
            timeout: Timeout in milliseconds
            
        Returns:
            bool: True if the element appeared, False if timed out
        """
        if self.page is None:
            return False
        
        try:
            self.page.wait_for_selector(selector, timeout=timeout)
            return True
        except Exception:
            logger.warning(f"Timeout waiting for element {selector}")
            return False
    
    def close(self):
        """Close the crawler and release resources."""
        if self.browser is not None:
            self.browser.close()
            self.browser = None
        
        if self.playwright is not None:
            self.playwright.stop()
            self.playwright = None


class WebCrawler:
    """
    Main web crawler class that uses a crawler engine.
    """
    
    def __init__(self, engine: str = "playwright", headless: bool = True):
        """
        Initialize the web crawler.
        
        Args:
            engine: Engine to use ("selenium" or "playwright")
            headless: Whether to run in headless mode
        """
        if engine.lower() == "selenium":
            self.engine = SeleniumEngine(headless=headless)
        elif engine.lower() == "playwright":
            self.engine = PlaywrightEngine(headless=headless)
        else:
            raise ValueError(f"Unsupported engine: {engine}")
        
        self.visited_urls: Set[str] = set()
        self.to_visit: List[str] = []
        self.base_url: Optional[str] = None
        self.max_depth: int = 3
        self.current_depth: int = 0
        self.same_domain_only: bool = True
    
    def crawl(self, start_url: str, max_depth: int = 3, same_domain_only: bool = True):
        """
        Crawl a website starting from a URL.
        
        Args:
            start_url: The starting URL
            max_depth: Maximum crawl depth
            same_domain_only: Whether to stay on the same domain
        """
        self.base_url = start_url
        self.max_depth = max_depth
        self.same_domain_only = same_domain_only
        self.to_visit = [start_url]
        self.visited_urls = set()
        self.current_depth = 0
        
        # Extract domain from start URL
        parsed_url = urllib.parse.urlparse(start_url)
        self.base_domain = parsed_url.netloc
        
        # Start the engine
        self.engine.start(start_url)
        
        # Process the starting URL
        self._process_current_page()
        
        # Continue crawling until max depth or no more URLs
        while self.to_visit and self.current_depth < self.max_depth:
            self.current_depth += 1
            next_level_urls = self.to_visit.copy()
            self.to_visit = []
            
            for url in next_level_urls:
                if url in self.visited_urls:
                    continue
                
                self.engine.navigate(url)
                self.visited_urls.add(url)
                self._process_current_page()
    
    def _process_current_page(self):
        """Process the current page and extract links."""
        # Get all links on the page
        links = self.engine.get_links()
        
        # Filter links if needed
        for link in links:
            if link in self.visited_urls or link in self.to_visit:
                continue
            
            if self.same_domain_only:
                parsed_url = urllib.parse.urlparse(link)
                if parsed_url.netloc != self.base_domain:
                    continue
            
            self.to_visit.append(link)
    
    def get_page_content(self) -> str:
        """
        Get the content of the current page.
        
        Returns:
            str: The page content as HTML
        """
        return self.engine.get_page_content()
    
    def navigate(self, url: str):
        """
        Navigate to a specific URL.
        
        Args:
            url: The URL to navigate to
        """
        self.engine.navigate(url)
    
    def close(self):
        """Close the crawler and release resources."""
        self.engine.close()
