# Fund Accounting System

Version 3.0 - Comprehensive fund accounting with investor tracking, fee calculations, and performance analytics.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Fund Accounting](#fund-accounting)
  - [Cash Management](#cash-management)
  - [Investor Tracking](#investor-tracking)
  - [Fee Calculations](#fee-calculations)
- [Performance Analytics](#performance-analytics)
  - [Monthly Performance Heatmap](#monthly-performance-heatmap)
  - [Cumulative Returns Comparison](#cumulative-returns-comparison)
  - [Alpha Analysis](#alpha-analysis)
- [API Reference](#api-reference)
- [Usage Examples](#usage-examples)

## Overview

The Fund Accounting System provides professional-grade fund management capabilities including:

- **Cash Position Tracking**: Monitor cash flows, deposits, and withdrawals
- **Investor Management**: Track each investor's stake and returns over time
- **Fee Calculation**: Automatic calculation of management (2%) and performance (20%) fees
- **Performance Analytics**: Monthly heatmaps, cumulative return comparisons, and alpha measurement
- **NAV Tracking**: Real-time Net Asset Value calculation including portfolio value, cash, and fees

## Features

### Fund Accounting Features

1. **Cash Management**
   - Track deposits and withdrawals by investor
   - Multi-currency support (BRL, USD, EUR)
   - Historical cash position tracking
   - CSV-based transaction logging

2. **Investor Tracking**
   - Individual investor stakes calculated automatically
   - Track each investor's deposits, withdrawals, and net contributions
   - Calculate individual investor NAV and returns
   - Time-weighted return calculations

3. **Fee Calculations**
   - **Management Fee**: 2% annual fee on NAV
   - **Performance Fee**: 20% on gains above high water mark
   - Fee accrual and payment tracking
   - Per-investor and fund-level fee calculations
   - Outstanding fee tracking

### Performance Analytics Features

1. **Monthly Performance Heatmap**
   - Visual representation of monthly returns by year
   - Color-coded performance (green = positive, red = negative)
   - Interactive Plotly charts or static Seaborn visualizations
   - Export to HTML or embed in dashboards

2. **Cumulative Returns Comparison**
   - Compare portfolio performance vs individual assets
   - Normalized to 100 at start date for easy comparison
   - Show which assets the portfolio outperformed
   - Interactive charts with hover details

3. **Alpha Analysis**
   - Simple alpha (excess return vs benchmark)
   - Jensen's alpha (risk-adjusted performance)
   - Beta calculation (portfolio sensitivity)
   - Information ratio (alpha per unit of tracking error)
   - Correlation analysis

## Fund Accounting

### Cash Management

Track all cash flows in and out of the fund.

#### Recording Deposits

```python
from src.portfolio_aggregator import PortfolioAggregator

portfolio = PortfolioAggregator()

# Record a client deposit
portfolio.fund_accounting.cash_manager.add_transaction(
    date='2024-01-15',
    investor_id='INV001',
    investor_name='João Silva',
    transaction_type='deposit',
    amount=1000000.00,
    currency='BRL',
    description='Initial investment'
)
```

#### Recording Withdrawals

```python
# Record a client withdrawal
portfolio.fund_accounting.cash_manager.add_transaction(
    date='2024-06-15',
    investor_id='INV001',
    investor_name='João Silva',
    transaction_type='withdrawal',
    amount=100000.00,
    currency='BRL',
    description='Partial withdrawal'
)
```

#### Getting Cash Position

```python
# Get current cash position
cash_position = portfolio.fund_accounting.cash_manager.get_cash_position()
print(f"Current Cash: R$ {cash_position:,.2f}")

# Get cash position as of a specific date
cash_position_past = portfolio.fund_accounting.cash_manager.get_cash_position('2024-06-30')
print(f"Cash on 2024-06-30: R$ {cash_position_past:,.2f}")
```

#### CSV Format

Deposits and withdrawals are stored in `data/fund/client_deposits_withdrawals.csv`:

```csv
date,investor_id,investor_name,type,amount,currency,amount_brl,description
2024-01-15,INV001,João Silva,deposit,1000000.00,BRL,1000000.00,Initial investment
2024-06-15,INV001,João Silva,withdrawal,100000.00,BRL,100000.00,Partial withdrawal
```

### Investor Tracking

Track each investor's stake in the fund.

#### Getting Investor Stakes

```python
# Get current investor stakes
investor_stakes = portfolio.fund_accounting.investor_tracker.get_investor_stakes()

for _, investor in investor_stakes.iterrows():
    print(f"{investor['investor_name']}: {investor['stake_pct']:.2f}% "
          f"(R$ {investor['net_contribution']:,.2f})")
```

#### Getting Investor Positions with NAV

```python
# Get investor positions including NAV allocation
investor_positions = portfolio.get_investor_positions()

print(f"Total Fund NAV: R$ {investor_positions['total_nav']:,.2f}")
print(f"Number of Investors: {investor_positions['num_investors']}")

for investor in investor_positions['investors']:
    print(f"\n{investor['investor_name']}:")
    print(f"  Stake: {investor['stake_pct']:.2f}%")
    print(f"  NAV: R$ {investor['nav']:,.2f}")
    print(f"  Net Contribution: R$ {investor['net_contribution']:,.2f}")
    print(f"  Unrealized Gain: R$ {investor['unrealized_gain']:,.2f}")
    print(f"  Return: {investor['return_pct']:.2f}%")
```

### Fee Calculations

Calculate management and performance fees.

#### Fee Structure

- **Management Fee**: 2% annual fee on NAV
  - Calculated daily as: `NAV * 0.02 / 365 * days_in_period`

- **Performance Fee**: 20% on gains above high water mark
  - Only charged when NAV exceeds previous high
  - Formula: `(NAV_end - High_Water_Mark) * 0.20`

#### Calculating Period Fees

```python
# Calculate fees for a period (e.g., 2024)
fees = portfolio.calculate_period_fees(
    period_start='2024-01-01',
    period_end='2024-12-31',
    calculate_management=True,
    calculate_performance=True
)

print(f"Management Fee (2%): R$ {fees['management_fee']:,.2f}")
print(f"Performance Fee (20%): R$ {fees['performance_fee']:,.2f}")
print(f"Total Fees: R$ {fees['total_fees']:,.2f}")
print(f"NAV After Fees: R$ {fees['nav_after_fees']:,.2f}")
```

#### Getting Fee Summary

```python
# Get summary of all fees
fee_summary = portfolio.get_fee_summary()

print(f"Total Management Fees: R$ {fee_summary['total_management_fees']:,.2f}")
print(f"Total Performance Fees: R$ {fee_summary['total_performance_fees']:,.2f}")
print(f"Outstanding Fees: R$ {fee_summary['outstanding_fees']:,.2f}")
print(f"Paid Fees: R$ {fee_summary['paid_fees']:,.2f}")
```

#### Marking Fees as Paid

```python
# Mark a specific fee as paid
fee_calculator = portfolio.fund_accounting.fee_calculator
outstanding_fees = fee_calculator.get_outstanding_fees()

# Mark first outstanding fee as paid
if not outstanding_fees.empty:
    fee_calculator.mark_fee_as_paid(
        payment_index=outstanding_fees.index[0],
        payment_date='2024-12-31'
    )
```

#### Fee CSV Format

Fees are tracked in `data/fund/payments_to_company.csv`:

```csv
date,investor_id,investor_name,fee_type,period_start,period_end,nav_start,nav_end,fee_rate,fee_amount,paid,payment_date
2024-12-31,FUND,Fund Level,management,2024-01-01,2024-12-31,1000000.00,1200000.00,0.02,24000.00,False,
2024-12-31,FUND,Fund Level,performance,2024-01-01,2024-12-31,1000000.00,1200000.00,0.20,40000.00,False,
```

## Performance Analytics

### Monthly Performance Heatmap

Visualize monthly returns in a heatmap format.

#### Generating Heatmap

```python
# Get heatmap (Plotly - interactive)
fig = portfolio.get_monthly_performance_heatmap(
    start_date='2022-01-01',
    end_date='2024-12-31',
    chart_type='plotly'
)

# Display in Jupyter notebook
fig.show()

# Save as HTML
fig.write_html('monthly_heatmap.html')

# Or use Seaborn (static, for reports)
fig_seaborn = portfolio.get_monthly_performance_heatmap(
    start_date='2022-01-01',
    chart_type='seaborn'
)
```

#### Example Output

```
Monthly Returns Heatmap:
        Jan    Feb    Mar    Apr    May    Jun    Jul    Aug    Sep    Oct    Nov    Dec
2024   2.5%   1.3%  -0.5%   3.2%   1.8%   2.1%   0.9%   1.5%  -1.2%   2.7%   1.4%   2.0%
2023   1.8%   2.2%   3.1%  -0.8%   2.5%   1.9%   1.3%   2.8%   0.7%   1.6%   2.4%   1.9%
2022  -1.2%   0.8%   2.3%   1.5%  -0.3%   1.7%   2.1%   0.9%   1.4%  -0.5%   1.8%   2.2%
```

### Cumulative Returns Comparison

Compare portfolio performance with individual assets.

#### Creating Comparison

```python
# Compare portfolio with key assets
result = portfolio.get_cumulative_returns_comparison(
    asset_symbols=['^BVSP', 'PETR4.SA', 'VALE3.SA', 'BTC-USD'],
    asset_names={
        '^BVSP': 'Bovespa',
        'PETR4.SA': 'Petrobras',
        'VALE3.SA': 'Vale',
        'BTC-USD': 'Bitcoin'
    },
    start_date='2023-01-01',
    end_date='2024-12-31'
)

# Display chart
result['chart'].show()

# Get comparison data
comparison_df = pd.DataFrame(result['comparison'])
print(comparison_df.tail())
```

#### Example Output

```
Cumulative Returns (Indexed to 100):
          Date  Portfolio  Bovespa  Petrobras  Vale  Bitcoin
2024-12-31    100.0     118.5     105.3      142.0  95.2     156.8
```

This shows the portfolio returned 18.5% compared to Bovespa's 5.3%.

### Alpha Analysis

Measure excess returns vs benchmark.

#### Calculating Alpha

```python
# Get alpha analysis vs Bovespa
alpha_result = portfolio.get_alpha_analysis(
    benchmark_symbol='^BVSP',
    start_date='2024-01-01',
    end_date='2024-12-31'
)

metrics = alpha_result['metrics']

print(f"Alpha (Simple): {metrics['alpha_simple']:.2f}%")
print(f"Jensen's Alpha: {metrics['jensens_alpha']:.2f}%")
print(f"Beta: {metrics['beta']:.2f}")
print(f"Information Ratio: {metrics['information_ratio']:.2f}")
print(f"Tracking Error: {metrics['tracking_error']:.2f}%")
print(f"Win Rate: {metrics['win_rate']:.2f}%")
print(f"Correlation: {metrics['correlation']:.2f}")

# Display alpha chart
alpha_result['chart'].show()
```

#### Alpha Metrics Explained

- **Alpha (Simple)**: Average excess return over benchmark (annualized)
  - Positive = outperforming benchmark
  - Formula: `(Portfolio_Return - Benchmark_Return) * 252`

- **Jensen's Alpha**: Risk-adjusted excess return
  - Accounts for portfolio beta
  - Formula: `Portfolio_Return - (RiskFree + Beta * (Benchmark_Return - RiskFree))`

- **Beta**: Portfolio sensitivity to benchmark
  - Beta > 1: More volatile than benchmark
  - Beta < 1: Less volatile than benchmark
  - Beta = 1: Moves with benchmark

- **Information Ratio**: Alpha per unit of tracking error
  - Higher is better
  - Formula: `Alpha / Tracking_Error`

- **Tracking Error**: Volatility of excess returns
  - Lower = portfolio tracks benchmark closely

- **Win Rate**: Percentage of days portfolio outperformed
  - Above 50% = more winning days than losing

## API Reference

### Fund Accounting Endpoints

#### GET /api/fund/nav

Get fund Net Asset Value.

**Parameters:**
- `as_of_date` (optional): Date for NAV calculation (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "date": "2024-12-31",
    "portfolio_value": 5250000.00,
    "cash_position": 250000.00,
    "outstanding_fees": 64000.00,
    "nav": 5436000.00
  }
}
```

#### GET /api/fund/investors

Get all investor positions and stakes.

**Parameters:**
- `as_of_date` (optional): Date for calculation (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "as_of_date": "2024-12-31",
    "total_nav": 5436000.00,
    "num_investors": 3,
    "investors": [
      {
        "investor_id": "INV001",
        "investor_name": "João Silva",
        "deposits": 2000000.00,
        "withdrawals": 0.00,
        "net_contribution": 2000000.00,
        "stake_pct": 50.0,
        "nav": 2718000.00,
        "unrealized_gain": 718000.00,
        "return_pct": 35.9
      }
    ]
  }
}
```

#### POST /api/fund/fees/calculate

Calculate fees for a period.

**Request Body:**
```json
{
  "period_start": "2024-01-01",
  "period_end": "2024-12-31",
  "calculate_management": true,
  "calculate_performance": true
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "period_start": "2024-01-01",
    "period_end": "2024-12-31",
    "nav_start": 4000000.00,
    "nav_end": 5500000.00,
    "management_fee": 109589.04,
    "performance_fee": 300000.00,
    "total_fees": 409589.04,
    "nav_after_fees": 5090410.96
  }
}
```

#### GET /api/fund/fees/summary

Get summary of all fees.

**Parameters:**
- `start_date` (optional): Filter start date
- `end_date` (optional): Filter end date

**Response:**
```json
{
  "success": true,
  "data": {
    "total_management_fees": 109589.04,
    "total_performance_fees": 300000.00,
    "total_fees": 409589.04,
    "outstanding_fees": 409589.04,
    "paid_fees": 0.00,
    "num_payments": 2,
    "num_outstanding": 2
  }
}
```

#### POST /api/fund/cash/deposit

Record a cash deposit.

**Request Body:**
```json
{
  "date": "2024-01-15",
  "investor_id": "INV001",
  "investor_name": "João Silva",
  "amount": 1000000.00,
  "currency": "BRL",
  "description": "Initial investment"
}
```

#### POST /api/fund/cash/withdrawal

Record a cash withdrawal.

**Request Body:**
```json
{
  "date": "2024-06-15",
  "investor_id": "INV001",
  "investor_name": "João Silva",
  "amount": 100000.00,
  "currency": "BRL",
  "description": "Partial withdrawal"
}
```

### Performance Analytics Endpoints

#### GET /api/analytics/heatmap

Get monthly performance heatmap.

**Parameters:**
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)
- `format` (optional): 'json' or 'html' (default: json)

**Response:** Plotly figure JSON or HTML

#### GET /api/analytics/cumulative-returns

Compare cumulative returns.

**Parameters:**
- `symbols` (required): Comma-separated list of symbols
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Example:**
```
GET /api/analytics/cumulative-returns?symbols=^BVSP,PETR4.SA,BTC-USD&start_date=2024-01-01
```

#### GET /api/analytics/alpha

Get alpha analysis.

**Parameters:**
- `benchmark` (optional): Benchmark symbol (default: ^BVSP)
- `start_date` (optional): Start date (YYYY-MM-DD)
- `end_date` (optional): End date (YYYY-MM-DD)

**Response:**
```json
{
  "success": true,
  "data": {
    "metrics": {
      "alpha_simple": 12.5,
      "jensens_alpha": 11.8,
      "beta": 0.95,
      "information_ratio": 1.45,
      "tracking_error": 8.6,
      "win_rate": 54.2,
      "correlation": 0.82
    },
    "comparison": [...],
    "chart": {...}
  }
}
```

#### GET /api/analytics/dashboard

Get complete analytics dashboard.

**Parameters:**
- `symbols` (optional): Comma-separated comparison symbols
- `benchmark` (optional): Benchmark symbol (default: ^BVSP)

## Usage Examples

### Complete Fund Workflow

```python
from src.portfolio_aggregator import PortfolioAggregator

# Initialize
portfolio = PortfolioAggregator()

# 1. Record investor deposits
portfolio.fund_accounting.cash_manager.add_transaction(
    date='2024-01-01',
    investor_id='INV001',
    investor_name='João Silva',
    transaction_type='deposit',
    amount=2000000.00,
    currency='BRL'
)

portfolio.fund_accounting.cash_manager.add_transaction(
    date='2024-01-01',
    investor_id='INV002',
    investor_name='Maria Santos',
    transaction_type='deposit',
    amount=1000000.00,
    currency='BRL'
)

# 2. Check fund NAV
nav_data = portfolio.get_fund_nav()
print(f"Fund NAV: R$ {nav_data['nav']:,.2f}")

# 3. Check investor positions
investors = portfolio.get_investor_positions()
for inv in investors['investors']:
    print(f"{inv['investor_name']}: {inv['stake_pct']:.1f}% "
          f"(R$ {inv['nav']:,.2f})")

# 4. Calculate annual fees
fees = portfolio.calculate_period_fees(
    period_start='2024-01-01',
    period_end='2024-12-31'
)
print(f"Total Fees: R$ {fees['total_fees']:,.2f}")

# 5. Generate monthly heatmap
heatmap = portfolio.get_monthly_performance_heatmap()
heatmap.show()

# 6. Compare with Bovespa
alpha = portfolio.get_alpha_analysis(benchmark_symbol='^BVSP')
print(f"Alpha: {alpha['metrics']['alpha_simple']:.2f}%")
print(f"Beta: {alpha['metrics']['beta']:.2f}")
```

### JavaScript/React Integration

```javascript
// Fetch fund NAV
const fetchFundNAV = async () => {
  const response = await fetch('http://localhost:5000/api/fund/nav');
  const result = await response.json();

  if (result.success) {
    console.log(`Fund NAV: R$ ${result.data.nav.toLocaleString()}`);
  }
};

// Get investor positions
const fetchInvestors = async () => {
  const response = await fetch('http://localhost:5000/api/fund/investors');
  const result = await response.json();

  if (result.success) {
    result.data.investors.forEach(investor => {
      console.log(`${investor.investor_name}: ${investor.stake_pct}%`);
    });
  }
};

// Record deposit
const recordDeposit = async (deposit) => {
  const response = await fetch('http://localhost:5000/api/fund/cash/deposit', {
    method: 'POST',
    headers: {'Content-Type': 'application/json'},
    body: JSON.stringify(deposit)
  });

  const result = await response.json();
  return result.success;
};

// Get monthly heatmap
const fetchHeatmap = async () => {
  const response = await fetch('http://localhost:5000/api/analytics/heatmap?format=json');
  const result = await response.json();

  if (result.success) {
    // Parse Plotly JSON and render
    const fig = JSON.parse(result.data);
    Plotly.newPlot('heatmap-div', fig.data, fig.layout);
  }
};

// Get alpha analysis
const fetchAlpha = async () => {
  const response = await fetch('http://localhost:5000/api/analytics/alpha?benchmark=^BVSP');
  const result = await response.json();

  if (result.success) {
    const metrics = result.data.metrics;
    console.log(`Alpha: ${metrics.alpha_simple.toFixed(2)}%`);
    console.log(`Beta: ${metrics.beta.toFixed(2)}`);
    console.log(`Info Ratio: ${metrics.information_ratio.toFixed(2)}`);
  }
};
```

## Best Practices

### Fee Calculation Timing

1. **Management Fees**: Calculate monthly or quarterly
   - Pro-rata based on days: `NAV * 0.02 * days / 365`

2. **Performance Fees**: Calculate annually
   - Only when NAV exceeds high water mark
   - Update high water mark after fee calculation

### Investor Onboarding

1. Record deposit transaction
2. Generate investor ID (e.g., INV001, INV002)
3. Calculate initial stake percentage
4. Update investor documentation

### Reporting Schedule

- **Daily**: NAV calculation
- **Monthly**: Performance reports, heatmap updates
- **Quarterly**: Fee calculations, investor statements
- **Annually**: Performance fees, tax documents

### Data Backup

- Back up CSV files regularly
- Keep historical copies of `client_deposits_withdrawals.csv`
- Archive `payments_to_company.csv` after payments processed
- Maintain historical NAV database

## Troubleshooting

### Issue: Fees not calculating correctly

**Solution**: Ensure NAV is calculated before fee calculation. Check that high water mark is initialized.

### Issue: Investor stakes don't sum to 100%

**Solution**: This is normal if there are outstanding withdrawals or if cash is included separately.

### Issue: Heatmap shows no data

**Solution**: Ensure historical data is initialized. Run `portfolio.initialize_historical_data()` first.

### Issue: Alpha calculation returns empty

**Solution**: Verify benchmark data is available in historical database. Ensure date ranges overlap.

## Support

For issues or questions:
- Check README.md for general setup
- Review API documentation above
- Test with provided usage examples

## Version History

- **v3.0.0**: Added fund accounting and performance analytics
- **v2.0.0**: Added historical performance tracking
- **v1.0.0**: Initial portfolio tracker release
