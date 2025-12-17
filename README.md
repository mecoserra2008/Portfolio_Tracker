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
Version: 1.0.0
Last Updated: December 2025
