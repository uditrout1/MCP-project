"""
Unit test script for AI Legacy Modernization PoC.
This script tests individual components.
"""

import os
import sys
import unittest
import logging
from unittest.mock import MagicMock, patch

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import components
from src.mcp.message import Message, MessageType
from src.mcp.router import MCPRouter
from src.api.connector import RESTConnector, AuthType
from src.llm.models import OpenAIProvider
from src.crawler.extractors import BeautifulSoupExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class TestMCPMessage(unittest.TestCase):
    """Test the MCP Message class."""
    
    def test_message_creation(self):
        """Test creating a message."""
        message = Message(
            message_type=MessageType.REQUEST,
            source="test_source",
            destination="test_destination",
            content={"test": "content"},
            correlation_id="test_correlation_id"
        )
        
        self.assertEqual(message.message_type, MessageType.REQUEST)
        self.assertEqual(message.source, "test_source")
        self.assertEqual(message.destination, "test_destination")
        self.assertEqual(message.content, {"test": "content"})
        self.assertEqual(message.correlation_id, "test_correlation_id")
    
    def test_message_to_dict(self):
        """Test converting a message to a dictionary."""
        message = Message(
            message_type=MessageType.REQUEST,
            source="test_source",
            destination="test_destination",
            content={"test": "content"},
            correlation_id="test_correlation_id"
        )
        
        message_dict = message.to_dict()
        
        self.assertEqual(message_dict["message_type"], MessageType.REQUEST.value)
        self.assertEqual(message_dict["source"], "test_source")
        self.assertEqual(message_dict["destination"], "test_destination")
        self.assertEqual(message_dict["content"], {"test": "content"})
        self.assertEqual(message_dict["correlation_id"], "test_correlation_id")
    
    def test_message_from_dict(self):
        """Test creating a message from a dictionary."""
        message_dict = {
            "message_type": MessageType.REQUEST.value,
            "source": "test_source",
            "destination": "test_destination",
            "content": {"test": "content"},
            "correlation_id": "test_correlation_id"
        }
        
        message = Message.from_dict(message_dict)
        
        self.assertEqual(message.message_type, MessageType.REQUEST)
        self.assertEqual(message.source, "test_source")
        self.assertEqual(message.destination, "test_destination")
        self.assertEqual(message.content, {"test": "content"})
        self.assertEqual(message.correlation_id, "test_correlation_id")


class TestMCPRouter(unittest.TestCase):
    """Test the MCP Router class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.router = MCPRouter()
    
    def test_register_handler(self):
        """Test registering a handler."""
        handler = MagicMock()
        
        self.router.register_handler("test_destination", handler)
        
        self.assertIn("test_destination", self.router.handlers)
        self.assertEqual(self.router.handlers["test_destination"], handler)
    
    def test_route_message(self):
        """Test routing a message."""
        handler = MagicMock()
        handler.return_value = Message(
            message_type=MessageType.RESPONSE,
            source="test_destination",
            destination="test_source",
            content={"response": "Test response"},
            correlation_id="test_correlation_id"
        )
        
        self.router.register_handler("test_destination", handler)
        
        message = Message(
            message_type=MessageType.REQUEST,
            source="test_source",
            destination="test_destination",
            content={"request": "Test request"},
            correlation_id="test_correlation_id"
        )
        
        response = self.router.route_message(message)
        
        handler.assert_called_once_with(message)
        self.assertEqual(response.message_type, MessageType.RESPONSE)
        self.assertEqual(response.source, "test_destination")
        self.assertEqual(response.destination, "test_source")
        self.assertEqual(response.content, {"response": "Test response"})
        self.assertEqual(response.correlation_id, "test_correlation_id")
    
    def test_route_message_no_handler(self):
        """Test routing a message with no handler."""
        message = Message(
            message_type=MessageType.REQUEST,
            source="test_source",
            destination="nonexistent_destination",
            content={"request": "Test request"},
            correlation_id="test_correlation_id"
        )
        
        response = self.router.route_message(message)
        
        self.assertEqual(response.message_type, MessageType.ERROR)
        self.assertEqual(response.source, "router")
        self.assertEqual(response.destination, "test_source")
        self.assertEqual(response.content["error"], "No handler found for destination: nonexistent_destination")
        self.assertEqual(response.correlation_id, "test_correlation_id")


class TestRESTConnector(unittest.TestCase):
    """Test the REST Connector class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.connector = RESTConnector(
            name="test_connector",
            base_url="https://api.example.com",
            auth_type=AuthType.API_KEY,
            auth_params={
                "key_name": "api_key",
                "key_value": "test_key",
                "key_location": "query"
            }
        )
    
    def test_register_endpoint(self):
        """Test registering an endpoint."""
        self.connector.register_endpoint(
            intent="test_intent",
            endpoint="test_endpoint",
            method="GET",
            params_mapping={
                "param1": "api_param1",
                "param2": "api_param2"
            }
        )
        
        self.assertIn("test_intent", self.connector.endpoints)
        endpoint = self.connector.endpoints["test_intent"]
        self.assertEqual(endpoint["endpoint"], "test_endpoint")
        self.assertEqual(endpoint["method"], "GET")
        self.assertEqual(endpoint["params_mapping"], {
            "param1": "api_param1",
            "param2": "api_param2"
        })
    
    @patch('requests.request')
    def test_handle_message(self, mock_request):
        """Test handling a message."""
        # Mock the response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"result": "test_result"}
        mock_request.return_value = mock_response
        
        # Register an endpoint
        self.connector.register_endpoint(
            intent="test_intent",
            endpoint="test_endpoint",
            method="GET",
            params_mapping={
                "param1": "api_param1",
                "param2": "api_param2"
            }
        )
        
        # Create a message
        message = Message(
            message_type=MessageType.REQUEST,
            source="test_source",
            destination="test_connector",
            content={
                "intent": "test_intent",
                "parameters": {
                    "param1": "value1",
                    "param2": "value2"
                }
            },
            correlation_id="test_correlation_id"
        )
        
        # Handle the message
        response = self.connector.handle_message(message)
        
        # Check the response
        self.assertEqual(response.message_type, MessageType.RESPONSE)
        self.assertEqual(response.source, "test_connector")
        self.assertEqual(response.destination, "test_source")
        self.assertEqual(response.content["status_code"], 200)
        self.assertEqual(response.content["data"], {"result": "test_result"})
        self.assertEqual(response.correlation_id, "test_correlation_id")
        
        # Check the request
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        self.assertEqual(kwargs["method"], "GET")
        self.assertEqual(kwargs["url"], "https://api.example.com/test_endpoint")
        self.assertEqual(kwargs["params"], {
            "api_param1": "value1",
            "api_param2": "value2",
            "api_key": "test_key"
        })


class TestBeautifulSoupExtractor(unittest.TestCase):
    """Test the BeautifulSoup Extractor class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.extractor = BeautifulSoupExtractor()
    
    def test_add_rule(self):
        """Test adding an extraction rule."""
        self.extractor.add_rule(
            key="test_key",
            selector="test_selector",
            attribute="test_attribute",
            multiple=True
        )
        
        self.assertIn("test_key", self.extractor.extraction_rules)
        rule = self.extractor.extraction_rules["test_key"]
        self.assertEqual(rule["selector"], "test_selector")
        self.assertEqual(rule["attribute"], "test_attribute")
        self.assertEqual(rule["multiple"], True)
    
    def test_extract(self):
        """Test extracting data."""
        # Add rules
        self.extractor.add_rule(
            key="title",
            selector="h1",
            multiple=False
        )
        self.extractor.add_rule(
            key="links",
            selector="a",
            attribute="href",
            multiple=True
        )
        
        # HTML content
        html_content = """
        <html>
            <head>
                <title>Test Page</title>
            </head>
            <body>
                <h1>Test Title</h1>
                <p>Test paragraph</p>
                <a href="https://example.com">Example</a>
                <a href="https://test.com">Test</a>
            </body>
        </html>
        """
        
        # Extract data
        extracted_data = self.extractor.extract(html_content)
        
        # Check the extracted data
        self.assertEqual(extracted_data["title"], "Test Title")
        self.assertEqual(extracted_data["links"], ["https://example.com", "https://test.com"])


if __name__ == "__main__":
    unittest.main()
