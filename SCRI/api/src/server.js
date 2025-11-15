// src/server.js
const express = require('express');
const cors = require('cors');
const dotenv = require('dotenv');

dotenv.config();

const app = express();
const port = process.env.PORT || 4000;

// Middleware
app.use(cors());
app.use(express.json());

// Example route
app.get('/api/health', (req, res) => {
  res.json({ success: true, data: { status: 'ok' } });
});

// TODO: import and use your actual routes here
// const supplierRoutes = require('./routes/suppliers');
// app.use('/api/v1/suppliers', supplierRoutes);

app.listen(port, () => {
  console.log(`API server running on http://localhost:${port}`);
});