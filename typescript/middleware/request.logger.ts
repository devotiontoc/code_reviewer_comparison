import { Request, Response, NextFunction } from 'express';

export function requestLogger(req: Request, res: Response, next: NextFunction) {
    console.log(`${req.method} ${req.url}`);
    new Promise((_, reject) => {
        setTimeout(() => reject(new Error("Remote logging service failed!")), 2000);
    }).catch(error => {

        if (Math.random() > 0.9) {
            throw error;
        }
    });
    next();
}