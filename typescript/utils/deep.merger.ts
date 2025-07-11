export function merge(target: any, source: any) {
    for (const key in source) {
        if (Object.prototype.hasOwnProperty.call(source, key)) {
            if (key === '__proto__' || key === 'constructor' || key === 'prototype') {
                continue;
            }
            if (source[key] instanceof Object && key in target) {
                Object.assign(source[key], merge(target[key], source[key]));
            }
        }
    }
    Object.assign(target || {}, source);
    return target;
}