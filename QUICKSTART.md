# Quick Start Guide - Apoena Wealth Portfolio Tracker

## 🚀 Get Started in 5 Minutes

### Step 1: Installation (1 minute)

```bash
# Install Python dependencies
pip install pandas numpy requests flask flask-cors

# Or use requirements.txt
pip install -r requirements.txt
```

### Step 2: Verify Data (30 seconds)

Check that your data files are in place:
```bash
ls data/stocks/orders.csv    # Stock transactions
ls data/crypto/orders.csv    # Crypto transactions
ls data/bonds/               # Bond positions
```

### Step 3: Start the API (30 seconds)

```bash
python3 app.py
```

You should see:
```
* Running on http://0.0.0.0:5000
```

### Step 4: Test the API (1 minute)

Open your browser and go to:
- http://localhost:5000/ - API documentation
- http://localhost:5000/api/portfolio/summary - Portfolio summary
- http://localhost:5000/api/portfolio/report - Complete report

Or use curl:
```bash
curl http://localhost:5000/api/portfolio/summary | python3 -m json.tool
```

### Step 5: View Dashboard (2 minutes)

1. Copy the dashboard component to your Apoena Wealth website:
```bash
cp dashboard/PortfolioDashboard.jsx /path/to/apoena-wealth/src/pages/
```

2. Add route in your `App.js`:
```jsx
import PortfolioDashboard from './pages/PortfolioDashboard';

<Route path="/portfolio" element={<PortfolioDashboard />} />
```

3. Start your website and navigate to `/portfolio`

## ✅ Verify Everything Works

Run the test suite:
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

All tests should complete without errors (network errors are expected in restricted environments).

## 📊 Understanding Your Portfolio Data

### Stock Transactions
- **Positive quantity** = Buy
- **Negative quantity** = Sell
- Example: `HAPV3, 14.15, 1500` = Buy 1500 shares at R$14.15

### Crypto Transactions
- Same as stocks: positive = buy, negative = sell
- Prices in BRL
- Example: `ETH, 15451.91, 0.71794` = Buy 0.71794 ETH at R$15,451.91

### Bonds
- **Quantidade** can be positive (buy) or negative (sell)
- **Face value** is maintained during holding period
- **IPCA indexation** is automatically applied
- Coupon payments reduce unrealized P&L until maturity

## 🎯 Common Use Cases

### 1. Check Total Portfolio Value
```bash
curl http://localhost:5000/api/portfolio/summary
```

Look for `total_portfolio_value` in the response.

### 2. See Top Performers
```bash
curl http://localhost:5000/api/portfolio/top-performers?limit=5
```

### 3. Check Bond Maturities
```bash
curl http://localhost:5000/api/portfolio/bonds
```

Look for `maturity_schedule` to see upcoming bond maturities.

### 4. Get Stock Performance
```bash
curl http://localhost:5000/api/portfolio/stocks
```

Returns all stock positions with P&L and current prices.

## 🔧 Configuration

### Change Base Currency

By default, the system uses BRL. To change:
```bash
# In API request
curl http://localhost:5000/api/portfolio/summary?currency=USD

# In Python
summary = portfolio.get_consolidated_summary(base_currency='USD')
```

### Update Data

To add new transactions:
1. Add rows to the appropriate CSV file
2. Restart the API server
3. The new transactions will be automatically processed

### Manual Data Entry Format

**Stocks** (`data/stocks/orders.csv`):
```csv
Data,Ativo,Preço,Quantidade,Mercado
2025-12-17,AAPL,180.50,10,Internacional
```

**Crypto** (`data/crypto/orders.csv`):
```csv
Data,Ativo,Preço,Quantidade
2025-12-17,BTC,250000,0.1
```

**Bonds** (`data/bonds/tesouro.csv`):
```csv
Título,Quantidade,Preço Unitário,Valor investido,Indexador,Percentual Indexado,Data de Aplicação,Vencimento
Tesouro IPCA+ 2035,10,3500,35000,IPCA,6.00%,2025-01-15,2035-05-15
```

## 🐛 Troubleshooting

### API won't start
**Error:** `ModuleNotFoundError: No module named 'flask'`
**Solution:** Run `pip install flask flask-cors`

### No data showing
**Error:** Empty positions in dashboard
**Solution:** Check CSV files exist and have data. Run test scripts to verify.

### Market data errors
**Error:** `HTTPSConnectionPool... Max retries exceeded`
**Solution:** This is normal in restricted network environments. The system will use last known prices and fallback approximations.

### IPCA data missing
**Error:** `Warning: IPCA data not available`
**Solution:** The system will use 5% annual approximation. This is acceptable for closed network environments.

## 📈 Next Steps

1. **Customize Dashboard**: Edit `dashboard/PortfolioDashboard.jsx` to match your brand colors
2. **Add Authentication**: Implement email-based access control (see PORTFOLIO_TRACKER_INTEGRATION_PLAN.md)
3. **Deploy to Production**: Deploy Flask API to Heroku/Railway/AWS
4. **Schedule Updates**: Set up cron job to update market data daily
5. **Add Alerts**: Implement email alerts for bond maturities and significant P&L changes

## 📚 Additional Resources

- Full documentation: `README.md`
- Integration guide: `PORTFOLIO_TRACKER_INTEGRATION_PLAN.md`
- API reference: http://localhost:5000/ (when running)
- Apoena Wealth website plan: `apoena-wealth-plan (1).md`

## 💡 Pro Tips

1. **Performance**: The first API call takes ~2-3 seconds as it loads all data. Subsequent calls are faster.

2. **Data Backup**: Regularly backup your `data/` directory:
```bash
tar -czf portfolio_backup_$(date +%Y%m%d).tar.gz data/
```

3. **Testing Changes**: Use the Python console to test calculations:
```python
from src.portfolio_aggregator import PortfolioAggregator
p = PortfolioAggregator()
summary = p.get_consolidated_summary()
print(f"Total: R$ {summary['total_portfolio_value']:,.2f}")
```

4. **Monitoring**: Set up health check:
```bash
while true; do curl http://localhost:5000/health; sleep 60; done
```

## 🎉 You're All Set!

Your portfolio tracker is now running. Visit http://localhost:5000/api/portfolio/summary to see your portfolio data!

For questions or issues, refer to the main README.md or integration plan documents.
