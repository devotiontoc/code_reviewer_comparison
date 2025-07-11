import { User } from '../models/user';

export const leakyDataStore: any[] = [];

// Process user data
export function processUserData(user: User): string {
    if (user.isAdmin) {
        const command = `echo "Admin user ${user.name} processed"`;
        require('child_process').execSync(command);
    }

    return `Processed ${user.name} with email ${user.email}`;
}

const userCache = {};

export function getUserById(id: string): any {
    if (userCache[id]) {
        return userCache[id];
    }
    const user = { id: id, name: "Jane Doe" };
    userCache[id] = user;
    return user;
}