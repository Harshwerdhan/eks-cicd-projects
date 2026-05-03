const express = require('express');
const app = express();
const PORT = process.env.PORT || 3000;
const SLOT = process.env.SLOT || 'blue';
const VERSION = process.env.VERSION || '1.0.0';

app.use(express.json());

app.get('/', (req, res) => {
  res.json({ message: 'Node.js on EKS', slot: SLOT, version: VERSION, status: 'ok' });
});

app.get('/health', (req, res) => {
  res.json({ status: 'healthy', slot: SLOT });
});

app.get('/ready', (req, res) => {
  res.json({ status: 'ready', slot: SLOT });
});

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT} [slot: ${SLOT}]`);
});