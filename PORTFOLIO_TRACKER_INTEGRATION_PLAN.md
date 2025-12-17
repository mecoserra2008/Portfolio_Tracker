# Portfolio Tracker Integration Plan
## Apoena Wealth Management - Private Portfolio Access System

---

## 📋 Executive Summary

This document outlines the architecture and integration strategy for building a **private portfolio tracker system** that connects with the Apoena Wealth Management website. The system will display real-time portfolio performance metrics with **email-based access control**, ensuring only authorized clients can view their specific portfolio data.

---

## 🎯 Project Goals

1. **Separate Portfolio Tracker Application** - Standalone system for portfolio tracking and analytics
2. **Seamless Website Integration** - Connect tracker with existing website structure
3. **Email-Based Authentication** - Whitelist system for authorized client access
4. **Private Performance Display** - Show metrics only to authenticated users
5. **Scalable Architecture** - Easy to add/remove client access

---

## 🏗️ System Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Apoena Wealth Website                     │
│                  (Public-facing frontend)                    │
│  - Home, About, Services, Contact (PUBLIC)                  │
│  - Login Portal Link (PUBLIC)                               │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Authentication Check
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              Authentication Service (Backend)                │
│  - Email verification                                        │
│  - Whitelist management                                     │
│  - JWT token generation                                     │
│  - Session management                                       │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Authenticated Access
                     ▼
┌─────────────────────────────────────────────────────────────┐
│            Portfolio Tracker Application                     │
│              (Private Client Portal)                         │
│  - Real-time portfolio performance                          │
│  - Historical data & charts                                 │
│  - Asset allocation                                         │
│  - Transaction history                                      │
│  - Reports & documents                                      │
└────────────────────┬────────────────────────────────────────┘
                     │
                     │ Data Layer
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                   Database Layer                             │
│  - User/Client data (email whitelist)                       │
│  - Portfolio holdings                                       │
│  - Performance metrics                                      │
│  - Historical data                                          │
└─────────────────────────────────────────────────────────────┘
```

---

## 📦 Component Breakdown

### 1. **Portfolio Tracker (Separate Application)**

**Purpose:** Standalone application for portfolio management and analytics

**Technology Stack (Recommended):**
- **Frontend:** React (matches existing website) or Next.js (for SSR)
- **Backend:** Node.js + Express OR Python + FastAPI
- **Database:** PostgreSQL (structured data) + TimescaleDB (time-series)
- **Authentication:** Auth0, Firebase Auth, or Custom JWT
- **Real-time Updates:** WebSocket (Socket.io) or Server-Sent Events (SSE)
- **Charts:** Recharts (already installed) or Chart.js

**Key Features:**
```javascript
// Core Modules
├── Authentication Module
│   ├── Email verification
│   ├── Magic link login (passwordless)
│   ├── JWT token management
│   └── Session handling
│
├── Portfolio Management
│   ├── Real-time portfolio valuation
│   ├── Holdings display
│   ├── Asset allocation breakdown
│   └── Performance attribution
│
├── Analytics & Reporting
│   ├── Performance charts (YTD, 1Y, 3Y, 5Y)
│   ├── Benchmark comparison
│   ├── Risk metrics (Sharpe, volatility, drawdown)
│   └── Monthly/quarterly reports
│
├── Data Integration
│   ├── Market data feeds (APIs)
│   ├── Manual position uploads
│   ├── Broker integrations (optional)
│   └── Data validation
│
└── Admin Panel
    ├── Client whitelist management
    ├── Permission control
    ├── Portfolio data management
    └── System monitoring
```

---

### 2. **Website Integration Points**

**Current Website Structure:**
```
apoena-wealth/
├── src/
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Header.jsx          ← ADD LOGIN BUTTON
│   │   │   └── Footer.jsx          ← ADD CLIENT PORTAL LINK
│   ├── pages/
│   │   ├── Performance.jsx         ← CREATE (Public overview)
│   │   └── ClientPortalLogin.jsx   ← CREATE (Login page)
│   └── App.js                      ← ADD ROUTES
```

**Integration Steps:**

#### Step 1: Add Login/Portal Access to Website
```jsx
// Update Header.jsx - Add Client Portal button
<nav>
  {/* Existing nav items */}
  <Button href="/client-login" variant="secondary" size="sm">
    Client Portal
  </Button>
</nav>

// Create new page: ClientPortalLogin.jsx
import React, { useState } from 'react';

const ClientPortalLogin = () => {
  const [email, setEmail] = useState('');

  const handleLogin = async (e) => {
    e.preventDefault();
    // Check if email is whitelisted
    // Send magic link or authenticate
    // Redirect to portfolio tracker
  };

  return (
    <div className="min-h-screen flex items-center justify-center">
      <Card className="max-w-md w-full p-8">
        <h2 className="text-3xl font-bold mb-6">Client Portal Access</h2>
        <form onSubmit={handleLogin}>
          <Input
            type="email"
            label="Email Address"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            placeholder="your.email@example.com"
            required
          />
          <Button type="submit" className="w-full mt-4">
            Access Portfolio
          </Button>
        </form>
        <p className="text-sm text-neutral-500 mt-4">
          Only authorized clients can access the portfolio.
          Contact us if you need assistance.
        </p>
      </Card>
    </div>
  );
};

export default ClientPortalLogin;
```

#### Step 2: Update App.js Routes
```jsx
import ClientPortalLogin from './pages/ClientPortalLogin';

// In Routes:
<Route path="/client-login" element={<ClientPortalLogin />} />
```

---

## 🔐 Authentication & Access Control System

### Email Whitelist Architecture

**Database Schema:**
```sql
-- Clients/Users Table
CREATE TABLE clients (
  id SERIAL PRIMARY KEY,
  email VARCHAR(255) UNIQUE NOT NULL,
  full_name VARCHAR(255) NOT NULL,
  status VARCHAR(50) DEFAULT 'active', -- active, inactive, suspended
  access_level VARCHAR(50) DEFAULT 'client', -- client, admin
  created_at TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP,
  metadata JSONB -- Additional client info
);

-- Access Tokens Table
CREATE TABLE access_tokens (
  id SERIAL PRIMARY KEY,
  client_id INTEGER REFERENCES clients(id),
  token VARCHAR(500) UNIQUE NOT NULL,
  expires_at TIMESTAMP NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Whitelist Audit Log
CREATE TABLE whitelist_audit (
  id SERIAL PRIMARY KEY,
  client_id INTEGER REFERENCES clients(id),
  action VARCHAR(50), -- added, removed, modified
  performed_by VARCHAR(255),
  performed_at TIMESTAMP DEFAULT NOW(),
  details JSONB
);
```

### Authentication Flow

```
1. User enters email on website login page
   │
   ├─→ Check if email exists in whitelist
   │   │
   │   ├─→ NO: Show "Access Denied" message
   │   │         "Contact Apoena Wealth for access"
   │   │
   │   └─→ YES: Continue to Step 2
   │
2. Generate magic link / OTP
   │
   ├─→ Send email with secure link/code
   │   - Link expires in 15 minutes
   │   - One-time use token
   │
3. User clicks link / enters code
   │
   ├─→ Verify token validity
   │   │
   │   └─→ Generate JWT session token
   │       - Includes: client_id, email, access_level
   │       - Expires: 7 days (configurable)
   │
4. Redirect to Portfolio Tracker with JWT
   │
   └─→ Portfolio app validates JWT on each request
       - Check signature
       - Check expiration
       - Load client-specific portfolio data
```

---

## 🔧 Implementation Guide

### Phase 1: Backend API Setup

**Option A: Node.js + Express**
```javascript
// server.js - Basic structure
const express = require('express');
const jwt = require('jsonwebtoken');
const nodemailer = require('nodemailer');
const { Pool } = require('pg');

const app = express();
const pool = new Pool({ /* DB config */ });

// Middleware
app.use(express.json());
app.use(cors());

// 1. Check if email is whitelisted
app.post('/api/auth/check-access', async (req, res) => {
  const { email } = req.body;

  const result = await pool.query(
    'SELECT id, email, full_name, status FROM clients WHERE email = $1 AND status = $2',
    [email, 'active']
  );

  if (result.rows.length === 0) {
    return res.status(403).json({
      error: 'Access denied',
      message: 'Email not authorized. Contact Apoena Wealth for access.'
    });
  }

  // Generate magic link token
  const token = jwt.sign(
    { email, purpose: 'magic-link' },
    process.env.JWT_SECRET,
    { expiresIn: '15m' }
  );

  // Send email with magic link
  await sendMagicLink(email, token);

  res.json({ success: true, message: 'Magic link sent to your email' });
});

// 2. Verify magic link and create session
app.post('/api/auth/verify-magic-link', async (req, res) => {
  const { token } = req.body;

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);

    // Get client data
    const client = await pool.query(
      'SELECT id, email, full_name, access_level FROM clients WHERE email = $1',
      [decoded.email]
    );

    // Generate session token (longer lived)
    const sessionToken = jwt.sign(
      {
        clientId: client.rows[0].id,
        email: client.rows[0].email,
        accessLevel: client.rows[0].access_level
      },
      process.env.JWT_SECRET,
      { expiresIn: '7d' }
    );

    // Update last login
    await pool.query(
      'UPDATE clients SET last_login = NOW() WHERE id = $1',
      [client.rows[0].id]
    );

    res.json({
      success: true,
      token: sessionToken,
      client: client.rows[0]
    });

  } catch (error) {
    res.status(401).json({ error: 'Invalid or expired token' });
  }
});

// 3. Protected route example - Get portfolio data
app.get('/api/portfolio/:clientId', authenticateToken, async (req, res) => {
  const { clientId } = req.params;

  // Verify user can only access their own portfolio
  if (req.user.clientId !== parseInt(clientId) && req.user.accessLevel !== 'admin') {
    return res.status(403).json({ error: 'Unauthorized' });
  }

  // Get portfolio data
  const portfolio = await pool.query(
    'SELECT * FROM portfolios WHERE client_id = $1',
    [clientId]
  );

  res.json(portfolio.rows[0]);
});

// Authentication middleware
function authenticateToken(req, res, next) {
  const token = req.headers['authorization']?.split(' ')[1];

  if (!token) {
    return res.status(401).json({ error: 'No token provided' });
  }

  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) return res.status(403).json({ error: 'Invalid token' });
    req.user = user;
    next();
  });
}

// Admin endpoint - Add email to whitelist
app.post('/api/admin/whitelist/add', authenticateToken, async (req, res) => {
  // Verify admin access
  if (req.user.accessLevel !== 'admin') {
    return res.status(403).json({ error: 'Admin access required' });
  }

  const { email, fullName } = req.body;

  try {
    const result = await pool.query(
      'INSERT INTO clients (email, full_name, status) VALUES ($1, $2, $3) RETURNING *',
      [email, fullName, 'active']
    );

    // Log audit trail
    await pool.query(
      'INSERT INTO whitelist_audit (client_id, action, performed_by) VALUES ($1, $2, $3)',
      [result.rows[0].id, 'added', req.user.email]
    );

    res.json({ success: true, client: result.rows[0] });
  } catch (error) {
    res.status(400).json({ error: 'Email already exists or invalid data' });
  }
});

app.listen(5000, () => console.log('Server running on port 5000'));
```

---

### Phase 2: Portfolio Tracker Frontend

**Create separate React app:**
```bash
# In APOENA_WEBSITE directory
npx create-react-app portfolio-tracker
cd portfolio-tracker
npm install axios recharts jwt-decode react-router-dom
```

**Basic Structure:**
```javascript
// portfolio-tracker/src/App.js
import React, { useState, useEffect } from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import Login from './pages/Login';

const PrivateRoute = ({ children }) => {
  const token = localStorage.getItem('apoena_token');
  return token ? children : <Navigate to="/login" />;
};

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<Login />} />
        <Route path="/dashboard" element={
          <PrivateRoute>
            <Dashboard />
          </PrivateRoute>
        } />
      </Routes>
    </BrowserRouter>
  );
}

// portfolio-tracker/src/pages/Dashboard.jsx
import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';

const Dashboard = () => {
  const [portfolio, setPortfolio] = useState(null);
  const [performance, setPerformance] = useState([]);

  useEffect(() => {
    const token = localStorage.getItem('apoena_token');
    const decoded = jwt_decode(token);

    // Fetch portfolio data
    axios.get(`/api/portfolio/${decoded.clientId}`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => setPortfolio(res.data))
    .catch(err => console.error(err));

    // Fetch performance data
    axios.get(`/api/portfolio/${decoded.clientId}/performance`, {
      headers: { Authorization: `Bearer ${token}` }
    })
    .then(res => setPerformance(res.data))
    .catch(err => console.error(err));
  }, []);

  if (!portfolio) return <div>Loading...</div>;

  return (
    <div className="p-8">
      <h1 className="text-4xl font-bold mb-8">Portfolio Dashboard</h1>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500 mb-2">Total Value</h3>
          <p className="text-3xl font-bold">${portfolio.total_value.toLocaleString()}</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500 mb-2">Total Return</h3>
          <p className="text-3xl font-bold text-green-600">+{portfolio.total_return}%</p>
        </div>
        <div className="bg-white p-6 rounded-lg shadow">
          <h3 className="text-sm text-gray-500 mb-2">YTD Return</h3>
          <p className="text-3xl font-bold">{portfolio.ytd_return}%</p>
        </div>
      </div>

      <div className="bg-white p-6 rounded-lg shadow">
        <h2 className="text-2xl font-bold mb-4">Performance</h2>
        <LineChart width={800} height={400} data={performance}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="date" />
          <YAxis />
          <Tooltip />
          <Line type="monotone" dataKey="value" stroke="#10B981" />
        </LineChart>
      </div>
    </div>
  );
};

export default Dashboard;
```

---

### Phase 3: Connecting Website to Portfolio Tracker

**Deployment Architecture:**

```
Domain Structure:
├── apoenawealth.com              → Main website (current)
└── portal.apoenawealth.com       → Portfolio tracker app
    OR
├── apoenawealth.com              → Main website
└── apoenawealth.com/portal       → Portfolio tracker (subpath)
```

**Integration Options:**

**Option 1: Subdomain (Recommended)**
```
- Main Website: apoenawealth.com (Netlify/Vercel)
- Portfolio App: portal.apoenawealth.com (Separate deployment)
- API Backend: api.apoenawealth.com (Node.js server)

Benefits:
✓ Clean separation
✓ Independent scaling
✓ Easier to maintain
✓ Different tech stacks possible
```

**Option 2: Subpath**
```
- Main Website: apoenawealth.com
- Portfolio App: apoenawealth.com/portal
- API Backend: apoenawealth.com/api

Benefits:
✓ Single domain
✓ Simplified SSL
✓ Shared authentication domain
```

**Connection Flow:**
```javascript
// In main website: ClientPortalLogin.jsx
const handleLogin = async (e) => {
  e.preventDefault();

  try {
    // Call your backend API
    const response = await fetch('https://api.apoenawealth.com/auth/check-access', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email })
    });

    if (response.ok) {
      // Magic link sent
      setMessage('Check your email for login link');
    } else {
      setError('Access denied. Contact us for access.');
    }
  } catch (error) {
    setError('Error. Please try again.');
  }
};

// Magic link format:
// https://portal.apoenawealth.com/auth/verify?token=xxx
// OR
// https://apoenawealth.com/portal/auth/verify?token=xxx
```

---

## 👤 Admin Management Interface

**Admin Panel Features:**

```javascript
// Admin Dashboard Structure
const AdminPanel = () => {
  return (
    <div>
      <h1>Client Access Management</h1>

      {/* 1. Add New Client */}
      <section>
        <h2>Add Client to Whitelist</h2>
        <form onSubmit={handleAddClient}>
          <input type="email" placeholder="client@example.com" />
          <input type="text" placeholder="Full Name" />
          <button>Add Client</button>
        </form>
      </section>

      {/* 2. Manage Existing Clients */}
      <section>
        <h2>Whitelisted Clients</h2>
        <table>
          <thead>
            <tr>
              <th>Email</th>
              <th>Name</th>
              <th>Status</th>
              <th>Last Login</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {clients.map(client => (
              <tr key={client.id}>
                <td>{client.email}</td>
                <td>{client.full_name}</td>
                <td>{client.status}</td>
                <td>{client.last_login}</td>
                <td>
                  <button onClick={() => deactivateClient(client.id)}>
                    Deactivate
                  </button>
                  <button onClick={() => deleteClient(client.id)}>
                    Remove
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>

      {/* 3. Bulk Upload */}
      <section>
        <h2>Bulk Upload Clients</h2>
        <input type="file" accept=".csv" onChange={handleBulkUpload} />
        <p>Upload CSV with columns: email, full_name</p>
      </section>

      {/* 4. Audit Log */}
      <section>
        <h2>Access Audit Log</h2>
        <table>
          <thead>
            <tr>
              <th>Date</th>
              <th>Action</th>
              <th>Client</th>
              <th>Performed By</th>
            </tr>
          </thead>
          <tbody>
            {auditLog.map(log => (
              <tr key={log.id}>
                <td>{log.performed_at}</td>
                <td>{log.action}</td>
                <td>{log.client_email}</td>
                <td>{log.performed_by}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
    </div>
  );
};
```

---

## 📊 Portfolio Data Structure

**Database Schema for Portfolio Tracking:**

```sql
-- Portfolios Table
CREATE TABLE portfolios (
  id SERIAL PRIMARY KEY,
  client_id INTEGER REFERENCES clients(id),
  name VARCHAR(255) DEFAULT 'Main Portfolio',
  total_value DECIMAL(15, 2),
  cash_balance DECIMAL(15, 2),
  invested_amount DECIMAL(15, 2),
  total_return_pct DECIMAL(8, 4),
  ytd_return_pct DECIMAL(8, 4),
  inception_date DATE,
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Holdings Table
CREATE TABLE holdings (
  id SERIAL PRIMARY KEY,
  portfolio_id INTEGER REFERENCES portfolios(id),
  asset_type VARCHAR(50), -- stock, bond, etf, crypto, etc.
  symbol VARCHAR(20),
  name VARCHAR(255),
  quantity DECIMAL(15, 6),
  avg_cost DECIMAL(15, 4),
  current_price DECIMAL(15, 4),
  market_value DECIMAL(15, 2),
  unrealized_gain_loss DECIMAL(15, 2),
  weight_pct DECIMAL(5, 2), -- % of portfolio
  updated_at TIMESTAMP DEFAULT NOW()
);

-- Performance History Table (Time-series)
CREATE TABLE performance_history (
  id SERIAL PRIMARY KEY,
  portfolio_id INTEGER REFERENCES portfolios(id),
  date DATE NOT NULL,
  portfolio_value DECIMAL(15, 2),
  daily_return_pct DECIMAL(8, 4),
  cumulative_return_pct DECIMAL(8, 4),
  benchmark_value DECIMAL(15, 2), -- for comparison
  benchmark_return_pct DECIMAL(8, 4),
  UNIQUE(portfolio_id, date)
);

-- Transactions Table
CREATE TABLE transactions (
  id SERIAL PRIMARY KEY,
  portfolio_id INTEGER REFERENCES portfolios(id),
  transaction_type VARCHAR(20), -- buy, sell, dividend, deposit, withdrawal
  asset_type VARCHAR(50),
  symbol VARCHAR(20),
  quantity DECIMAL(15, 6),
  price DECIMAL(15, 4),
  total_amount DECIMAL(15, 2),
  fee DECIMAL(10, 2),
  transaction_date TIMESTAMP,
  notes TEXT,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX idx_holdings_portfolio ON holdings(portfolio_id);
CREATE INDEX idx_performance_portfolio_date ON performance_history(portfolio_id, date DESC);
CREATE INDEX idx_transactions_portfolio ON transactions(portfolio_id, transaction_date DESC);
```

---

## 🔄 Data Flow & Updates

### Real-time Updates Strategy

```javascript
// Option 1: WebSocket for real-time updates
const WebSocket = require('ws');
const wss = new WebSocket.Server({ port: 8080 });

wss.on('connection', (ws, req) => {
  // Authenticate connection
  const token = req.headers.authorization;
  const user = verifyToken(token);

  // Subscribe to portfolio updates for this user
  ws.on('message', (message) => {
    const data = JSON.parse(message);
    if (data.type === 'subscribe_portfolio') {
      // Add to subscriber list
      subscribers[user.clientId] = ws;
    }
  });
});

// When portfolio updates (from market data or admin):
function broadcastPortfolioUpdate(clientId, portfolioData) {
  if (subscribers[clientId]) {
    subscribers[clientId].send(JSON.stringify({
      type: 'portfolio_update',
      data: portfolioData
    }));
  }
}

// Option 2: Polling (simpler)
// Client polls every 30 seconds for updates
useEffect(() => {
  const interval = setInterval(() => {
    fetchPortfolioData();
  }, 30000); // 30 seconds

  return () => clearInterval(interval);
}, []);
```

### Market Data Integration

```javascript
// Example: Integrate with financial data API
const fetchMarketData = async (symbols) => {
  // Option 1: Alpha Vantage (free tier available)
  const API_KEY = 'your_api_key';
  const url = `https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol=${symbols}&apikey=${API_KEY}`;

  // Option 2: Yahoo Finance (via unofficial API)
  // Option 3: IEX Cloud
  // Option 4: Twelve Data

  const response = await fetch(url);
  const data = await response.json();
  return data;
};

// Update portfolio values based on current market prices
const updatePortfolioValues = async (portfolioId) => {
  // Get all holdings
  const holdings = await db.query(
    'SELECT * FROM holdings WHERE portfolio_id = $1',
    [portfolioId]
  );

  // Fetch current prices for all symbols
  const symbols = holdings.rows.map(h => h.symbol);
  const prices = await fetchMarketData(symbols);

  // Update each holding
  for (const holding of holdings.rows) {
    const currentPrice = prices[holding.symbol];
    const marketValue = holding.quantity * currentPrice;
    const unrealizedGain = marketValue - (holding.quantity * holding.avg_cost);

    await db.query(
      'UPDATE holdings SET current_price = $1, market_value = $2, unrealized_gain_loss = $3, updated_at = NOW() WHERE id = $4',
      [currentPrice, marketValue, unrealizedGain, holding.id]
    );
  }

  // Recalculate portfolio total
  const portfolioTotal = await db.query(
    'SELECT SUM(market_value) as total FROM holdings WHERE portfolio_id = $1',
    [portfolioId]
  );

  await db.query(
    'UPDATE portfolios SET total_value = $1, updated_at = NOW() WHERE id = $2',
    [portfolioTotal.rows[0].total, portfolioId]
  );
};

// Schedule regular updates
const cron = require('node-cron');

// Update all portfolios every 5 minutes during market hours
cron.schedule('*/5 9-16 * * 1-5', async () => {
  const portfolios = await db.query('SELECT id FROM portfolios');
  for (const portfolio of portfolios.rows) {
    await updatePortfolioValues(portfolio.id);
  }
});
```

---

## 🚀 Deployment Strategy

### Step-by-Step Deployment

**1. Backend API Deployment**
```bash
# Option 1: Heroku
heroku create apoena-api
heroku addons:create heroku-postgresql:hobby-dev
git push heroku main

# Option 2: Railway
railway init
railway add postgresql
railway up

# Option 3: DigitalOcean App Platform
doctl apps create --spec api-spec.yaml

# Option 4: AWS (EC2 + RDS)
# More complex but more control
```

**2. Database Setup**
```bash
# Run migrations
psql $DATABASE_URL -f migrations/001_create_tables.sql
psql $DATABASE_URL -f migrations/002_create_indexes.sql

# Seed admin user
psql $DATABASE_URL -c "INSERT INTO clients (email, full_name, access_level) VALUES ('admin@apoenawealth.com', 'Admin', 'admin')"
```

**3. Portfolio Tracker Frontend**
```bash
# Build
cd portfolio-tracker
npm run build

# Deploy to Vercel
vercel --prod

# OR Deploy to Netlify
netlify deploy --prod --dir=build
```

**4. Configure DNS**
```
Add CNAME records:
api.apoenawealth.com  → your-backend-url.herokuapp.com
portal.apoenawealth.com → your-vercel-url.vercel.app
```

**5. Environment Variables**
```bash
# Backend (.env)
DATABASE_URL=postgresql://...
JWT_SECRET=your-secret-key-here-use-random-string
SENDGRID_API_KEY=your-sendgrid-key  # for emails
ALPHA_VANTAGE_KEY=your-api-key      # for market data
CORS_ORIGIN=https://apoenawealth.com,https://portal.apoenawealth.com
NODE_ENV=production

# Frontend (.env)
REACT_APP_API_URL=https://api.apoenawealth.com
REACT_APP_MAIN_SITE_URL=https://apoenawealth.com
```

---

## 📝 Implementation Checklist

### Phase 1: Backend Foundation (Week 1-2)
- [ ] Set up Node.js/Express server
- [ ] Configure PostgreSQL database
- [ ] Create database schema (clients, portfolios, holdings, etc.)
- [ ] Implement email whitelist system
- [ ] Build authentication endpoints (check-access, verify-token)
- [ ] Set up JWT token generation
- [ ] Configure email service (SendGrid/AWS SES)
- [ ] Create magic link email templates
- [ ] Test authentication flow end-to-end

### Phase 2: Portfolio Tracker App (Week 2-3)
- [ ] Create new React app for portfolio tracker
- [ ] Build login page (receives magic link)
- [ ] Implement token validation
- [ ] Create dashboard layout
- [ ] Build portfolio overview component
- [ ] Add performance chart component
- [ ] Create holdings table component
- [ ] Add transaction history view
- [ ] Implement responsive design
- [ ] Add loading states & error handling

### Phase 3: Website Integration (Week 3-4)
- [ ] Add "Client Portal" button to Header
- [ ] Create ClientPortalLogin page in main website
- [ ] Build email verification form
- [ ] Add success/error messaging
- [ ] Update App.js with new routes
- [ ] Style login page to match website design
- [ ] Add link in Footer
- [ ] Test navigation flow

### Phase 4: Admin Panel (Week 4)
- [ ] Create admin authentication
- [ ] Build admin dashboard
- [ ] Implement "Add Client" form
- [ ] Create client list view with filters
- [ ] Add activate/deactivate functionality
- [ ] Build bulk upload feature (CSV)
- [ ] Create audit log view
- [ ] Add client search functionality

### Phase 5: Data Integration (Week 5)
- [ ] Choose market data provider (Alpha Vantage, etc.)
- [ ] Build market data fetching service
- [ ] Create portfolio valuation calculator
- [ ] Implement performance calculations
- [ ] Set up automated data updates (cron jobs)
- [ ] Build manual data entry interface (admin)
- [ ] Add data validation

### Phase 6: Testing & Security (Week 6)
- [ ] Security audit (SQL injection, XSS, CSRF)
- [ ] Rate limiting on API endpoints
- [ ] Test email whitelist system
- [ ] Test authentication flow (happy path & errors)
- [ ] Cross-browser testing
- [ ] Mobile responsiveness testing
- [ ] Load testing (simulate multiple users)
- [ ] Backup strategy implementation

### Phase 7: Deployment (Week 7)
- [ ] Deploy backend API
- [ ] Deploy database (with backups)
- [ ] Deploy portfolio tracker frontend
- [ ] Configure DNS records
- [ ] Set up SSL certificates
- [ ] Configure CORS properly
- [ ] Set up monitoring (errors, uptime)
- [ ] Deploy admin panel
- [ ] Create deployment documentation

### Phase 8: Launch & Handoff (Week 8)
- [ ] Add first batch of client emails
- [ ] Send welcome emails to clients
- [ ] Create user documentation
- [ ] Create admin documentation
- [ ] Set up support email/system
- [ ] Final testing with real users
- [ ] Monitor for issues
- [ ] Gather feedback

---

## 🔒 Security Best Practices

### Critical Security Measures

1. **JWT Token Security**
   - Use strong secret (min 32 characters random)
   - Set reasonable expiration (7 days max)
   - Store tokens in httpOnly cookies (not localStorage for production)
   - Implement token refresh mechanism
   - Blacklist on logout

2. **Email Verification**
   - Rate limit login attempts (5 per hour per email)
   - Magic links expire in 15 minutes
   - One-time use tokens
   - Log all login attempts

3. **Database Security**
   - Use parameterized queries (prevent SQL injection)
   - Encrypt sensitive data at rest
   - Regular backups (daily minimum)
   - Principle of least privilege for DB user

4. **API Security**
   - HTTPS only (enforce SSL)
   - CORS configured properly
   - Rate limiting on all endpoints
   - Input validation & sanitization
   - API versioning (/api/v1/...)

5. **Client Data Privacy**
   - Each client can ONLY see their own data
   - Double-check authorization on every request
   - Audit log all data access
   - GDPR compliance considerations
   - Data retention policies

---

## 💰 Cost Estimates

### Hosting & Services (Monthly)

**Option 1: Minimal Cost (Startup)**
- Backend API: Heroku/Railway free tier → $0-7
- Database: Heroku Postgres Hobby → $0-9
- Frontend: Netlify/Vercel free tier → $0
- Email: SendGrid free tier (100/day) → $0
- Market Data: Alpha Vantage free → $0
- **Total: $0-16/month**

**Option 2: Production Ready**
- Backend API: Heroku Standard → $25
- Database: Heroku Postgres Standard → $50
- Frontend: Vercel Pro → $20
- Email: SendGrid Essentials → $15
- Market Data: IEX Cloud (paid) → $9
- Monitoring: DataDog/Sentry → $0-30
- **Total: $119-149/month**

**Option 3: Enterprise**
- Backend: AWS EC2 + Load Balancer → $100
- Database: AWS RDS Postgres → $150
- Frontend: AWS CloudFront + S3 → $20
- Email: AWS SES → $10
- Market Data: Premium provider → $50-200
- Monitoring & Security → $50
- **Total: $380-530/month**

---

## 📚 Additional Resources

### APIs for Market Data
- **Alpha Vantage** (free): https://www.alphavantage.co
- **IEX Cloud**: https://iexcloud.io
- **Twelve Data**: https://twelvedata.com
- **Polygon.io**: https://polygon.io
- **Yahoo Finance** (unofficial): yfinance library

### Authentication Libraries
- **Passport.js** (Node): http://www.passportjs.org
- **Auth0**: https://auth0.com (managed service)
- **Firebase Auth**: https://firebase.google.com/products/auth
- **Supabase Auth**: https://supabase.com/auth

### Email Services
- **SendGrid**: https://sendgrid.com
- **AWS SES**: https://aws.amazon.com/ses
- **Postmark**: https://postmarkapp.com
- **Mailgun**: https://www.mailgun.com

### Deployment Platforms
- **Heroku**: https://www.heroku.com
- **Railway**: https://railway.app
- **Render**: https://render.com
- **Vercel**: https://vercel.com
- **Netlify**: https://www.netlify.com
- **DigitalOcean**: https://www.digitalocean.com

---

## 🎯 Next Immediate Steps

1. **Decision Point: Choose Tech Stack**
   - Backend: Node.js vs Python?
   - Database: PostgreSQL (recommended)
   - Deployment: Heroku/Railway vs AWS?

2. **Set Up Development Environment**
   ```bash
   # Create backend folder
   mkdir apoena-api
   cd apoena-api
   npm init -y
   npm install express pg jsonwebtoken bcrypt cors dotenv nodemailer

   # Create portfolio tracker
   cd ..
   npx create-react-app portfolio-tracker
   ```

3. **Database Schema First**
   - Create migration files
   - Set up local PostgreSQL
   - Run initial schema

4. **Build MVP Authentication**
   - Email whitelist check
   - Magic link generation
   - Token verification
   - Protected route example

5. **Test Integration**
   - Add test email to whitelist
   - Try login flow from main website
   - Verify access to portfolio tracker
   - Confirm data isolation

---

## 📧 Contact & Questions

For implementation assistance or questions about this integration:

**Technical Questions:**
- Architecture decisions
- Technology choices
- Security implementation
- Deployment strategy

**Business Requirements:**
- Client onboarding process
- Data display preferences
- Access level definitions
- Reporting requirements

---

## 📄 Appendix: Sample Files

### Sample .env file
```env
# Backend API Environment Variables
NODE_ENV=production
PORT=5000
DATABASE_URL=postgresql://user:password@localhost:5432/apoena_db
JWT_SECRET=your-super-secret-jwt-key-min-32-chars
JWT_EXPIRES_IN=7d
MAGIC_LINK_EXPIRES_IN=15m

# Email Service (SendGrid)
SENDGRID_API_KEY=SG.xxxxxxxxxxxxx
FROM_EMAIL=noreply@apoenawealth.com
FROM_NAME=Apoena Wealth Management

# CORS Configuration
CORS_ORIGIN=https://apoenawealth.com,https://portal.apoenawealth.com

# Market Data API
ALPHA_VANTAGE_KEY=your_api_key_here

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000  # 15 minutes
RATE_LIMIT_MAX_REQUESTS=100

# Logging
LOG_LEVEL=info
```

### Sample Email Template
```html
<!DOCTYPE html>
<html>
<head>
  <style>
    body { font-family: 'Inter', sans-serif; }
    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
    .button {
      background: #10B981;
      color: white;
      padding: 12px 24px;
      text-decoration: none;
      border-radius: 8px;
      display: inline-block;
    }
  </style>
</head>
<body>
  <div class="container">
    <h1 style="color: #0A4D3C;">Access Your Portfolio</h1>
    <p>Hello,</p>
    <p>Click the button below to securely access your Apoena Wealth portfolio:</p>
    <p>
      <a href="{{magic_link}}" class="button">Access Portfolio</a>
    </p>
    <p>This link will expire in 15 minutes.</p>
    <p>If you didn't request this, please ignore this email.</p>
    <hr style="margin: 30px 0; border: none; border-top: 1px solid #E5E7EB;">
    <p style="color: #6B7280; font-size: 14px;">
      Apoena Wealth Management<br>
      Lisbon, Portugal<br>
      contact@apoenawealth.com
    </p>
  </div>
</body>
</html>
```

---

**Document Version:** 1.0
**Last Updated:** December 2025
**Status:** Ready for Implementation

---

This integration plan provides a complete roadmap for building and connecting your private portfolio tracker to the Apoena Wealth website. Follow the phases sequentially, and you'll have a secure, scalable system for managing client portfolio access.
