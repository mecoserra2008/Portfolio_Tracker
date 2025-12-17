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
from .market_data import MarketDataFetcher
from .historical_data import HistoricalDataManager
from .portfolio_performance import PortfolioPerformanceCalculator


class PortfolioAggregator:
    """
    Aggregates all portfolio types (stocks, crypto, bonds) into unified views
    """

    def __init__(self):
        """Initialize portfolio aggregator"""
        self.market_data = MarketDataFetcher()

        # Initialize individual portfolios
        self.stock_portfolio = StockPortfolio('data/stocks/orders.csv', self.market_data)
        self.crypto_portfolio = CryptoPortfolio('data/crypto/orders.csv', self.market_data)
        self.bond_portfolio = BondPortfolio('data/bonds', self.market_data)

        # Historical data and performance
        self.historical_manager = HistoricalDataManager()
        self.performance_calculator = PortfolioPerformanceCalculator(self.historical_manager)

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

        # Exchange rates
        rates = self._get_exchange_rates()

        # Convert stock values to base currency (assuming stocks are in their local currencies)
        # For now, assuming most values are already in BRL or will need conversion
        stock_value_brl = stock_summary['total_market_value']
        crypto_value_brl = crypto_summary['total_market_value']
        bond_value_brl = bond_summary['total_current_value']

        # Total portfolio
        total_value = stock_value_brl + crypto_value_brl + bond_value_brl

        # Calculate allocations
        stock_allocation = (stock_value_brl / total_value * 100) if total_value > 0 else 0
        crypto_allocation = (crypto_value_brl / total_value * 100) if total_value > 0 else 0
        bond_allocation = (bond_value_brl / total_value * 100) if total_value > 0 else 0

        # Calculate total P&L
        total_pnl = (stock_summary['total_pnl'] +
                     crypto_summary['total_pnl'] +
                     bond_summary['total_pnl'])

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
            'bonds': self.bond_portfolio.get_current_values().to_dict('records')
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
