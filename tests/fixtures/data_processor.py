"""
Data processing utilities for handling various data formats.
This fixture demonstrates list comprehensions, decorators, and error handling.
"""

import json
import csv
import functools
from typing import List, Dict, Any, Callable, Optional
from datetime import datetime


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure execution time of functions."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        result = func(*args, **kwargs)
        end_time = datetime.now()
        execution_time = (end_time - start_time).total_seconds()
        print(f"{func.__name__} executed in {execution_time:.4f} seconds")
        return result
    return wrapper


def validate_input(data_type: type) -> Callable:
    """Decorator to validate input types."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for arg in args:
                if not isinstance(arg, data_type):
                    raise TypeError(f"Expected {data_type.__name__}, got {type(arg).__name__}")
            return func(*args, **kwargs)
        return wrapper
    return decorator


class DataProcessor:
    """A utility class for processing various types of data."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.processed_count = 0
        self.errors = []
    
    @timing_decorator
    @validate_input(list)
    def filter_numbers(self, data: List[Any], min_value: float = 0) -> List[float]:
        """Filter numeric values from a list that are above minimum value."""
        try:
            numbers = [float(item) for item in data if isinstance(item, (int, float, str)) and self._is_numeric(item)]
            filtered = [num for num in numbers if num >= min_value]
            self.processed_count += len(filtered)
            return filtered
        except Exception as e:
            self.errors.append(f"Error filtering numbers: {str(e)}")
            return []
    
    def _is_numeric(self, value: Any) -> bool:
        """Check if a value can be converted to a number."""
        try:
            float(value)
            return True
        except (ValueError, TypeError):
            return False
    
    @timing_decorator
    def process_json_data(self, json_string: str) -> Dict[str, Any]:
        """Parse and process JSON data."""
        try:
            data = json.loads(json_string)
            if isinstance(data, dict):
                # Process each value in the dictionary
                processed_data = {}
                for key, value in data.items():
                    if isinstance(value, str) and value.isdigit():
                        processed_data[key] = int(value)
                    elif isinstance(value, list):
                        processed_data[key] = self.filter_numbers(value)
                    else:
                        processed_data[key] = value
                self.processed_count += len(processed_data)
                return processed_data
            return data
        except json.JSONDecodeError as e:
            self.errors.append(f"JSON decode error: {str(e)}")
            return {}
    
    def batch_process(self, data_list: List[Any], processor_func: Callable) -> List[Any]:
        """Process a batch of data using the specified processor function."""
        results = []
        for item in data_list:
            try:
                result = processor_func(item)
                results.append(result)
            except Exception as e:
                self.errors.append(f"Error processing item {item}: {str(e)}")
                results.append(None)
        return results
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get processing statistics."""
        return {
            "processed_count": self.processed_count,
            "error_count": len(self.errors),
            "errors": self.errors.copy()
        }


def transform_data(data: List[Dict[str, Any]], 
                  field_mappings: Dict[str, str]) -> List[Dict[str, Any]]:
    """
    Transform data by renaming fields according to mappings.
    
    Args:
        data: List of dictionaries to transform
        field_mappings: Dictionary mapping old field names to new field names
    
    Returns:
        List of transformed dictionaries
    """
    transformed = []
    for record in data:
        new_record = {}
        for old_key, value in record.items():
            new_key = field_mappings.get(old_key, old_key)
            new_record[new_key] = value
        transformed.append(new_record)
    return transformed


def aggregate_by_field(data: List[Dict[str, Any]], 
                      group_by: str, 
                      aggregate_field: str, 
                      operation: str = 'sum') -> Dict[str, float]:
    """
    Aggregate data by a field using specified operation.
    
    Args:
        data: List of dictionaries to aggregate
        group_by: Field to group by
        aggregate_field: Field to aggregate
        operation: 'sum', 'avg', 'count', 'min', or 'max'
    
    Returns:
        Dictionary with grouped results
    """
    from collections import defaultdict
    
    groups = defaultdict(list)
    for record in data:
        if group_by in record and aggregate_field in record:
            groups[record[group_by]].append(record[aggregate_field])
    
    results = {}
    for key, values in groups.items():
        if operation == 'sum':
            results[key] = sum(values)
        elif operation == 'avg':
            results[key] = sum(values) / len(values) if values else 0
        elif operation == 'count':
            results[key] = len(values)
        elif operation == 'min':
            results[key] = min(values) if values else 0
        elif operation == 'max':
            results[key] = max(values) if values else 0
        else:
            raise ValueError(f"Unsupported operation: {operation}")
    
    return results


# Example usage and test data
SAMPLE_JSON = '''
{
    "users": ["1", "2", "3"],
    "scores": [85.5, 92.0, 78.5, 95.0],
    "metadata": {
        "version": "1.0",
        "created": "2023-01-01"
    }
}
'''

SAMPLE_DATA = [
    {"name": "Alice", "department": "Engineering", "salary": 75000},
    {"name": "Bob", "department": "Sales", "salary": 65000},
    {"name": "Charlie", "department": "Engineering", "salary": 80000},
    {"name": "Diana", "department": "Sales", "salary": 70000}
]