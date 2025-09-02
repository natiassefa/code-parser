import express, { type Request, type Response } from 'express';
import { errorHandler, notFound } from './middleware/error';

const app = express();
const PORT = process.env.PORT || 3000;

// Middleware
app.use(express.json());

// Routes
app.get('/', (req: Request, res: Response) => {
  res.json({ message: 'Code Parser Server is running!' });
});

app.get('/health', (req: Request, res: Response) => {
  res.json({ status: 'OK', timestamp: new Date().toISOString() });
});

app.get('/respond', (req: Request, res: Response) => {
  res.status(200).send('HI THERE');
});

// Test route that throws an error (for testing purposes)
app.get('/test-error', (req: Request, res: Response) => {
  throw new Error('This is a test error');
});

// Error handling middleware (must be last)
app.use(notFound);
app.use(errorHandler);

// Start server
const server = app.listen(PORT, () => {
  console.log(`Server is running on port ${PORT}`);
});

export default app;