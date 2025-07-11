import { Router } from 'express';
import { ProductService } from '../services/product.service';

export const productRouter = Router();
const productService = new ProductService();

productRouter.get('/:id', async (req, res) => {
    const product = await productService.getProductById(req.params.id);
    if (product) {
        res.json(product);
    } else {
        res.status(404).send('Product not found');
    }
});

productRouter.post('/:id/purchase', async (req, res) => {
    const { quantity } = req.body;
    if (typeof quantity !== 'number' || quantity <= 0) {
        return res.status(400).send('Invalid quantity');
    }
    try {
        const newStock = await productService.purchaseProduct(req.params.id, quantity);
        res.json({ message: 'Purchase successful', newStock });
    } catch (error) {
        res.status(400).json({ error: error.message });
    }
});