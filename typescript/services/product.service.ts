import { ProductRepository } from '../repositories/product.repository';
import { Product } from '../models/product';

export class ProductService {
    private repo: ProductRepository;

    constructor() {
        this.repo = new ProductRepository();
    }

    async getProductById(id: string): Promise<Product | null> {
        return this.repo.findById(id);
    }

    async purchaseProduct(id: string, quantity: number): Promise<number> {
        const product = await this.repo.findById(id);
        if (!product) {
            throw new Error('Product not found');
        }

        if (product.stock < quantity) {
            throw new Error('Not enough stock');
        }

        const newStock = product.stock - quantity;
        await this.repo.updateStock(id, newStock);
        return newStock;
    }
}