"""
Portfolio Performance Calculator
Calculates historical portfolio values and performance metrics
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from .historical_data import HistoricalDataManager
from .stock_portfolio import StockPortfolio
from .crypto_portfolio import CryptoPortfolio
from .bond_portfolio import BondPortfolio


class PortfolioPerformanceCalculator:
    """
    Calculates portfolio performance over time using historical data
    """

    def __init__(self, historical_manager: HistoricalDataManager = None):
        """Initialize performance calculator"""
        self.historical_manager = historical_manager or HistoricalDataManager()

    def calculate_portfolio_history(
        self,
        stock_portfolio: StockPortfolio,
        crypto_portfolio: CryptoPortfolio,
        bond_portfolio: BondPortfolio,
        start_date: str,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Calculate daily portfolio values over time

        Args:
            stock_portfolio: StockPortfolio instance
            crypto_portfolio: CryptoPortfolio instance
            bond_portfolio: BondPortfolio instance
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), default is today

        Returns:
            DataFrame with columns: date, stock_value, crypto_value, bond_value,
                                   total_value, daily_return, cumulative_return
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # Generate date range
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        results = []

        for date in dates:
            date_str = date.strftime('%Y-%m-%d')

            # Calculate portfolio values for this date
            stock_value = self._calculate_stock_value_at_date(
                stock_portfolio, date_str
            )

            crypto_value = self._calculate_crypto_value_at_date(
                crypto_portfolio, date_str
            )

            bond_value = self._calculate_bond_value_at_date(
                bond_portfolio, date
            )

            total_value = stock_value + crypto_value + bond_value

            results.append({
                'date': date,
                'stock_value': stock_value,
                'crypto_value': crypto_value,
                'bond_value': bond_value,
                'total_value': total_value
            })

        df = pd.DataFrame(results)

        if not df.empty:
            # Calculate returns
            df['daily_return'] = df['total_value'].pct_change() * 100
            df['cumulative_return'] = ((df['total_value'] / df['total_value'].iloc[0]) - 1) * 100

        return df

    def _calculate_stock_value_at_date(
        self,
        portfolio: StockPortfolio,
        date: str
    ) -> float:
        """Calculate stock portfolio value at a specific date"""
        if not portfolio.positions:
            portfolio.calculate_positions()

        total_value = 0.0

        for symbol, pos in portfolio.positions.items():
            if pos['quantity'] == 0:
                continue

            # Get holdings at this date
            holdings_at_date = self._get_holdings_at_date(
                pos['transactions'], date
            )

            if holdings_at_date == 0:
                continue

            # Get price at this date
            yahoo_symbol = portfolio._get_yahoo_symbol(symbol, pos['market'])
            price = self._get_price_at_date(yahoo_symbol, date)

            if price:
                total_value += holdings_at_date * price

        return total_value

    def _calculate_crypto_value_at_date(
        self,
        portfolio: CryptoPortfolio,
        date: str
    ) -> float:
        """Calculate crypto portfolio value at a specific date"""
        if not portfolio.positions:
            portfolio.calculate_positions()

        total_value = 0.0

        for symbol, pos in portfolio.positions.items():
            if pos['quantity'] == 0:
                continue

            # Get holdings at this date
            holdings_at_date = self._get_holdings_at_date(
                pos['transactions'], date
            )

            if holdings_at_date == 0:
                continue

            # Get price at this date
            crypto_symbol = f"{symbol}-USD" if not symbol.endswith('-USD') else symbol
            price = self._get_price_at_date(crypto_symbol, date)

            if price:
                total_value += holdings_at_date * price

        return total_value

    def _calculate_bond_value_at_date(
        self,
        portfolio: BondPortfolio,
        date: pd.Timestamp
    ) -> float:
        """Calculate bond portfolio value at a specific date"""
        bond_values = portfolio.get_current_values(valuation_date=date)

        if bond_values.empty:
            return 0.0

        return bond_values['Valor Atual'].sum()

    def _get_holdings_at_date(self, transactions: List[Dict], date: str) -> float:
        """
        Calculate holdings quantity at a specific date

        Args:
            transactions: List of transactions
            date: Date to calculate holdings

        Returns:
            Quantity held at date
        """
        date_ts = pd.Timestamp(date)
        holdings = 0.0

        for txn in transactions:
            if txn['date'] <= date_ts:
                holdings += txn['quantity']

        return holdings

    def _get_price_at_date(self, symbol: str, date: str) -> float:
        """Get price for symbol at specific date"""
        # Try to get from historical database
        df = self.historical_manager.get_historical_data(symbol, date, date)

        if not df.empty:
            return float(df.iloc[0]['close'])

        # If not in database, try to fetch
        try:
            df = self.historical_manager.fetch_historical_data(
                symbol,
                date,
                date,
                batch_days=1
            )
            if not df.empty:
                return float(df.iloc[0]['close'])
        except:
            pass

        return None

    def calculate_risk_metrics(self, performance_df: pd.DataFrame) -> Dict:
        """
        Calculate risk metrics from performance data

        Args:
            performance_df: DataFrame with daily performance data

        Returns:
            Dictionary with risk metrics
        """
        if performance_df.empty or len(performance_df) < 2:
            return {}

        # Daily returns
        returns = performance_df['daily_return'].dropna()

        if len(returns) == 0:
            return {}

        # Annualization factor (252 trading days)
        annual_factor = 252

        # Calculate metrics
        metrics = {
            # Return metrics
            'total_return_pct': performance_df['cumulative_return'].iloc[-1],
            'annualized_return': returns.mean() * annual_factor,

            # Volatility metrics
            'volatility_daily': returns.std(),
            'volatility_annual': returns.std() * np.sqrt(annual_factor),

            # Sharpe ratio (assuming 0% risk-free rate for simplicity)
            'sharpe_ratio': (returns.mean() * annual_factor) / (returns.std() * np.sqrt(annual_factor))
            if returns.std() > 0 else 0,

            # Sortino ratio (downside deviation)
            'sortino_ratio': self._calculate_sortino_ratio(returns, annual_factor),

            # Maximum drawdown
            'max_drawdown': self._calculate_max_drawdown(performance_df['total_value']),
            'max_drawdown_pct': self._calculate_max_drawdown_pct(performance_df['total_value']),

            # Win rate
            'win_rate': (returns > 0).sum() / len(returns) * 100,

            # Best and worst days
            'best_day': returns.max(),
            'worst_day': returns.min(),

            # Calmar ratio (return / max drawdown)
            'calmar_ratio': self._calculate_calmar_ratio(returns, performance_df['total_value'], annual_factor),

            # Value at Risk (95%)
            'var_95': np.percentile(returns, 5),
            'var_99': np.percentile(returns, 1),

            # Conditional VaR (Expected Shortfall)
            'cvar_95': returns[returns <= np.percentile(returns, 5)].mean(),
            'cvar_99': returns[returns <= np.percentile(returns, 1)].mean(),
        }

        return metrics

    def _calculate_sortino_ratio(self, returns: pd.Series, annual_factor: int) -> float:
        """Calculate Sortino ratio (uses only downside volatility)"""
        downside_returns = returns[returns < 0]

        if len(downside_returns) == 0:
            return 0.0

        downside_std = downside_returns.std()

        if downside_std == 0:
            return 0.0

        return (returns.mean() * annual_factor) / (downside_std * np.sqrt(annual_factor))

    def _calculate_max_drawdown(self, values: pd.Series) -> float:
        """Calculate maximum drawdown in absolute terms"""
        rolling_max = values.expanding().max()
        drawdown = values - rolling_max
        return drawdown.min()

    def _calculate_max_drawdown_pct(self, values: pd.Series) -> float:
        """Calculate maximum drawdown in percentage"""
        rolling_max = values.expanding().max()
        drawdown_pct = ((values - rolling_max) / rolling_max) * 100
        return drawdown_pct.min()

    def _calculate_calmar_ratio(self, returns: pd.Series, values: pd.Series, annual_factor: int) -> float:
        """Calculate Calmar ratio (annualized return / max drawdown)"""
        annual_return = returns.mean() * annual_factor
        max_dd_pct = abs(self._calculate_max_drawdown_pct(values))

        if max_dd_pct == 0:
            return 0.0

        return annual_return / max_dd_pct

    def get_drawdown_series(self, values: pd.Series) -> pd.DataFrame:
        """
        Get drawdown time series

        Args:
            values: Series of portfolio values

        Returns:
            DataFrame with drawdown information
        """
        rolling_max = values.expanding().max()
        drawdown = values - rolling_max
        drawdown_pct = ((values - rolling_max) / rolling_max) * 100

        return pd.DataFrame({
            'value': values,
            'peak': rolling_max,
            'drawdown': drawdown,
            'drawdown_pct': drawdown_pct
        })

    def get_rolling_metrics(
        self,
        performance_df: pd.DataFrame,
        window_days: int = 30
    ) -> pd.DataFrame:
        """
        Calculate rolling performance metrics

        Args:
            performance_df: Performance DataFrame
            window_days: Rolling window size in days

        Returns:
            DataFrame with rolling metrics
        """
        returns = performance_df['daily_return'].fillna(0)

        rolling_metrics = pd.DataFrame({
            'date': performance_df['date'],
            'rolling_return': returns.rolling(window_days).mean() * 252,  # Annualized
            'rolling_volatility': returns.rolling(window_days).std() * np.sqrt(252),
            'rolling_sharpe': (
                returns.rolling(window_days).mean() * 252
            ) / (
                returns.rolling(window_days).std() * np.sqrt(252)
            )
        })

        return rolling_metrics

    def compare_to_benchmark(
        self,
        performance_df: pd.DataFrame,
        benchmark_symbol: str = '^GSPC'  # S&P 500
    ) -> pd.DataFrame:
        """
        Compare portfolio performance to benchmark

        Args:
            performance_df: Portfolio performance DataFrame
            benchmark_symbol: Benchmark symbol (default: S&P 500)

        Returns:
            DataFrame with portfolio and benchmark comparison
        """
        # Fetch benchmark data
        start_date = performance_df['date'].min().strftime('%Y-%m-%d')
        end_date = performance_df['date'].max().strftime('%Y-%m-%d')

        benchmark_data = self.historical_manager.get_historical_data(
            benchmark_symbol, start_date, end_date
        )

        if benchmark_data.empty:
            # Try to fetch
            benchmark_data = self.historical_manager.fetch_historical_data(
                benchmark_symbol, start_date, end_date
            )

        if benchmark_data.empty:
            return performance_df

        # Merge with performance data
        comparison = performance_df.copy()
        comparison['date'] = pd.to_datetime(comparison['date'])

        benchmark_data = benchmark_data.rename(columns={'date': 'date', 'close': 'benchmark_close'})
        benchmark_data['date'] = pd.to_datetime(benchmark_data['date'])

        comparison = comparison.merge(
            benchmark_data[['date', 'benchmark_close']],
            on='date',
            how='left'
        )

        # Calculate benchmark returns
        if 'benchmark_close' in comparison.columns:
            comparison['benchmark_return'] = comparison['benchmark_close'].pct_change() * 100
            comparison['benchmark_cumulative'] = (
                (comparison['benchmark_close'] / comparison['benchmark_close'].iloc[0]) - 1
            ) * 100

            # Calculate alpha (portfolio return - benchmark return)
            comparison['alpha'] = comparison['daily_return'] - comparison['benchmark_return']
            comparison['cumulative_alpha'] = comparison['cumulative_return'] - comparison['benchmark_cumulative']

        return comparison


def test_portfolio_performance():
    """Test portfolio performance calculator"""
    print("Testing Portfolio Performance Calculator")
    print("=" * 60)

    # This would normally use real portfolios
    print("\nNote: This test requires populated historical database")
    print("Run historical data manager test first to populate data")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_portfolio_performance()
