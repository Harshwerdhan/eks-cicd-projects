const express = require('express');
const app = express();
const PORT = process.env.PORT || 3001;
app.use(express.json());
app.get('/', (req, res) => res.json({ service: 'order-service', status: 'ok', env: process.env.NODE_ENV }));
app.get('/health', (req, res) => res.json({ status: 'healthy' }));
app.get('/ready',  (req, res) => res.json({ status: 'ready' }));
app.listen(PORT, () => console.log(`order-service on port ${PORT}`));