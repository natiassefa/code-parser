import sys
import os
from unittest.mock import Mock, patch, MagicMock

# Add parent directory to path to import qa.py
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import qa


class TestQA:
    
    def test_empty_input_handling(self):
        """Test that ask function handles empty question input"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            # Mock the chromadb collection
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Mock the LLM backend
            with patch('qa.generate_with_ollama', return_value="I don't know based on the provided context.") as mock_llm:
                result = qa.ask("", "test_collection", ".test_chroma", 5, "ollama", "llama3:latest")
                
                # Verify the function completes without error
                assert isinstance(result, str)
                # Verify collection was queried with empty string
                mock_collection.query.assert_called_once_with(query_texts=[""], n_results=5)
    
    def test_invalid_input_type_handling(self):
        """Test that ask function handles invalid input types"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="Test response") as mock_llm:
                # Test with None input - should convert to string
                result = qa.ask(None, "test_collection", ".test_chroma", 5, "ollama", "llama3:latest")
                assert isinstance(result, str)
                
                # Test with number input - should convert to string
                result = qa.ask(123, "test_collection", ".test_chroma", 5, "ollama", "llama3:latest")
                assert isinstance(result, str)
                
                # Test with list input - should convert to string
                result = qa.ask(["test"], "test_collection", ".test_chroma", 5, "ollama", "llama3:latest")
                assert isinstance(result, str)
    
    def test_basic_string_input_works(self):
        """Test that ask function works correctly with basic string input"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            # Mock successful query response
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def test_function():\n    return 'hello'"]],
                "metadatas": [[{"file": "test.py", "name": "test_function", "kind": "function", "language": "python", "range": "1-2"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Mock LLM response
            with patch('qa.generate_with_ollama', return_value="This function returns 'hello'") as mock_llm:
                result = qa.ask("What does test_function do?", "test_collection", ".test_chroma", 5, "ollama", "llama3:latest")
                
                # Verify the function returns expected result
                assert result == "This function returns 'hello'"
                
                # Verify collection was queried correctly
                mock_collection.query.assert_called_once_with(query_texts=["What does test_function do?"], n_results=5)
                
                # Verify LLM was called with formatted context
                mock_llm.assert_called_once()
                args = mock_llm.call_args[0]
                assert "What does test_function do?" in args[1]  # user_prompt contains question
                assert "test_function" in args[1]  # context is formatted correctly

class TestFormatContext:
    
    def test_format_context_empty_inputs(self):
        """Test format_context function with empty inputs"""
        result = qa.format_context([], [])
        assert result == ""
    
    def test_format_context_valid_inputs(self):
        """Test format_context function with valid inputs"""
        docs = ["def hello():\n    return 'world'"]
        metas = [{
            "file": "example.py", 
            "name": "hello", 
            "kind": "function", 
            "language": "python",
            "range": "1-2"
        }]
        
        result = qa.format_context(docs, metas)
        
        # Verify the formatted output contains expected elements
        assert "[1] PYTHON function: hello" in result
        assert "example.py (lines 1-2)" in result
        assert "def hello():" in result
        assert "return 'world'" in result
        
    def test_format_context_unnamed_construct(self):
        """Test format_context function with unnamed constructs"""
        docs = ["if x > 0:\n    print(x)"]
        metas = [{
            "file": "test.py",
            "name": "if",
            "kind": "if",
            "language": "python", 
            "range": "5-6"
        }]
        
        result = qa.format_context(docs, metas)
        
        # Should use generic format for unnamed constructs
        assert "[1] PYTHON if" in result
        assert "hello" not in result  # Should not include the name for generic constructs
        assert "test.py (lines 5-6)" in result


class TestQuestionExtraction:
    
    def test_question_extraction_from_string(self):
        """Test that questions are properly extracted from string input"""
        question = "What does the main function do?"
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def main(): pass"]],
                "metadatas": [[{"file": "main.py", "name": "main", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="Test response") as mock_llm:
                qa.ask(question, "test_collection", ".test_chroma", 5, "ollama", "llama3:latest")
                
                # Verify the question was passed correctly to the query
                mock_collection.query.assert_called_once_with(query_texts=[question], n_results=5)
                
                # Verify the question appears in the user prompt
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert question in user_prompt
    
    def test_question_extraction_with_special_characters(self):
        """Test question extraction with special characters and formatting"""
        question = "What does func() -> List[str] return?"
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def func() -> List[str]: return []"]],
                "metadatas": [[{"file": "test.py", "name": "func", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value="Test response") as mock_llm:
                qa.ask(question, "test_collection", ".test_chroma", 3, "anthropic", "claude-3-5-sonnet")
                
                # Verify special characters are preserved in query
                mock_collection.query.assert_called_once_with(query_texts=[question], n_results=3)
                
                # Verify question formatting in prompt
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "What does func() -> List[str] return?" in user_prompt


class TestAnswerExtraction:
    
    def test_answer_extraction_from_llm_response(self):
        """Test that answers are properly extracted from LLM responses"""
        expected_answer = "The main function initializes the application and starts the main loop."
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def main(): app.run()"]],
                "metadatas": [[{"file": "app.py", "name": "main", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_openai', return_value=expected_answer) as mock_llm:
                result = qa.ask("What does main do?", "test_collection", ".test_chroma", 5, "openai", "gpt-4o-mini")
                
                # Verify the answer is returned correctly
                assert result == expected_answer
                
                # Verify LLM was called once
                mock_llm.assert_called_once()
    
    def test_answer_extraction_with_citations(self):
        """Test answer extraction when response includes citations"""
        answer_with_citations = "Based on app.py:1-1, the main function starts the application by calling app.run()."
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def main():\n    app.run()"]],
                "metadatas": [[{"file": "app.py", "name": "main", "kind": "function", "language": "python", "range": "1-2"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value=answer_with_citations) as mock_llm:
                result = qa.ask("What does main do?", "test_collection", ".test_chroma", 5, "anthropic", "claude-3-5-sonnet")
                
                # Verify the full answer with citations is preserved
                assert result == answer_with_citations
                assert "app.py:1-1" in result
                assert "app.run()" in result
    
    def test_answer_extraction_unknown_context(self):
        """Test answer extraction when LLM responds with unknown context"""
        unknown_response = "I don't know based on the provided context."
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value=unknown_response) as mock_llm:
                result = qa.ask("What is quantum computing?", "test_collection", ".test_chroma", 5, "ollama", "llama3:latest")
                
                # Verify the "don't know" response is returned correctly
                assert result == unknown_response


class TestQAPairFormatting:
    
    def test_complete_qa_pair_formatting(self):
        """Test that complete QA pairs are formatted correctly"""
        question = "How does the user authentication work?"
        expected_answer = "The authenticate_user function in auth.py:15-25 validates credentials using bcrypt hashing."
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def authenticate_user(username, password):\n    # Validation logic\n    return bcrypt.checkpw(password, hashed)"]],
                "metadatas": [[{
                    "file": "auth.py", 
                    "name": "authenticate_user", 
                    "kind": "function", 
                    "language": "python",
                    "range": "15-25"
                }]],
                "distances": [[0.2]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value=expected_answer) as mock_llm:
                result = qa.ask(question, "test_collection", ".test_chroma", 3, "anthropic", "claude-3-5-sonnet")
                
                # Verify QA pair components are present
                assert result == expected_answer
                
                # Verify the user prompt was formatted correctly with question and context
                mock_llm.assert_called_once()
                system_prompt, user_prompt = mock_llm.call_args[0]
                
                # Check question is in user prompt
                assert question in user_prompt
                
                # Check context formatting includes all required elements
                assert "[1] PYTHON function: authenticate_user" in user_prompt
                assert "auth.py (lines 15-25)" in user_prompt
                assert "def authenticate_user(username, password):" in user_prompt
                assert "bcrypt.checkpw" in user_prompt
                
                # Check proper template structure
                assert "Question:" in user_prompt
                assert "Context (top 3 results):" in user_prompt
                assert "Instructions:" in user_prompt
    
    def test_qa_pair_formatting_with_multiple_contexts(self):
        """Test QA pair formatting with multiple context results"""
        question = "What are the main database operations?"
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [
                    "def create_user(data): db.insert('users', data)",
                    "def get_user(id): return db.select('users', id)",
                    "def update_user(id, data): db.update('users', id, data)"
                ],
                "metadatas": [[
                    {"file": "db.py", "name": "create_user", "kind": "function", "language": "python", "range": "10-11"},
                    {"file": "db.py", "name": "get_user", "kind": "function", "language": "python", "range": "13-14"},
                    {"file": "db.py", "name": "update_user", "kind": "function", "language": "python", "range": "16-17"}
                ]],
                "distances": [[0.1, 0.2, 0.3]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_openai', return_value="CRUD operations: create, read, update") as mock_llm:
                result = qa.ask(question, "test_collection", ".test_chroma", 3, "openai", "gpt-4o-mini")
                
                # Verify all contexts are properly formatted
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                
                # Check all three contexts appear with proper numbering
                assert "[1] PYTHON function: create_user" in user_prompt
                assert "[2] PYTHON function: get_user" in user_prompt  
                assert "[3] PYTHON function: update_user" in user_prompt
                
                # Check all file references are correct
                assert "db.py (lines 10-11)" in user_prompt
                assert "db.py (lines 13-14)" in user_prompt
                assert "db.py (lines 16-17)" in user_prompt
                
                # Check all code snippets are included
                assert "def create_user(data):" in user_prompt
                assert "def get_user(id):" in user_prompt
                assert "def update_user(id, data):" in user_prompt
    
    def test_qa_pair_formatting_edge_cases(self):
        """Test QA pair formatting with edge cases like missing metadata"""
        question = "What is this code doing?"
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": ["x = 42"],
                "metadatas": [[{
                    "file": "script.py",
                    "name": "assignment", 
                    "kind": "assignment",
                    "language": "python",
                    "range": "5-5"
                }]],
                "distances": [[0.5]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="This assigns value 42 to variable x") as mock_llm:
                result = qa.ask(question, "test_collection", ".test_chroma", 1, "ollama", "mistral:7b")
                
                # Verify assignment construct is handled as unnamed (generic format)
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                
                # Should use generic format for assignment (unnamed construct)
                assert "[1] PYTHON assignment" in user_prompt
                assert "assignment: assignment" not in user_prompt  # Should not double the name
                assert "script.py (lines 5-5)" in user_prompt
                assert "x = 42" in user_prompt


class TestRetrievalFunctionality:
    
    def test_chromadb_query_parameters(self):
        """Test that ChromaDB query is called with correct parameters"""
        question = "How do I initialize the app?"
        collection_name = "my_code_collection"
        top_k = 7
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def init_app(): pass"]],
                "metadatas": [[{"file": "app.py", "name": "init_app", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="Test response") as mock_llm:
                qa.ask(question, collection_name, ".test_chroma", top_k, "ollama", "llama3:latest")
                
                # Verify PersistentClient was initialized with correct path
                mock_client.assert_called_once_with(path="./.chroma_db")
                
                # Verify get_collection was called with correct collection name
                mock_client.return_value.get_collection.assert_called_once_with(collection_name)
                
                # Verify query was called with correct parameters
                mock_collection.query.assert_called_once_with(query_texts=[question], n_results=top_k)
    
    def test_retrieval_with_empty_results(self):
        """Test retrieval behavior when no documents are found"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [[]],
                "metadatas": [[]],
                "distances": [[]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value="No relevant code found") as mock_llm:
                result = qa.ask("Unknown topic", "test_collection", ".test_chroma", 5, "anthropic", "claude-3-5-sonnet")
                
                # Should still call LLM even with empty results
                mock_llm.assert_called_once()
                
                # Verify user prompt contains empty context
                user_prompt = mock_llm.call_args[0][1]
                assert "Unknown topic" in user_prompt
                assert "Context (top 5 results):" in user_prompt
    
    def test_retrieval_metadata_processing(self):
        """Test that retrieved metadata is properly processed and passed to context formatting"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            test_metadata = {
                "file": "utils.py",
                "name": "helper_func", 
                "kind": "function",
                "language": "python",
                "range": "42-50"
            }
            mock_collection.query.return_value = {
                "documents": [["def helper_func(): return True"]],
                "metadatas": [[test_metadata]],
                "distances": [[0.3]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_openai', return_value="Helper function") as mock_llm:
                qa.ask("What is helper_func?", "test_collection", ".test_chroma", 1, "openai", "gpt-4o-mini")
                
                # Verify metadata is properly formatted in context
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                
                # Check all metadata fields are included in formatted context
                assert "[1] PYTHON function: helper_func" in user_prompt
                assert "utils.py (lines 42-50)" in user_prompt
                assert "def helper_func(): return True" in user_prompt


class TestLLMBackends:
    
    def test_openai_backend(self):
        """Test that OpenAI backend is called correctly"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["test code"]],
                "metadatas": [[{"file": "test.py", "name": "test", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_openai', return_value="OpenAI response") as mock_openai:
                result = qa.ask("Test question", "test_collection", ".test_chroma", 3, "openai", "gpt-4o-mini")
                
                # Verify OpenAI backend was called
                mock_openai.assert_called_once()
                
                # Verify correct parameters were passed
                system_prompt, user_prompt = mock_openai.call_args[0]
                assert system_prompt == qa.SYSTEM_PROMPT
                assert "Test question" in user_prompt
                assert result == "OpenAI response"
    
    def test_anthropic_backend(self):
        """Test that Anthropic backend is called correctly"""  
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["test code"]],
                "metadatas": [[{"file": "test.py", "name": "test", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value="Anthropic response") as mock_anthropic:
                result = qa.ask("Test question", "test_collection", ".test_chroma", 3, "anthropic", "claude-3-5-sonnet")
                
                # Verify Anthropic backend was called
                mock_anthropic.assert_called_once()
                
                # Verify correct parameters were passed 
                system_prompt, user_prompt = mock_anthropic.call_args[0]
                assert system_prompt == qa.SYSTEM_PROMPT
                assert "Test question" in user_prompt
                assert result == "Anthropic response"
    
    def test_ollama_backend(self):
        """Test that Ollama backend is called correctly"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["test code"]],
                "metadatas": [[{"file": "test.py", "name": "test", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="Ollama response") as mock_ollama:
                result = qa.ask("Test question", "test_collection", ".test_chroma", 3, "ollama", "mistral:7b")
                
                # Verify Ollama backend was called
                mock_ollama.assert_called_once()
                
                # Verify correct parameters were passed including model
                system_prompt, user_prompt, model = mock_ollama.call_args[0]
                assert system_prompt == qa.SYSTEM_PROMPT
                assert "Test question" in user_prompt
                assert model == "mistral:7b"
                assert result == "Ollama response"
    
    def test_unsupported_backend_error(self):
        """Test that unsupported backend raises ValueError"""
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["test code"]],
                "metadatas": [[{"file": "test.py", "name": "test", "kind": "function", "language": "python", "range": "1-1"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            # Test unsupported backend
            try:
                qa.ask("Test question", "test_collection", ".test_chroma", 3, "unsupported", "model")
                assert False, "Should have raised ValueError"
            except ValueError as e:
                assert "Unsupported backend: unsupported" in str(e)


class TestEdgeCaseInputs:
    """Test edge cases for non-standard inputs as specified in requirements"""
    
    def test_multiline_question_input(self):
        """Test that ask function handles multi-line question inputs correctly"""
        multiline_question = """How does the authentication system work?
        
        Specifically, I want to know:
        - How are passwords validated?
        - What hashing algorithm is used?
        - Are there any rate limiting mechanisms?"""
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def authenticate(user, password):\n    return bcrypt.checkpw(password, hash)"]],
                "metadatas": [[{"file": "auth.py", "name": "authenticate", "kind": "function", "language": "python", "range": "10-12"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value="Authentication uses bcrypt hashing") as mock_llm:
                result = qa.ask(multiline_question, "test_collection", ".test_chroma", 3, "anthropic", "claude-3-5-sonnet")
                
                # Verify multi-line question is preserved in query
                mock_collection.query.assert_called_once_with(query_texts=[multiline_question], n_results=3)
                
                # Verify complete multi-line question appears in user prompt
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "How does the authentication system work?" in user_prompt
                assert "How are passwords validated?" in user_prompt
                assert "What hashing algorithm is used?" in user_prompt
                assert "Are there any rate limiting mechanisms?" in user_prompt
                
                # Verify function completes successfully
                assert isinstance(result, str)
                assert result == "Authentication uses bcrypt hashing"
    
    def test_question_with_code_blocks(self):
        """Test questions containing code block formatting"""
        question_with_code = """What does this function do?
        
        ```python
        def process_data(data):
            return [x * 2 for x in data]
        ```
        
        Is it similar to any function in the codebase?"""
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def transform_data(items):\n    return [item * 2 for item in items]"]],
                "metadatas": [[{"file": "utils.py", "name": "transform_data", "kind": "function", "language": "python", "range": "5-6"}]],
                "distances": [[0.2]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="Similar to transform_data function") as mock_llm:
                result = qa.ask(question_with_code, "test_collection", ".test_chroma", 3, "ollama", "llama3:latest")
                
                # Verify code formatting is preserved
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "```python" in user_prompt
                assert "def process_data(data):" in user_prompt
                assert "[x * 2 for x in data]" in user_prompt
                assert "```" in user_prompt
                
                assert result == "Similar to transform_data function"
    
    def test_special_characters_and_unicode(self):
        """Test that ask function handles special characters and unicode correctly"""
        special_question = "How does the función_especial() handle données with émojis 🚀 and symbols like @#$%^&*()?"
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def función_especial(données):\n    # Handle special chars\n    return clean_text(données)"]],
                "metadatas": [[{"file": "i18n.py", "name": "función_especial", "kind": "function", "language": "python", "range": "15-17"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_openai', return_value="The función_especial handles unicode properly") as mock_llm:
                result = qa.ask(special_question, "test_collection", ".test_chroma", 3, "openai", "gpt-4o-mini")
                
                # Verify special characters and unicode are preserved in query
                mock_collection.query.assert_called_once_with(query_texts=[special_question], n_results=3)
                
                # Verify special characters appear in user prompt
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "función_especial()" in user_prompt
                assert "données" in user_prompt
                assert "émojis 🚀" in user_prompt
                assert "@#$%^&*()" in user_prompt
                
                assert result == "The función_especial handles unicode properly"
    
    def test_markdown_and_html_like_syntax(self):
        """Test questions with markdown and HTML-like syntax"""
        markdown_question = """What does the **main** function do?
        
        Does it handle <input> tags or support _italics_ formatting?
        
        * Does it process lists?
        * What about [links](https://example.com)?
        * How about #hashtags and @mentions?"""
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def main():\n    process_markdown_content()\n    return 'done'"]],
                "metadatas": [[{"file": "main.py", "name": "main", "kind": "function", "language": "python", "range": "1-3"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value="Main function processes markdown") as mock_llm:
                result = qa.ask(markdown_question, "test_collection", ".test_chroma", 5, "anthropic", "claude-3-5-sonnet")
                
                # Verify markdown syntax is preserved
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "**main**" in user_prompt
                assert "<input>" in user_prompt
                assert "_italics_" in user_prompt
                assert "[links](https://example.com)" in user_prompt
                assert "#hashtags" in user_prompt
                assert "@mentions" in user_prompt
                
                assert result == "Main function processes markdown"
    
    def test_very_long_question_input(self):
        """Test that ask function handles very long question inputs appropriately"""
        # Create a very long question (over 1000 characters)
        long_question = "What does the authentication system do? " * 50  # ~1500 characters
        long_question += "Can you explain in detail how it works with all the edge cases and error handling mechanisms?"
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def authenticate_user():\n    # Complex auth logic\n    return validated"]],
                "metadatas": [[{"file": "auth.py", "name": "authenticate_user", "kind": "function", "language": "python", "range": "20-22"}]],
                "distances": [[0.1]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_ollama', return_value="Long authentication explanation...") as mock_llm:
                result = qa.ask(long_question, "test_collection", ".test_chroma", 5, "ollama", "mistral:7b")
                
                # Verify very long question is handled without truncation in query
                mock_collection.query.assert_called_once()
                query_args = mock_collection.query.call_args[1]
                assert len(query_args["query_texts"][0]) > 1000  # Verify long input preserved
                
                # Verify long question appears in user prompt
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "authentication system do?" in user_prompt  # Part of repeated text
                assert "edge cases and error handling" in user_prompt  # End of question
                
                # Verify function completes successfully with long input
                assert isinstance(result, str)
                assert result == "Long authentication explanation..."
    
    def test_question_with_sql_injection_like_syntax(self):
        """Test questions with SQL-like or injection-like syntax are handled safely"""
        injection_question = "What does SELECT * FROM users WHERE id = 1; DROP TABLE users; -- do?"
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def get_user_data(query):\n    # Safe query execution\n    return sanitized_result"]],
                "metadatas": [[{"file": "db.py", "name": "get_user_data", "kind": "function", "language": "python", "range": "30-32"}]],
                "distances": [[0.3]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_openai', return_value="This appears to be SQL syntax") as mock_llm:
                result = qa.ask(injection_question, "test_collection", ".test_chroma", 3, "openai", "gpt-4o-mini")
                
                # Verify the injection-like syntax is treated as plain text
                mock_collection.query.assert_called_once_with(query_texts=[injection_question], n_results=3)
                
                # Verify SQL syntax appears as-is in user prompt (not executed)
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "SELECT * FROM users" in user_prompt
                assert "DROP TABLE users" in user_prompt
                assert "--" in user_prompt
                
                # Verify safe handling - returns string response
                assert isinstance(result, str)
                assert result == "This appears to be SQL syntax"
    
    def test_question_with_extreme_whitespace(self):
        """Test questions with excessive whitespace and formatting"""
        whitespace_question = """
        
        
        What    does    the     function     do?
        
        
        
        Can   you   explain   it?
        
        
        """
        
        with patch('qa.chromadb.PersistentClient') as mock_client:
            mock_collection = Mock()
            mock_collection.query.return_value = {
                "documents": [["def example_func():\n    return 'test'"]],
                "metadatas": [[{"file": "test.py", "name": "example_func", "kind": "function", "language": "python", "range": "1-2"}]],
                "distances": [[0.2]]
            }
            mock_client.return_value.get_collection.return_value = mock_collection
            
            with patch('qa.generate_with_anthropic', return_value="Function returns test string") as mock_llm:
                result = qa.ask(whitespace_question, "test_collection", ".test_chroma", 3, "anthropic", "claude-3-5-sonnet")
                
                # Verify whitespace is preserved in query (no preprocessing)
                mock_collection.query.assert_called_once_with(query_texts=[whitespace_question], n_results=3)
                
                # Verify whitespace formatting appears in user prompt
                mock_llm.assert_called_once()
                user_prompt = mock_llm.call_args[0][1]
                assert "What    does    the     function" in user_prompt
                assert "Can   you   explain" in user_prompt
                
                assert result == "Function returns test string"