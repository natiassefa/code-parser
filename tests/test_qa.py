import unittest
import sys
import os
from unittest.mock import patch, MagicMock

# Add parent directory to path to import qa module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qa


class TestQA(unittest.TestCase):
    """Basic test class for QA functionality"""
    
    @classmethod
    def setUpClass(cls):
        """Set up test fixtures once for all tests."""
        cls.fixtures_dir = os.path.join(os.path.dirname(__file__), 'fixtures')
        cls.fixture_files = [
            'calculator.py',
            'data_processor.py', 
            'web_scraper.py'
        ]
        cls.fixtures = cls._load_fixtures()
    
    @classmethod
    def _load_fixtures(cls) -> dict:
        """Load all fixture files into memory."""
        fixtures = {}
        for filename in cls.fixture_files:
            filepath = os.path.join(cls.fixtures_dir, filename)
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    fixtures[filename] = f.read()
            except FileNotFoundError:
                fixtures[filename] = None
        return fixtures
    
    def get_fixture_content(self, filename: str) -> str:
        """Get the content of a specific fixture file."""
        return self.fixtures.get(filename, "")
    
    def create_mock_metadata(self, filename: str, name: str, kind: str, language: str = "python", lines: str = "1-10") -> dict:
        """Helper method to create mock metadata for fixtures."""
        return {
            "file": filename,
            "name": name, 
            "kind": kind,
            "language": language,
            "range": lines
        }
    
    def test_empty_question_handling(self):
        """Test handling of empty or None question input"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }
            
            # Test empty string
            with patch('qa.generate_with_ollama', return_value="No context provided"):
                result = qa.ask("", "test_collection", ".chroma", 5, "ollama", "llama3:latest")
                assert isinstance(result, str)
                mock_collection.query.assert_called_with(query_texts=[""], n_results=5)
            
            # Test whitespace-only string
            with patch('qa.generate_with_ollama', return_value="No context provided"):
                result = qa.ask("   ", "test_collection", ".chroma", 5, "ollama", "llama3:latest")
                assert isinstance(result, str)
                mock_collection.query.assert_called_with(query_texts=["   "], n_results=5)
    
    def test_invalid_backend_handling(self):
        """Test handling of invalid backend parameter"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            mock_collection.query.return_value = {
                "documents": [["test doc"]],
                "metadatas": [[{"file": "test.py", "name": "test", "kind": "function"}]],
                "distances": [[0.5]]
            }
            
            # Test invalid backend
            with self.assertRaisesRegex(ValueError, "Unsupported backend: invalid_backend"):
                qa.ask("test question", "test_collection", ".chroma", 5, "invalid_backend", "model")
    
    def test_invalid_collection_handling(self):
        """Test handling of invalid collection name"""
        with patch('chromadb.PersistentClient') as mock_client:
            # Mock ChromaDB to raise exception for invalid collection
            mock_client.return_value.get_collection.side_effect = Exception("Collection not found")
            
            with self.assertRaisesRegex(Exception, "Collection not found"):
                qa.ask("test question", "nonexistent_collection", ".chroma", 5, "ollama", "llama3:latest")
    
    def test_basic_string_input_handling(self):
        """Test handling of basic valid string inputs"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            mock_collection.query.return_value = {
                "documents": [["def example_function():\n    return 'Hello World'"]],
                "metadatas": [[{
                    "file": "example.py",
                    "name": "example_function",
                    "kind": "function",
                    "language": "python",
                    "range": "1-2"
                }]],
                "distances": [[0.2]]
            }
            
            with patch('qa.generate_with_ollama', return_value="This function returns 'Hello World'") as mock_generate:
                result = qa.ask("What does example_function do?", "test_collection", ".chroma", 5, "ollama", "llama3:latest")
                
                # Verify the function was called with correct parameters
                mock_collection.query.assert_called_with(query_texts=["What does example_function do?"], n_results=5)
                
                # Verify the result is a string
                assert isinstance(result, str)
                assert result == "This function returns 'Hello World'"
                
                # Verify the LLM was called with formatted context
                mock_generate.assert_called_once()
                call_args = mock_generate.call_args
                system_prompt, user_prompt = call_args[0][:2]
                
                assert "You are a senior code assistant" in system_prompt
                assert "What does example_function do?" in user_prompt
                assert "PYTHON function: example_function" in user_prompt
                assert "example.py (lines 1-2)" in user_prompt
    
    def test_basic_code_parsing_functionality(self):
        """Test that basic code parsing works correctly"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Mock response with various code constructs
            mock_collection.query.return_value = {
                "documents": [[
                    "class Calculator:\n    def __init__(self):\n        self.value = 0",
                    "def add(self, x, y):\n    return x + y",
                    "import math\nimport os"
                ]],
                "metadatas": [[
                    {"file": "calculator.py", "name": "Calculator", "kind": "class", "language": "python", "range": "1-3"},
                    {"file": "utils.py", "name": "add", "kind": "function", "language": "python", "range": "5-6"},
                    {"file": "imports.py", "name": "import", "kind": "import", "language": "python", "range": "1-2"}
                ]],
                "distances": [[0.1, 0.3, 0.5]]
            }
            
            with patch('qa.generate_with_ollama', return_value="Found Calculator class and add function") as mock_generate:
                result = qa.ask("Show me the calculator code", "test_collection", ".chroma", 3, "ollama", "llama3:latest")
                
                # Verify query was made
                mock_collection.query.assert_called_with(query_texts=["Show me the calculator code"], n_results=3)
                
                # Verify result is string
                assert isinstance(result, str)
                assert result == "Found Calculator class and add function"
                
                # Verify context formatting includes all types
                call_args = mock_generate.call_args
                user_prompt = call_args[0][1]
                assert "PYTHON class: Calculator" in user_prompt
                assert "PYTHON function: add" in user_prompt
                assert "PYTHON import" in user_prompt
    
    def test_code_analysis_with_multiple_languages(self):
        """Test simple code analysis with multiple programming languages"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Mock response with different languages
            mock_collection.query.return_value = {
                "documents": [[
                    "function processData(data) {\n  return data.map(x => x * 2);\n}",
                    "def process_data(data):\n    return [x * 2 for x in data]",
                    "fn process_data(data: Vec<i32>) -> Vec<i32> {\n    data.iter().map(|x| x * 2).collect()\n}"
                ]],
                "metadatas": [[
                    {"file": "script.js", "name": "processData", "kind": "function", "language": "javascript", "range": "10-12"},
                    {"file": "script.py", "name": "process_data", "kind": "function", "language": "python", "range": "15-16"},
                    {"file": "script.rs", "name": "process_data", "kind": "function", "language": "rust", "range": "20-22"}
                ]],
                "distances": [[0.2, 0.25, 0.3]]
            }
            
            with patch('qa.generate_with_ollama', return_value="All three functions double array elements") as mock_generate:
                result = qa.ask("How do these functions process data?", "test_collection", ".chroma", 3, "ollama", "llama3:latest")
                
                # Verify the analysis worked
                assert isinstance(result, str)
                assert result == "All three functions double array elements"
                
                # Verify context includes all languages
                call_args = mock_generate.call_args
                user_prompt = call_args[0][1]
                assert "JAVASCRIPT function: processData" in user_prompt
                assert "PYTHON function: process_data" in user_prompt  
                assert "RUST function: process_data" in user_prompt
    
    def test_context_formatting_output_structure(self):
        """Test that context formatting produces the expected output format"""
        # Test the format_context function directly
        docs = [
            "def hello_world():\n    print('Hello, World!')",
            "class Person:\n    def __init__(self, name):\n        self.name = name"
        ]
        metas = [
            {"file": "hello.py", "name": "hello_world", "kind": "function", "language": "python", "range": "1-2"},
            {"file": "person.py", "name": "Person", "kind": "class", "language": "python", "range": "5-7"}
        ]
        
        formatted = qa.format_context(docs, metas)
        
        # Verify expected format structure
        assert "[1] PYTHON function: hello_world" in formatted
        assert "hello.py (lines 1-2)" in formatted
        assert "def hello_world():" in formatted
        assert "print('Hello, World!')" in formatted
        
        assert "[2] PYTHON class: Person" in formatted
        assert "person.py (lines 5-7)" in formatted
        assert "class Person:" in formatted
        assert "def __init__(self, name):" in formatted
        
        # Verify separation between blocks
        assert "\n\n" in formatted
        assert "---" in formatted
    
    def test_backend_integration_flow(self):
        """Test the complete flow from query to response for each backend"""
        backends_to_test = ["ollama", "openai", "anthropic"]
        
        for backend in backends_to_test:
            with patch('chromadb.PersistentClient') as mock_client:
                mock_collection = MagicMock()
                mock_client.return_value.get_collection.return_value = mock_collection
                mock_collection.query.return_value = {
                    "documents": [["def test(): pass"]],
                    "metadatas": [[{"file": "test.py", "name": "test", "kind": "function", "language": "python", "range": "1-1"}]],
                    "distances": [[0.1]]
                }
                
                expected_response = f"Response from {backend}"
                
                # Patch the appropriate backend function
                if backend == "ollama":
                    with patch('qa.generate_with_ollama', return_value=expected_response) as mock_generate:
                        result = qa.ask("What does this function do?", "test_collection", ".chroma", 1, backend, "test-model")
                        assert result == expected_response
                        mock_generate.assert_called_once()
                elif backend == "openai":
                    with patch('qa.generate_with_openai', return_value=expected_response) as mock_generate:
                        result = qa.ask("What does this function do?", "test_collection", ".chroma", 1, backend, "test-model")
                        assert result == expected_response
                        mock_generate.assert_called_once()
                elif backend == "anthropic":
                    with patch('qa.generate_with_anthropic', return_value=expected_response) as mock_generate:
                        result = qa.ask("What does this function do?", "test_collection", ".chroma", 1, backend, "test-model")
                        assert result == expected_response
                        mock_generate.assert_called_once()


    def test_fixture_loading(self):
        """Test that fixtures are properly loaded"""
        # Verify fixtures directory exists
        self.assertTrue(os.path.exists(self.fixtures_dir), "Fixtures directory should exist")
        
        # Verify fixture files are loaded
        for filename in self.fixture_files:
            fixture_content = self.get_fixture_content(filename)
            self.assertIsNotNone(fixture_content, f"Fixture {filename} should be loaded")
            self.assertGreater(len(fixture_content), 0, f"Fixture {filename} should have content")
    
    def test_qa_with_calculator_fixture(self):
        """Test QA functionality using calculator fixture"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Use calculator fixture content
            calculator_content = self.get_fixture_content('calculator.py')
            calculator_snippet = calculator_content[:500]  # First 500 chars
            
            mock_collection.query.return_value = {
                "documents": [[calculator_snippet]],
                "metadatas": [[self.create_mock_metadata(
                    "calculator.py", "Calculator", "class", "python", "18-50"
                )]],
                "distances": [[0.1]]
            }
            
            with patch('qa.generate_with_ollama', return_value="The Calculator class provides arithmetic operations") as mock_generate:
                result = qa.ask("What does the Calculator class do?", "test_collection", ".chroma", 1, "ollama", "llama3:latest")
                
                # Verify the query was made
                mock_collection.query.assert_called_with(query_texts=["What does the Calculator class do?"], n_results=1)
                
                # Verify result
                assert isinstance(result, str)
                assert result == "The Calculator class provides arithmetic operations"
                
                # Verify context formatting includes fixture content
                call_args = mock_generate.call_args
                user_prompt = call_args[0][1]
                assert "PYTHON class: Calculator" in user_prompt
                assert "calculator.py" in user_prompt
    
    def test_qa_with_data_processor_fixture(self):
        """Test QA functionality using data processor fixture"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Use data processor fixture content - extract decorator function
            data_processor_content = self.get_fixture_content('data_processor.py')
            lines = data_processor_content.split('\n')
            decorator_lines = []
            in_decorator = False
            for line in lines:
                if 'def timing_decorator' in line:
                    in_decorator = True
                if in_decorator:
                    decorator_lines.append(line)
                    if line.strip() == 'return wrapper':
                        break
            
            decorator_snippet = '\n'.join(decorator_lines)
            
            mock_collection.query.return_value = {
                "documents": [[decorator_snippet]],
                "metadatas": [[self.create_mock_metadata(
                    "data_processor.py", "timing_decorator", "function", "python", "12-22"
                )]],
                "distances": [[0.15]]
            }
            
            with patch('qa.generate_with_ollama', return_value="The timing_decorator measures function execution time") as mock_generate:
                result = qa.ask("How does the timing decorator work?", "test_collection", ".chroma", 1, "ollama", "llama3:latest")
                
                # Verify the query was made
                mock_collection.query.assert_called_with(query_texts=["How does the timing decorator work?"], n_results=1)
                
                # Verify result
                assert isinstance(result, str)
                assert result == "The timing_decorator measures function execution time"
                
                # Verify context formatting
                call_args = mock_generate.call_args
                user_prompt = call_args[0][1]
                assert "PYTHON function: timing_decorator" in user_prompt
                assert "data_processor.py" in user_prompt
    
    def test_qa_with_web_scraper_fixture(self):
        """Test QA functionality using web scraper fixture with async code"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Use web scraper fixture - extract async function
            web_scraper_content = self.get_fixture_content('web_scraper.py')
            lines = web_scraper_content.split('\n')
            async_func_lines = []
            in_function = False
            brace_count = 0
            
            for line in lines:
                if 'async def fetch_url' in line:
                    in_function = True
                if in_function:
                    async_func_lines.append(line)
                    # Simple way to detect end of function
                    if line.strip().startswith('async def ') and 'fetch_url' not in line:
                        break
                    if len(async_func_lines) > 50:  # Limit to reasonable length
                        break
            
            async_snippet = '\n'.join(async_func_lines[:30])  # First 30 lines
            
            mock_collection.query.return_value = {
                "documents": [[async_snippet]],
                "metadatas": [[self.create_mock_metadata(
                    "web_scraper.py", "fetch_url", "function", "python", "85-120"
                )]],
                "distances": [[0.08]]
            }
            
            with patch('qa.generate_with_ollama', return_value="The fetch_url method is an async function for web scraping") as mock_generate:
                result = qa.ask("Explain the fetch_url async function", "test_collection", ".chroma", 1, "ollama", "llama3:latest")
                
                # Verify the query was made
                mock_collection.query.assert_called_with(query_texts=["Explain the fetch_url async function"], n_results=1)
                
                # Verify result
                assert isinstance(result, str)
                assert result == "The fetch_url method is an async function for web scraping"
                
                # Verify context formatting
                call_args = mock_generate.call_args
                user_prompt = call_args[0][1]
                assert "PYTHON function: fetch_url" in user_prompt
                assert "web_scraper.py" in user_prompt
    
    def test_qa_with_multiple_fixtures(self):
        """Test QA functionality using multiple fixtures simultaneously"""
        with patch('chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Get snippets from multiple fixtures
            calc_content = self.get_fixture_content('calculator.py')
            processor_content = self.get_fixture_content('data_processor.py')
            
            # Extract specific functions
            calc_snippet = calc_content[calc_content.find('def add'):calc_content.find('def subtract')]
            processor_snippet = processor_content[processor_content.find('def filter_numbers'):processor_content.find('def _is_numeric')]
            
            mock_collection.query.return_value = {
                "documents": [[calc_snippet, processor_snippet]],
                "metadatas": [[
                    self.create_mock_metadata("calculator.py", "add", "function", "python", "24-28"),
                    self.create_mock_metadata("data_processor.py", "filter_numbers", "function", "python", "40-50")
                ]],
                "distances": [[0.12, 0.18]]
            }
            
            with patch('qa.generate_with_ollama', return_value="Both functions perform mathematical operations on numbers") as mock_generate:
                result = qa.ask("How do these functions handle numbers?", "test_collection", ".chroma", 2, "ollama", "llama3:latest")
                
                # Verify the query was made
                mock_collection.query.assert_called_with(query_texts=["How do these functions handle numbers?"], n_results=2)
                
                # Verify result
                assert isinstance(result, str)
                assert result == "Both functions perform mathematical operations on numbers"
                
                # Verify context formatting includes both fixtures
                call_args = mock_generate.call_args
                user_prompt = call_args[0][1]
                assert "PYTHON function: add" in user_prompt
                assert "PYTHON function: filter_numbers" in user_prompt
                assert "calculator.py" in user_prompt
                assert "data_processor.py" in user_prompt


if __name__ == '__main__':
    unittest.main()