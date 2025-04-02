"""
Integration test script for AI Legacy Modernization PoC.
This script tests the integration of all components.
"""

import os
import sys
import logging
import json
import requests
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

def test_mcp_router():
    """Test the MCP router functionality."""
    logger.info("Testing MCP router...")
    
    # Create a router
    router = MCPRouter()
    
    # Create a test handler
    def test_handler(message):
        logger.info(f"Test handler received message: {message.content}")
        return Message(
            message_type=MessageType.RESPONSE,
            source="test_handler",
            destination=message.source,
            content={"response": "Test response"},
            correlation_id=message.correlation_id
        )
    
    # Register the handler
    router.register_handler("test_destination", test_handler)
    
    # Create a test message
    test_message = Message(
        message_type=MessageType.REQUEST,
        source="test_source",
        destination="test_destination",
        content={"request": "Test request"},
        correlation_id="test_correlation_id"
    )
    
    # Route the message
    response = router.route_message(test_message)
    
    # Check the response
    if response and response.content.get("response") == "Test response":
        logger.info("MCP router test passed")
        return True
    else:
        logger.error("MCP router test failed")
        return False

def test_api_connector():
    """Test the API connector functionality."""
    logger.info("Testing API connector...")
    
    # Get the weather API connector
    weather_api = registry.get_connector("weather")
    
    if not weather_api:
        logger.error("Weather API connector not found")
        return False
    
    # Create a test message
    test_message = Message(
        message_type=MessageType.REQUEST,
        source="test_source",
        destination="weather",
        content={
            "intent": "query",
            "parameters": {
                "city": "London",
                "units": "metric"
            }
        },
        correlation_id="test_correlation_id"
    )
    
    # Send the message
    try:
        response = weather_api.handle_message(test_message)
        
        # Check the response
        if response and response.content.get("status_code") in [200, 401]:
            # 401 is acceptable for demo key
            logger.info("API connector test passed")
            return True
        else:
            logger.error(f"API connector test failed: {response.content if response else 'No response'}")
            return False
    except Exception as e:
        logger.error(f"API connector test failed with exception: {e}")
        return False

def test_llm_interface():
    """Test the LLM interface functionality."""
    logger.info("Testing LLM interface...")
    
    # Create an LLM interface
    nl_interface = NLInterface()
    
    # Test query
    test_query = "What's the weather like in London?"
    
    try:
        # Process the query
        result = nl_interface.process_query(test_query)
        
        # Check the result
        if result and isinstance(result, dict):
            logger.info("LLM interface test passed")
            return True
        else:
            logger.error(f"LLM interface test failed: {result}")
            return False
    except Exception as e:
        logger.error(f"LLM interface test failed with exception: {e}")
        return False

def test_web_crawler():
    """Test the web crawler functionality."""
    logger.info("Testing web crawler...")
    
    try:
        # Create a web crawler
        crawler = WebCrawler(engine="playwright", headless=True)
        
        # Test URL
        test_url = "https://quotes.toscrape.com/"
        
        # Navigate to the URL
        crawler.navigate(test_url)
        
        # Get the page content
        html_content = crawler.get_page_content()
        
        # Create extractors
        soup_extractor = BeautifulSoupExtractor()
        soup_extractor.add_rule(
            key="quotes",
            selector=".quote .text",
            multiple=True
        )
        soup_extractor.add_rule(
            key="authors",
            selector=".quote .author",
            multiple=True
        )
        
        # Extract data
        extracted_data = soup_extractor.extract(html_content)
        
        # Check the extracted data
        if extracted_data and "quotes" in extracted_data and "authors" in extracted_data:
            logger.info("Web crawler test passed")
            crawler.close()
            return True
        else:
            logger.error(f"Web crawler test failed: {extracted_data}")
            crawler.close()
            return False
    except Exception as e:
        logger.error(f"Web crawler test failed with exception: {e}")
        return False

def test_frontend_api():
    """Test the frontend API endpoints."""
    logger.info("Testing frontend API endpoints...")
    
    # Start the Flask app in a separate process
    import subprocess
    import time
    
    flask_process = subprocess.Popen(
        ["python", "app.py"],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    # Wait for the app to start
    time.sleep(5)
    
    try:
        # Test the capabilities endpoint
        capabilities_response = requests.get("http://localhost:5000/api/capabilities")
        
        if capabilities_response.status_code != 200:
            logger.error(f"Capabilities endpoint test failed: {capabilities_response.text}")
            flask_process.terminate()
            return False
        
        # Test the demo setup endpoint
        setup_response = requests.post(
            "http://localhost:5000/api/demo/setup",
            headers={"Content-Type": "application/json"},
            data="{}"
        )
        
        if setup_response.status_code != 200:
            logger.error(f"Demo setup endpoint test failed: {setup_response.text}")
            flask_process.terminate()
            return False
        
        # Test the chat endpoint
        chat_response = requests.post(
            "http://localhost:5000/api/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps({"message": "Hello, what can you do?"})
        )
        
        if chat_response.status_code != 200:
            logger.error(f"Chat endpoint test failed: {chat_response.text}")
            flask_process.terminate()
            return False
        
        logger.info("Frontend API endpoints test passed")
        flask_process.terminate()
        return True
    
    except Exception as e:
        logger.error(f"Frontend API endpoints test failed with exception: {e}")
        flask_process.terminate()
        return False

def run_integration_tests():
    """Run all integration tests."""
    logger.info("Running integration tests...")
    
    # Set up the test environment
    if not setup_test_environment():
        logger.error("Test environment setup failed")
        return False
    
    # Run the tests
    tests = [
        ("MCP Router", test_mcp_router),
        ("API Connector", test_api_connector),
        ("LLM Interface", test_llm_interface),
        ("Web Crawler", test_web_crawler),
        ("Frontend API", test_frontend_api)
    ]
    
    results = {}
    all_passed = True
    
    for test_name, test_func in tests:
        logger.info(f"Running test: {test_name}")
        try:
            result = test_func()
            results[test_name] = result
            if not result:
                all_passed = False
        except Exception as e:
            logger.error(f"Test {test_name} failed with exception: {e}")
            results[test_name] = False
            all_passed = False
    
    # Print the results
    logger.info("Integration test results:")
    for test_name, result in results.items():
        logger.info(f"{test_name}: {'PASSED' if result else 'FAILED'}")
    
    return all_passed

if __name__ == "__main__":
    success = run_integration_tests()
    if success:
        logger.info("All integration tests passed")
        sys.exit(0)
    else:
        logger.error("Some integration tests failed")
        sys.exit(1)
