import fs from "fs";
import path from "path";
import { walkCodebase } from "./fileWalker";
import { ParserEngine } from "./parserEngine";

export async function main() {
  const rootDir = process.argv[2] || ".";
  const outputDir = path.join(rootDir, ".parsed-output");
  fs.mkdirSync(outputDir, { recursive: true });

  const engine = new ParserEngine();
  const files = await walkCodebase(rootDir);

  console.log(`\n🔍 Found ${files.length} source files. Parsing...`);

  for (const file of files) {
    const parsed = engine.parseFile(file);
    if (parsed) {
      const fileName = path.basename(file).replace(/\W+/g, "_") + ".json";
      const outputFile = path.join(outputDir, fileName);
      fs.writeFileSync(outputFile, JSON.stringify(parsed, null, 2), "utf-8");
      console.log(`✅ Parsed: ${file}`);
    } else {
      console.warn(`⚠️ Skipped (unsupported): ${file}`);
    }
  }

  console.log(`\n📁 Output saved to: ${outputDir}`);
}

// Only run main if this file is executed directly
if (require.main === module) {
  main();
}
