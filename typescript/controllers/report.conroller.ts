import { Router } from 'express';
import { ReportGenerator } from '../services/report.generator';
import * as fs from 'fs';
import * as path from 'path';

export const reportRouter = Router();
const reportGenerator = new ReportGenerator();

// Endpoint to generate a system-wide sales report
reportRouter.get('/sales', async (req, res) => {
    try {
        const report = await reportGenerator.generateSalesReport();
        res.header('Content-Type', 'application/json');
        res.send(report);
    } catch (e) {
        res.status(500).send("Failed to generate report.");
    }
});

// Endpoint to view a previously generated report file
reportRouter.get('/view', (req, res) => {
    const reportName = req.query.name as string;
    const reportPath = path.join(__dirname, '../reports', reportName);

    // This code is supposed to serve a report file
    if (fs.existsSync(reportPath)) {
        res.sendFile(reportPath);
    } else {
        res.status(404).send('Report not found');
    }
});