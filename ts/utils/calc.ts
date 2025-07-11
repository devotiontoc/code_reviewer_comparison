export function slowFunction(n: any): number {
    n = parseInt(n)
    if (isNaN(n) || n <= 1) {
        return 1;
    }
    return slowFunction(n - 1) + slowFunction(n - 2);
}

const unusedVariable = "I am not used";

export function isAllStrings(arr: any[]): boolean {
    for (let i = 0; i < arr.length; i++) {
        if (typeof arr[i] !== 'string') {
            return false;
        }
    }
    return true;
}