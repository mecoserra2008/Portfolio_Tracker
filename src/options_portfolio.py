"""
Options Portfolio Calculator
Tracks options positions with Greeks and premium P&L
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import os


class OptionsPortfolio:
    """
    Manages options portfolio with Greeks tracking and P&L calculations
    """

    def __init__(self, orders_csv: str, data_fetcher=None):
        """
        Initialize options portfolio

        Args:
            orders_csv: Path to options orders CSV
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
                'underlying',    # Underlying symbol (SPY, QQQ, AAPL, etc.)
                'expiry',        # Expiry date (YYYYMMDD)
                'strike',        # Strike price
                'type',          # 'call' or 'put'
                'side',          # 'long' (buy) or 'short' (sell)
                'quantity',      # Number of contracts (positive = open, negative = close)
                'premium',       # Premium per share
                'multiplier',    # Contract multiplier (usually 100)
                'currency',      # Currency
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
        underlying: str,
        expiry: str,
        strike: float,
        option_type: str,
        side: str,
        quantity: int,
        premium: float,
        multiplier: int = 100,
        currency: str = 'USD',
        commission: float = 0.0,
        description: str = ''
    ):
        """
        Add an options transaction

        Args:
            date: Transaction date (YYYY-MM-DD)
            underlying: Underlying symbol
            expiry: Expiry date (YYYYMMDD)
            strike: Strike price
            option_type: 'call' or 'put'
            side: 'long' (buy) or 'short' (sell)
            quantity: Number of contracts (positive to open, negative to close)
            premium: Premium per share
            multiplier: Contract multiplier (usually 100)
            currency: Currency
            commission: Commission paid
            description: Optional description
        """
        new_transaction = pd.DataFrame([{
            'date': pd.to_datetime(date),
            'underlying': underlying,
            'expiry': expiry,
            'strike': strike,
            'type': option_type.lower(),
            'side': side.lower(),
            'quantity': quantity,
            'premium': premium,
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
        Calculate current options positions

        Returns:
            Dictionary of positions by contract
        """
        if self.transactions.empty:
            return {}

        positions = {}

        for _, txn in self.transactions.iterrows():
            contract_key = f"{txn['underlying']}_{txn['expiry']}_{txn['strike']}_{txn['type']}"

            if contract_key not in positions:
                positions[contract_key] = {
                    'underlying': txn['underlying'],
                    'expiry': txn['expiry'],
                    'strike': txn['strike'],
                    'type': txn['type'],
                    'multiplier': txn['multiplier'],
                    'currency': txn['currency'],
                    'long_quantity': 0,
                    'short_quantity': 0,
                    'long_avg_premium': 0.0,
                    'short_avg_premium': 0.0,
                    'total_commission': 0.0,
                    'realized_pnl': 0.0
                }

            pos = positions[contract_key]
            side = txn['side']
            quantity = txn['quantity']
            premium = txn['premium']
            commission = txn['commission']

            pos['total_commission'] += commission

            if side == 'long':  # Buying options
                if quantity > 0:  # Opening long
                    old_value = pos['long_quantity'] * pos['long_avg_premium']
                    new_value = quantity * premium
                    pos['long_quantity'] += quantity
                    if pos['long_quantity'] > 0:
                        pos['long_avg_premium'] = (old_value + new_value) / pos['long_quantity']
                else:  # Closing long (selling to close)
                    close_qty = abs(quantity)
                    realized = (premium - pos['long_avg_premium']) * close_qty * pos['multiplier']
                    pos['realized_pnl'] += realized
                    pos['long_quantity'] -= close_qty

            elif side == 'short':  # Selling options
                if quantity > 0:  # Opening short (selling to open)
                    old_value = pos['short_quantity'] * pos['short_avg_premium']
                    new_value = quantity * premium
                    pos['short_quantity'] += quantity
                    if pos['short_quantity'] > 0:
                        pos['short_avg_premium'] = (old_value + new_value) / pos['short_quantity']
                else:  # Closing short (buying to close)
                    close_qty = abs(quantity)
                    realized = (pos['short_avg_premium'] - premium) * close_qty * pos['multiplier']
                    pos['realized_pnl'] += realized
                    pos['short_quantity'] -= close_qty

        # Calculate net position
        for contract_key, pos in positions.items():
            pos['net_quantity'] = pos['long_quantity'] - pos['short_quantity']
            pos['net_side'] = 'long' if pos['net_quantity'] > 0 else 'short' if pos['net_quantity'] < 0 else 'flat'
            pos['abs_quantity'] = abs(pos['net_quantity'])

            # Average premium for net position
            if pos['net_quantity'] > 0:
                pos['avg_premium'] = pos['long_avg_premium']
            elif pos['net_quantity'] < 0:
                pos['avg_premium'] = pos['short_avg_premium']
            else:
                pos['avg_premium'] = 0.0

        self.positions = positions
        return positions

    def get_current_values(self, as_of_date: str = None) -> pd.DataFrame:
        """
        Get current portfolio values with mark-to-market P&L and Greeks

        Args:
            as_of_date: Date for valuation (default: today)

        Returns:
            DataFrame with position values and Greeks
        """
        if not self.positions:
            self.calculate_positions()

        if not self.positions:
            return pd.DataFrame()

        position_list = []

        for contract_key, pos in self.positions.items():
            if pos['abs_quantity'] == 0:
                continue

            # Get current premium
            current_premium = self._get_current_premium(
                pos['underlying'],
                pos['expiry'],
                pos['strike'],
                pos['type'],
                as_of_date
            )

            if current_premium is None:
                current_premium = pos['avg_premium']

            # Calculate unrealized P&L
            if pos['net_side'] == 'long':
                # Long options: profit when value increases
                unrealized_pnl = (current_premium - pos['avg_premium']) * pos['abs_quantity'] * pos['multiplier']
            elif pos['net_side'] == 'short':
                # Short options: profit when value decreases
                unrealized_pnl = (pos['avg_premium'] - current_premium) * pos['abs_quantity'] * pos['multiplier']
            else:
                unrealized_pnl = 0.0

            total_pnl = pos['realized_pnl'] + unrealized_pnl - pos['total_commission']

            # Market value
            market_value = current_premium * pos['abs_quantity'] * pos['multiplier']

            # Days to expiry
            expiry_date = pd.to_datetime(pos['expiry'], format='%Y%m%d')
            today = pd.Timestamp.now() if as_of_date is None else pd.to_datetime(as_of_date)
            days_to_expiry = max(0, (expiry_date - today).days)

            # Get Greeks
            greeks = self._get_greeks(
                pos['underlying'],
                pos['strike'],
                pos['type'],
                days_to_expiry
            )

            # Adjust Greeks for position size and side
            position_delta = greeks.get('delta', 0) * pos['net_quantity'] * pos['multiplier']
            if pos['net_side'] == 'short':
                position_delta = -position_delta

            position_list.append({
                'Contract': contract_key,
                'Underlying': pos['underlying'],
                'Expiry': pos['expiry'],
                'Strike': pos['strike'],
                'Type': pos['type'].upper(),
                'Days to Expiry': days_to_expiry,
                'Side': pos['net_side'],
                'Quantity': pos['abs_quantity'],
                'Avg Premium': pos['avg_premium'],
                'Current Premium': current_premium,
                'Market Value': market_value,
                'Unrealized P&L': unrealized_pnl,
                'Realized P&L': pos['realized_pnl'],
                'Commission': pos['total_commission'],
                'Total P&L': total_pnl,
                'Delta': greeks.get('delta', 0),
                'Gamma': greeks.get('gamma', 0),
                'Theta': greeks.get('theta', 0),
                'Vega': greeks.get('vega', 0),
                'Implied Vol': greeks.get('implied_vol', 0),
                'Position Delta': position_delta,
                'Currency': pos['currency']
            })

        return pd.DataFrame(position_list)

    def _get_current_premium(
        self,
        underlying: str,
        expiry: str,
        strike: float,
        option_type: str,
        as_of_date: str = None
    ) -> Optional[float]:
        """
        Get current premium for an options contract

        Args:
            underlying: Underlying symbol
            expiry: Expiry date
            strike: Strike price
            option_type: 'call' or 'put'
            as_of_date: Date for historical premium (None = current)

        Returns:
            Current or historical premium
        """
        if self.data_fetcher is None:
            return None

        try:
            contract_id = f"{underlying}_{expiry}_{strike}_{option_type}"

            if hasattr(self.data_fetcher, 'get_current_price') and as_of_date is None:
                return self.data_fetcher.get_current_price(contract_id, 'option')
            elif hasattr(self.data_fetcher, 'get_historical_data'):
                end_date = as_of_date or datetime.now().strftime('%Y-%m-%d')
                start_date = (pd.to_datetime(end_date) - timedelta(days=7)).strftime('%Y-%m-%d')

                df = self.data_fetcher.get_historical_data(
                    contract_id,
                    'option',
                    start_date,
                    end_date
                )

                if not df.empty:
                    return float(df.iloc[-1]['close'])
            return None
        except Exception as e:
            print(f"Error getting premium for {underlying}: {str(e)}")
            return None

    def _get_greeks(
        self,
        underlying: str,
        strike: float,
        option_type: str,
        days_to_expiry: int
    ) -> Dict:
        """
        Get option Greeks

        Args:
            underlying: Underlying symbol
            strike: Strike price
            option_type: 'call' or 'put'
            days_to_expiry: Days until expiration

        Returns:
            Dictionary with Greeks
        """
        if self.data_fetcher is None:
            return {}

        try:
            if hasattr(self.data_fetcher, 'get_option_greeks'):
                return self.data_fetcher.get_option_greeks(underlying, strike, days_to_expiry)
            return {}
        except Exception as e:
            print(f"Error getting Greeks: {str(e)}")
            return {}

    def get_portfolio_summary(self) -> Dict:
        """
        Get options portfolio summary

        Returns:
            Dictionary with summary statistics
        """
        values_df = self.get_current_values()

        if values_df.empty:
            return {
                'num_contracts': 0,
                'total_market_value': 0.0,
                'total_unrealized_pnl': 0.0,
                'total_realized_pnl': 0.0,
                'total_commission': 0.0,
                'total_pnl': 0.0,
                'long_contracts': 0,
                'short_contracts': 0,
                'portfolio_delta': 0.0,
                'portfolio_gamma': 0.0,
                'portfolio_theta': 0.0,
                'portfolio_vega': 0.0
            }

        return {
            'num_contracts': len(values_df),
            'total_market_value': values_df['Market Value'].sum(),
            'total_unrealized_pnl': values_df['Unrealized P&L'].sum(),
            'total_realized_pnl': values_df['Realized P&L'].sum(),
            'total_commission': values_df['Commission'].sum(),
            'total_pnl': values_df['Total P&L'].sum(),
            'long_contracts': len(values_df[values_df['Side'] == 'long']),
            'short_contracts': len(values_df[values_df['Side'] == 'short']),
            'portfolio_delta': values_df['Position Delta'].sum(),
            'portfolio_gamma': (values_df['Gamma'] * values_df['Quantity'] * values_df['Quantity'].apply(lambda x: 1 if x > 0 else -1)).sum() if 'Gamma' in values_df.columns else 0.0,
            'portfolio_theta': (values_df['Theta'] * values_df['Quantity']).sum() if 'Theta' in values_df.columns else 0.0,
            'portfolio_vega': (values_df['Vega'] * values_df['Quantity']).sum() if 'Vega' in values_df.columns else 0.0
        }

    def get_expiring_contracts(self, days_ahead: int = 30) -> pd.DataFrame:
        """
        Get options expiring within specified days

        Args:
            days_ahead: Number of days to look ahead

        Returns:
            DataFrame with expiring options
        """
        values_df = self.get_current_values()

        if values_df.empty:
            return pd.DataFrame()

        expiring = values_df[values_df['Days to Expiry'] <= days_ahead].copy()
        expiring = expiring.sort_values('Days to Expiry')

        return expiring

    def get_by_underlying(self, underlying: str) -> pd.DataFrame:
        """
        Get all options for a specific underlying

        Args:
            underlying: Underlying symbol

        Returns:
            DataFrame with options for that underlying
        """
        values_df = self.get_current_values()

        if values_df.empty:
            return pd.DataFrame()

        return values_df[values_df['Underlying'] == underlying].copy()

    def get_risk_profile(self) -> Dict:
        """
        Get portfolio risk profile based on Greeks

        Returns:
            Dictionary with risk assessment
        """
        summary = self.get_portfolio_summary()

        delta = summary['portfolio_delta']
        theta = summary['portfolio_theta']
        vega = summary['portfolio_vega']

        # Directional risk
        if abs(delta) < 10:
            directional_risk = 'Low (Delta Neutral)'
        elif abs(delta) < 50:
            directional_risk = 'Medium'
        else:
            directional_risk = 'High'

        directional_bias = 'Bullish' if delta > 0 else 'Bearish' if delta < 0 else 'Neutral'

        # Time decay risk
        if abs(theta) < 10:
            time_decay_risk = 'Low'
        elif abs(theta) < 50:
            time_decay_risk = 'Medium'
        else:
            time_decay_risk = 'High'

        # Volatility risk
        if abs(vega) < 100:
            volatility_risk = 'Low'
        elif abs(vega) < 500:
            volatility_risk = 'Medium'
        else:
            volatility_risk = 'High'

        return {
            'portfolio_delta': delta,
            'portfolio_theta': theta,
            'portfolio_vega': vega,
            'directional_risk': directional_risk,
            'directional_bias': directional_bias,
            'time_decay_risk': time_decay_risk,
            'time_decay_impact': 'Positive' if theta > 0 else 'Negative',
            'volatility_risk': volatility_risk,
            'volatility_exposure': 'Long Vol' if vega > 0 else 'Short Vol' if vega < 0 else 'Neutral'
        }

    def get_transactions_history(self) -> pd.DataFrame:
        """Get complete transaction history"""
        return self.transactions.copy()


def test_options_portfolio():
    """Test options portfolio"""
    print("Testing Options Portfolio")
    print("=" * 60)

    # Import mock data fetcher
    from .ibkr_data import IBKRDataFetcherMock
    fetcher = IBKRDataFetcherMock()
    fetcher.connect()

    # Initialize portfolio
    portfolio = OptionsPortfolio('data/options/orders.csv', fetcher)

    # Add test transactions
    print("\n1. Adding test options transactions...")
    print("-" * 60)

    # Buy call
    portfolio.add_transaction(
        date='2024-01-15',
        underlying='SPY',
        expiry='20240315',
        strike=450,
        option_type='call',
        side='long',
        quantity=5,
        premium=12.50,
        multiplier=100,
        currency='USD',
        commission=6.50,
        description='Long 5 SPY Mar 450 Calls'
    )

    # Sell put (short)
    portfolio.add_transaction(
        date='2024-01-20',
        underlying='SPY',
        expiry='20240315',
        strike=440,
        option_type='put',
        side='short',
        quantity=3,
        premium=8.00,
        multiplier=100,
        currency='USD',
        commission=4.50,
        description='Short 3 SPY Mar 440 Puts'
    )

    # Buy put (protective)
    portfolio.add_transaction(
        date='2024-02-01',
        underlying='QQQ',
        expiry='20240315',
        strike=380,
        option_type='put',
        side='long',
        quantity=2,
        premium=6.25,
        multiplier=100,
        currency='USD',
        commission=3.00,
        description='Long 2 QQQ Mar 380 Puts'
    )

    print("✓ Added 3 options transactions")

    # Calculate positions
    print("\n2. Current Positions:")
    print("-" * 60)
    positions_df = portfolio.get_current_values()
    if not positions_df.empty:
        cols = ['Underlying', 'Type', 'Strike', 'Days to Expiry', 'Side', 'Quantity',
                'Avg Premium', 'Current Premium', 'Total P&L', 'Delta']
        print(positions_df[cols].to_string(index=False))
    else:
        print("No open positions")

    # Get summary
    print("\n3. Portfolio Summary:")
    print("-" * 60)
    summary = portfolio.get_portfolio_summary()
    print(f"Total Contracts: {summary['num_contracts']}")
    print(f"Long Contracts: {summary['long_contracts']}")
    print(f"Short Contracts: {summary['short_contracts']}")
    print(f"Total Market Value: ${summary['total_market_value']:,.2f}")
    print(f"Unrealized P&L: ${summary['total_unrealized_pnl']:,.2f}")
    print(f"Realized P&L: ${summary['total_realized_pnl']:,.2f}")
    print(f"Total P&L: ${summary['total_pnl']:,.2f}")
    print(f"\nPortfolio Greeks:")
    print(f"  Delta: {summary['portfolio_delta']:.2f}")
    print(f"  Gamma: {summary['portfolio_gamma']:.4f}")
    print(f"  Theta: ${summary['portfolio_theta']:.2f}/day")
    print(f"  Vega: ${summary['portfolio_vega']:.2f}")

    # Get risk profile
    print("\n4. Risk Profile:")
    print("-" * 60)
    risk = portfolio.get_risk_profile()
    print(f"Directional Risk: {risk['directional_risk']} ({risk['directional_bias']})")
    print(f"Time Decay Risk: {risk['time_decay_risk']} ({risk['time_decay_impact']})")
    print(f"Volatility Risk: {risk['volatility_risk']} ({risk['volatility_exposure']})")

    # Check expiring contracts
    print("\n5. Contracts Expiring in Next 60 Days:")
    print("-" * 60)
    expiring = portfolio.get_expiring_contracts(60)
    if not expiring.empty:
        print(expiring[['Underlying', 'Type', 'Strike', 'Days to Expiry', 'Side', 'Quantity']].to_string(index=False))

    fetcher.disconnect()
    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_options_portfolio()
