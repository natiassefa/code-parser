import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock
from qa import ask, main, format_context, generate_with_anthropic, generate_with_openai, generate_with_ollama
import argparse
import sys
from io import StringIO

# Import test fixtures
from test_fixtures.python_samples import (
    SAMPLE_FUNCTION_1, SAMPLE_FUNCTION_2, SAMPLE_CLASS_1, SAMPLE_ALGORITHM,
    ALL_FIXTURES, get_documents_from_fixtures, get_metadata_from_fixtures
)
from test_fixtures.complex_samples import (
    COMPLEX_CLASS, ASYNC_FUNCTION, DECORATOR_FUNCTION, ERROR_HANDLING_FUNCTION,
    COMPLEX_FIXTURES, EDGE_CASE_FIXTURES, ALL_COMPLEX_FIXTURES
)


class TestQA:
    def test_empty_question_handling(self):
        """Test that ask function handles empty question strings"""
        # Mock chromadb client to avoid actual database calls
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Test empty string
            with patch('qa.generate_with_ollama', return_value="No context available"):
                result = ask("", "test_collection", ".test_chroma", 5, "ollama", "test_model")
                assert result == "No context available"
            
            # Test whitespace-only string
            with patch('qa.generate_with_ollama', return_value="No context available"):
                result = ask("   ", "test_collection", ".test_chroma", 5, "ollama", "test_model")
                assert result == "No context available"

    def test_invalid_backend_handling(self):
        """Test that ask function handles invalid backend parameter"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "documents": [["test code"]],
                "metadatas": [[{"file": "test.py", "name": "test_func", "kind": "function", "language": "python", "range": "1-5"}]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Test invalid backend
            with pytest.raises(ValueError, match="Unsupported backend: invalid_backend"):
                ask("test question", "test_collection", ".test_chroma", 5, "invalid_backend", "test_model")

    def test_basic_string_input_handling(self):
        """Test that ask function handles basic string inputs correctly"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "documents": [["def test_func():\n    return 'hello'"]],
                "metadatas": [[{"file": "test.py", "name": "test_func", "kind": "function", "language": "python", "range": "1-2"}]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="This is a test function"):
                result = ask("What does test_func do?", "test_collection", ".test_chroma", 5, "ollama", "test_model")
                assert result == "This is a test function"
                
                # Verify the query was called with the question
                mock_collection.query.assert_called_with(query_texts=["What does test_func do?"], n_results=5)

    def test_main_with_empty_question_arg(self):
        """Test main function handling of empty question argument"""
        # Test that main handles empty question by starting REPL mode
        test_args = ["qa.py", "--question", ""]
        
        with patch('sys.argv', test_args):
            with patch('qa.chromadb.PersistentClient') as mock_client:
                mock_collection = MagicMock()
                mock_collection.query.return_value = {
                    "documents": [[]],
                    "metadatas": [[]]
                }
                mock_client.return_value.get_collection.return_value = mock_collection
                
                with patch('qa.generate_with_ollama', return_value="No context"):
                    with patch('sys.stdout', new=StringIO()) as fake_out:
                        main()
                        output = fake_out.getvalue()
                        assert "No context" in output

    def test_main_repl_empty_input(self):
        """Test REPL mode handling of empty input"""
        # Mock input to simulate empty input followed by exit
        with patch('builtins.input', side_effect=["", "   ", "exit"]):
            with patch('sys.stdout', new=StringIO()) as fake_out:
                with patch('sys.argv', ["qa.py"]):  # No question arg to trigger REPL
                    main()
                    output = fake_out.getvalue()
                    assert "RAG REPL" in output

    def test_invalid_collection_name_handling(self):
        """Test that ask function handles invalid collection names"""
        # Mock chromadb to raise an error for non-existent collection
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_client.return_value.get_collection.side_effect = Exception("Collection 'nonexistent' does not exist")
            
            with pytest.raises(Exception, match="Collection 'nonexistent' does not exist"):
                ask("test question", "nonexistent", ".test_chroma", 5, "ollama", "test_model")

    def test_invalid_persist_directory_handling(self):
        """Test that ask function handles invalid persist directory paths"""
        # Mock chromadb to raise an error for invalid persist directory
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_client.side_effect = Exception("Invalid persist directory")
            
            with pytest.raises(Exception, match="Invalid persist directory"):
                ask("test question", "test_collection", "/nonexistent/path", 5, "ollama", "test_model")

    def test_chromadb_connection_error_handling(self):
        """Test handling when ChromaDB is not accessible"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_client.side_effect = Exception("Could not connect to ChromaDB")
            
            with pytest.raises(Exception, match="Could not connect to ChromaDB"):
                ask("test question", "test_collection", ".test_chroma", 5, "ollama", "test_model")

    # Core functionality tests as required by the prompt
    def test_basic_code_parsing_works(self):
        """Test that basic code parsing works correctly using fixtures"""
        # Use fixture data
        sample_docs = [SAMPLE_FUNCTION_1["code"]]
        sample_metadata = [SAMPLE_FUNCTION_1["metadata"]]
        
        result = format_context(sample_docs, sample_metadata)
        
        # Verify basic parsing works
        assert "PYTHON function: add_numbers" in result
        assert "calculator.py" in result
        assert "lines 1-3" in result
        assert "def add_numbers(a, b):" in result
        assert "return a + b" in result

    def test_expected_output_format_is_correct(self):
        """Test that expected output format is correct"""
        sample_metadata = [{
            "file": "utils.py",
            "name": "process_data",
            "kind": "function", 
            "language": "python",
            "range": "10-15"
        }]
        sample_docs = ["def process_data(data):\n    return data.strip().lower()"]
        
        result = format_context(sample_docs, sample_metadata)
        
        # Verify correct format structure
        assert result.startswith("[1] PYTHON function: process_data in utils.py (lines 10-15)")
        assert "\n---\n" in result
        assert result.endswith("def process_data(data):\n    return data.strip().lower()")
        
        # Test with multiple items to verify numbering
        double_metadata = [
            {
                "file": "math.py",
                "name": "multiply", 
                "kind": "function",
                "language": "python", 
                "range": "1-2"
            },
            {
                "file": "string_utils.py", 
                "name": "capitalize_words",
                "kind": "function",
                "language": "python",
                "range": "5-8" 
            }
        ]
        double_docs = [
            "def multiply(x, y):\n    return x * y",
            "def capitalize_words(text):\n    return text.title()"
        ]
        
        result = format_context(double_docs, double_metadata)
        assert "[1] PYTHON function: multiply" in result
        assert "[2] PYTHON function: capitalize_words" in result
        assert result.count("\n\n") == 1  # Proper separation between entries

    def test_python_code_sample_1(self):
        """Test first valid Python code sample - list processing function using fixtures"""
        sample_docs = [SAMPLE_FUNCTION_2["code"]]
        sample_metadata = [SAMPLE_FUNCTION_2["metadata"]]
        
        result = format_context(sample_docs, sample_metadata)
        
        # Verify parsing of this Python code sample
        assert "PYTHON function: filter_evens" in result
        assert "list_utils.py" in result
        assert "def filter_evens(numbers):" in result
        assert "return [n for n in numbers if n % 2 == 0]" in result
        assert "Filter even numbers from a list" in result

    def test_python_code_sample_2(self):
        """Test second valid Python code sample - class definition using fixtures"""
        sample_docs = [SAMPLE_CLASS_1["code"]]
        sample_metadata = [SAMPLE_CLASS_1["metadata"]]
        
        result = format_context(sample_docs, sample_metadata)
        
        # Verify parsing of this Python code sample 
        assert "PYTHON class: Person" in result
        assert "models.py" in result
        assert "class Person:" in result
        assert "def __init__(self, name, age):" in result
        assert "def introduce(self):" in result
        assert "return f\"Hi, I'm {self.name}" in result

    def test_core_parsing_integration(self):
        """Test core parsing functionality with integration to ask function using fixtures"""
        # Mock ChromaDB to return Python code samples using fixtures
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = MagicMock()
            mock_collection.query.return_value = {
                "documents": [[SAMPLE_ALGORITHM["code"]]],
                "metadatas": [[SAMPLE_ALGORITHM["metadata"]]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="This function calculates fibonacci numbers recursively") as mock_generate:
                result = ask("What does fibonacci function do?", "code_chunks", ".chroma", 5, "ollama", "llama3")
                
                # Verify the integration works
                assert result == "This function calculates fibonacci numbers recursively"
                
                # Verify format_context was called with correct data
                call_args = mock_generate.call_args[0][1]  # Get user prompt
                assert "PYTHON function: fibonacci" in call_args
                assert "algorithms.py" in call_args
                assert "def fibonacci(n):" in call_args

    def test_multiple_fixtures_loading(self):
        """Test loading multiple fixtures at once"""
        docs = get_documents_from_fixtures(ALL_FIXTURES[:3])
        metadata = get_metadata_from_fixtures(ALL_FIXTURES[:3])
        
        result = format_context(docs, metadata)
        
        # Verify all three fixtures are properly formatted
        assert "[1] PYTHON function: add_numbers" in result
        assert "[2] PYTHON function: filter_evens" in result
        assert "[3] PYTHON class: Person" in result

    def test_complex_fixtures_parsing(self):
        """Test parsing of complex fixtures like async functions and decorators"""
        # Test async function fixture
        async_docs = [ASYNC_FUNCTION["code"]]
        async_metadata = [ASYNC_FUNCTION["metadata"]]
        
        result = format_context(async_docs, async_metadata)
        assert "PYTHON function: fetch_user_data" in result
        assert "async def fetch_user_data" in result
        assert "api_client.py" in result

        # Test decorator fixture
        decorator_docs = [DECORATOR_FUNCTION["code"]]
        decorator_metadata = [DECORATOR_FUNCTION["metadata"]]
        
        result = format_context(decorator_docs, decorator_metadata)
        assert "PYTHON function: timing_decorator" in result
        assert "def timing_decorator(func):" in result
        assert "utils.py" in result

    def test_edge_case_fixtures(self):
        """Test edge case fixtures like empty functions and one-liners"""
        edge_docs = get_documents_from_fixtures(EDGE_CASE_FIXTURES)
        edge_metadata = get_metadata_from_fixtures(EDGE_CASE_FIXTURES)
        
        result = format_context(edge_docs, edge_metadata)
        
        # Verify edge cases are handled correctly
        assert "PYTHON function: empty_function" in result
        assert "PYTHON function: one_liner" in result
        assert "def empty_function():" in result
        assert "def one_liner(x): return x * 2" in result

    def test_fixture_helper_functions(self):
        """Test the fixture helper functions work correctly"""
        # Test get_documents_from_fixtures
        docs = get_documents_from_fixtures([SAMPLE_FUNCTION_1, SAMPLE_CLASS_1])
        assert len(docs) == 2
        assert "def add_numbers(a, b):" in docs[0]
        assert "class Person:" in docs[1]
        
        # Test get_metadata_from_fixtures
        metadata = get_metadata_from_fixtures([SAMPLE_FUNCTION_1, SAMPLE_CLASS_1])
        assert len(metadata) == 2
        assert metadata[0]["name"] == "add_numbers"
        assert metadata[1]["name"] == "Person"