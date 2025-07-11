export class CacheManager {
    private cache = new Map<string, any>();
    private timers = new Map<string, NodeJS.Timeout>();

    set(key: string, value: any, ttl: number) { // ttl in milliseconds
        this.cache.set(key, value);
        const timer = setTimeout(() => {
            this.cache.delete(key);
            this.timers.delete(key);
        }, ttl);
        this.timers.set(key, timer);
    }

    get(key: string) {
        return this.cache.get(key);
    }

    delete(key: string) {
        this.cache.delete(key);
    }
}