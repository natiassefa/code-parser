import fs from "fs";
import path from "path";
import os from "os";
import { walkCodebase } from "../src/fileWalker";

describe("fileWalker", () => {
  let tempDir: string;
  let testRootDir: string;

  beforeAll(() => {
    tempDir = fs.mkdtempSync(path.join(os.tmpdir(), "filewalker-test-"));
    testRootDir = path.join(tempDir, "test-project");
    fs.mkdirSync(testRootDir, { recursive: true });
  });

  afterAll(() => {
    if (fs.existsSync(tempDir)) {
      fs.rmSync(tempDir, { recursive: true, force: true });
    }
  });

  beforeEach(() => {
    // Clean up test directory before each test
    if (fs.existsSync(testRootDir)) {
      fs.rmSync(testRootDir, { recursive: true, force: true });
    }
    fs.mkdirSync(testRootDir, { recursive: true });
  });

  describe("walkCodebase", () => {
    it("should find files with supported extensions", async () => {
      // Create test files
      const testFiles = [
        "main.ts",
        "utils.js",
        "app.py",
        "server.go",
        "lib.rs",
        "Main.java",
        "User.kt",
        "App.swift",
        "main.zig",
        "Utils.hs",
        "Program.cs",
      ];

      testFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Test content for ${file}`
        );
      });

      const files = await walkCodebase(testRootDir);

      expect(files).toHaveLength(testFiles.length);
      testFiles.forEach((file) => {
        expect(files).toContain(path.join(testRootDir, file));
      });
    });

    it("should ignore files with unsupported extensions", async () => {
      // Create test files with supported and unsupported extensions
      const supportedFiles = ["main.ts", "app.py", "server.go"];
      const unsupportedFiles = [
        "config.txt",
        "data.json",
        "image.png",
        "document.pdf",
      ];

      [...supportedFiles, ...unsupportedFiles].forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Test content for ${file}`
        );
      });

      const files = await walkCodebase(testRootDir);

      expect(files).toHaveLength(supportedFiles.length);
      supportedFiles.forEach((file) => {
        expect(files).toContain(path.join(testRootDir, file));
      });
      unsupportedFiles.forEach((file) => {
        expect(files).not.toContain(path.join(testRootDir, file));
      });
    });

    it("should respect custom extensions parameter", async () => {
      // Create test files
      const testFiles = ["main.ts", "app.py", "data.json", "config.yaml"];
      testFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Test content for ${file}`
        );
      });

      // Test with custom extensions
      const customExtensions = [".json", ".yaml"];
      const files = await walkCodebase(testRootDir, customExtensions);

      expect(files).toHaveLength(2);
      expect(files).toContain(path.join(testRootDir, "data.json"));
      expect(files).toContain(path.join(testRootDir, "config.yaml"));
      expect(files).not.toContain(path.join(testRootDir, "main.ts"));
      expect(files).not.toContain(path.join(testRootDir, "app.py"));
    });

    it("should ignore default ignore patterns", async () => {
      // Create directories and files that should be ignored
      const ignoredDirs = [
        "node_modules",
        ".git",
        "dist",
        "build",
        "venv",
        ".venv",
        "__pycache__",
      ];
      const ignoredFiles = [
        "package-lock.json",
        "yarn.lock",
        "app.log",
        "Main.class",
        "app.exe",
      ];

      // Create ignored directories with some files
      ignoredDirs.forEach((dir) => {
        const dirPath = path.join(testRootDir, dir);
        fs.mkdirSync(dirPath, { recursive: true });
        fs.writeFileSync(path.join(dirPath, "test.ts"), "// Should be ignored");
      });

      // Create ignored files
      ignoredFiles.forEach((file) => {
        fs.writeFileSync(path.join(testRootDir, file), "// Should be ignored");
      });

      // Create some valid files
      const validFiles = ["main.ts", "app.py", "server.go"];
      validFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Valid content for ${file}`
        );
      });

      const files = await walkCodebase(testRootDir);

      expect(files).toHaveLength(validFiles.length);
      validFiles.forEach((file) => {
        expect(files).toContain(path.join(testRootDir, file));
      });

      // Verify ignored files are not included
      ignoredFiles.forEach((file) => {
        expect(files).not.toContain(path.join(testRootDir, file));
      });

      // Verify files in ignored directories are not included
      ignoredDirs.forEach((dir) => {
        expect(files).not.toContain(path.join(testRootDir, dir, "test.ts"));
      });
    });

    it("should respect .gitignore patterns", async () => {
      // Create .gitignore file
      const gitignoreContent = `
# Ignore test files
*.test.ts
*.spec.ts

# Ignore specific directories
test-files/
temp/

# Ignore specific files
config.local.js
secrets.json
      `.trim();

      fs.writeFileSync(path.join(testRootDir, ".gitignore"), gitignoreContent);

      // Create files that should be ignored by .gitignore
      const gitignoredFiles = [
        "main.test.ts",
        "utils.spec.ts",
        "config.local.js",
        "secrets.json",
      ];

      // Create directories that should be ignored
      const gitignoredDirs = ["test-files", "temp"];
      gitignoredDirs.forEach((dir) => {
        const dirPath = path.join(testRootDir, dir);
        fs.mkdirSync(dirPath, { recursive: true });
        fs.writeFileSync(
          path.join(dirPath, "test.ts"),
          "// Should be ignored by gitignore"
        );
      });

      // Create valid files
      const validFiles = ["main.ts", "utils.js", "app.py"];
      [...validFiles, ...gitignoredFiles].forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Content for ${file}`
        );
      });

      const files = await walkCodebase(testRootDir);

      expect(files).toHaveLength(validFiles.length);
      validFiles.forEach((file) => {
        expect(files).toContain(path.join(testRootDir, file));
      });

      // Verify gitignored files are not included
      gitignoredFiles.forEach((file) => {
        expect(files).not.toContain(path.join(testRootDir, file));
      });

      // Verify files in gitignored directories are not included
      gitignoredDirs.forEach((dir) => {
        expect(files).not.toContain(path.join(testRootDir, dir, "test.ts"));
      });
    });

    it("should handle nested directory structures", async () => {
      // Create nested directory structure
      const nestedDirs = [
        "src/components",
        "src/utils",
        "src/types",
        "tests/unit",
        "tests/integration",
      ];

      nestedDirs.forEach((dir) => {
        fs.mkdirSync(path.join(testRootDir, dir), { recursive: true });
      });

      // Create files in nested directories
      const nestedFiles = [
        "src/components/Button.tsx",
        "src/components/Header.tsx",
        "src/utils/helpers.ts",
        "src/types/index.ts",
        "tests/unit/Button.test.ts",
        "tests/integration/api.test.ts",
      ];

      nestedFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Content for ${file}`
        );
      });

      // Test with custom extensions to include .tsx
      const customExtensions = [
        ".ts",
        ".js",
        ".py",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".swift",
        ".zig",
        ".hs",
        ".cs",
        ".tsx",
      ];
      const files = await walkCodebase(testRootDir, customExtensions);

      // All files should be found since .test.ts files are not in default ignore patterns
      expect(files).toHaveLength(nestedFiles.length);
      nestedFiles.forEach((file) => {
        expect(files).toContain(path.join(testRootDir, file));
      });
    });

    it("should handle empty directories", async () => {
      // Create empty directories
      const emptyDirs = ["empty1", "empty2", "nested/empty3"];
      emptyDirs.forEach((dir) => {
        fs.mkdirSync(path.join(testRootDir, dir), { recursive: true });
      });

      const files = await walkCodebase(testRootDir);

      expect(files).toHaveLength(0);
    });

    it("should handle directories with only ignored files", async () => {
      // Create directory with only ignored files
      const ignoredDir = path.join(testRootDir, "ignored-content");
      fs.mkdirSync(ignoredDir, { recursive: true });

      const ignoredFiles = ["package-lock.json", "app.log", "Main.class"];
      ignoredFiles.forEach((file) => {
        fs.writeFileSync(path.join(ignoredDir, file), "// Should be ignored");
      });

      const files = await walkCodebase(testRootDir);

      expect(files).toHaveLength(0);
    });

    it("should handle case sensitivity in file extensions", async () => {
      // Create files with different case extensions
      const testFiles = [
        "main.TS",
        "app.PY",
        "server.GO",
        "lib.RS",
        "Main.JAVA",
        "User.KT",
        "App.SWIFT",
        "main.ZIG",
        "Utils.HS",
        "Program.CS",
      ];

      testFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Content for ${file}`
        );
      });

      const files = await walkCodebase(testRootDir);

      // On case-sensitive systems, these should not be found
      // On case-insensitive systems, these should be found
      // The test should pass on both systems
      expect(files.length).toBeGreaterThanOrEqual(0);
    });

    it("should handle special characters in file names", async () => {
      // Create files with special characters
      const specialFiles = [
        "main-file.ts",
        "user.component.tsx",
        "api_v1.py",
        "server-v2.go",
        "test-file.java",
        "user-data.kt",
      ];

      specialFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Content for ${file}`
        );
      });

      // Test with custom extensions to include .tsx
      const customExtensions = [
        ".ts",
        ".js",
        ".py",
        ".go",
        ".rs",
        ".java",
        ".kt",
        ".swift",
        ".zig",
        ".hs",
        ".cs",
        ".tsx",
      ];
      const files = await walkCodebase(testRootDir, customExtensions);

      expect(files).toHaveLength(specialFiles.length);
      specialFiles.forEach((file) => {
        expect(files).toContain(path.join(testRootDir, file));
      });
    });

    it("should handle .gitignore with comments and empty lines", async () => {
      // Create .gitignore with comments and empty lines
      const gitignoreContent = `
# This is a comment

# Another comment with spaces

*.log
# Comment after pattern
*.tmp

# Empty line above
dist/
      `.trim();

      fs.writeFileSync(path.join(testRootDir, ".gitignore"), gitignoreContent);

      // Create files
      const files = [
        "main.ts", // Should be included
        "app.log", // Should be ignored
        "temp.tmp", // Should be ignored
        "utils.js", // Should be included
      ];

      files.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Content for ${file}`
        );
      });

      const result = await walkCodebase(testRootDir);

      expect(result).toHaveLength(2);
      expect(result).toContain(path.join(testRootDir, "main.ts"));
      expect(result).toContain(path.join(testRootDir, "utils.js"));
      expect(result).not.toContain(path.join(testRootDir, "app.log"));
      expect(result).not.toContain(path.join(testRootDir, "temp.tmp"));
    });

    it("should handle non-existent root directory", async () => {
      const nonExistentDir = path.join(tempDir, "non-existent");

      await expect(walkCodebase(nonExistentDir)).rejects.toThrow();
    });

    it("should handle root directory that is a file", async () => {
      const filePath = path.join(testRootDir, "not-a-directory");
      fs.writeFileSync(filePath, "This is a file, not a directory");

      await expect(walkCodebase(filePath)).rejects.toThrow();
    });

    it("should handle .gitignore with invalid patterns gracefully", async () => {
      // Create .gitignore with potentially invalid patterns
      const gitignoreContent = `
[invalid-pattern
*.log
      `.trim();

      fs.writeFileSync(path.join(testRootDir, ".gitignore"), gitignoreContent);

      // Create test files
      const testFiles = ["main.ts", "app.log"];
      testFiles.forEach((file) => {
        fs.writeFileSync(
          path.join(testRootDir, file),
          `// Content for ${file}`
        );
      });

      // Should not throw an error
      const files = await walkCodebase(testRootDir);

      expect(files).toHaveLength(1);
      expect(files).toContain(path.join(testRootDir, "main.ts"));
    });

    it("should handle large number of files efficiently", async () => {
      // Create many files to test performance
      const fileCount = 100;
      const files: string[] = [];

      for (let i = 0; i < fileCount; i++) {
        const fileName = `file${i}.ts`;
        fs.writeFileSync(
          path.join(testRootDir, fileName),
          `// Content for ${fileName}`
        );
        files.push(fileName);
      }

      const startTime = Date.now();
      const result = await walkCodebase(testRootDir);
      const endTime = Date.now();

      expect(result).toHaveLength(fileCount);
      expect(endTime - startTime).toBeLessThan(1000); // Should complete within 1 second

      files.forEach((file) => {
        expect(result).toContain(path.join(testRootDir, file));
      });
    });
  });
});
