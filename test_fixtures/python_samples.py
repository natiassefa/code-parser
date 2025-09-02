"""Test fixtures containing Python code samples for testing"""

# Sample Python function fixtures
SAMPLE_FUNCTION_1 = {
    "metadata": {
        "file": "calculator.py",
        "name": "add_numbers", 
        "kind": "function",
        "language": "python",
        "range": "1-3"
    },
    "code": "def add_numbers(a, b):\n    \"\"\"Add two numbers and return the result\"\"\"\n    return a + b"
}

SAMPLE_FUNCTION_2 = {
    "metadata": {
        "file": "list_utils.py",
        "name": "filter_evens",
        "kind": "function",
        "language": "python", 
        "range": "1-4"
    },
    "code": """def filter_evens(numbers):
    \"\"\"Filter even numbers from a list\"\"\"
    return [n for n in numbers if n % 2 == 0]"""
}

# Sample Python class fixture
SAMPLE_CLASS_1 = {
    "metadata": {
        "file": "models.py", 
        "name": "Person",
        "kind": "class",
        "language": "python",
        "range": "10-18"
    },
    "code": """class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age
    
    def introduce(self):
        return f"Hi, I'm {self.name} and I'm {self.age} years old\""""
}

# Sample algorithm fixture
SAMPLE_ALGORITHM = {
    "metadata": {
        "file": "algorithms.py",
        "name": "fibonacci", 
        "kind": "function",
        "language": "python",
        "range": "1-5"
    },
    "code": """def fibonacci(n):
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)"""
}

# Collection of all fixtures for easy access
ALL_FIXTURES = [
    SAMPLE_FUNCTION_1,
    SAMPLE_FUNCTION_2,
    SAMPLE_CLASS_1,
    SAMPLE_ALGORITHM
]

# Helper functions for test data
def get_documents_from_fixtures(fixtures):
    """Extract document strings from fixtures"""
    return [fixture["code"] for fixture in fixtures]

def get_metadata_from_fixtures(fixtures):
    """Extract metadata from fixtures"""
    return [fixture["metadata"] for fixture in fixtures]