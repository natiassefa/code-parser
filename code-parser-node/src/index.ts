import fs from "fs";
import path from "path";
import { walkCodebase } from "./fileWalker";
import { ParserEngine } from "./parserEngine";

export async function main() {
  const rootDir = process.argv[2] || ".";
  const outputDir = path.join(".", ".parsed-output");
  const chunksDir = path.join(".", ".chunks-output");

  fs.mkdirSync(outputDir, { recursive: true });
  fs.mkdirSync(chunksDir, { recursive: true });

  const engine = new ParserEngine();

  // Check if rootDir is a file or directory
  const stats = fs.statSync(rootDir);
  const files = stats.isFile() ? [rootDir] : await walkCodebase(rootDir);

  console.log(`\n🔍 Found ${files.length} source files. Parsing...`);

  for (const file of files) {
    // Parse full AST
    const parsed = engine.parseFile(file);
    if (parsed) {
      const fileName = path.basename(file).replace(/\W+/g, "_") + ".json";
      const outputFile = path.join(outputDir, fileName);
      fs.writeFileSync(outputFile, JSON.stringify(parsed, null, 2), "utf-8");
      console.log(`✅ Parsed: ${file}`);
    } else {
      console.warn(`⚠️ Skipped (unsupported): ${file}`);
    }

    // Extract code chunks
    const chunks = engine.chunkFile(file);
    if (chunks.length > 0) {
      const chunksFileName =
        path.basename(file).replace(/\W+/g, "_") + "_chunks.json";
      const chunksFile = path.join(chunksDir, chunksFileName);
      fs.writeFileSync(chunksFile, JSON.stringify(chunks, null, 2), "utf-8");
      console.log(`📦 Extracted ${chunks.length} chunks from: ${file}`);
    }
  }

  console.log(`\n📁 Full ASTs saved to: ${outputDir}`);
  console.log(`📁 Code chunks saved to: ${chunksDir}`);
}

// Only run main if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main();
}
