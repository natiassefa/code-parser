"use strict";
var __importDefault = (this && this.__importDefault) || function (mod) {
    return (mod && mod.__esModule) ? mod : { "default": mod };
};
Object.defineProperty(exports, "__esModule", { value: true });
const express_1 = __importDefault(require("express"));
const error_1 = require("./middleware/error");
const app = (0, express_1.default)();
const PORT = process.env.PORT || 3000;
// Middleware
app.use(express_1.default.json());
// Routes
app.get('/', (req, res) => {
    res.json({ message: 'Code Parser Server is running!' });
});
app.get('/health', (req, res) => {
    res.json({ status: 'OK', timestamp: new Date().toISOString() });
});
app.get('/respond', (req, res) => {
    res.status(200).send('HI THERE');
});
// Test route that throws an error (for testing purposes)
app.get('/test-error', (req, res) => {
    throw new Error('This is a test error');
});
// Error handling middleware (must be last)
app.use(error_1.notFound);
app.use(error_1.errorHandler);
// Start server
const server = app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});
exports.default = app;
