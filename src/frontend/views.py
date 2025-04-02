"""
Frontend views module.
This module provides the routes and view functions for the application.
"""

from flask import render_template, request, jsonify, redirect, url_for
import logging
import json
import os
from . import app
from ..llm.interface import NLInterface
from ..api.registry import registry, create_rest_connector, AuthType
from ..crawler.engines import WebCrawler
from ..crawler.extractors import BeautifulSoupExtractor, JSONExtractor, CompositeExtractor
from ..crawler.processors import BasicProcessor, LLMProcessor, CompositeProcessor

# Set up logging
logger = logging.getLogger(__name__)

# Initialize components
nl_interface = NLInterface()
web_crawler = None  # Initialize on demand

# Sample API for demonstration
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


@app.route('/')
def index():
    """Render the main page."""
    return render_template('index.html')


@app.route('/chat')
def chat():
    """Render the chat interface."""
    return render_template('chat.html')


@app.route('/crawler')
def crawler():
    """Render the web crawler interface."""
    return render_template('crawler.html')


@app.route('/api/chat', methods=['POST'])
def api_chat():
    """Process a chat message."""
    try:
        data = request.json
        query = data.get('message', '')
        
        if not query:
            return jsonify({"error": "No message provided"}), 400
        
        # Process the query
        result = nl_interface.process_query(query)
        
        return jsonify(result)
    
    except Exception as e:
        logger.exception(f"Error processing chat message: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/crawl', methods=['POST'])
def api_crawl():
    """Crawl a website and extract data."""
    try:
        data = request.json
        url = data.get('url', '')
        extraction_rules = data.get('extraction_rules', {})
        
        if not url:
            return jsonify({"error": "No URL provided"}), 400
        
        # Initialize web crawler if needed
        global web_crawler
        if web_crawler is None:
            web_crawler = WebCrawler(engine="playwright", headless=True)
        
        # Set up extractors
        soup_extractor = BeautifulSoupExtractor()
        for key, rule in extraction_rules.items():
            soup_extractor.add_rule(
                key=key,
                selector=rule.get('selector', ''),
                attribute=rule.get('attribute'),
                multiple=rule.get('multiple', False)
            )
        
        json_extractor = JSONExtractor()
        composite_extractor = CompositeExtractor([soup_extractor, json_extractor])
        
        # Crawl the website
        web_crawler.navigate(url)
        html_content = web_crawler.get_page_content()
        
        # Extract data
        extracted_data = composite_extractor.extract(html_content)
        
        # Process data with LLM if requested
        if data.get('enrich', False):
            llm_processor = LLMProcessor()
            llm_processor.add_enrichment_prompt(
                output_key="summary",
                prompt_template="Summarize the following information in a concise paragraph:\n\n{}"
                .format(json.dumps(extracted_data, indent=2))
            )
            
            processor = CompositeProcessor([llm_processor])
            processed_data = processor.process(extracted_data)
        else:
            processed_data = extracted_data
        
        return jsonify({
            "url": url,
            "data": processed_data
        })
    
    except Exception as e:
        logger.exception(f"Error crawling website: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/capabilities')
def api_capabilities():
    """Get the capabilities of the system."""
    try:
        capabilities = {
            "apis": registry.list_connectors(),
            "description": nl_interface.explain_capabilities()
        }
        
        return jsonify(capabilities)
    
    except Exception as e:
        logger.exception(f"Error getting capabilities: {e}")
        return jsonify({"error": str(e)}), 500


@app.route('/demo')
def demo():
    """Render the demo page."""
    return render_template('demo.html')


@app.route('/api/demo/setup', methods=['POST'])
def api_demo_setup():
    """Set up the demo environment."""
    try:
        # Set up sample APIs
        setup_sample_apis()
        
        return jsonify({"status": "success", "message": "Demo environment set up successfully"})
    
    except Exception as e:
        logger.exception(f"Error setting up demo: {e}")
        return jsonify({"error": str(e)}), 500


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    """Handle 404 errors."""
    return render_template('404.html'), 404


@app.errorhandler(500)
def server_error(e):
    """Handle 500 errors."""
    return render_template('500.html'), 500
