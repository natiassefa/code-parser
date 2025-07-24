// Test setup file
import { jest } from "@jest/globals";

// Increase timeout for tree-sitter operations
jest.setTimeout(30000);

// Mock console methods to reduce noise in tests
global.console = {
  ...console,
  log: jest.fn(),
  warn: jest.fn(),
  error: jest.fn(),
};
