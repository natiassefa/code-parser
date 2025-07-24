import fs from "fs";
import Parser from "tree-sitter";

import Go from "tree-sitter-go";
import Python from "tree-sitter-python";
import Rust from "tree-sitter-rust";
import TypeScript from "tree-sitter-typescript";
import JavaScript from "tree-sitter-javascript";
import Java from "tree-sitter-java";
import Kotlin from "tree-sitter-kotlin";
import CSharp from "tree-sitter-c-sharp";
import Swift from "tree-sitter-swift";
// @ts-ignore
import Zig from "tree-sitter-zig";
import Haskell from "tree-sitter-haskell";

export type ParsedFile = {
  filePath: string;
  language: string;
  ast: string;
};

export type CodeChunk = {
  filePath: string;
  kind: string;
  name: string;
  code: string;
  language: string;
  range: {
    start: { line: number };
    end: { line: number };
  };
};

export class ParserEngine {
  private languageMap: Record<
    string,
    { langId: string; parser: Parser.Language }
  > = {};

  constructor() {
    this.languageMap = {
      ".go": { langId: "go", parser: Go as Parser.Language },
      ".py": { langId: "python", parser: Python as Parser.Language },
      ".rs": { langId: "rust", parser: Rust as Parser.Language },
      ".ts": {
        langId: "typescript",
        parser: TypeScript.typescript as Parser.Language,
      },
      ".tsx": {
        langId: "typescript",
        parser: TypeScript.typescript as Parser.Language,
      },
      ".js": { langId: "javascript", parser: JavaScript as Parser.Language },
      ".jsx": { langId: "javascript", parser: JavaScript as Parser.Language },
      ".java": { langId: "java", parser: Java as Parser.Language },
      ".kt": { langId: "kotlin", parser: Kotlin as Parser.Language },
      ".cs": { langId: "csharp", parser: CSharp as Parser.Language },
      ".swift": { langId: "swift", parser: Swift as Parser.Language },
      ".zig": { langId: "zig", parser: Zig as Parser.Language },
      ".hs": { langId: "haskell", parser: Haskell as Parser.Language },
    };
  }

  public parseFile(filePath: string): ParsedFile | null {
    const ext = Object.keys(this.languageMap).find((key) =>
      filePath.endsWith(key)
    );
    if (!ext) return null;

    // Check if file exists
    if (!fs.existsSync(filePath)) return null;

    const langInfo = this.languageMap[ext];
    const parser = new Parser();
    parser.setLanguage(langInfo.parser);

    const code = fs.readFileSync(filePath, "utf-8");
    const tree = parser.parse(code);

    return {
      filePath,
      language: langInfo.langId,
      ast: tree.rootNode.toString(),
    };
  }

  /**
   * Extracts top-level functions, classes, and methods from a source file.
   * Returns an array of chunk objects with code and metadata.
   */
  public chunkFile(filePath: string): CodeChunk[] {
    const ext = Object.keys(this.languageMap).find((key) =>
      filePath.endsWith(key)
    );
    if (!ext || !fs.existsSync(filePath)) return [];

    const langInfo = this.languageMap[ext];
    const parser = new Parser();
    parser.setLanguage(langInfo.parser);

    const code = fs.readFileSync(filePath, "utf-8");
    const tree = parser.parse(code);

    if (!tree || !tree.rootNode) {
      console.warn(`Failed to parse ${filePath}: Invalid tree structure`);
      return [];
    }

    const root = tree.rootNode;

    // Node types to extract per language with improved mapping
    const CHUNK_TYPES: Record<string, string[]> = {
      python: [
        "function_definition",
        "class_definition",
        "async_function_definition",
        "import_statement",
        "import_from_statement",
        "assignment",
        "augmented_assignment",
        "ann_assign",
        "decorator",
        "decorated_definition",
        "lambda",
        "if_statement",
        "for_statement",
        "while_statement",
        "try_statement",
        "with_statement",
        "list",
        "dictionary",
        "set",
        "tuple",
        "type_alias",
        "type_annotation",
        "assert_statement",
        "raise_statement",
        "return_statement",
        "yield_statement",
        "expression_statement",
      ],
      go: ["function_declaration", "method_declaration", "type_declaration"],
      rust: [
        "function_item",
        "impl_item",
        "struct_item",
        "enum_item",
        "trait_item",
      ],
      typescript: [
        "function_declaration",
        "class_declaration",
        "method_definition",
        "arrow_function",
        "function_expression",
      ],
      javascript: [
        "function_declaration",
        "class_declaration",
        "method_definition",
        "arrow_function",
        "function_expression",
      ],
      java: [
        "method_declaration",
        "class_declaration",
        "interface_declaration",
      ],
      kotlin: [
        "function_declaration",
        "class_declaration",
        "object_declaration",
      ],
      csharp: [
        "method_declaration",
        "class_declaration",
        "interface_declaration",
      ],
      swift: [
        "function_declaration",
        "class_declaration",
        "struct_declaration",
      ],
      zig: ["fn_declaration", "const_declaration"],
      haskell: ["function", "type_declaration", "data_declaration"],
    };

    const supportedNodeTypes = CHUNK_TYPES[langInfo.langId] || [];
    const chunks: CodeChunk[] = [];

    root
      .descendantsOfType(supportedNodeTypes)
      .forEach((node: Parser.SyntaxNode) => {
        const name = this.extractNodeName(node, langInfo.langId);
        const kind = this.mapNodeTypeToKind(node.type, langInfo.langId);

        if (name) {
          const chunk: CodeChunk = {
            filePath,
            kind,
            name,
            language: langInfo.langId,
            code: code.slice(node.startIndex, node.endIndex),
            range: {
              start: { line: node.startPosition.row + 1 }, // Convert to 1-based indexing
              end: { line: node.endPosition.row + 1 },
            },
          };
          chunks.push(chunk);
        }
      });

    return chunks;
  }

  /**
   * Extracts the name from a syntax node based on language-specific patterns
   */
  private extractNodeName(
    node: Parser.SyntaxNode,
    language: string
  ): string | null {
    // Try to get name from the "name" field first
    const nameNode = node.childForFieldName("name");
    if (nameNode) {
      return nameNode.text;
    }

    // Language-specific name extraction patterns
    switch (language) {
      case "python":
        return this.extractPythonName(node);
      case "go":
        return this.extractGoName(node);
      case "rust":
        return this.extractRustName(node);
      case "typescript":
      case "javascript":
        return this.extractJSName(node);
      case "java":
        return this.extractJavaName(node);
      case "kotlin":
        return this.extractKotlinName(node);
      case "csharp":
        return this.extractCSharpName(node);
      case "swift":
        return this.extractSwiftName(node);
      case "zig":
        return this.extractZigName(node);
      case "haskell":
        return this.extractHaskellName(node);
      default:
        return null;
    }
  }

  /**
   * Maps Tree-sitter node types to user-friendly kind names
   */
  private mapNodeTypeToKind(nodeType: string, language: string): string {
    const kindMap: Record<string, Record<string, string>> = {
      python: {
        function_definition: "function",
        async_function_definition: "function",
        class_definition: "class",
        import_statement: "import",
        import_from_statement: "import",
        assignment: "assignment",
        augmented_assignment: "assignment",
        ann_assign: "assignment",
        decorator: "decorator",
        decorated_definition: "decorated",
        lambda: "lambda",
        if_statement: "if",
        for_statement: "for",
        while_statement: "while",
        try_statement: "try",
        with_statement: "with",
        list: "list",
        dictionary: "dict",
        set: "set",
        tuple: "tuple",
        type_alias: "type_alias",
        type_annotation: "type_annotation",
        assert_statement: "assert",
        raise_statement: "raise",
        return_statement: "return",
        yield_statement: "yield",
        expression_statement: "expression",
      },
      go: {
        function_declaration: "function",
        method_declaration: "method",
        type_declaration: "type",
      },
      rust: {
        function_item: "function",
        impl_item: "impl",
        struct_item: "struct",
        enum_item: "enum",
        trait_item: "trait",
      },
      typescript: {
        function_declaration: "function",
        class_declaration: "class",
        method_definition: "method",
        arrow_function: "function",
        function_expression: "function",
      },
      javascript: {
        function_declaration: "function",
        class_declaration: "class",
        method_definition: "method",
        arrow_function: "function",
        function_expression: "function",
      },
      java: {
        method_declaration: "method",
        class_declaration: "class",
        interface_declaration: "interface",
      },
      kotlin: {
        function_declaration: "function",
        class_declaration: "class",
        object_declaration: "object",
      },
      csharp: {
        method_declaration: "method",
        class_declaration: "class",
        interface_declaration: "interface",
      },
      swift: {
        function_declaration: "function",
        class_declaration: "class",
        struct_declaration: "struct",
      },
      zig: {
        fn_declaration: "function",
        const_declaration: "constant",
      },
      haskell: {
        function: "function",
        type_declaration: "type",
        data_declaration: "data",
      },
    };

    return kindMap[language]?.[nodeType] || nodeType;
  }

  // Language-specific name extraction methods
  private extractPythonName(node: Parser.SyntaxNode): string | null {
    // Python functions and classes have a name field
    const nameNode = node.childForFieldName("name");
    if (nameNode) {
      return nameNode.text;
    }

    // Handle different node types
    switch (node.type) {
      case "import_statement":
      case "import_from_statement":
        // For imports, use the module name or first imported item
        const moduleName = node.childForFieldName("module_name")?.text;
        const nameList = node.childForFieldName("name")?.text;
        return moduleName || nameList || "import";

      case "assignment":
      case "augmented_assignment":
      case "ann_assign":
        // For assignments, use the target name
        const target = node.childForFieldName("target");
        if (target) {
          return target.text;
        }
        return "assignment";

      case "decorator":
        // For decorators, use the decorator name
        const decoratorName = node.childForFieldName("name")?.text;
        return decoratorName || "decorator";

      case "lambda":
        return "lambda";

      case "if_statement":
        return "if";

      case "for_statement":
        return "for";

      case "while_statement":
        return "while";

      case "try_statement":
        return "try";

      case "with_statement":
        return "with";

      case "list":
        return "list";

      case "dictionary":
        return "dict";

      case "set":
        return "set";

      case "tuple":
        return "tuple";

      case "type_alias":
        const aliasName = node.childForFieldName("name")?.text;
        return aliasName || "type_alias";

      case "type_annotation":
        return "type_annotation";

      case "assert_statement":
        return "assert";

      case "raise_statement":
        return "raise";

      case "return_statement":
        return "return";

      case "yield_statement":
        return "yield";

      case "expression_statement":
        return "expression";

      default:
        return null;
    }
  }

  private extractGoName(node: Parser.SyntaxNode): string | null {
    // Go functions and methods have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractRustName(node: Parser.SyntaxNode): string | null {
    // Rust items have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractJSName(node: Parser.SyntaxNode): string | null {
    // JavaScript/TypeScript functions and classes have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractJavaName(node: Parser.SyntaxNode): string | null {
    // Java methods and classes have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractKotlinName(node: Parser.SyntaxNode): string | null {
    // Kotlin functions and classes have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractCSharpName(node: Parser.SyntaxNode): string | null {
    // C# methods and classes have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractSwiftName(node: Parser.SyntaxNode): string | null {
    // Swift functions and classes have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractZigName(node: Parser.SyntaxNode): string | null {
    // Zig functions have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }

  private extractHaskellName(node: Parser.SyntaxNode): string | null {
    // Haskell functions have a name field
    const nameNode = node.childForFieldName("name");
    return nameNode?.text || null;
  }
}
