import { execSync } from "child_process";

// cli options:
// --codebase=../agentflow
// --step=parse, embed, all

// Parse CLI options
const args = process.argv.slice(2);
let step = "all";
let codebase = "."; // default

for (const arg of args) {
  switch (arg) {
    case "--codebase":
      codebase = args[1];
      break;
    case "--step":
      step = args[1];
      break;
  }
}

function runNodeParser(dir?: string) {
  console.log("🔧 Running Node parser...");
  execSync(`npx tsx code-parser-node/src/index.ts ${dir}`, {
    stdio: "inherit",
  });
}

function runPythonEmbedding() {
  console.log("🧠 Running Python embedding...");
  execSync("python3 code-parser-python/embed_chunks.py", {
    stdio: "inherit",
  });
}

function runQuery() {
  console.log("🔍 Running query...");
  execSync("python3 code-parser-python/check_embeddings.py", {
    stdio: "inherit",
  });
}

if (require.main === module) {
  if (step === "parse") {
    runNodeParser(codebase);
    console.log("✅ Node parsing done!");
  } else if (step === "embed") {
    runPythonEmbedding();
    console.log("✅ Embedding done!");
  } else if (step === "query") {
    runQuery();
    console.log("✅ Query done!");
  } else if (step === "all") {
    runNodeParser(codebase);
    runPythonEmbedding();
    runQuery();
    console.log("✅ Done!");
  } else {
    console.error(`Unknown step: ${step}`);
    process.exit(1);
  }
}
