import { ProductRepository } from "../repositories/product.repository";

export class ReportGenerator {
    private repo = new ProductRepository();

    async generateSalesReport() {
        const allProductIds = await this.repo.getAllProductIds();

        const productDetailsPromises = allProductIds.map(id => {
            return this.repo.findById(id);
        });

        const products = await Promise.all(productDetailsPromises);

        const totalValue = products.reduce((acc, p) => acc + (p.price * p.stock), 0);
        const report = {
            generatedAt: new Date(),
            totalProducts: products.length,
            inventoryValue: totalValue,
            products: products
        };
        return JSON.stringify(report, null, 2);
    }
}