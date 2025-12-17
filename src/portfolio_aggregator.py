"""
Portfolio Aggregator
Combines stocks, crypto, and bonds into a unified portfolio view
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from .stock_portfolio import StockPortfolio
from .crypto_portfolio import CryptoPortfolio
from .bond_portfolio import BondPortfolio
from .futures_portfolio import FuturesPortfolio
from .options_portfolio import OptionsPortfolio
from .market_data import MarketDataFetcher
from .ibkr_data import IBKRDataFetcherMock
from .historical_data import HistoricalDataManager
from .portfolio_performance import PortfolioPerformanceCalculator
from .fund_accounting import FundAccountingSystem
from .performance_analytics import PerformanceAnalytics


class PortfolioAggregator:
    """
    Aggregates all portfolio types (stocks, crypto, bonds) into unified views
    """

    def __init__(self):
        """Initialize portfolio aggregator"""
        self.market_data = MarketDataFetcher()

        # IBKR data fetcher for derivatives
        self.ibkr_data = IBKRDataFetcherMock()
        self.ibkr_data.connect()

        # Initialize individual portfolios
        self.stock_portfolio = StockPortfolio('data/stocks/orders.csv', self.market_data)
        self.crypto_portfolio = CryptoPortfolio('data/crypto/orders.csv', self.market_data)
        self.bond_portfolio = BondPortfolio('data/bonds', self.market_data)
        self.futures_portfolio = FuturesPortfolio('data/futures/orders.csv', self.ibkr_data)
        self.options_portfolio = OptionsPortfolio('data/options/orders.csv', self.ibkr_data)

        # Historical data and performance
        self.historical_manager = HistoricalDataManager()
        self.performance_calculator = PortfolioPerformanceCalculator(self.historical_manager)

        # Fund accounting and analytics
        self.fund_accounting = FundAccountingSystem()
        self.performance_analytics = PerformanceAnalytics(self.performance_calculator)

        # Currency conversions
        self.usd_brl = None
        self.eur_brl = None

    def _get_exchange_rates(self):
        """Fetch current exchange rates"""
        if self.usd_brl is None:
            self.usd_brl = self.market_data.get_exchange_rate('USD', 'BRL') or 5.0
        if self.eur_brl is None:
            self.eur_brl = self.market_data.get_exchange_rate('EUR', 'BRL') or 5.5

        return {
            'USD/BRL': self.usd_brl,
            'EUR/BRL': self.eur_brl,
            'BRL/USD': 1.0 / self.usd_brl if self.usd_brl else 0.2,
            'BRL/EUR': 1.0 / self.eur_brl if self.eur_brl else 0.18
        }

    def get_consolidated_summary(self, base_currency: str = 'BRL') -> Dict:
        """
        Get consolidated portfolio summary across all asset types

        Args:
            base_currency: Currency for reporting (BRL, USD, EUR)

        Returns:
            Dictionary with consolidated metrics
        """
        # Get individual summaries
        stock_summary = self.stock_portfolio.get_portfolio_summary()
        crypto_summary = self.crypto_portfolio.get_portfolio_summary(currency=base_currency)
        bond_summary = self.bond_portfolio.get_portfolio_summary()
        futures_summary = self.futures_portfolio.get_portfolio_summary()
        options_summary = self.options_portfolio.get_portfolio_summary()

        # Exchange rates
        rates = self._get_exchange_rates()

        # Convert values to base currency
        stock_value_brl = stock_summary['total_market_value']
        crypto_value_brl = crypto_summary['total_market_value']
        bond_value_brl = bond_summary['total_current_value']
        futures_value_brl = futures_summary['total_notional']  # Notional value for futures
        options_value_brl = options_summary['total_market_value']

        # Total portfolio
        total_value = stock_value_brl + crypto_value_brl + bond_value_brl + futures_value_brl + options_value_brl

        # Calculate allocations
        stock_allocation = (stock_value_brl / total_value * 100) if total_value > 0 else 0
        crypto_allocation = (crypto_value_brl / total_value * 100) if total_value > 0 else 0
        bond_allocation = (bond_value_brl / total_value * 100) if total_value > 0 else 0
        futures_allocation = (futures_value_brl / total_value * 100) if total_value > 0 else 0
        options_allocation = (options_value_brl / total_value * 100) if total_value > 0 else 0

        # Calculate total P&L
        total_pnl = (stock_summary['total_pnl'] +
                     crypto_summary['total_pnl'] +
                     bond_summary['total_pnl'] +
                     futures_summary['total_pnl'] +
                     options_summary['total_pnl'])

        total_cost = (stock_summary['total_cost_basis'] +
                      crypto_summary['total_cost_basis'] +
                      bond_summary['total_invested'])

        total_return_pct = (total_pnl / total_cost * 100) if total_cost > 0 else 0

        return {
            'total_portfolio_value': total_value,
            'base_currency': base_currency,
            'total_pnl': total_pnl,
            'total_return_pct': total_return_pct,
            'asset_allocation': {
                'stocks': {
                    'value': stock_value_brl,
                    'allocation_pct': stock_allocation,
                    'num_positions': stock_summary['num_positions'],
                    'pnl': stock_summary['total_pnl'],
                    'return_pct': stock_summary['total_return_pct']
                },
                'crypto': {
                    'value': crypto_value_brl,
                    'allocation_pct': crypto_allocation,
                    'num_positions': crypto_summary['num_positions'],
                    'pnl': crypto_summary['total_pnl'],
                    'return_pct': crypto_summary['total_return_pct']
                },
                'bonds': {
                    'value': bond_value_brl,
                    'allocation_pct': bond_allocation,
                    'num_positions': bond_summary['num_bonds'],
                    'pnl': bond_summary['total_pnl'],
                    'return_pct': bond_summary['total_return_pct']
                },
                'futures': {
                    'value': futures_value_brl,
                    'allocation_pct': futures_allocation,
                    'num_contracts': futures_summary['num_contracts'],
                    'pnl': futures_summary['total_pnl'],
                    'unrealized_pnl': futures_summary['total_unrealized_pnl'],
                    'realized_pnl': futures_summary['total_realized_pnl'],
                    'long_contracts': futures_summary['long_contracts'],
                    'short_contracts': futures_summary['short_contracts']
                },
                'options': {
                    'value': options_value_brl,
                    'allocation_pct': options_allocation,
                    'num_contracts': options_summary['num_contracts'],
                    'pnl': options_summary['total_pnl'],
                    'unrealized_pnl': options_summary['total_unrealized_pnl'],
                    'realized_pnl': options_summary['total_realized_pnl'],
                    'portfolio_delta': options_summary['portfolio_delta'],
                    'portfolio_theta': options_summary['portfolio_theta'],
                    'long_contracts': options_summary['long_contracts'],
                    'short_contracts': options_summary['short_contracts']
                }
            },
            'exchange_rates': rates
        }

    def get_all_positions(self) -> Dict:
        """
        Get all positions across all asset types

        Returns:
            Dictionary with positions by asset type
        """
        return {
            'stocks': self.stock_portfolio.get_current_values().to_dict('records'),
            'crypto': self.crypto_portfolio.get_current_values().to_dict('records'),
            'bonds': self.bond_portfolio.get_current_values().to_dict('records'),
            'futures': self.futures_portfolio.get_current_values().to_dict('records'),
            'options': self.options_portfolio.get_current_values().to_dict('records')
        }

    def get_top_performers(self, n: int = 10) -> pd.DataFrame:
        """
        Get top performing positions across all assets

        Args:
            n: Number of top performers to return

        Returns:
            DataFrame with top performers
        """
        performers = []

        # Stocks
        stock_positions = self.stock_portfolio.get_current_values()
        if not stock_positions.empty:
            for _, pos in stock_positions.iterrows():
                performers.append({
                    'Asset': pos['Symbol'],
                    'Type': 'Stock',
                    'Market': pos['Market'],
                    'Value': pos['Market Value'],
                    'P&L %': pos['Total P&L %']
                })

        # Crypto
        crypto_positions = self.crypto_portfolio.get_current_values()
        if not crypto_positions.empty:
            for _, pos in crypto_positions.iterrows():
                performers.append({
                    'Asset': pos['Symbol'],
                    'Type': 'Crypto',
                    'Market': 'Global',
                    'Value': pos['Market Value'],
                    'P&L %': pos['Total P&L %']
                })

        # Bonds
        bond_positions = self.bond_portfolio.get_current_values()
        if not bond_positions.empty:
            for _, pos in bond_positions.iterrows():
                performers.append({
                    'Asset': pos['Título'][:30],  # Truncate long bond names
                    'Type': 'Bond',
                    'Market': 'Brasil',
                    'Value': pos['Valor Atual'],
                    'P&L %': pos['P&L %']
                })

        df = pd.DataFrame(performers)

        if df.empty:
            return df

        # Sort by P&L % descending
        df = df.sort_values('P&L %', ascending=False)

        return df.head(n)

    def get_allocation_chart_data(self) -> Dict:
        """
        Get data formatted for allocation charts

        Returns:
            Dictionary with chart-ready data
        """
        summary = self.get_consolidated_summary()

        # Asset type allocation
        asset_allocation = [
            {'name': 'Stocks', 'value': summary['asset_allocation']['stocks']['value']},
            {'name': 'Crypto', 'value': summary['asset_allocation']['crypto']['value']},
            {'name': 'Bonds', 'value': summary['asset_allocation']['bonds']['value']}
        ]

        # Market allocation (for stocks)
        stock_df = self.stock_portfolio.get_current_values()
        market_allocation = []
        if not stock_df.empty:
            by_market = stock_df.groupby('Market')['Market Value'].sum()
            for market, value in by_market.items():
                market_allocation.append({'name': market, 'value': value})

        # Bond type allocation
        bond_type_allocation = []
        bond_by_type = self.bond_portfolio.get_allocation_by_type()
        if not bond_by_type.empty:
            for _, row in bond_by_type.iterrows():
                bond_type_allocation.append({
                    'name': row['Tipo'],
                    'value': row['Valor Atual']
                })

        return {
            'asset_allocation': asset_allocation,
            'market_allocation': market_allocation,
            'bond_type_allocation': bond_type_allocation
        }

    def export_complete_report(self, filename: str = None) -> Dict:
        """
        Export complete portfolio report

        Args:
            filename: Optional filename to save JSON report

        Returns:
            Complete portfolio data dictionary
        """
        report = {
            'generated_at': datetime.now().isoformat(),
            'summary': self.get_consolidated_summary(),
            'positions': self.get_all_positions(),
            'stocks': {
                'summary': self.stock_portfolio.get_portfolio_summary(),
                'positions': self.stock_portfolio.get_current_values().to_dict('records'),
                'transactions': self.stock_portfolio.get_transactions_history().to_dict('records')
            },
            'crypto': {
                'summary': self.crypto_portfolio.get_portfolio_summary(),
                'positions': self.crypto_portfolio.get_current_values().to_dict('records'),
                'allocation': self.crypto_portfolio.get_allocation().to_dict('records'),
                'transactions': self.crypto_portfolio.get_transactions_history().to_dict('records')
            },
            'bonds': {
                'summary': self.bond_portfolio.get_portfolio_summary(),
                'positions': self.bond_portfolio.get_current_values().to_dict('records'),
                'allocation_by_type': self.bond_portfolio.get_allocation_by_type().to_dict('records'),
                'allocation_by_indexer': self.bond_portfolio.get_allocation_by_indexer().to_dict('records'),
                'maturity_schedule': self.bond_portfolio.get_maturity_schedule().to_dict('records')
            },
            'top_performers': self.get_top_performers(20).to_dict('records'),
            'chart_data': self.get_allocation_chart_data()
        }

        if filename:
            import json
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(report, f, indent=2, ensure_ascii=False, default=str)

        return report

    def initialize_historical_data(self, start_date: str = '2020-01-01', batch_days: int = 90):
        """
        Initialize historical data for all portfolio assets

        Args:
            start_date: Start date for historical data
            batch_days: Days per batch for fetching

        Returns:
            Dictionary with fetch statistics
        """
        print(f"\n{'='*60}")
        print("Initializing Historical Data for Portfolio")
        print(f"{'='*60}\n")

        # Get all unique symbols from portfolios
        symbols = []

        # Stocks
        if not self.stock_portfolio.positions:
            self.stock_portfolio.calculate_positions()

        for symbol, pos in self.stock_portfolio.positions.items():
            if pos['quantity'] != 0:
                yahoo_symbol = self.stock_portfolio._get_yahoo_symbol(symbol, pos['market'])
                symbols.append(yahoo_symbol)

        # Crypto
        if not self.crypto_portfolio.positions:
            self.crypto_portfolio.calculate_positions()

        for symbol in self.crypto_portfolio.positions.keys():
            crypto_symbol = f"{symbol}-USD" if not symbol.endswith('-USD') else symbol
            symbols.append(crypto_symbol)

        # Remove duplicates
        symbols = list(set(symbols))

        print(f"Found {len(symbols)} unique symbols to fetch")
        print(f"Symbols: {', '.join(symbols[:10])}{'...' if len(symbols) > 10 else ''}\n")

        # Bulk fetch
        self.historical_manager.bulk_fetch(symbols, start_date, batch_days=batch_days)

        # Get stats
        stats = self.historical_manager.get_database_stats()

        print(f"\n{'='*60}")
        print("Historical Data Initialization Complete!")
        print(f"{'='*60}")
        print(f"Total symbols: {stats['total_symbols']}")
        print(f"Total records: {stats['total_records']}")
        print(f"{'='*60}\n")

        return stats

    def get_historical_performance(
        self,
        start_date: str = None,
        end_date: str = None,
        period: str = '1Y'
    ) -> Dict:
        """
        Get historical portfolio performance

        Args:
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)
            period: Preset period (1M, 3M, 6M, 1Y, 3Y, 5Y, YTD, MAX)

        Returns:
            Dictionary with performance data and metrics
        """
        # Handle preset periods
        if not start_date:
            end_date = end_date or datetime.now().strftime('%Y-%m-%d')
            end_ts = pd.Timestamp(end_date)

            if period == '1M':
                start_date = (end_ts - timedelta(days=30)).strftime('%Y-%m-%d')
            elif period == '3M':
                start_date = (end_ts - timedelta(days=90)).strftime('%Y-%m-%d')
            elif period == '6M':
                start_date = (end_ts - timedelta(days=180)).strftime('%Y-%m-%d')
            elif period == '1Y':
                start_date = (end_ts - timedelta(days=365)).strftime('%Y-%m-%d')
            elif period == '3Y':
                start_date = (end_ts - timedelta(days=1095)).strftime('%Y-%m-%d')
            elif period == '5Y':
                start_date = (end_ts - timedelta(days=1825)).strftime('%Y-%m-%d')
            elif period == 'YTD':
                start_date = f"{end_ts.year}-01-01"
            elif period == 'MAX':
                start_date = '2020-01-01'
            else:
                start_date = (end_ts - timedelta(days=365)).strftime('%Y-%m-%d')

        # Calculate portfolio history
        history_df = self.performance_calculator.calculate_portfolio_history(
            self.stock_portfolio,
            self.crypto_portfolio,
            self.bond_portfolio,
            start_date,
            end_date
        )

        if history_df.empty:
            return {
                'performance': [],
                'metrics': {},
                'period': period,
                'start_date': start_date,
                'end_date': end_date
            }

        # Calculate risk metrics
        metrics = self.performance_calculator.calculate_risk_metrics(history_df)

        # Get drawdown data
        drawdown_df = self.performance_calculator.get_drawdown_series(history_df['total_value'])

        # Get rolling metrics
        rolling_metrics = self.performance_calculator.get_rolling_metrics(history_df, window_days=30)

        return {
            'performance': history_df.to_dict('records'),
            'metrics': metrics,
            'drawdown': drawdown_df.to_dict('records'),
            'rolling_metrics': rolling_metrics.to_dict('records'),
            'period': period,
            'start_date': start_date,
            'end_date': end_date or datetime.now().strftime('%Y-%m-%d')
        }

    def get_performance_comparison(
        self,
        start_date: str = None,
        end_date: str = None,
        benchmark: str = '^BVSP'  # Bovespa Index for Brazilian portfolio
    ) -> Dict:
        """
        Compare portfolio performance to benchmark

        Args:
            start_date: Start date
            end_date: End date
            benchmark: Benchmark symbol (default: Bovespa)

        Returns:
            Dictionary with comparison data
        """
        if not start_date:
            end_date = end_date or datetime.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp(end_date) - timedelta(days=365)).strftime('%Y-%m-%d')

        # Get portfolio history
        history_df = self.performance_calculator.calculate_portfolio_history(
            self.stock_portfolio,
            self.crypto_portfolio,
            self.bond_portfolio,
            start_date,
            end_date
        )

        if history_df.empty:
            return {}

        # Compare to benchmark
        comparison_df = self.performance_calculator.compare_to_benchmark(
            history_df,
            benchmark
        )

        return {
            'comparison': comparison_df.to_dict('records'),
            'benchmark_symbol': benchmark,
            'start_date': start_date,
            'end_date': end_date
        }

    # ===== Fund Accounting Methods =====

    def get_fund_nav(self, as_of_date: str = None) -> Dict:
        """
        Get fund Net Asset Value (NAV) including cash and fees

        Args:
            as_of_date: Date for NAV calculation (default: today)

        Returns:
            Dictionary with NAV breakdown
        """
        summary = self.get_consolidated_summary()
        portfolio_value = summary['total_portfolio_value']
        cash_position = self.fund_accounting.cash_manager.get_cash_position(as_of_date)
        nav = self.fund_accounting.calculate_nav(portfolio_value, cash_position)

        return {
            'date': as_of_date or datetime.now().strftime('%Y-%m-%d'),
            'portfolio_value': portfolio_value,
            'cash_position': cash_position,
            'outstanding_fees': self.fund_accounting.fee_calculator.get_outstanding_fees()['fee_amount'].sum(),
            'nav': nav
        }

    def get_investor_positions(self, as_of_date: str = None) -> Dict:
        """
        Get all investor positions and their NAV shares

        Args:
            as_of_date: Date for calculation (default: today)

        Returns:
            Dictionary with investor positions
        """
        nav_info = self.get_fund_nav(as_of_date)
        total_nav = nav_info['nav']

        investor_stakes = self.fund_accounting.investor_tracker.get_investor_stakes(as_of_date)

        investors = []
        for _, investor in investor_stakes.iterrows():
            investor_nav = total_nav * (investor['stake_pct'] / 100)
            investors.append({
                'investor_id': investor['investor_id'],
                'investor_name': investor['investor_name'],
                'deposits': investor['deposits'],
                'withdrawals': investor['withdrawals'],
                'net_contribution': investor['net_contribution'],
                'stake_pct': investor['stake_pct'],
                'nav': investor_nav,
                'unrealized_gain': investor_nav - investor['net_contribution'],
                'return_pct': ((investor_nav - investor['net_contribution']) / investor['net_contribution'] * 100)
                    if investor['net_contribution'] > 0 else 0
            })

        return {
            'as_of_date': as_of_date or datetime.now().strftime('%Y-%m-%d'),
            'total_nav': total_nav,
            'num_investors': len(investors),
            'investors': investors
        }

    def calculate_period_fees(
        self,
        period_start: str,
        period_end: str,
        calculate_management: bool = True,
        calculate_performance: bool = True
    ) -> Dict:
        """
        Calculate management and performance fees for a period

        Args:
            period_start: Period start date
            period_end: Period end date
            calculate_management: Calculate 2% management fee
            calculate_performance: Calculate 20% performance fee

        Returns:
            Dictionary with fee calculations
        """
        nav_start = self.get_fund_nav(period_start)['nav']
        nav_end = self.get_fund_nav(period_end)['nav']

        fees = self.fund_accounting.process_period_fees(
            period_start,
            period_end,
            nav_start,
            nav_end,
            calculate_management,
            calculate_performance
        )

        return fees

    def get_fee_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get summary of all fees

        Args:
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            Fee summary
        """
        return self.fund_accounting.fee_calculator.get_fee_summary(start_date, end_date)

    # ===== Performance Analytics Methods =====

    def get_monthly_performance_heatmap(
        self,
        start_date: str = None,
        end_date: str = None,
        chart_type: str = 'plotly'
    ):
        """
        Get monthly performance heatmap

        Args:
            start_date: Start date (default: 3 years ago)
            end_date: End date (default: today)
            chart_type: 'plotly' or 'seaborn'

        Returns:
            Plotly or Matplotlib figure
        """
        if not start_date:
            end_date = end_date or datetime.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp(end_date) - timedelta(days=1095)).strftime('%Y-%m-%d')  # 3 years

        # Get portfolio history
        history_df = self.performance_calculator.calculate_portfolio_history(
            self.stock_portfolio,
            self.crypto_portfolio,
            self.bond_portfolio,
            start_date,
            end_date
        )

        if history_df.empty:
            return None

        # Calculate monthly returns
        monthly_returns = self.performance_analytics.calculate_monthly_returns(history_df)

        if chart_type == 'seaborn':
            return self.performance_analytics.create_monthly_returns_heatmap_seaborn(monthly_returns)
        else:
            return self.performance_analytics.create_monthly_returns_heatmap_plotly(monthly_returns)

    def get_cumulative_returns_comparison(
        self,
        asset_symbols: List[str],
        asset_names: Dict[str, str] = None,
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        Compare portfolio cumulative returns with individual assets

        Args:
            asset_symbols: List of symbols to compare
            asset_names: Optional display names for symbols
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)

        Returns:
            Dictionary with comparison data and chart
        """
        if not start_date:
            end_date = end_date or datetime.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp(end_date) - timedelta(days=365)).strftime('%Y-%m-%d')

        # Get portfolio history
        history_df = self.performance_calculator.calculate_portfolio_history(
            self.stock_portfolio,
            self.crypto_portfolio,
            self.bond_portfolio,
            start_date,
            end_date
        )

        if history_df.empty:
            return {'comparison': [], 'chart': None}

        # Compare with assets
        comparison_df = self.performance_analytics.compare_cumulative_returns(
            history_df,
            asset_symbols,
            asset_names
        )

        # Create chart
        chart = self.performance_analytics.create_cumulative_return_chart(comparison_df)

        return {
            'comparison': comparison_df.to_dict('records'),
            'chart': chart
        }

    def get_alpha_analysis(
        self,
        benchmark_symbol: str = '^BVSP',
        start_date: str = None,
        end_date: str = None
    ) -> Dict:
        """
        Get alpha analysis vs benchmark

        Args:
            benchmark_symbol: Benchmark symbol (default: Bovespa)
            start_date: Start date (default: 1 year ago)
            end_date: End date (default: today)

        Returns:
            Dictionary with alpha metrics and visualization
        """
        if not start_date:
            end_date = end_date or datetime.now().strftime('%Y-%m-%d')
            start_date = (pd.Timestamp(end_date) - timedelta(days=365)).strftime('%Y-%m-%d')

        # Get portfolio history
        history_df = self.performance_calculator.calculate_portfolio_history(
            self.stock_portfolio,
            self.crypto_portfolio,
            self.bond_portfolio,
            start_date,
            end_date
        )

        if history_df.empty:
            return {'metrics': {}, 'chart': None}

        # Compare to benchmark
        comparison_df = self.performance_calculator.compare_to_benchmark(
            history_df,
            benchmark_symbol
        )

        # Calculate alpha metrics
        alpha_metrics = {}
        if 'daily_return' in comparison_df.columns and 'benchmark_return' in comparison_df.columns:
            alpha_metrics = self.performance_analytics.calculate_alpha(
                comparison_df['daily_return'],
                comparison_df['benchmark_return']
            )

        # Create visualization
        chart = self.performance_analytics.create_alpha_visualization(
            comparison_df,
            comparison_df,
            title=f'Alpha Analysis vs {benchmark_symbol}'
        )

        return {
            'metrics': alpha_metrics,
            'comparison': comparison_df[['date', 'cumulative_return', 'benchmark_cumulative',
                                        'cumulative_alpha']].to_dict('records') if 'cumulative_alpha' in comparison_df.columns else [],
            'chart': chart,
            'benchmark_symbol': benchmark_symbol,
            'start_date': start_date,
            'end_date': end_date
        }

    def generate_analytics_dashboard(
        self,
        comparison_assets: List[str] = None,
        asset_names: Dict[str, str] = None,
        benchmark_symbol: str = '^BVSP'
    ) -> Dict:
        """
        Generate complete performance analytics dashboard

        Args:
            comparison_assets: Assets to compare with portfolio
            asset_names: Display names for assets
            benchmark_symbol: Benchmark for alpha calculation

        Returns:
            Dictionary with all analytics figures
        """
        # Get 1-year history
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (pd.Timestamp(end_date) - timedelta(days=365)).strftime('%Y-%m-%d')

        history_df = self.performance_calculator.calculate_portfolio_history(
            self.stock_portfolio,
            self.crypto_portfolio,
            self.bond_portfolio,
            start_date,
            end_date
        )

        if history_df.empty:
            return {}

        figures = self.performance_analytics.create_performance_dashboard(
            history_df,
            comparison_assets,
            asset_names,
            benchmark_symbol
        )

        return figures


def test_portfolio_aggregator():
    """Test portfolio aggregator"""
    print("Testing Portfolio Aggregator")
    print("=" * 80)

    aggregator = PortfolioAggregator()

    # Get consolidated summary
    print("\n1. Consolidated Portfolio Summary:")
    print("-" * 80)
    summary = aggregator.get_consolidated_summary()
    print(f"Total Portfolio Value: R$ {summary['total_portfolio_value']:,.2f}")
    print(f"Total P&L: R$ {summary['total_pnl']:,.2f}")
    print(f"Total Return: {summary['total_return_pct']:.2f}%")

    print("\n2. Asset Allocation:")
    print("-" * 80)
    for asset_type, data in summary['asset_allocation'].items():
        print(f"\n{asset_type.upper()}:")
        print(f"  Value: R$ {data['value']:,.2f}")
        print(f"  Allocation: {data['allocation_pct']:.2f}%")
        print(f"  Positions: {data['num_positions']}")
        print(f"  P&L: R$ {data['pnl']:,.2f}")
        print(f"  Return: {data['return_pct']:.2f}%")

    print("\n3. Top 10 Performers:")
    print("-" * 80)
    top_performers = aggregator.get_top_performers(10)
    if not top_performers.empty:
        print(top_performers.to_string())

    # Export complete report
    print("\n4. Exporting complete report...")
    report = aggregator.export_complete_report('portfolio_report.json')
    print("   ✓ Report exported to portfolio_report.json")

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_portfolio_aggregator()
