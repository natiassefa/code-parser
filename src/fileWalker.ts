import fs from 'fs';
import path from 'path';
import ignore from 'ignore';

const DEFAULT_IGNORES = [
  'node_modules/',
  '.git/',
  '.DS_Store',
  '*.lock',
  '*.log',
  'dist/',
  'build/',
  'venv/',
  '.venv/',
  '__pycache__/',
  '*.class',
  '*.exe',
];

export async function walkCodebase(
  rootDir: string,
  extensions: string[] = ['.ts', '.js', '.py', '.go', '.rs', '.java', '.kt', '.swift', '.zig', '.hs', '.cs']
): Promise<string[]> {
  const files: string[] = [];
  const ig = ignore();

  const gitignorePath = path.join(rootDir, '.gitignore');
  if (fs.existsSync(gitignorePath)) {
    const gitignoreContent = fs.readFileSync(gitignorePath, 'utf-8');
    ig.add(gitignoreContent.split('\n'));
  }

  ig.add(DEFAULT_IGNORES);

  async function recurse(dir: string) {
    const entries = fs.readdirSync(dir, { withFileTypes: true });
    for (const entry of entries) {
      const fullPath = path.join(dir, entry.name);
      const relativePath = path.relative(rootDir, fullPath);
      if (ig.ignores(relativePath)) continue;

      if (entry.isDirectory()) {
        await recurse(fullPath);
      } else if (extensions.includes(path.extname(entry.name))) {
        files.push(fullPath);
      }
    }
  }

  await recurse(rootDir);
  return files;
}
