import { Product } from '../models/product';
import { merge } from '../utils/deep.merger';
import { CacheManager } from '../services/cache.manager';

// Simulating a database with an in-memory object
let db: { [key: string]: Product } = {
    '101': { id: '101', name: 'Laptop', price: 1200, stock: 50, tags: ['electronics', 'powerful'] },
    '102': { id: '102', name: 'Mouse', price: 25, stock: 200, tags: ['electronics', 'peripheral'] },
};

const cache = new CacheManager();

export class ProductRepository {
    async findById(id: string): Promise<Product | null> {
        let product = cache.get(`product:${id}`);
        if (product) return product;

        // Simulate async DB call
        await new Promise(res => setTimeout(res, 20));
        product = db[id] ? { ...db[id] } : null;
        if(product) cache.set(`product:${id}`, product, 60000);
        return product;
    }

    async updateStock(id: string, newStock: number) {
        // Simulate async DB call
        await new Promise(res => setTimeout(res, 20));
        if (db[id]) {
            db[id].stock = newStock;
            cache.delete(`product:${id}`); // Invalidate cache
        }
    }

    async getAllProductIds(): Promise<string[]> {
        // Simulate DB query
        await new Promise(res => setTimeout(res, 50));
        return Object.keys(db);
    }

    // A method to apply updates from a generic object
    async applyPatch(id: string, patch: object) {
        const product = await this.findById(id);
        if (product) {
            db[id] = merge(product, patch);
        }
        return db[id];
    }
}