"""
Cryptocurrency Portfolio Calculator
Handles crypto tracking with P&L and multi-currency support
"""

import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict, List
from .market_data import MarketDataFetcher


class CryptoPortfolio:
    """
    Manages cryptocurrency portfolio calculations including:
    - Position tracking (buys and sells)
    - Average cost calculation
    - Realized and unrealized P&L
    - Multi-currency support (BRL, USD, etc.)
    """

    def __init__(self, orders_file: str, market_data: MarketDataFetcher = None):
        """
        Initialize crypto portfolio

        Args:
            orders_file: Path to CSV file with crypto orders
            market_data: MarketDataFetcher instance (optional)
        """
        self.orders = pd.read_csv(orders_file)
        self.orders['Data'] = pd.to_datetime(self.orders['Data'])
        self.orders = self.orders.sort_values('Data')

        self.market_data = market_data or MarketDataFetcher()

        # Process orders to build positions
        self.positions = {}

    def calculate_positions(self) -> Dict:
        """
        Calculate current positions from orders

        Returns:
            Dictionary with position details per symbol
        """
        positions = {}

        for _, order in self.orders.iterrows():
            symbol = order['Ativo']
            date = order['Data']
            price = float(order['Preço'])
            quantity = float(order['Quantidade'])

            if symbol not in positions:
                positions[symbol] = {
                    'symbol': symbol,
                    'quantity': 0,
                    'avg_cost': 0,
                    'total_invested': 0,
                    'realized_pnl': 0,
                    'transactions': []
                }

            pos = positions[symbol]

            # Buy transaction (positive quantity)
            if quantity > 0:
                # Update average cost
                old_value = pos['quantity'] * pos['avg_cost']
                new_value = quantity * price
                total_quantity = pos['quantity'] + quantity

                if total_quantity > 0:
                    pos['avg_cost'] = (old_value + new_value) / total_quantity

                pos['quantity'] += quantity
                pos['total_invested'] += (quantity * price)

            # Sell transaction (negative quantity)
            else:
                sell_quantity = abs(quantity)
                sell_price = price

                # Calculate realized P&L
                cost_basis = sell_quantity * pos['avg_cost']
                proceeds = sell_quantity * sell_price
                realized_pnl = proceeds - cost_basis

                pos['realized_pnl'] += realized_pnl
                pos['quantity'] += quantity  # quantity is negative
                pos['total_invested'] -= cost_basis

            # Record transaction
            pos['transactions'].append({
                'date': date,
                'price': price,
                'quantity': quantity,
                'type': 'BUY' if quantity > 0 else 'SELL'
            })

        self.positions = positions
        return positions

    def get_current_values(self, currency: str = 'BRL') -> pd.DataFrame:
        """
        Get current portfolio values with market prices

        Args:
            currency: Currency for valuation (BRL, USD, etc.)

        Returns:
            DataFrame with position details and P&L
        """
        if not self.positions:
            self.calculate_positions()

        results = []

        for symbol, pos in self.positions.items():
            if pos['quantity'] == 0:
                # Skip closed positions
                continue

            # Get current market price
            current_price = self.market_data.get_current_price(f"{symbol}-USD")

            if current_price is None:
                print(f"Warning: Could not get price for {symbol}, using last trade price")
                # Use last transaction price
                current_price = pos['transactions'][-1]['price']
            else:
                # Convert to desired currency if needed
                if currency == 'BRL':
                    usd_brl = self.market_data.get_exchange_rate('USD', 'BRL')
                    if usd_brl:
                        current_price *= usd_brl

            # Calculate unrealized P&L
            market_value = pos['quantity'] * current_price
            cost_basis = pos['quantity'] * pos['avg_cost']
            unrealized_pnl = market_value - cost_basis
            unrealized_pnl_pct = (unrealized_pnl / cost_basis * 100) if cost_basis > 0 else 0

            # Total P&L (realized + unrealized)
            total_pnl = pos['realized_pnl'] + unrealized_pnl

            results.append({
                'Symbol': symbol,
                'Quantity': pos['quantity'],
                'Avg Cost': pos['avg_cost'],
                'Current Price': current_price,
                'Market Value': market_value,
                'Cost Basis': cost_basis,
                'Unrealized P&L': unrealized_pnl,
                'Unrealized P&L %': unrealized_pnl_pct,
                'Realized P&L': pos['realized_pnl'],
                'Total P&L': total_pnl,
                'Total P&L %': (total_pnl / (cost_basis + abs(pos['realized_pnl'])) * 100) if (cost_basis + abs(pos['realized_pnl'])) > 0 else 0,
                'Currency': currency
            })

        df = pd.DataFrame(results)

        if df.empty:
            return df

        # Sort by market value descending
        df = df.sort_values('Market Value', ascending=False)

        return df

    def get_portfolio_summary(self, currency: str = 'BRL') -> Dict:
        """
        Get portfolio summary statistics

        Args:
            currency: Currency for valuation

        Returns:
            Dictionary with summary metrics
        """
        df = self.get_current_values(currency)

        if df.empty:
            return {
                'total_market_value': 0,
                'total_cost_basis': 0,
                'total_unrealized_pnl': 0,
                'total_realized_pnl': 0,
                'total_pnl': 0,
                'total_return_pct': 0,
                'num_positions': 0,
                'currency': currency
            }

        return {
            'total_market_value': df['Market Value'].sum(),
            'total_cost_basis': df['Cost Basis'].sum(),
            'total_unrealized_pnl': df['Unrealized P&L'].sum(),
            'total_realized_pnl': df['Realized P&L'].sum(),
            'total_pnl': df['Total P&L'].sum(),
            'total_return_pct': (df['Total P&L'].sum() / df['Cost Basis'].sum() * 100) if df['Cost Basis'].sum() > 0 else 0,
            'num_positions': len(df),
            'currency': currency
        }

    def get_transactions_history(self, symbol: str = None) -> pd.DataFrame:
        """
        Get transaction history for all or specific symbol

        Args:
            symbol: Crypto symbol (optional, if None returns all)

        Returns:
            DataFrame with transaction history
        """
        if not self.positions:
            self.calculate_positions()

        transactions = []

        positions_to_check = [self.positions[symbol]] if symbol else self.positions.values()

        for pos in positions_to_check:
            for txn in pos['transactions']:
                transactions.append({
                    'Date': txn['date'],
                    'Symbol': pos['symbol'],
                    'Type': txn['type'],
                    'Quantity': abs(txn['quantity']),
                    'Price': txn['price'],
                    'Value': abs(txn['quantity'] * txn['price'])
                })

        df = pd.DataFrame(transactions)

        if df.empty:
            return df

        df = df.sort_values('Date', ascending=False)

        return df

    def get_allocation(self) -> pd.DataFrame:
        """
        Get portfolio allocation by asset

        Returns:
            DataFrame with allocation percentages
        """
        df = self.get_current_values()

        if df.empty:
            return df

        total_value = df['Market Value'].sum()

        allocation = df[['Symbol', 'Market Value']].copy()
        allocation['Allocation %'] = (allocation['Market Value'] / total_value * 100)
        allocation = allocation.sort_values('Allocation %', ascending=False)

        return allocation

    def to_dict(self) -> Dict:
        """Export portfolio to dictionary format"""
        return {
            'positions': self.get_current_values().to_dict('records'),
            'summary': self.get_portfolio_summary(),
            'transactions': self.get_transactions_history().to_dict('records'),
            'allocation': self.get_allocation().to_dict('records')
        }


def test_crypto_portfolio():
    """Test crypto portfolio calculator"""
    print("Testing Crypto Portfolio Calculator")
    print("=" * 60)

    # Initialize portfolio
    portfolio = CryptoPortfolio('data/crypto/orders.csv')

    # Calculate positions
    print("\n1. Calculating positions from orders...")
    positions = portfolio.calculate_positions()
    print(f"   Found {len(positions)} unique cryptocurrencies")

    # Get current values
    print("\n2. Current Crypto Holdings (in BRL):")
    print("-" * 60)
    current = portfolio.get_current_values(currency='BRL')
    if not current.empty:
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(current.to_string())
    else:
        print("   No open positions")

    # Get summary
    print("\n3. Portfolio Summary:")
    print("-" * 60)
    summary = portfolio.get_portfolio_summary(currency='BRL')
    for key, value in summary.items():
        if 'pct' in key or 'return' in key:
            print(f"   {key}: {value:.2f}%")
        elif isinstance(value, float):
            print(f"   {key}: R$ {value:,.2f}")
        else:
            print(f"   {key}: {value}")

    # Allocation
    print("\n4. Portfolio Allocation:")
    print("-" * 60)
    allocation = portfolio.get_allocation()
    if not allocation.empty:
        print(allocation.to_string())

    # Transaction history
    print("\n5. Recent Transactions (last 10):")
    print("-" * 60)
    txns = portfolio.get_transactions_history()
    if not txns.empty:
        print(txns.head(10).to_string())

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_crypto_portfolio()
