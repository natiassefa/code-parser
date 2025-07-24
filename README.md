# Code Parser

A powerful code parsing tool that uses Tree-sitter to parse multiple programming languages and extract their Abstract Syntax Trees (ASTs).

## Supported Languages

- Go (`.go`)
- Python (`.py`)
- Rust (`.rs`)
- TypeScript (`.ts`, `.tsx`)
- JavaScript (`.js`, `.jsx`)
- Java (`.java`)
- Kotlin (`.kt`)
- C# (`.cs`)
- Swift (`.swift`)
- Haskell (`.hs`)

**Note:** Zig (`.zig`) support is currently limited due to issues with the `tree-sitter-zig` package. The parser will throw an error when attempting to parse Zig files.

## Prerequisites

- Node.js 18.0.0 or higher
- npm or yarn
- C++ compiler with C++20 support (for native module compilation)

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

2. Install dependencies:

```bash
npm install
```

**Note:** If you encounter C++ compilation errors, try:

```bash
CXXFLAGS="-std=c++20" npm install --legacy-peer-deps
```

3. Build the project:

```bash
npm run build
```

## Usage

### Basic Usage

Parse the current directory:

```bash
npm start
```

Parse a specific directory:

```bash
npm start /path/to/your/codebase
```

### Development

For development with automatic rebuild:

```bash
npm run dev
```

### Output

The parser will:

1. Scan the specified directory for supported file types
2. Parse each file using the appropriate Tree-sitter grammar
3. Generate JSON files containing the AST in the `.parsed-output` directory
4. Each output file is named after the source file with `.json` extension

### Example Output

```json
{
  "filePath": "/path/to/file.go",
  "language": "go",
  "ast": "(source_file (package_clause (package_identifier)) (function_declaration name: (identifier) parameters: (parameter_list) body: (block)))"
}
```

## Configuration

The parser automatically:

- Ignores common directories (`node_modules/`, `.git/`, `dist/`, etc.)
- Respects `.gitignore` files
- Skips unsupported file types

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

## Development

### Testing

Run the test suite:

```bash
npm test
```

Run tests in watch mode:

```bash
npm run test:watch
```

Run tests with coverage:

```bash
npm run test:coverage
```

### Project Structure

```
src/
├── index.ts          # Main entry point
├── parserEngine.ts   # Tree-sitter parser engine
└── fileWalker.ts     # File system traversal

tests/
├── setup.ts          # Test configuration
├── parserEngine.test.ts  # Comprehensive parser tests
└── fileWalker.test.ts    # File system traversal tests
```

### Adding New Languages

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

## License

MIT
