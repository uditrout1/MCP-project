"""
Data Extractor module.
This module provides functionality for extracting structured data from web pages.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import logging
import re
import json
from bs4 import BeautifulSoup
import pandas as pd

logger = logging.getLogger(__name__)


class DataExtractor(ABC):
    """
    Abstract base class for data extractors.
    
    This class defines the interface for extracting data from web pages.
    """
    
    @abstractmethod
    def extract(self, html_content: str) -> Dict[str, Any]:
        """
        Extract data from HTML content.
        
        Args:
            html_content: The HTML content to extract data from
            
        Returns:
            Dict[str, Any]: The extracted data
        """
        pass


class BeautifulSoupExtractor(DataExtractor):
    """
    Data extractor using BeautifulSoup.
    """
    
    def __init__(self, extraction_rules: Dict[str, Any] = None):
        """
        Initialize the BeautifulSoup extractor.
        
        Args:
            extraction_rules: Rules for extracting data
        """
        self.extraction_rules = extraction_rules or {}
    
    def extract(self, html_content: str) -> Dict[str, Any]:
        """
        Extract data from HTML content using BeautifulSoup.
        
        Args:
            html_content: The HTML content to extract data from
            
        Returns:
            Dict[str, Any]: The extracted data
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        result = {}
        
        # Apply extraction rules
        for key, rule in self.extraction_rules.items():
            selector = rule.get('selector')
            attribute = rule.get('attribute')
            multiple = rule.get('multiple', False)
            
            if not selector:
                continue
            
            try:
                if multiple:
                    elements = soup.select(selector)
                    if attribute:
                        result[key] = [elem.get(attribute) for elem in elements if elem.get(attribute)]
                    else:
                        result[key] = [elem.get_text(strip=True) for elem in elements]
                else:
                    element = soup.select_one(selector)
                    if element:
                        if attribute:
                            result[key] = element.get(attribute)
                        else:
                            result[key] = element.get_text(strip=True)
            except Exception as e:
                logger.error(f"Error extracting {key} with rule {rule}: {e}")
        
        return result
    
    def add_rule(self, key: str, selector: str, attribute: str = None, multiple: bool = False):
        """
        Add an extraction rule.
        
        Args:
            key: Key for the extracted data
            selector: CSS selector for the element(s)
            attribute: Attribute to extract, or None for text content
            multiple: Whether to extract multiple elements
        """
        self.extraction_rules[key] = {
            'selector': selector,
            'attribute': attribute,
            'multiple': multiple
        }
    
    def extract_table(self, html_content: str, table_selector: str = 'table') -> Optional[pd.DataFrame]:
        """
        Extract a table from HTML content.
        
        Args:
            html_content: The HTML content to extract from
            table_selector: CSS selector for the table
            
        Returns:
            Optional[pd.DataFrame]: The extracted table as a DataFrame, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            tables = pd.read_html(str(soup.select_one(table_selector)))
            if tables:
                return tables[0]
            return None
        except Exception as e:
            logger.error(f"Error extracting table with selector {table_selector}: {e}")
            return None


class JSONExtractor(DataExtractor):
    """
    Data extractor for JSON data embedded in web pages.
    """
    
    def __init__(self, json_paths: Dict[str, str] = None):
        """
        Initialize the JSON extractor.
        
        Args:
            json_paths: Mapping of output keys to JSON paths
        """
        self.json_paths = json_paths or {}
    
    def extract(self, html_content: str) -> Dict[str, Any]:
        """
        Extract JSON data from HTML content.
        
        Args:
            html_content: The HTML content to extract data from
            
        Returns:
            Dict[str, Any]: The extracted data
        """
        result = {}
        
        # Try to find JSON in script tags
        soup = BeautifulSoup(html_content, 'html.parser')
        script_tags = soup.find_all('script')
        
        json_objects = []
        
        # Extract JSON from script tags
        for script in script_tags:
            script_content = script.string
            if not script_content:
                continue
            
            # Look for JSON objects
            json_matches = re.findall(r'(\{.*?\}|\[.*?\])', script_content, re.DOTALL)
            for json_str in json_matches:
                try:
                    json_obj = json.loads(json_str)
                    json_objects.append(json_obj)
                except json.JSONDecodeError:
                    pass
        
        # Apply JSON paths to extracted objects
        for key, path in self.json_paths.items():
            for json_obj in json_objects:
                value = self._get_by_path(json_obj, path)
                if value is not None:
                    result[key] = value
                    break
        
        return result
    
    def _get_by_path(self, json_obj: Dict[str, Any], path: str) -> Any:
        """
        Get a value from a JSON object by path.
        
        Args:
            json_obj: The JSON object
            path: The path to the value (e.g., "data.items[0].name")
            
        Returns:
            Any: The value at the path, or None if not found
        """
        try:
            parts = path.split('.')
            current = json_obj
            
            for part in parts:
                # Handle array indexing
                if '[' in part and ']' in part:
                    key, index_str = part.split('[', 1)
                    index = int(index_str.rstrip(']'))
                    current = current.get(key, [])[index]
                else:
                    current = current.get(part)
                
                if current is None:
                    return None
            
            return current
        except (KeyError, IndexError, TypeError):
            return None
    
    def add_path(self, key: str, path: str):
        """
        Add a JSON path.
        
        Args:
            key: Key for the extracted data
            path: JSON path to the value
        """
        self.json_paths[key] = path


class RegexExtractor(DataExtractor):
    """
    Data extractor using regular expressions.
    """
    
    def __init__(self, patterns: Dict[str, str] = None):
        """
        Initialize the regex extractor.
        
        Args:
            patterns: Mapping of output keys to regex patterns
        """
        self.patterns = patterns or {}
    
    def extract(self, html_content: str) -> Dict[str, Any]:
        """
        Extract data from HTML content using regex.
        
        Args:
            html_content: The HTML content to extract data from
            
        Returns:
            Dict[str, Any]: The extracted data
        """
        result = {}
        
        for key, pattern in self.patterns.items():
            try:
                matches = re.findall(pattern, html_content)
                if matches:
                    # If the pattern has groups, use the first group
                    if isinstance(matches[0], tuple):
                        result[key] = matches[0][0]
                    else:
                        result[key] = matches[0]
            except Exception as e:
                logger.error(f"Error extracting {key} with pattern {pattern}: {e}")
        
        return result
    
    def add_pattern(self, key: str, pattern: str):
        """
        Add a regex pattern.
        
        Args:
            key: Key for the extracted data
            pattern: Regex pattern to match
        """
        self.patterns[key] = pattern


class CompositeExtractor(DataExtractor):
    """
    Composite extractor that combines multiple extractors.
    """
    
    def __init__(self, extractors: List[DataExtractor] = None):
        """
        Initialize the composite extractor.
        
        Args:
            extractors: List of extractors to use
        """
        self.extractors = extractors or []
    
    def extract(self, html_content: str) -> Dict[str, Any]:
        """
        Extract data using all registered extractors.
        
        Args:
            html_content: The HTML content to extract data from
            
        Returns:
            Dict[str, Any]: The combined extracted data
        """
        result = {}
        
        for extractor in self.extractors:
            try:
                extracted_data = extractor.extract(html_content)
                result.update(extracted_data)
            except Exception as e:
                logger.error(f"Error with extractor {extractor.__class__.__name__}: {e}")
        
        return result
    
    def add_extractor(self, extractor: DataExtractor):
        """
        Add an extractor.
        
        Args:
            extractor: The extractor to add
        """
        self.extractors.append(extractor)
