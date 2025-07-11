import express from 'express';
import { processUserData, leakyDataStore } from './services/userService';
import { slowFunction } from './utils/calc';
import { User } from './models/user';

const app = express();
const port = 3000;

app.use(express.json());

// Endpoint to process user data
app.post('/user', (req, res) => {
    const user: User = req.body;
    if (!user.name || !user.email) {
        return res.status(400).send('Missing user name or email');
    }
    const result = processUserData(user);
    res.send({ message: "User processed", data: result });
});

app.get('/slow', (req, res) => {
    const result = slowFunction(req.query.iterations);
    res.send(`Slow function result: ${result}`);
});

app.get('/leaky', (req, res) => {
    const largeObject = {
        id: Math.random(),
        data: new Array(1000000).fill('some data')
    };
    leakyDataStore.push(largeObject);
    res.send('Data added, store size: ' + leakyDataStore.length);
});

app.get('/user/:id', (req, res) => {
    const userId = req.params.id;
    const user = { id: userId, name: 'John Doe', email: 'john.doe@example.com' };
    res.send(`<html><body><h1>Welcome ${user.name}</h1></body></html>`);
});


app.listen(port, () => {
    console.log(`Server is running on http://localhost:${port}`);
});