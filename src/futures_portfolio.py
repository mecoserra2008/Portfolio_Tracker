"""
Futures Portfolio Calculator
Tracks futures positions with mark-to-market P&L
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class FuturesPortfolio:
    """
    Manages futures portfolio with mark-to-market P&L calculations
    """

    def __init__(self, orders_csv: str, data_fetcher=None):
        """
        Initialize futures portfolio

        Args:
            orders_csv: Path to futures orders CSV
            data_fetcher: IBKR data fetcher instance
        """
        self.orders_csv = orders_csv
        self.data_fetcher = data_fetcher
        self.positions = {}
        self.transactions = pd.DataFrame()

        self._ensure_csv_exists()
        self._load_transactions()

    def _ensure_csv_exists(self):
        """Create CSV file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.orders_csv), exist_ok=True)

        if not os.path.exists(self.orders_csv):
            df = pd.DataFrame(columns=[
                'date',          # Transaction date (YYYY-MM-DD)
                'symbol',        # Futures symbol (ES, NQ, CL, GC, etc.)
                'exchange',      # Exchange (CME, NYMEX, CBOT, etc.)
                'expiry',        # Contract expiry (YYYYMMDD)
                'side',          # 'long' or 'short'
                'quantity',      # Number of contracts (positive = open, negative = close)
                'price',         # Entry/exit price
                'multiplier',    # Contract multiplier
                'currency',      # Contract currency
                'commission',    # Commission paid
                'description'    # Optional description
            ])
            df.to_csv(self.orders_csv, index=False)

    def _load_transactions(self):
        """Load transactions from CSV"""
        self.transactions = pd.read_csv(self.orders_csv)

        if not self.transactions.empty:
            self.transactions['date'] = pd.to_datetime(self.transactions['date'])
            self.transactions = self.transactions.sort_values('date')

    def add_transaction(
        self,
        date: str,
        symbol: str,
        exchange: str,
        expiry: str,
        side: str,
        quantity: int,
        price: float,
        multiplier: float = 1.0,
        currency: str = 'USD',
        commission: float = 0.0,
        description: str = ''
    ):
        """
        Add a futures transaction

        Args:
            date: Transaction date (YYYY-MM-DD)
            symbol: Futures symbol
            exchange: Exchange
            expiry: Expiry date (YYYYMMDD)
            side: 'long' or 'short'
            quantity: Number of contracts (positive to open, negative to close)
            price: Transaction price
            multiplier: Contract multiplier
            currency: Currency
            commission: Commission paid
            description: Optional description
        """
        new_transaction = pd.DataFrame([{
            'date': pd.to_datetime(date),
            'symbol': symbol,
            'exchange': exchange,
            'expiry': expiry,
            'side': side.lower(),
            'quantity': quantity,
            'price': price,
            'multiplier': multiplier,
            'currency': currency,
            'commission': commission,
            'description': description
        }])

        self.transactions = pd.concat([self.transactions, new_transaction], ignore_index=True)
        self.transactions = self.transactions.sort_values('date')
        self._save_transactions()

    def _save_transactions(self):
        """Save transactions to CSV"""
        self.transactions.to_csv(self.orders_csv, index=False)

    def calculate_positions(self) -> Dict:
        """
        Calculate current futures positions

        Returns:
            Dictionary of positions by contract
        """
        if self.transactions.empty:
            return {}

        positions = {}

        for _, txn in self.transactions.iterrows():
            contract_key = f"{txn['symbol']}_{txn['expiry']}_{txn['exchange']}"

            if contract_key not in positions:
                positions[contract_key] = {
                    'symbol': txn['symbol'],
                    'exchange': txn['exchange'],
                    'expiry': txn['expiry'],
                    'multiplier': txn['multiplier'],
                    'currency': txn['currency'],
                    'long_quantity': 0,
                    'short_quantity': 0,
                    'long_avg_price': 0.0,
                    'short_avg_price': 0.0,
                    'total_commission': 0.0,
                    'realized_pnl': 0.0
                }

            pos = positions[contract_key]
            side = txn['side']
            quantity = txn['quantity']
            price = txn['price']
            commission = txn['commission']

            pos['total_commission'] += commission

            if side == 'long':
                if quantity > 0:  # Opening long
                    old_value = pos['long_quantity'] * pos['long_avg_price']
                    new_value = quantity * price
                    pos['long_quantity'] += quantity
                    if pos['long_quantity'] > 0:
                        pos['long_avg_price'] = (old_value + new_value) / pos['long_quantity']
                else:  # Closing long
                    close_qty = abs(quantity)
                    realized = (price - pos['long_avg_price']) * close_qty * pos['multiplier']
                    pos['realized_pnl'] += realized
                    pos['long_quantity'] -= close_qty

            elif side == 'short':
                if quantity > 0:  # Opening short
                    old_value = pos['short_quantity'] * pos['short_avg_price']
                    new_value = quantity * price
                    pos['short_quantity'] += quantity
                    if pos['short_quantity'] > 0:
                        pos['short_avg_price'] = (old_value + new_value) / pos['short_quantity']
                else:  # Closing short
                    close_qty = abs(quantity)
                    realized = (pos['short_avg_price'] - price) * close_qty * pos['multiplier']
                    pos['realized_pnl'] += realized
                    pos['short_quantity'] -= close_qty

        # Calculate net position
        for contract_key, pos in positions.items():
            pos['net_quantity'] = pos['long_quantity'] - pos['short_quantity']
            pos['net_side'] = 'long' if pos['net_quantity'] > 0 else 'short' if pos['net_quantity'] < 0 else 'flat'
            pos['abs_quantity'] = abs(pos['net_quantity'])

            # Average entry price for net position
            if pos['net_quantity'] > 0:
                pos['avg_entry_price'] = pos['long_avg_price']
            elif pos['net_quantity'] < 0:
                pos['avg_entry_price'] = pos['short_avg_price']
            else:
                pos['avg_entry_price'] = 0.0

        self.positions = positions
        return positions

    def get_current_values(self, as_of_date: str = None) -> pd.DataFrame:
        """
        Get current portfolio values with mark-to-market P&L

        Args:
            as_of_date: Date for valuation (default: today)

        Returns:
            DataFrame with position values
        """
        if not self.positions:
            self.calculate_positions()

        if not self.positions:
            return pd.DataFrame()

        position_list = []

        for contract_key, pos in self.positions.items():
            if pos['abs_quantity'] == 0:
                continue

            # Get current price
            current_price = self._get_current_price(
                pos['symbol'],
                pos['exchange'],
                pos['expiry'],
                as_of_date
            )

            if current_price is None:
                current_price = pos['avg_entry_price']

            # Calculate unrealized P&L
            if pos['net_side'] == 'long':
                unrealized_pnl = (current_price - pos['avg_entry_price']) * pos['abs_quantity'] * pos['multiplier']
            elif pos['net_side'] == 'short':
                unrealized_pnl = (pos['avg_entry_price'] - current_price) * pos['abs_quantity'] * pos['multiplier']
            else:
                unrealized_pnl = 0.0

            total_pnl = pos['realized_pnl'] + unrealized_pnl - pos['total_commission']

            # Notional value
            notional_value = current_price * pos['abs_quantity'] * pos['multiplier']

            # Days to expiry
            expiry_date = pd.to_datetime(pos['expiry'], format='%Y%m%d')
            today = pd.Timestamp.now() if as_of_date is None else pd.to_datetime(as_of_date)
            days_to_expiry = (expiry_date - today).days

            position_list.append({
                'Contract': contract_key,
                'Symbol': pos['symbol'],
                'Exchange': pos['exchange'],
                'Expiry': pos['expiry'],
                'Days to Expiry': days_to_expiry,
                'Side': pos['net_side'],
                'Quantity': pos['abs_quantity'],
                'Entry Price': pos['avg_entry_price'],
                'Current Price': current_price,
                'Multiplier': pos['multiplier'],
                'Notional Value': notional_value,
                'Unrealized P&L': unrealized_pnl,
                'Realized P&L': pos['realized_pnl'],
                'Commission': pos['total_commission'],
                'Total P&L': total_pnl,
                'Currency': pos['currency']
            })

        return pd.DataFrame(position_list)

    def _get_current_price(
        self,
        symbol: str,
        exchange: str,
        expiry: str,
        as_of_date: str = None
    ) -> Optional[float]:
        """
        Get current price for a futures contract

        Args:
            symbol: Futures symbol
            exchange: Exchange
            expiry: Expiry date
            as_of_date: Date for historical price (None = current)

        Returns:
            Current or historical price
        """
        if self.data_fetcher is None:
            return None

        try:
            if hasattr(self.data_fetcher, 'get_current_price') and as_of_date is None:
                return self.data_fetcher.get_current_price(f"{symbol}_{expiry}", 'future')
            elif hasattr(self.data_fetcher, 'get_historical_data'):
                end_date = as_of_date or datetime.now().strftime('%Y-%m-%d')
                start_date = (pd.to_datetime(end_date) - timedelta(days=7)).strftime('%Y-%m-%d')

                df = self.data_fetcher.get_historical_data(
                    f"{symbol}_{expiry}",
                    'future',
                    start_date,
                    end_date
                )

                if not df.empty:
                    return float(df.iloc[-1]['close'])
            return None
        except Exception as e:
            print(f"Error getting price for {symbol}: {str(e)}")
            return None

    def get_portfolio_summary(self) -> Dict:
        """
        Get futures portfolio summary

        Returns:
            Dictionary with summary statistics
        """
        values_df = self.get_current_values()

        if values_df.empty:
            return {
                'num_contracts': 0,
                'total_notional': 0.0,
                'total_unrealized_pnl': 0.0,
                'total_realized_pnl': 0.0,
                'total_commission': 0.0,
                'total_pnl': 0.0,
                'long_contracts': 0,
                'short_contracts': 0
            }

        return {
            'num_contracts': len(values_df),
            'total_notional': values_df['Notional Value'].sum(),
            'total_unrealized_pnl': values_df['Unrealized P&L'].sum(),
            'total_realized_pnl': values_df['Realized P&L'].sum(),
            'total_commission': values_df['Commission'].sum(),
            'total_pnl': values_df['Total P&L'].sum(),
            'long_contracts': len(values_df[values_df['Side'] == 'long']),
            'short_contracts': len(values_df[values_df['Side'] == 'short'])
        }

    def get_expiring_contracts(self, days_ahead: int = 30) -> pd.DataFrame:
        """
        Get contracts expiring within specified days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            DataFrame with expiring contracts
        """
        values_df = self.get_current_values()

        if values_df.empty:
            return pd.DataFrame()

        expiring = values_df[values_df['Days to Expiry'] <= days_ahead].copy()
        expiring = expiring.sort_values('Days to Expiry')

        return expiring

    def get_transactions_history(self) -> pd.DataFrame:
        """Get complete transaction history"""
        return self.transactions.copy()


def test_futures_portfolio():
    """Test futures portfolio"""
    print("Testing Futures Portfolio")
    print("=" * 60)

    # Import mock data fetcher
    from .ibkr_data import IBKRDataFetcherMock
    fetcher = IBKRDataFetcherMock()
    fetcher.connect()

    # Initialize portfolio
    portfolio = FuturesPortfolio('data/futures/orders.csv', fetcher)

    # Add test transactions
    print("\n1. Adding test futures transactions...")
    print("-" * 60)

    # Open long position in ES (E-mini S&P 500)
    portfolio.add_transaction(
        date='2024-01-15',
        symbol='ES',
        exchange='CME',
        expiry='20240315',
        side='long',
        quantity=2,
        price=4750.00,
        multiplier=50,
        currency='USD',
        commission=5.00,
        description='Long 2 ES March 2024'
    )

    # Close partial position
    portfolio.add_transaction(
        date='2024-02-01',
        symbol='ES',
        exchange='CME',
        expiry='20240315',
        side='long',
        quantity=-1,
        price=4850.00,
        multiplier=50,
        currency='USD',
        commission=2.50,
        description='Close 1 ES contract'
    )

    # Open short position in NQ (E-mini Nasdaq)
    portfolio.add_transaction(
        date='2024-01-20',
        symbol='NQ',
        exchange='CME',
        expiry='20240315',
        side='short',
        quantity=1,
        price=17500.00,
        multiplier=20,
        currency='USD',
        commission=3.00,
        description='Short 1 NQ March 2024'
    )

    print("✓ Added 3 futures transactions")

    # Calculate positions
    print("\n2. Current Positions:")
    print("-" * 60)
    positions_df = portfolio.get_current_values()
    if not positions_df.empty:
        print(positions_df.to_string(index=False))
    else:
        print("No open positions")

    # Get summary
    print("\n3. Portfolio Summary:")
    print("-" * 60)
    summary = portfolio.get_portfolio_summary()
    print(f"Total Contracts: {summary['num_contracts']}")
    print(f"Long Contracts: {summary['long_contracts']}")
    print(f"Short Contracts: {summary['short_contracts']}")
    print(f"Total Notional: ${summary['total_notional']:,.2f}")
    print(f"Unrealized P&L: ${summary['total_unrealized_pnl']:,.2f}")
    print(f"Realized P&L: ${summary['total_realized_pnl']:,.2f}")
    print(f"Total Commission: ${summary['total_commission']:,.2f}")
    print(f"Total P&L: ${summary['total_pnl']:,.2f}")

    # Check expiring contracts
    print("\n4. Contracts Expiring in Next 90 Days:")
    print("-" * 60)
    expiring = portfolio.get_expiring_contracts(90)
    if not expiring.empty:
        print(expiring[['Symbol', 'Expiry', 'Days to Expiry', 'Side', 'Quantity']].to_string(index=False))

    fetcher.disconnect()
    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_futures_portfolio()
