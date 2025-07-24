# Code Parser

A powerful code parsing tool that uses Tree-sitter to parse multiple programming languages, extract their Abstract Syntax Trees (ASTs), and intelligently chunk code into semantically meaningful units for enhanced code analysis and RAG (Retrieval-Augmented Generation) applications.

## Features

- **Multi-language Support**: Parse and chunk code from 10+ programming languages
- **Intelligent AST Chunking**: Break down large codebases into meaningful, searchable chunks
- **Enhanced Context Formatting**: Optimized output for LLM-based code analysis
- **RAG Integration**: Ready-to-use embeddings and vector search capabilities
- **Comprehensive Testing**: Full test suite with unit and integration tests

## Supported Languages

- Go (`.go`)
- Python (`.py`) - **Enhanced with 25+ granular chunk types**
- Rust (`.rs`)
- TypeScript (`.ts`, `.tsx`)
- JavaScript (`.js`, `.jsx`)
- Java (`.java`)
- Kotlin (`.kt`)
- C# (`.cs`)
- Swift (`.swift`)
- Haskell (`.hs`)

**Note:** Zig (`.zig`) support is currently limited due to issues with the `tree-sitter-zig` package.

## Prerequisites

- Node.js 18.0.0 or higher
- npm or yarn
- C++ compiler with C++20 support (for native module compilation)
- Python 3.8+ (for RAG features)

### C++ Compiler Setup

**macOS:**

```bash
# Install Xcode Command Line Tools
xcode-select --install
```

**Linux:**

```bash
# Ubuntu/Debian
sudo apt-get install build-essential

# CentOS/RHEL
sudo yum groupinstall "Development Tools"
```

**Windows:**

- Install Visual Studio Build Tools or Visual Studio Community
- Ensure C++ build tools are included

## Installation

1. Clone the repository:

```bash
git clone https://github.com/natiassefa/code-parser.git
cd code-parser
```

2. Install Node.js dependencies:

```bash
npm install --legacy-peer-deps
```

**Note:** If you encounter C++ compilation errors, try:

```bash
CXXFLAGS="-std=c++20" npm install --legacy-peer-deps
```

3. Install Python dependencies (for RAG features):

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

4. Build the project:

```bash
npm run build
```

## Usage

### Basic Usage

Parse and chunk the current directory:

```bash
npm start
```

Parse and chunk a specific directory:

```bash
npm start /path/to/your/codebase
```

### Output Structure

The parser generates two types of output:

1. **AST Output** (`.parsed-output/`): Raw Abstract Syntax Trees
2. **Chunks Output** (`.chunks-output/`): Structured code chunks optimized for analysis

### Chunk Format

Each chunk contains:

```json
{
  "filePath": "/path/to/file.py",
  "kind": "function_definition",
  "name": "calculate_total",
  "code": "def calculate_total(items):\n    return sum(items)",
  "range": {
    "start": { "line": 10 },
    "end": { "line": 12 }
  }
}
```

### Enhanced Python Chunking

Python files are parsed with exceptional granularity, extracting:

- **Functions & Classes**: `function_definition`, `class_definition`, `async_function_definition`
- **Imports**: `import_statement`, `import_from_statement`
- **Data Structures**: `list`, `dictionary`, `set`, `tuple`
- **Control Flow**: `if_statement`, `for_statement`, `while_statement`, `try_statement`
- **Assignments**: `assignment`, `augmented_assignment`, `ann_assign`
- **Type System**: `type_alias`, `type_annotation`
- **Expressions**: `lambda`, `decorator`, `expression_statement`
- **Statements**: `assert_statement`, `raise_statement`, `return_statement`, `yield_statement`

## RAG Integration

### Embedding Code Chunks

```bash
cd code-parser-python
python embed_chunks.py
```

This creates embeddings in ChromaDB for semantic search.

### Querying with RAG

```bash
python qa.py "What does the calculate_total function do?"
```

Supports multiple LLM backends:

- OpenAI GPT-4
- Anthropic Claude
- Ollama (local)

## Development

### Testing

Run all tests:

```bash
npm test
```

Run unit tests only:

```bash
npm run test:unit
```

Run integration tests only:

```bash
npm run test:integration
```

Run full test suite (unit tests first, then integration):

```bash
npm run test:full
```

Run tests in watch mode:

```bash
npm run test:watch
```

Run tests with coverage:

```bash
npm run test:coverage
```

**Note:** Integration tests are run separately from unit tests to avoid interference with tree-sitter native modules.

### Project Structure

```
src/
├── index.ts          # Main entry point and CLI
├── parserEngine.ts   # Tree-sitter parser and chunking engine
└── fileWalker.ts     # File system traversal

tests/
├── setup.ts                    # Test configuration
├── parserEngine.test.ts        # Comprehensive parser tests
├── fileWalker.test.ts          # File system traversal tests
├── astChunker.test.ts          # AST chunking tests
└── index.integration.test.ts   # End-to-end workflow tests

code-parser-python/
├── embed_chunks.py             # ChromaDB embedding script
└── qa.py                      # RAG query interface

code-parser-node/
├── package.json               # Node.js parser configuration
└── tsconfig.json             # TypeScript configuration
```

### Enhanced Context Formatting

The RAG system provides intelligently formatted context:

```
[1] PYTHON function: calculate_total in /path/to/file.py (lines 10-12)
---
def calculate_total(items):
    return sum(items)

[2] PYTHON import in /path/to/file.py (lines 1-1)
---
import json
```

This format helps LLMs understand:

- Programming language context
- Code construct types and names
- File organization and line locations
- Relationships between code elements

## Configuration

The parser automatically:

- Ignores common directories (`node_modules/`, `.git/`, `dist/`, etc.)
- Respects `.gitignore` files
- Skips unsupported file types
- Creates separate output directories for ASTs and chunks

## Troubleshooting

### C++ Compilation Errors

If you see errors like `"C++20 or later required"`:

1. Ensure you have a C++20 compatible compiler
2. Try installing with explicit C++20 flags:
   ```bash
   CXXFLAGS="-std=c++20" npm install --legacy-peer-deps
   ```

### TypeScript Errors

If you encounter TypeScript compilation errors:

1. Ensure TypeScript is installed: `npm install typescript`
2. Rebuild: `npm run build`

### ChromaDB Issues

If ChromaDB operations fail:

1. Ensure the `.chroma_db` directory exists
2. Check that metadata values are strings (not objects)
3. Verify Python dependencies are installed

## Adding New Languages

To add support for a new language:

1. Install the Tree-sitter grammar:

   ```bash
   npm install tree-sitter-[language]
   ```

2. Add the import and mapping in `src/parserEngine.ts`:

   ```typescript
   import NewLanguage from 'tree-sitter-[language]';

   // In the languageMap:
   '.ext': { langId: 'language', parser: NewLanguage as Parser.Language },
   ```

3. Define chunk types for the language in the `CHUNK_TYPES` mapping

## License

MIT
