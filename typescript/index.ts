import express from 'express';
import { productRouter } from './controllers/product.cotroller';
import { reportRouter } from './controllers/report.conroller';
import { requestLogger } from './middleware/request.logger';

const app = express();
const PORT = 3000;

app.use(express.json());
app.use(requestLogger); // Apply logging middleware

app.use('/api/products', productRouter);
app.use('/api/reports', reportRouter);

app.listen(PORT, () => {
    console.log(`Server is running on port ${PORT}`);
});