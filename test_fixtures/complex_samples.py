"""Test fixtures containing more complex Python code samples"""

# Complex class with methods
COMPLEX_CLASS = {
    "metadata": {
        "file": "data_processor.py",
        "name": "DataProcessor",
        "kind": "class",
        "language": "python",
        "range": "1-25"
    },
    "code": """class DataProcessor:
    def __init__(self, data_source):
        self.data_source = data_source
        self.processed_data = []
    
    def load_data(self):
        \"\"\"Load data from the source\"\"\"
        with open(self.data_source, 'r') as f:
            return f.readlines()
    
    def process_data(self, data):
        \"\"\"Process the loaded data\"\"\"
        return [line.strip().lower() for line in data if line.strip()]
    
    def save_processed_data(self, output_file):
        \"\"\"Save processed data to file\"\"\"
        with open(output_file, 'w') as f:
            for item in self.processed_data:
                f.write(f"{item}\\n")"""
}

# Async function fixture
ASYNC_FUNCTION = {
    "metadata": {
        "file": "api_client.py",
        "name": "fetch_user_data",
        "kind": "function",
        "language": "python",
        "range": "15-25"
    },
    "code": """async def fetch_user_data(user_id):
    \"\"\"Fetch user data from API asynchronously\"\"\"
    async with aiohttp.ClientSession() as session:
        async with session.get(f'/api/users/{user_id}') as response:
            if response.status == 200:
                return await response.json()
            else:
                raise Exception(f"Failed to fetch user {user_id}")"""
}

# Decorator function fixture
DECORATOR_FUNCTION = {
    "metadata": {
        "file": "utils.py",
        "name": "timing_decorator",
        "kind": "function", 
        "language": "python",
        "range": "5-15"
    },
    "code": """def timing_decorator(func):
    \"\"\"Decorator to measure function execution time\"\"\"
    import time
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        print(f"{func.__name__} took {end_time - start_time:.4f} seconds")
        return result
    return wrapper"""
}

# Error handling fixture
ERROR_HANDLING_FUNCTION = {
    "metadata": {
        "file": "file_operations.py",
        "name": "safe_file_read",
        "kind": "function",
        "language": "python", 
        "range": "1-12"
    },
    "code": """def safe_file_read(filename):
    \"\"\"Safely read a file with proper error handling\"\"\"
    try:
        with open(filename, 'r') as f:
            return f.read()
    except FileNotFoundError:
        print(f"File {filename} not found")
        return None
    except IOError as e:
        print(f"Error reading file {filename}: {e}")
        return None"""
}

# Collection of complex fixtures
COMPLEX_FIXTURES = [
    COMPLEX_CLASS,
    ASYNC_FUNCTION,
    DECORATOR_FUNCTION,
    ERROR_HANDLING_FUNCTION
]

# Edge case fixtures for testing
EDGE_CASE_FIXTURES = [
    {
        "metadata": {
            "file": "empty.py",
            "name": "empty_function",
            "kind": "function",
            "language": "python",
            "range": "1-2"
        },
        "code": "def empty_function():\n    pass"
    },
    {
        "metadata": {
            "file": "single_line.py",
            "name": "one_liner",
            "kind": "function",
            "language": "python",
            "range": "1-1"
        },
        "code": "def one_liner(x): return x * 2"
    }
]

# All fixtures combined
ALL_COMPLEX_FIXTURES = COMPLEX_FIXTURES + EDGE_CASE_FIXTURES