"""
Main application module.
This module provides the entry point for the application.
"""

import os
import logging
from dotenv import load_dotenv
from src.frontend import app
from src.api.registry import create_rest_connector, AuthType
from src.llm.interface import NLInterface

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def setup_sample_apis():
    """Set up sample APIs for demonstration."""
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
    
    logger.info("Sample APIs set up successfully")

def initialize_app():
    """Initialize the application components."""
    # Set up sample APIs
    setup_sample_apis()
    
    # Initialize NL interface
    nl_interface = NLInterface()
    
    logger.info("Application initialized successfully")
    return app

if __name__ == "__main__":
    # Initialize the application
    app = initialize_app()
    
    # Run the application
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
