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
}
