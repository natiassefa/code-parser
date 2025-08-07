import express, { Request, Response } from 'express';

const app = express();
const PORT = process.env.PORT || 3000;

app.get('/respond', (req: Request, res: Response) => {
    res.status(200).send('HI');
});

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});

export default app;