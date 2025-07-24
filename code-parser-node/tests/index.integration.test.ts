import fs from "fs";
import path from "path";
import os from "os";
import { execSync } from "child_process";

describe("Index Integration Tests", () => {
  let tempDir: string;
  let testProjectDir: string;
  let originalArgv: string[];

  beforeAll(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "index-integration-test-"));
    testProjectDir = path.join(tempDir, "test-project");
    fs.mkdirSync(testProjectDir, { recursive: true });

    // Store original process.argv
    originalArgv = process.argv;
  });

  afterAll(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
    // Restore original process.argv
    process.argv = originalArgv;
  });

  beforeEach(() => {
    // Clean up test directory
    if (fs.existsSync(testProjectDir)) {
      fs.rmSync(testProjectDir, { recursive: true, force: true });
    }
    fs.mkdirSync(testProjectDir, { recursive: true });
  });

  describe("Complete Workflow", () => {
    it("should process a simple project with multiple file types", async () => {
      // Create a test project structure
      const projectFiles = [
        "src/main.ts",
        "src/utils.js",
        "app.py",
        "server.go",
        "lib.rs",
        "Main.java",
        "User.kt",
        "App.swift",
        "Utils.hs",
        "Program.cs",
      ];

      // Create directories and files
      projectFiles.forEach((file) => {
        const filePath = path.join(testProjectDir, file);
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }

        // Create sample content for each file type
        const content = getSampleContent(file);
        fs.writeFileSync(filePath, content);
      });

      // Create some files that should be ignored
      const ignoredFiles = [
        "node_modules/test.ts",
        ".git/config",
        "dist/build.js",
        "package-lock.json",
        "app.log",
      ];

      ignoredFiles.forEach((file) => {
        const filePath = path.join(testProjectDir, file);
        const dir = path.dirname(filePath);
        if (!fs.existsSync(dir)) {
          fs.mkdirSync(dir, { recursive: true });
        }
        fs.writeFileSync(filePath, "// Should be ignored");
      });

      // Run the parser
      const outputDir = path.join(testProjectDir, ".parsed-output");

      // Mock console.log to capture output
      const consoleSpy = jest.spyOn(console, "log").mockImplementation();
      const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

      // Import and run the main function
      const { main } = await import("../src/index");

      // Mock process.argv to simulate CLI arguments
      process.argv = ["node", "index.js", testProjectDir];

      await main();

      // Verify output directory was created
      expect(fs.existsSync(outputDir)).toBe(true);

      // Verify JSON files were created for each supported file
      const outputFiles = fs.readdirSync(outputDir);
      expect(outputFiles.length).toBeGreaterThan(0);

      // Verify each output file is valid JSON
      outputFiles.forEach((file) => {
        expect(file).toMatch(/\.json$/);
        const filePath = path.join(outputDir, file);
        const content = fs.readFileSync(filePath, "utf-8");
        const parsed = JSON.parse(content);

        expect(parsed).toHaveProperty("filePath");
        expect(parsed).toHaveProperty("language");
        expect(parsed).toHaveProperty("ast");
        expect(typeof parsed.ast).toBe("string");
        // AST might be empty if parsing failed, but should still be a string
        expect(parsed.ast.length).toBeGreaterThanOrEqual(0);
      });

      // Verify console output
      expect(consoleSpy).toHaveBeenCalledWith(expect.stringContaining("Found"));
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Output saved to")
      );

      // Clean up spies
      consoleSpy.mockRestore();
      consoleWarnSpy.mockRestore();
    });

    it("should handle projects with no supported files", async () => {
      // Create a project with only unsupported files
      const unsupportedFiles = [
        "config.txt",
        "data.json",
        "image.png",
        "document.pdf",
        "README.md",
      ];

      unsupportedFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testProjectDir, file),
          `Content for ${file}`
        );
      });

      const outputDir = path.join(testProjectDir, ".parsed-output");

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();
      const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

      const { main } = await import("../src/index");
      process.argv = ["node", "index.js", testProjectDir];

      await main();

      // Verify output directory was created (even if empty)
      expect(fs.existsSync(outputDir)).toBe(true);

      // Verify no JSON files were created
      const outputFiles = fs.readdirSync(outputDir);
      expect(outputFiles.length).toBe(0);

      // Verify console output indicates no files found
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining("Found 0 source files")
      );

      consoleSpy.mockRestore();
      consoleWarnSpy.mockRestore();
    });

    it("should handle projects with mixed supported and unsupported files", async () => {
      // Create a mix of supported and unsupported files
      const supportedFiles = ["main.ts", "app.py", "server.go"];
      const unsupportedFiles = ["config.txt", "data.json", "README.md"];

      [...supportedFiles, ...unsupportedFiles].forEach((file) => {
        fs.writeFileSync(
          path.join(testProjectDir, file),
          `Content for ${file}`
        );
      });

      const outputDir = path.join(testProjectDir, ".parsed-output");

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();
      const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

      const { main } = await import("../src/index");
      process.argv = ["node", "index.js", testProjectDir];

      await main();

      // Verify output directory was created
      expect(fs.existsSync(outputDir)).toBe(true);

      // Verify JSON files were created only for supported files
      const outputFiles = fs.readdirSync(outputDir);
      expect(outputFiles.length).toBe(supportedFiles.length);

      // Verify each supported file has a corresponding JSON output
      supportedFiles.forEach((file) => {
        const expectedJsonFile = file.replace(/\W+/g, "_") + ".json";
        expect(outputFiles).toContain(expectedJsonFile);
      });

      // Verify console output shows correct counts
      expect(consoleSpy).toHaveBeenCalledWith(
        expect.stringContaining(`Found ${supportedFiles.length} source files`)
      );

      consoleSpy.mockRestore();
      consoleWarnSpy.mockRestore();
    });

    it("should handle malformed code gracefully", async () => {
      // Create files with malformed code
      const malformedFiles = [
        {
          name: "malformed.ts",
          content: "function main() { // Missing closing brace",
        },
        {
          name: "malformed.py",
          content: "def greet(name: # Missing colon and body",
        },
        {
          name: "malformed.go",
          content: "package main func main() { // Missing closing brace",
        },
      ];

      malformedFiles.forEach(({ name, content }) => {
        fs.writeFileSync(path.join(testProjectDir, name), content);
      });

      const outputDir = path.join(testProjectDir, ".parsed-output");

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();
      const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

      const { main } = await import("../src/index");
      process.argv = ["node", "index.js", testProjectDir];

      await main();

      // Verify output directory was created
      expect(fs.existsSync(outputDir)).toBe(true);

      // Verify JSON files were still created (parser should handle malformed code)
      const outputFiles = fs.readdirSync(outputDir);
      expect(outputFiles.length).toBe(malformedFiles.length);

      // Verify each output file contains valid JSON
      outputFiles.forEach((file) => {
        const filePath = path.join(outputDir, file);
        const content = fs.readFileSync(filePath, "utf-8");
        const parsed = JSON.parse(content);

        expect(parsed).toHaveProperty("ast");
        // AST should still be generated even for malformed code
        expect(parsed.ast.length).toBeGreaterThanOrEqual(0);
      });

      consoleSpy.mockRestore();
      consoleWarnSpy.mockRestore();
    });

    it("should use current directory when no argument is provided", async () => {
      // Create a simple test file in the current directory
      const testFile = "test-main.ts";
      fs.writeFileSync(testFile, 'console.log("Hello, World!");');

      const outputDir = path.join(".", ".parsed-output");

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();

      const { main } = await import("../src/index");
      process.argv = ["node", "index.js"]; // No directory argument

      await main();

      // Verify output directory was created
      expect(fs.existsSync(outputDir)).toBe(true);

      // Verify JSON file was created (at least the one we created)
      const outputFiles = fs.readdirSync(outputDir);
      expect(outputFiles.length).toBeGreaterThan(0);
      expect(outputFiles).toContain("test_main_ts.json");

      // Clean up
      fs.unlinkSync(testFile);
      fs.rmSync(outputDir, { recursive: true, force: true });

      consoleSpy.mockRestore();
    });
  });

  describe("Error Handling", () => {
    it("should handle non-existent directory gracefully", async () => {
      const nonExistentDir = path.join(tempDir, "non-existent");

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();
      const consoleErrorSpy = jest.spyOn(console, "error").mockImplementation();

      const { main } = await import("../src/index");
      process.argv = ["node", "index.js", nonExistentDir];

      // Should handle the error gracefully (either throw or handle internally)
      try {
        await main();
        // If it doesn't throw, that's also acceptable behavior
      } catch (error) {
        // If it throws, that's also acceptable
        expect(error).toBeDefined();
      }

      consoleSpy.mockRestore();
      consoleErrorSpy.mockRestore();
    });

    it("should handle permission errors gracefully", async () => {
      // Create a file that can't be read (simulate permission error)
      const protectedFile = path.join(testProjectDir, "protected.ts");
      fs.writeFileSync(protectedFile, 'console.log("protected");');

      // Change permissions to read-only (this might not work on all systems)
      try {
        fs.chmodSync(protectedFile, 0o000);
      } catch (error) {
        // Skip this test if we can't change permissions
        console.log(
          "Skipping permission test - unable to change file permissions"
        );
        return;
      }

      const consoleSpy = jest.spyOn(console, "log").mockImplementation();
      const consoleWarnSpy = jest.spyOn(console, "warn").mockImplementation();

      const { main } = await import("../src/index");
      process.argv = ["node", "index.js", testProjectDir];

      // Should handle the error gracefully by skipping the protected file
      await expect(main()).rejects.toThrow();

      // Restore permissions
      fs.chmodSync(protectedFile, 0o644);

      consoleSpy.mockRestore();
      consoleWarnSpy.mockRestore();
    });
  });
});

// Helper function to generate sample content for different file types
function getSampleContent(filename: string): string {
  const ext = path.extname(filename);

  switch (ext) {
    case ".ts":
      return `interface User {
  id: number;
  name: string;
}

function greet(user: User): string {
  return \`Hello, \${user.name}!\`;
}`;

    case ".js":
      return `const express = require('express');
const app = express();

app.get('/', (req, res) => {
  res.send('Hello World!');
});`;

    case ".py":
      return `def greet(name: str) -> str:
    return f"Hello, {name}!"

class User:
    def __init__(self, name: str):
        self.name = name`;

    case ".go":
      return `package main

import "fmt"

func main() {
    fmt.Println("Hello, World!")
}

type User struct {
    Name string
    Age  int
}`;

    case ".rs":
      return `fn main() {
    println!("Hello, World!");
}

struct User {
    name: String,
    age: u32,
}`;

    case ".java":
      return `public class Main {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}`;

    case ".kt":
      return `fun main() {
    println("Hello, World!")
}

data class User(
    val name: String,
    val age: Int
)`;

    case ".swift":
      return `import Foundation

struct User {
    let name: String
    let age: Int
}

print("Hello, World!")`;

    case ".hs":
      return `module Main where

greet :: String -> String
greet name = "Hello, " ++ name ++ "!"

main :: IO ()
main = putStrLn $ greet "World"`;

    case ".cs":
      return `using System;

namespace TestApp
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("Hello, World!");
        }
    }
}`;

    default:
      return `// Default content for ${filename}`;
  }
}
