import fs from 'fs';
import Parser from 'tree-sitter';

import Go from 'tree-sitter-go';
import Python from 'tree-sitter-python';
import Rust from 'tree-sitter-rust';
import TypeScript from 'tree-sitter-typescript';
import JavaScript from 'tree-sitter-javascript';
import Java from 'tree-sitter-java';
import Kotlin from 'tree-sitter-kotlin';
import CSharp from 'tree-sitter-c-sharp';
import Swift from 'tree-sitter-swift';
import Zig from 'tree-sitter-zig';
import Haskell from 'tree-sitter-haskell';

export type ParsedFile = {
  filePath: string;
  language: string;
  ast: string;
};

export class ParserEngine {
  private languageMap: Record<string, { langId: string; parser: Parser.Language }> = {};

  constructor() {
    this.languageMap = {
      '.go': { langId: 'go', parser: Go },
      '.py': { langId: 'python', parser: Python },
      '.rs': { langId: 'rust', parser: Rust },
      '.ts': { langId: 'typescript', parser: TypeScript.typescript },
      '.tsx': { langId: 'typescript', parser: TypeScript.typescript },
      '.js': { langId: 'javascript', parser: JavaScript },
      '.jsx': { langId: 'javascript', parser: JavaScript },
      '.java': { langId: 'java', parser: Java },
      '.kt': { langId: 'kotlin', parser: Kotlin },
      '.cs': { langId: 'csharp', parser: CSharp },
      '.swift': { langId: 'swift', parser: Swift },
      '.zig': { langId: 'zig', parser: Zig },
      '.hs': { langId: 'haskell', parser: Haskell },
    };
  }

  public parseFile(filePath: string): ParsedFile | null {
    const ext = Object.keys(this.languageMap).find((key) => filePath.endsWith(key));
    if (!ext) return null;

    const langInfo = this.languageMap[ext];
    const parser = new Parser();
    parser.setLanguage(langInfo.parser);

    const code = fs.readFileSync(filePath, 'utf-8');
    const tree = parser.parse(code);

    return {
      filePath,
      language: langInfo.langId,
      ast: tree.rootNode.toString(),
    };
  }
}
