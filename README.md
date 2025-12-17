# Apoena Wealth Portfolio Tracker

A comprehensive portfolio tracking system for managing stocks, cryptocurrencies, and bonds with real-time market data, P&L tracking, and advanced analytics.

## Features

### Multi-Asset Portfolio Tracking
- **Stocks**: International and Brazilian stocks with dividend and stock split tracking
- **Cryptocurrencies**: BTC, ETH, ADA, and other digital assets
- **Bonds**: Brazilian bonds including:
  - CDB (Certificado de Depósito Bancário)
  - LCA (Letra de Crédito do Agronegócio)
  - CRI (Certificado de Recebíveis Imobiliários)
  - Tesouro Direto (Prefixado, IPCA+, Selic)
  - NTN-B, LTN, LFT
  - COE (Certificado de Operações Estruturadas)

### Advanced Features
- **Real-time Market Data**: Integration with Yahoo Finance for stocks and crypto
- **IPCA Indexation**: Automatic inflation adjustment for Brazilian bonds using Bacen API
- **P&L Tracking**: Realized and unrealized profit/loss calculations
- **Multi-Currency Support**: BRL, USD, EUR conversions
- **Performance Analytics**: Portfolio returns, allocation analysis, top performers
- **Maturity Tracking**: Bond maturity schedules and alerts

## Project Structure

```
Portfolio_Tracker/
├── data/
│   ├── stocks/
│   │   └── orders.csv           # Stock transaction history
│   ├── crypto/
│   │   └── orders.csv           # Crypto transaction history
│   └── bonds/
│       ├── emissao_bancaria.csv # Bank issued bonds
│       ├── credito_privado.csv  # Private credit bonds
│       ├── tesouro.csv          # Treasury bonds
│       ├── titulos_publicos.csv # Public bonds
│       └── coe.csv              # Structured notes
├── src/
│   ├── market_data.py           # Market data fetcher (Yahoo Finance, Bacen)
│   ├── stock_portfolio.py       # Stock portfolio calculator
│   ├── crypto_portfolio.py      # Crypto portfolio calculator
│   ├── bond_portfolio.py        # Bond portfolio calculator with IPCA
│   └── portfolio_aggregator.py  # Unified portfolio aggregator
├── dashboard/
│   └── PortfolioDashboard.jsx   # React dashboard component
├── app.py                       # Flask API server
├── Orders (1).xlsx              # Original Excel data file
└── README.md
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Node.js 14+ (for React dashboard)
- pip (Python package manager)
- npm or yarn (for JavaScript packages)

### Backend Setup

1. **Clone the repository**
```bash
cd Portfolio_Tracker
```

2. **Install Python dependencies**
```bash
pip install pandas numpy requests beautifulsoup4 lxml
pip install flask flask-cors
```

3. **Extract data from Excel to CSV** (already done)
```bash
python3 -c "from src.market_data import test_market_data; test_market_data()"
```

4. **Test portfolio calculations**
```bash
# Test stock portfolio
python3 src/stock_portfolio.py

# Test crypto portfolio
python3 src/crypto_portfolio.py

# Test bond portfolio
python3 src/bond_portfolio.py

# Test complete aggregator
python3 src/portfolio_aggregator.py
```

5. **Start the Flask API server**
```bash
python3 app.py
```

The API will be available at `http://localhost:5000`

### Frontend Setup (React Dashboard)

1. **Install dependencies**
```bash
cd dashboard
npm install react recharts
# or
yarn add react recharts
```

2. **Configure API endpoint**

Create `.env` file in the dashboard directory:
```
REACT_APP_API_URL=http://localhost:5000/api
```

3. **Import the dashboard component in your Apoena Wealth website**

```jsx
import PortfolioDashboard from './dashboard/PortfolioDashboard';

// In your app
<PortfolioDashboard />
```

## API Documentation

### Base URL
```
http://localhost:5000/api
```

### Endpoints

#### 1. Portfolio Summary
```
GET /api/portfolio/summary
```
Returns consolidated portfolio summary across all asset types.

**Query Parameters:**
- `currency` (optional): Base currency (BRL, USD, EUR). Default: BRL

**Response:**
```json
{
  "success": true,
  "data": {
    "total_portfolio_value": 1500000.00,
    "total_pnl": 150000.00,
    "total_return_pct": 11.54,
    "asset_allocation": {
      "stocks": { "value": 750000, "allocation_pct": 50.0, ... },
      "crypto": { "value": 300000, "allocation_pct": 20.0, ... },
      "bonds": { "value": 450000, "allocation_pct": 30.0, ... }
    },
    "exchange_rates": { "USD/BRL": 5.02, "EUR/BRL": 5.45 }
  },
  "timestamp": "2025-12-17T..."
}
```

#### 2. All Positions
```
GET /api/portfolio/positions
```
Returns all positions across stocks, crypto, and bonds.

#### 3. Stock Portfolio
```
GET /api/portfolio/stocks
```
Returns detailed stock portfolio data.

#### 4. Crypto Portfolio
```
GET /api/portfolio/crypto
```
Returns detailed crypto portfolio data.

**Query Parameters:**
- `currency` (optional): Currency for valuation. Default: BRL

#### 5. Bond Portfolio
```
GET /api/portfolio/bonds
```
Returns detailed bond portfolio data including maturity schedules.

#### 6. Top Performers
```
GET /api/portfolio/top-performers
```
Returns top performing assets across all types.

**Query Parameters:**
- `limit` (optional): Number of results. Default: 10

#### 7. Allocation Data
```
GET /api/portfolio/allocation
```
Returns allocation data formatted for charts.

#### 8. Complete Report
```
GET /api/portfolio/report
```
Returns comprehensive portfolio report with all data.

## Usage Examples

### Python Usage

```python
from src.portfolio_aggregator import PortfolioAggregator

# Initialize aggregator
portfolio = PortfolioAggregator()

# Get summary
summary = portfolio.get_consolidated_summary(base_currency='BRL')
print(f"Total Portfolio Value: R$ {summary['total_portfolio_value']:,.2f}")
print(f"Total Return: {summary['total_return_pct']:.2f}%")

# Get all positions
positions = portfolio.get_all_positions()

# Get top performers
top_10 = portfolio.get_top_performers(n=10)

# Export complete report
report = portfolio.export_complete_report('portfolio_report.json')
```

### JavaScript/React Usage

```jsx
import React, { useEffect, useState } from 'react';

const MyPortfolio = () => {
  const [summary, setSummary] = useState(null);

  useEffect(() => {
    fetch('http://localhost:5000/api/portfolio/summary')
      .then(res => res.json())
      .then(data => {
        if (data.success) {
          setSummary(data.data);
        }
      });
  }, []);

  if (!summary) return <div>Loading...</div>;

  return (
    <div>
      <h1>Portfolio Value: {formatCurrency(summary.total_portfolio_value)}</h1>
      <p>Return: {summary.total_return_pct.toFixed(2)}%</p>
    </div>
  );
};
```

## Data Format

### Stock Orders CSV
```csv
Data,Ativo,Preço,Quantidade,Mercado
2025-12-08,HAPV3,14.15,1500,Nacional
2025-11-27,HAPV3,15.6,100,Nacional
2025-11-18,AAPL,180.50,-10,Internacional
```

**Note:**
- Positive quantity = BUY
- Negative quantity = SELL

### Crypto Orders CSV
```csv
Data,Ativo,Preço,Quantidade
2025-11-21,ETH,15451.91,0.71794
2025-11-15,ETH,16780.35,-0.017878
```

### Bond CSV
```csv
Título,Emissor,Quantidade,Preço Unitário,Valor investido,Indexador,Percentual Indexado,Data de Aplicação,Vencimento
CDB FLU CDB425CTI84,Banco XYZ,1,1000,1000,CDI,100%,2024-01-28,2026-01-28
```

## Integration with Apoena Wealth Website

### Step 1: Add Route to Your Website

In your main `App.js` or routing file:

```jsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import PortfolioDashboard from './components/PortfolioDashboard';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Existing routes */}
        <Route path="/" element={<Home />} />
        <Route path="/about" element={<About />} />

        {/* New portfolio route */}
        <Route path="/portfolio" element={<PortfolioDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}
```

### Step 2: Add Navigation Link

In your `Header.jsx`:

```jsx
<nav>
  <Link to="/">Home</Link>
  <Link to="/about">About</Link>
  <Link to="/services">Services</Link>
  <Link to="/portfolio">Portfolio</Link>  {/* NEW */}
  <Link to="/contact">Contact</Link>
</nav>
```

### Step 3: Deploy API

For production, deploy the Flask API to:
- Heroku
- Railway
- AWS EC2
- DigitalOcean

Update the `REACT_APP_API_URL` in your `.env` to point to production API.

## Calculation Logic

### Stock P&L Calculation
```python
# Buy/Sell tracking
if quantity > 0:  # BUY
    new_avg_cost = (old_quantity * old_avg_cost + quantity * price) / (old_quantity + quantity)
else:  # SELL
    realized_pnl = abs(quantity) * (sell_price - avg_cost)
    unrealized_pnl = remaining_quantity * (current_price - avg_cost)
```

### Bond Valuation with IPCA
```python
# For IPCA-indexed bonds
ipca_adjusted_value = base_value * cumulative_ipca_factor
final_value = ipca_adjusted_value * (1 + fixed_rate) ^ years
```

### Crypto P&L
```python
# Similar to stocks but without dividends/splits
unrealized_pnl = quantity * (current_price - avg_cost)
total_pnl = realized_pnl + unrealized_pnl
```

## Market Data Sources

- **Stocks**: Yahoo Finance API (`query1.finance.yahoo.com`)
- **Crypto**: Yahoo Finance API (BTC-USD, ETH-USD, etc.)
- **IPCA**: Banco Central do Brasil API (`api.bcb.gov.br`)
- **SELIC**: Banco Central do Brasil API
- **Exchange Rates**: Yahoo Finance Forex API

## Environment Variables

Create a `.env` file:

```bash
# API Configuration
FLASK_ENV=production
API_PORT=5000

# Data Sources
YAHOO_FINANCE_API=https://query1.finance.yahoo.com
BACEN_API=https://api.bcb.gov.br

# CORS
CORS_ORIGINS=https://apoenawealth.com,https://www.apoenawealth.com
```

## Troubleshooting

### Issue: Market data not loading
**Solution**: Check internet connection and API endpoints. Yahoo Finance may have rate limits.

### Issue: IPCA data missing
**Solution**: Bacen API may be temporarily unavailable. The system will use 5% annual approximation as fallback.

### Issue: Currency conversion errors
**Solution**: Verify exchange rate symbols (BRLUSD=X for BRL to USD).

### Issue: Bond calculations seem incorrect
**Solution**: Verify bond indexer and percentage fields in CSV. Check date formats (YYYY-MM-DD).

## Performance Optimization

- API responses are cached for 5 minutes
- Market data is fetched on-demand, not for every calculation
- Large portfolios (>1000 positions) may require pagination
- Consider using Redis for caching in production

## Security Considerations

- Implement authentication for production deployment
- Use HTTPS for all API communication
- Store sensitive data (API keys) in environment variables
- Implement rate limiting on API endpoints
- Use CORS to restrict access to authorized domains

## Future Enhancements

- [ ] Real-time WebSocket updates
- [ ] Historical performance charts
- [ ] Custom portfolio reports (PDF generation)
- [ ] Email alerts for maturity dates
- [ ] Multi-user support with authentication
- [ ] Mobile app (React Native)
- [ ] Portfolio comparison and benchmarking
- [ ] Tax reporting features

## License

Proprietary - Apoena Wealth Management

## Support

For questions or issues:
- Email: support@apoenawealth.com
- Documentation: See integration plans in repository

## Credits

Developed for Apoena Wealth Management
Version: 2.0.0 - Now with Historical Performance & Risk Analytics!
Last Updated: December 2025

---

# 📈 HISTORICAL PERFORMANCE & RISK ANALYTICS (NEW!)

## Overview

Version 2.0 introduces comprehensive historical performance tracking with:
- **Batch Data Fetching**: Overcomes API rate limits with intelligent batch processing
- **SQLite Storage**: Persistent historical price database for all assets
- **Portfolio Valuation**: Daily portfolio value calculation over time
- **Risk Metrics**: Industry-standard risk calculations (Sharpe, Sortino, VaR, etc.)
- **Benchmark Comparison**: Compare portfolio vs market indices
- **Performance Charts**: Ready-to-use data for visualization

## Architecture

```
Historical Performance System
├── Historical Data Manager (historical_data.py)
│   ├── Batch fetching from Yahoo Finance
│   ├── SQLite database storage
│   ├── Incremental updates (fetch only missing data)
│   └── Bulk operations for multiple symbols
│
├── Portfolio Performance Calculator (portfolio_performance.py)
│   ├── Daily portfolio valuation
│   ├── Asset-level performance tracking
│   ├── Risk metrics calculation
│   ├── Drawdown analysis
│   └── Benchmark comparison
│
└── Integration (portfolio_aggregator.py)
    ├── Initialize historical data for portfolio
    ├── Get historical performance
    └── Generate chart data
```

## Database Schema

### SQLite Database (`data/historical_data.db`)

**price_history table:**
```sql
CREATE TABLE price_history (
    symbol TEXT NOT NULL,
    date DATE NOT NULL,
    open REAL,
    high REAL,
    low REAL,
    close REAL,
    adj_close REAL,
    volume INTEGER,
    dividend REAL DEFAULT 0,
    split REAL DEFAULT 1,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (symbol, date)
);
```

**symbol_metadata table:**
```sql
CREATE TABLE symbol_metadata (
    symbol TEXT PRIMARY KEY,
    first_date DATE,
    last_date DATE,
    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    total_records INTEGER DEFAULT 0
);
```

## Batch Data Fetching

### Why Batch Fetching?

Yahoo Finance API has rate limits. Requesting large date ranges in one call can fail or be throttled. Our batch fetching system:
- Splits requests into configurable batches (default: 100 days)
- Adds delays between batches (500ms) and symbols (1s)
- Only fetches missing data (incremental updates)
- Handles network errors gracefully
- Provides progress feedback

### How It Works

```python
from src.historical_data import HistoricalDataManager

manager = HistoricalDataManager()

# Fetch 5 years of data for AAPL in 90-day batches
df = manager.fetch_historical_data(
    symbol='AAPL',
    start_date='2020-01-01',
    end_date='2025-12-17',
    batch_days=90  # Fetch in 90-day chunks
)

# Output:
# Fetching AAPL from 2020-01-01 to 2025-12-17...
#   Batch: 2020-01-01 to 2020-03-31 ✓ (90 records)
#   Batch: 2020-04-01 to 2020-06-30 ✓ (91 records)
#   ...
# ✓ Total: 1500 records stored for AAPL
```

### Bulk Fetching Multiple Symbols

```python
# Fetch multiple symbols at once
symbols = ['AAPL', 'PETR4.SA', 'BTC-USD', 'ETH-USD']

manager.bulk_fetch(
    symbols=symbols,
    start_date='2024-01-01',
    batch_days=100
)

# Output:
# ============================================================
# Bulk fetching 4 symbols
# ============================================================
#
# [1/4] AAPL
# Fetching AAPL from 2024-01-01 to 2025-12-17...
#   Batch: 2024-01-01 to 2024-04-10 ✓ (100 records)
#   ...
# ✓ Total: 350 records stored for AAPL
#
# [2/4] PETR4.SA
# ...
```

### Incremental Updates

The system is smart about what to fetch:
```python
# First fetch: Gets all data from 2024-01-01 to today
manager.fetch_historical_data('AAPL', '2024-01-01')

# Second fetch: Only gets new data since last fetch
manager.fetch_historical_data('AAPL', '2024-01-01')
# Output: ✓ AAPL: All data already cached
```

## Risk Metrics

### Available Metrics

| Metric | Description | Formula |
|--------|-------------|---------|
| **Sharpe Ratio** | Return per unit of risk | (Return - RiskFree) / Volatility |
| **Sortino Ratio** | Return per unit of downside risk | Return / Downside Deviation |
| **Max Drawdown** | Largest peak-to-trough decline | Max(Peak - Trough) / Peak |
| **Volatility** | Standard deviation of returns | σ(returns) × √252 |
| **VaR (95%)** | Value at Risk - 95th percentile | 5th percentile of returns |
| **CVaR (95%)** | Conditional VaR - Expected Shortfall | E[Return \| Return ≤ VaR] |
| **Calmar Ratio** | Return / Max Drawdown | Annual Return / Max Drawdown % |
| **Win Rate** | Percentage of positive days | Positive Days / Total Days × 100 |

### Calculation Example

```python
from src.portfolio_aggregator import PortfolioAggregator

portfolio = PortfolioAggregator()

# Get 1-year performance with risk metrics
performance = portfolio.get_historical_performance(period='1Y')

metrics = performance['metrics']
print(f"Sharpe Ratio: {metrics['sharpe_ratio']:.2f}")
print(f"Sortino Ratio: {metrics['sortino_ratio']:.2f}")
print(f"Max Drawdown: {metrics['max_drawdown_pct']:.2f}%")
print(f"Volatility (Annual): {metrics['volatility_annual']:.2f}%")
print(f"VaR (95%): {metrics['var_95']:.2f}%")
print(f"Win Rate: {metrics['win_rate']:.2f}%")

# Output:
# Sharpe Ratio: 1.42
# Sortino Ratio: 1.98
# Max Drawdown: -18.24%
# Volatility (Annual): 15.30%
# VaR (95%): -2.15%
# Win Rate: 58.30%
```

## Usage Examples

### 1. Initialize Historical Data for Your Portfolio

Before using historical features, initialize the database:

```python
from src.portfolio_aggregator import PortfolioAggregator

portfolio = PortfolioAggregator()

# This fetches historical data for ALL assets in your portfolio
# Starting from 2020-01-01, in 90-day batches
stats = portfolio.initialize_historical_data(
    start_date='2020-01-01',
    batch_days=90
)

print(f"Initialized {stats['total_symbols']} symbols")
print(f"Total records: {stats['total_records']}")
```

**⚠️ Note**: This can take 5-30 minutes depending on:
- Number of assets in your portfolio
- Date range
- Network speed
- API rate limits

**Tip**: Run this once, then only update incrementally.

### 2. Get Historical Performance

```python
# Get 1-year performance
perf_1y = portfolio.get_historical_performance(period='1Y')

# Get Year-to-Date performance
perf_ytd = portfolio.get_historical_performance(period='YTD')

# Get custom date range
perf_custom = portfolio.get_historical_performance(
    start_date='2024-06-01',
    end_date='2024-12-01'
)

# Available periods: 1M, 3M, 6M, 1Y, 3Y, 5Y, YTD, MAX

# Access data
daily_values = perf_1y['performance']  # List of daily portfolio values
risk_metrics = perf_1y['metrics']       # Risk calculations
drawdowns = perf_1y['drawdown']         # Drawdown analysis
rolling = perf_1y['rolling_metrics']    # 30-day rolling metrics
```

### 3. Compare to Benchmark

```python
# Compare to Bovespa Index (default for Brazilian portfolio)
comparison = portfolio.get_performance_comparison()

# Compare to S&P 500
comparison_sp = portfolio.get_performance_comparison(
    benchmark='^GSPC',
    start_date='2024-01-01'
)

# Access comparison data
for record in comparison['comparison']:
    date = record['date']
    portfolio_return = record['cumulative_return']
    benchmark_return = record['benchmark_cumulative']
    alpha = record['cumulative_alpha']  # Portfolio - Benchmark
    
    print(f"{date}: Portfolio={portfolio_return:.2f}%, "
          f"Benchmark={benchmark_return:.2f}%, Alpha={alpha:.2f}%")
```

### 4. Visualize Performance (Chart Data Ready)

```python
# Get performance data formatted for charts
perf = portfolio.get_historical_performance(period='1Y')

# For line chart (portfolio value over time)
chart_data = [
    {
        'date': record['date'],
        'value': record['total_value'],
        'stocks': record['stock_value'],
        'crypto': record['crypto_value'],
        'bonds': record['bond_value']
    }
    for record in perf['performance']
]

# For drawdown chart
drawdown_data = [
    {
        'date': record['date'] if 'date' in record else None,
        'drawdown_pct': record['drawdown_pct']
    }
    for record in perf['drawdown']
]

# For rolling Sharpe ratio
rolling_data = [
    {
        'date': record['date'],
        'sharpe': record['rolling_sharpe']
    }
    for record in perf['rolling_metrics']
]
```

## API Endpoints (New)

### 1. Get Historical Performance

```http
GET /api/portfolio/historical?period=1Y
```

**Query Parameters:**
- `period` (optional): 1M, 3M, 6M, 1Y, 3Y, 5Y, YTD, MAX
- `start_date` (optional): YYYY-MM-DD
- `end_date` (optional): YYYY-MM-DD

**Response:**
```json
{
  "success": true,
  "data": {
    "performance": [
      {
        "date": "2024-01-01",
        "stock_value": 500000,
        "crypto_value": 200000,
        "bond_value": 300000,
        "total_value": 1000000,
        "daily_return": 0.5,
        "cumulative_return": 12.5
      },
      ...
    ],
    "metrics": {
      "sharpe_ratio": 1.42,
      "sortino_ratio": 1.98,
      "max_drawdown_pct": -18.24,
      "volatility_annual": 15.30,
      "var_95": -2.15,
      "win_rate": 58.30
    },
    "period": "1Y",
    "start_date": "2024-01-01",
    "end_date": "2025-01-01"
  }
}
```

### 2. Compare to Benchmark

```http
GET /api/portfolio/comparison?benchmark=^BVSP&start_date=2024-01-01
```

**Response:**
```json
{
  "success": true,
  "data": {
    "comparison": [
      {
        "date": "2024-01-01",
        "total_value": 1000000,
        "daily_return": 0.5,
        "cumulative_return": 12.5,
        "benchmark_close": 120000,
        "benchmark_return": 0.3,
        "benchmark_cumulative": 8.2,
        "alpha": 0.2,
        "cumulative_alpha": 4.3
      },
      ...
    ],
    "benchmark_symbol": "^BVSP"
  }
}
```

### 3. Initialize Historical Data

```http
POST /api/historical/initialize
Content-Type: application/json

{
  "start_date": "2020-01-01",
  "batch_days": 90
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_symbols": 25,
    "total_records": 45000,
    "date_range": {
      "start": "2020-01-01",
      "end": "2025-12-17"
    }
  },
  "message": "Historical data initialization complete"
}
```

### 4. Get Historical Data Statistics

```http
GET /api/historical/stats
```

**Response:**
```json
{
  "success": true,
  "data": {
    "total_symbols": 25,
    "total_records": 45000,
    "date_range": {
      "start": "2020-01-01",
      "end": "2025-12-17"
    },
    "symbols": [
      {
        "symbol": "AAPL",
        "records": 1500,
        "first_date": "2020-01-01",
        "last_date": "2025-12-17"
      },
      ...
    ]
  }
}
```

## React Dashboard Integration

Add historical performance charts to your dashboard:

```jsx
import React, { useState, useEffect } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

const HistoricalPerformanceChart = () => {
  const [data, setData] = useState([]);
  const [period, setPeriod] = useState('1Y');
  const [metrics, setMetrics] = useState({});

  useEffect(() => {
    fetch(`http://localhost:5000/api/portfolio/historical?period=${period}`)
      .then(res => res.json())
      .then(result => {
        if (result.success) {
          setData(result.data.performance);
          setMetrics(result.data.metrics);
        }
      });
  }, [period]);

  return (
    <div>
      <div className="period-selector">
        {['1M', '3M', '6M', '1Y', 'YTD', 'MAX'].map(p => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={period === p ? 'active' : ''}
          >
            {p}
          </button>
        ))}
      </div>

      <div className="metrics-summary">
        <div>Sharpe Ratio: {metrics.sharpe_ratio?.toFixed(2)}</div>
        <div>Max Drawdown: {metrics.max_drawdown_pct?.toFixed(2)}%</div>
        <div>Volatility: {metrics.volatility_annual?.toFixed(2)}%</div>
        <div>Win Rate: {metrics.win_rate?.toFixed(2)}%</div>
      </div>

      <LineChart width={800} height={400} data={data}>
        <CartesianGrid strokeDasharray="3 3" />
        <XAxis dataKey="date" />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line type="monotone" dataKey="total_value" stroke="#10B981" name="Portfolio" />
        <Line type="monotone" dataKey="stock_value" stroke="#3B82F6" name="Stocks" />
        <Line type="monotone" dataKey="crypto_value" stroke="#F59E0B" name="Crypto" />
        <Line type="monotone" dataKey="bond_value" stroke="#8B5CF6" name="Bonds" />
      </LineChart>
    </div>
  );
};

export default HistoricalPerformanceChart;
```

## Performance Optimization

### Database Indexing

Indexes are automatically created for optimal query performance:
- `idx_price_date`: Fast date-range queries
- `idx_price_symbol_date`: Fast symbol lookups

### Query Optimization Tips

```python
# ✅ GOOD: Query specific date range
df = manager.get_historical_data('AAPL', '2024-01-01', '2024-12-31')

# ❌ BAD: Query all data then filter
df = manager.get_historical_data('AAPL')
df = df[df['date'] > '2024-01-01']

# ✅ GOOD: Bulk fetch symbols
manager.bulk_fetch(['AAPL', 'GOOGL', 'MSFT'], '2024-01-01')

# ❌ BAD: Individual fetches
for symbol in ['AAPL', 'GOOGL', 'MSFT']:
    manager.fetch_historical_data(symbol, '2024-01-01')
```

### Database Maintenance

```python
# Clean old data to save space (keep last 2 years)
manager.clear_old_data(days_to_keep=730)

# Get database size
import os
db_size = os.path.getsize('data/historical_data.db')
print(f"Database size: {db_size / 1024 / 1024:.2f} MB")
```

## Troubleshooting

### Issue: Fetch takes too long

**Solution**: Reduce batch size and increase delays
```python
manager.fetch_historical_data(
    symbol='AAPL',
    start_date='2020-01-01',
    batch_days=30  # Smaller batches
)
```

### Issue: API rate limit errors

**Solution**: Increase delay between requests
```python
# Edit historical_data.py:
# Line ~220: time.sleep(0.5) → time.sleep(2)  # 2 second delay
# Line ~350: time.sleep(1) → time.sleep(3)    # 3 second delay
```

### Issue: Missing data for certain dates

**Solution**: Market holidays/weekends have no data. This is normal.

### Issue: Database locked error

**Solution**: Only one process can write at a time. Close other connections.

```python
# If you get "database is locked", wait and retry
import time
for attempt in range(3):
    try:
        manager.fetch_historical_data(...)
        break
    except sqlite3.OperationalError:
        time.sleep(5)
```

## Best Practices

### 1. Initialize Once, Update Incrementally

```python
# Initial setup (run once)
portfolio.initialize_historical_data(start_date='2020-01-01')

# Daily updates (run daily via cron)
portfolio.initialize_historical_data(start_date='2024-01-01')  # Only fetches new data
```

### 2. Cache Performance Calculations

```python
# Cache expensive calculations
import json
from datetime import datetime

cache_file = f'cache/performance_{datetime.now().strftime("%Y%m%d")}.json'

# Try to load from cache
try:
    with open(cache_file, 'r') as f:
        performance = json.load(f)
except FileNotFoundError:
    # Calculate and cache
    performance = portfolio.get_historical_performance(period='1Y')
    with open(cache_file, 'w') as f:
        json.dump(performance, f)
```

### 3. Monitor Database Growth

```python
# Check database stats regularly
stats = manager.get_database_stats()
print(f"Symbols: {stats['total_symbols']}")
print(f"Records: {stats['total_records']}")

# If database is too large, clean old data
if stats['total_records'] > 100000:
    manager.clear_old_data(days_to_keep=365)
```

### 4. Handle Network Errors Gracefully

```python
try:
    perf = portfolio.get_historical_performance(period='1Y')
except Exception as e:
    print(f"Error fetching performance: {e}")
    # Fall back to cached data or show error to user
    perf = load_cached_performance()
```

## Risk Calculation Deep Dive

### Sharpe Ratio

Measures risk-adjusted returns. Higher is better.

```
Sharpe = (Portfolio Return - Risk Free Rate) / Volatility

Where:
- Portfolio Return = Annualized return
- Risk Free Rate = 0% (assumed for simplicity)
- Volatility = Standard deviation of returns × √252
```

**Interpretation:**
- < 1.0: Poor risk-adjusted returns
- 1.0 - 2.0: Good
- 2.0 - 3.0: Very good
- > 3.0: Excellent

### Sortino Ratio

Like Sharpe but only penalizes downside volatility.

```
Sortino = Portfolio Return / Downside Deviation

Where:
- Downside Deviation = Std dev of negative returns only
```

### Maximum Drawdown

Largest peak-to-trough decline.

```
Max Drawdown = Max(Peak Value - Trough Value) / Peak Value × 100%
```

**Example:**
- Portfolio peaks at $1,000,000
- Falls to $800,000
- Max Drawdown = ($1M - $800K) / $1M = 20%

### Value at Risk (VaR)

What's the worst daily loss you can expect 95% of the time?

```
VaR(95%) = 5th percentile of daily returns
```

If VaR(95%) = -2%, then:
- 95% of days, you lose less than 2%
- 5% of days, you lose more than 2%

### Conditional VaR (CVaR)

Given that you're in the worst 5% of days, what's the average loss?

```
CVaR(95%) = Average of returns ≤ VaR(95%)
```

## Production Deployment

### Scheduled Updates

Set up a cron job to update historical data daily:

```bash
# crontab -e
# Run at 6 PM daily (after market close)
0 18 * * * cd /path/to/Portfolio_Tracker && python3 -c "from src.portfolio_aggregator import PortfolioAggregator; p = PortfolioAggregator(); p.initialize_historical_data()"
```

### Database Backup

```bash
# Daily backup of historical database
0 2 * * * cp /path/to/Portfolio_Tracker/data/historical_data.db /backups/historical_data_$(date +\%Y\%m\%d).db
```

### Monitoring

```python
# Add to your monitoring system
from src.historical_data import HistoricalDataManager

manager = HistoricalDataManager()
stats = manager.get_database_stats()

# Alert if database hasn't been updated in 7 days
last_update = max(sym['last_date'] for sym in stats['symbols'])
days_since_update = (datetime.now() - datetime.strptime(last_update, '%Y-%m-%d')).days

if days_since_update > 7:
    send_alert(f"Historical data outdated: {days_since_update} days old")
```

## Future Enhancements

Coming in future versions:
- [ ] Async batch fetching for faster initialization
- [ ] Support for custom benchmarks
- [ ] Monte Carlo simulation for risk analysis
- [ ] Correlation matrix visualization
- [ ] Portfolio optimization suggestions
- [ ] Automated rebalancing recommendations
- [ ] Tax-loss harvesting identification
- [ ] Factor analysis (Fama-French)
- [ ] Attribution analysis (performance sources)
- [ ] Scenario analysis (what-if simulations)

---

