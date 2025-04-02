"""
Data Processor module.
This module provides functionality for processing and enriching extracted data.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional, Union
import logging
import json
import pandas as pd
from ..llm.models import LLMProvider, create_llm_provider

logger = logging.getLogger(__name__)


class DataProcessor(ABC):
    """
    Abstract base class for data processors.
    
    This class defines the interface for processing and enriching extracted data.
    """
    
    @abstractmethod
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and enrich data.
        
        Args:
            data: The data to process
            
        Returns:
            Dict[str, Any]: The processed data
        """
        pass


class BasicProcessor(DataProcessor):
    """
    Basic data processor that performs simple transformations.
    """
    
    def __init__(self, transformations: Dict[str, callable] = None):
        """
        Initialize the basic processor.
        
        Args:
            transformations: Mapping of keys to transformation functions
        """
        self.transformations = transformations or {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data using defined transformations.
        
        Args:
            data: The data to process
            
        Returns:
            Dict[str, Any]: The processed data
        """
        result = data.copy()
        
        for key, transform_func in self.transformations.items():
            if key in result:
                try:
                    result[key] = transform_func(result[key])
                except Exception as e:
                    logger.error(f"Error transforming {key}: {e}")
        
        return result
    
    def add_transformation(self, key: str, transform_func: callable):
        """
        Add a transformation function.
        
        Args:
            key: Key for the data to transform
            transform_func: Function to apply to the data
        """
        self.transformations[key] = transform_func


class LLMProcessor(DataProcessor):
    """
    Data processor that uses LLMs to enrich data.
    """
    
    def __init__(self, llm_provider: LLMProvider = None, enrichment_prompts: Dict[str, str] = None):
        """
        Initialize the LLM processor.
        
        Args:
            llm_provider: LLM provider to use
            enrichment_prompts: Mapping of output keys to prompts
        """
        self.llm_provider = llm_provider or create_llm_provider("openai")
        self.enrichment_prompts = enrichment_prompts or {}
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process and enrich data using LLMs.
        
        Args:
            data: The data to process
            
        Returns:
            Dict[str, Any]: The processed data
        """
        result = data.copy()
        
        for output_key, prompt_template in self.enrichment_prompts.items():
            try:
                # Format the prompt with the data
                prompt = prompt_template.format(**result)
                
                # Generate text with the LLM
                enriched_text = self.llm_provider.generate_text(prompt)
                
                # Add the enriched data
                result[output_key] = enriched_text
            except Exception as e:
                logger.error(f"Error enriching data with key {output_key}: {e}")
        
        return result
    
    def add_enrichment_prompt(self, output_key: str, prompt_template: str):
        """
        Add an enrichment prompt.
        
        Args:
            output_key: Key for the enriched data
            prompt_template: Prompt template with placeholders for data
        """
        self.enrichment_prompts[output_key] = prompt_template


class DataFrameProcessor(DataProcessor):
    """
    Data processor that works with pandas DataFrames.
    """
    
    def __init__(self, dataframe_operations: List[Dict[str, Any]] = None):
        """
        Initialize the DataFrame processor.
        
        Args:
            dataframe_operations: List of operations to perform on DataFrames
        """
        self.dataframe_operations = dataframe_operations or []
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data using pandas operations.
        
        Args:
            data: The data to process, should contain DataFrame objects
            
        Returns:
            Dict[str, Any]: The processed data
        """
        result = data.copy()
        
        for operation in self.dataframe_operations:
            input_key = operation.get('input_key')
            output_key = operation.get('output_key', input_key)
            op_type = operation.get('type')
            params = operation.get('params', {})
            
            if input_key not in result or not isinstance(result[input_key], pd.DataFrame):
                continue
            
            df = result[input_key]
            
            try:
                if op_type == 'filter':
                    # Filter rows
                    column = params.get('column')
                    value = params.get('value')
                    operator = params.get('operator', '==')
                    
                    if column and value is not None:
                        if operator == '==':
                            df = df[df[column] == value]
                        elif operator == '!=':
                            df = df[df[column] != value]
                        elif operator == '>':
                            df = df[df[column] > value]
                        elif operator == '<':
                            df = df[df[column] < value]
                        elif operator == 'in':
                            df = df[df[column].isin(value)]
                
                elif op_type == 'sort':
                    # Sort DataFrame
                    column = params.get('column')
                    ascending = params.get('ascending', True)
                    
                    if column:
                        df = df.sort_values(by=column, ascending=ascending)
                
                elif op_type == 'select':
                    # Select columns
                    columns = params.get('columns', [])
                    
                    if columns:
                        df = df[columns]
                
                elif op_type == 'aggregate':
                    # Aggregate data
                    group_by = params.get('group_by', [])
                    agg_funcs = params.get('agg_funcs', {})
                    
                    if group_by and agg_funcs:
                        df = df.groupby(group_by).agg(agg_funcs).reset_index()
                
                elif op_type == 'transform':
                    # Apply transformation to columns
                    transforms = params.get('transforms', {})
                    
                    for col, func_name in transforms.items():
                        if hasattr(df[col], func_name):
                            df[col] = getattr(df[col], func_name)()
                
                # Store the result
                result[output_key] = df
            
            except Exception as e:
                logger.error(f"Error processing DataFrame with operation {op_type}: {e}")
        
        return result
    
    def add_operation(self, input_key: str, op_type: str, params: Dict[str, Any], output_key: str = None):
        """
        Add a DataFrame operation.
        
        Args:
            input_key: Key for the input DataFrame
            op_type: Type of operation ('filter', 'sort', 'select', 'aggregate', 'transform')
            params: Parameters for the operation
            output_key: Key for the output DataFrame, defaults to input_key
        """
        self.dataframe_operations.append({
            'input_key': input_key,
            'output_key': output_key or input_key,
            'type': op_type,
            'params': params
        })


class CompositeProcessor(DataProcessor):
    """
    Composite processor that combines multiple processors.
    """
    
    def __init__(self, processors: List[DataProcessor] = None):
        """
        Initialize the composite processor.
        
        Args:
            processors: List of processors to use
        """
        self.processors = processors or []
    
    def process(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process data using all registered processors.
        
        Args:
            data: The data to process
            
        Returns:
            Dict[str, Any]: The processed data
        """
        result = data.copy()
        
        for processor in self.processors:
            try:
                result = processor.process(result)
            except Exception as e:
                logger.error(f"Error with processor {processor.__class__.__name__}: {e}")
        
        return result
    
    def add_processor(self, processor: DataProcessor):
        """
        Add a processor.
        
        Args:
            processor: The processor to add
        """
        self.processors.append(processor)
