"""
End-to-end test script for AI Legacy Modernization PoC.
This script tests complete workflows from user input to final output.
"""

import os
import sys
import logging
import json
import time
from dotenv import load_dotenv

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
from src.mcp.message import Message, MessageType
from src.mcp.router import MCPRouter
from src.api.registry import registry, create_rest_connector, AuthType
from src.llm.interface import NLInterface
from src.crawler.engines import WebCrawler
from src.crawler.extractors import BeautifulSoupExtractor, JSONExtractor, CompositeExtractor
from src.crawler.processors import BasicProcessor, LLMProcessor, CompositeProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_test_environment():
    """Set up the test environment with sample APIs."""
    logger.info("Setting up test environment...")
    
    # Weather API
    weather_api = create_rest_connector(
        name="weather",
        base_url="https://api.openweathermap.org/data/2.5",
        auth_type=AuthType.API_KEY,
        auth_params={
            "key_name": "appid",
            "key_value": os.environ.get("OPENWEATHER_API_KEY", "demo_key"),
            "key_location": "query"
        }
    )
    weather_api.register_endpoint(
        intent="query",
        endpoint="weather",
        method="GET",
        params_mapping={
            "city": "q",
            "units": "units"
        }
    )
    
    # News API
    news_api = create_rest_connector(
        name="news",
        base_url="https://newsapi.org/v2",
        auth_type=AuthType.API_KEY,
        auth_params={
            "key_name": "apiKey",
            "key_value": os.environ.get("NEWS_API_KEY", "demo_key"),
            "key_location": "query"
        }
    )
    news_api.register_endpoint(
        intent="query",
        endpoint="top-headlines",
        method="GET",
        params_mapping={
            "country": "country",
            "category": "category",
            "query": "q"
        }
    )
    
    logger.info("Test environment set up successfully")
    return True

def test_natural_language_to_api_workflow():
    """Test the natural language to API workflow."""
    logger.info("Testing natural language to API workflow...")
    
    # Create an LLM interface
    nl_interface = NLInterface()
    
    # Test queries
    test_queries = [
        "What's the weather like in London?",
        "Show me the latest technology news",
        "What's the temperature in Tokyo in Celsius?"
    ]
    
    results = []
    
    for query in test_queries:
        logger.info(f"Processing query: {query}")
        
        try:
            # Process the query
            result = nl_interface.process_query(query)
            
            # Check the result
            if result and isinstance(result, dict):
                logger.info(f"Query processed successfully: {query}")
                results.append((query, True, result))
            else:
                logger.error(f"Query processing failed: {query}")
                results.append((query, False, result))
        except Exception as e:
            logger.error(f"Query processing failed with exception: {e}")
            results.append((query, False, str(e)))
    
    # Check if all queries were processed successfully
    success = all(result[1] for result in results)
    
    if success:
        logger.info("Natural language to API workflow test passed")
    else:
        logger.error("Natural language to API workflow test failed")
    
    return success, results

def test_web_crawling_workflow():
    """Test the web crawling workflow."""
    logger.info("Testing web crawling workflow...")
    
    try:
        # Create a web crawler
        crawler = WebCrawler(engine="playwright", headless=True)
        
        # Test URLs and extraction rules
        test_cases = [
            {
                "url": "https://quotes.toscrape.com/",
                "rules": {
                    "quotes": {
                        "selector": ".quote .text",
                        "multiple": True
                    },
                    "authors": {
                        "selector": ".quote .author",
                        "multiple": True
                    }
                }
            },
            {
                "url": "https://news.ycombinator.com/",
                "rules": {
                    "titles": {
                        "selector": ".titleline > a",
                        "multiple": True
                    },
                    "scores": {
                        "selector": ".score",
                        "multiple": True
                    }
                }
            }
        ]
        
        results = []
        
        for test_case in test_cases:
            url = test_case["url"]
            rules = test_case["rules"]
            
            logger.info(f"Crawling URL: {url}")
            
            try:
                # Navigate to the URL
                crawler.navigate(url)
                
                # Get the page content
                html_content = crawler.get_page_content()
                
                # Create extractor
                soup_extractor = BeautifulSoupExtractor()
                
                # Add rules
                for key, rule in rules.items():
                    soup_extractor.add_rule(
                        key=key,
                        selector=rule["selector"],
                        multiple=rule.get("multiple", False),
                        attribute=rule.get("attribute")
                    )
                
                # Extract data
                extracted_data = soup_extractor.extract(html_content)
                
                # Check if all expected keys are present
                expected_keys = list(rules.keys())
                actual_keys = list(extracted_data.keys())
                
                missing_keys = [key for key in expected_keys if key not in actual_keys]
                
                if not missing_keys:
                    logger.info(f"URL crawled successfully: {url}")
                    results.append((url, True, extracted_data))
                else:
                    logger.error(f"URL crawling failed, missing keys {missing_keys}: {url}")
                    results.append((url, False, extracted_data))
            
            except Exception as e:
                logger.error(f"URL crawling failed with exception: {e}")
                results.append((url, False, str(e)))
        
        # Close the crawler
        crawler.close()
        
        # Check if all URLs were crawled successfully
        success = all(result[1] for result in results)
        
        if success:
            logger.info("Web crawling workflow test passed")
        else:
            logger.error("Web crawling workflow test failed")
        
        return success, results
    
    except Exception as e:
        logger.error(f"Web crawling workflow test failed with exception: {e}")
        return False, [(None, False, str(e))]

def test_combined_workflow():
    """Test a combined workflow with natural language, API, and web crawling."""
    logger.info("Testing combined workflow...")
    
    try:
        # Create components
        nl_interface = NLInterface()
        crawler = WebCrawler(engine="playwright", headless=True)
        
        # Test query that combines API and web crawling
        test_query = "Extract the top headlines from Hacker News and compare them with the latest technology news from the News API"
        
        logger.info(f"Processing combined query: {test_query}")
        
        # First, process with NL interface to get API data
        api_result = nl_interface.process_query("Show me the latest technology news")
        
        # Then, crawl Hacker News
        crawler.navigate("https://news.ycombinator.com/")
        html_content = crawler.get_page_content()
        
        # Extract headlines
        soup_extractor = BeautifulSoupExtractor()
        soup_extractor.add_rule(
            key="headlines",
            selector=".titleline > a",
            multiple=True
        )
        
        web_result = soup_extractor.extract(html_content)
        
        # Close the crawler
        crawler.close()
        
        # Combine results
        combined_result = {
            "api_news": api_result.get("raw_data", {}),
            "web_headlines": web_result.get("headlines", [])
        }
        
        # Check if both API and web results are present
        if "api_news" in combined_result and "web_headlines" in combined_result:
            logger.info("Combined workflow test passed")
            return True, combined_result
        else:
            logger.error("Combined workflow test failed")
            return False, combined_result
    
    except Exception as e:
        logger.error(f"Combined workflow test failed with exception: {e}")
        return False, str(e)

def run_end_to_end_tests():
    """Run all end-to-end tests."""
    logger.info("Running end-to-end tests...")
    
    # Set up the test environment
    if not setup_test_environment():
        logger.error("Test environment setup failed")
        return False
    
    # Run the tests
    tests = [
        ("Natural Language to API Workflow", test_natural_language_to_api_workflow),
        ("Web Crawling Workflow", test_web_crawling_workflow),
        ("Combined Workflow", test_combined_workflow)
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            success, test_results = test_func()
            results[test_name] = (success, test_results)
            if not success:
                all_passed = False
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = (False, str(e))
            all_passed = False
    
    # Print the results
    logger.info("End-to-end test results:")
    for test_name, (success, _) in results.items():
        logger.info(f"{test_name}: {'PASSED' if success else 'FAILED'}")
    
    # Save detailed results to file
    with open("e2e_test_results.json", "w") as f:
        json.dump({k: {"success": v[0], "results": str(v[1])} for k, v in results.items()}, f, indent=2)
    
    return all_passed

if __name__ == "__main__":
    success = run_end_to_end_tests()
    if success:
        logger.info("All end-to-end tests passed")
        sys.exit(0)
    else:
        logger.error("Some end-to-end tests failed")
        sys.exit(1)
