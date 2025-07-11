export interface User {
    id?: string;
    name: string;
    email: string;
    isAdmin?: boolean;
    last_login: Date;
}