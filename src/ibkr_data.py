"""
IBKR Data Fetcher
Fetches futures and options data from Interactive Brokers API
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time

# IBKR API integration
try:
    from ib_insync import IB, Future, Option, Stock, util
    IBKR_AVAILABLE = True
except ImportError:
    IBKR_AVAILABLE = False
    IB = None
    Future = None
    Option = None
    Stock = None
    util = None
    print("Warning: ib_insync not installed. Install with: pip install ib_insync")


class IBKRDataFetcher:
    """
    Fetches futures and options data from Interactive Brokers

    Note: Requires IB Gateway or TWS to be running
    """

    def __init__(self, host: str = '127.0.0.1', port: int = 7497, client_id: int = 1):
        """
        Initialize IBKR connection

        Args:
            host: IB Gateway host (default: localhost)
            port: IB Gateway port (7497 for live, 7496 for paper trading)
            client_id: Unique client ID
        """
        self.host = host
        self.port = port
        self.client_id = client_id
        self.ib = None
        self.connected = False

        if not IBKR_AVAILABLE:
            print("Warning: IBKR API not available. Install ib_insync to use this feature.")

    def connect(self) -> bool:
        """
        Connect to IB Gateway or TWS

        Returns:
            True if connected successfully
        """
        if not IBKR_AVAILABLE:
            return False

        try:
            self.ib = IB()
            self.ib.connect(self.host, self.port, clientId=self.client_id)
            self.connected = True
            print(f"✓ Connected to IBKR at {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"✗ Failed to connect to IBKR: {str(e)}")
            print("  Make sure IB Gateway or TWS is running")
            self.connected = False
            return False

    def disconnect(self):
        """Disconnect from IBKR"""
        if self.ib and self.connected:
            self.ib.disconnect()
            self.connected = False
            print("✓ Disconnected from IBKR")

    def get_futures_contract(
        self,
        symbol: str,
        exchange: str,
        expiry: str,
        currency: str = 'USD',
        multiplier: float = None
    ):
        """
        Get futures contract details

        Args:
            symbol: Futures symbol (e.g., 'ES', 'NQ', 'CL')
            exchange: Exchange (e.g., 'CME', 'NYMEX', 'CBOT')
            expiry: Expiry date (YYYYMMDD format)
            currency: Contract currency
            multiplier: Contract multiplier

        Returns:
            Future contract object or None
        """
        if not self.connected:
            print("Not connected to IBKR")
            return None

        try:
            contract = Future(
                symbol=symbol,
                lastTradeDateOrContractMonth=expiry,
                exchange=exchange,
                currency=currency,
                multiplier=str(multiplier) if multiplier else ''
            )

            qualified = self.ib.qualifyContracts(contract)
            if qualified:
                return qualified[0]
            return None
        except Exception as e:
            print(f"Error getting futures contract: {str(e)}")
            return None

    def get_options_contract(
        self,
        underlying: str,
        expiry: str,
        strike: float,
        right: str,  # 'C' for call, 'P' for put
        exchange: str = 'SMART',
        currency: str = 'USD',
        multiplier: float = 100
    ):
        """
        Get options contract details

        Args:
            underlying: Underlying symbol
            expiry: Expiry date (YYYYMMDD format)
            strike: Strike price
            right: 'C' for call, 'P' for put
            exchange: Exchange
            currency: Contract currency
            multiplier: Contract multiplier (usually 100)

        Returns:
            Option contract object or None
        """
        if not self.connected:
            print("Not connected to IBKR")
            return None

        try:
            contract = Option(
                symbol=underlying,
                lastTradeDateOrContractMonth=expiry,
                strike=strike,
                right=right.upper(),
                exchange=exchange,
                currency=currency,
                multiplier=str(multiplier)
            )

            qualified = self.ib.qualifyContracts(contract)
            if qualified:
                return qualified[0]
            return None
        except Exception as e:
            print(f"Error getting options contract: {str(e)}")
            return None

    def get_historical_data(
        self,
        contract,
        end_date: str = '',
        duration: str = '1 M',
        bar_size: str = '1 day',
        what_to_show: str = 'TRADES'
    ) -> pd.DataFrame:
        """
        Get historical data for a contract

        Args:
            contract: IBKR contract object
            end_date: End date (empty string = now)
            duration: Data duration ('1 D', '1 W', '1 M', '1 Y', etc.)
            bar_size: Bar size ('1 day', '1 hour', '15 mins', etc.)
            what_to_show: Data type ('TRADES', 'MIDPOINT', 'BID', 'ASK')

        Returns:
            DataFrame with historical data
        """
        if not self.connected:
            print("Not connected to IBKR")
            return pd.DataFrame()

        try:
            bars = self.ib.reqHistoricalData(
                contract,
                endDateTime=end_date,
                durationStr=duration,
                barSizeSetting=bar_size,
                whatToShow=what_to_show,
                useRTH=True,  # Regular trading hours only
                formatDate=1
            )

            if bars:
                df = util.df(bars)
                df['date'] = pd.to_datetime(df['date'])
                return df
            return pd.DataFrame()
        except Exception as e:
            print(f"Error getting historical data: {str(e)}")
            return pd.DataFrame()

    def get_option_greeks(self, contract) -> Dict:
        """
        Get option Greeks (delta, gamma, theta, vega)

        Args:
            contract: Option contract

        Returns:
            Dictionary with Greeks
        """
        if not self.connected:
            return {}

        try:
            self.ib.reqMarketDataType(4)  # Delayed data if no subscription
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)  # Wait for data

            greeks = {
                'delta': ticker.modelGreeks.delta if ticker.modelGreeks else None,
                'gamma': ticker.modelGreeks.gamma if ticker.modelGreeks else None,
                'theta': ticker.modelGreeks.theta if ticker.modelGreeks else None,
                'vega': ticker.modelGreeks.vega if ticker.modelGreeks else None,
                'implied_vol': ticker.modelGreeks.impliedVol if ticker.modelGreeks else None
            }

            self.ib.cancelMktData(contract)
            return greeks
        except Exception as e:
            print(f"Error getting Greeks: {str(e)}")
            return {}

    def get_current_price(self, contract) -> Optional[float]:
        """
        Get current price for a contract

        Args:
            contract: IBKR contract

        Returns:
            Current price or None
        """
        if not self.connected:
            return None

        try:
            self.ib.reqMarketDataType(4)  # Delayed data if no subscription
            ticker = self.ib.reqMktData(contract, '', False, False)
            self.ib.sleep(2)

            # Try to get last price, fall back to close
            price = ticker.last
            if not price or price <= 0:
                price = ticker.close
            if not price or price <= 0:
                price = (ticker.bid + ticker.ask) / 2 if ticker.bid and ticker.ask else None

            self.ib.cancelMktData(contract)
            return float(price) if price else None
        except Exception as e:
            print(f"Error getting current price: {str(e)}")
            return None

    def get_futures_chain(
        self,
        symbol: str,
        exchange: str,
        currency: str = 'USD'
    ) -> List[str]:
        """
        Get available futures expiry dates for a symbol

        Args:
            symbol: Futures symbol
            exchange: Exchange
            currency: Currency

        Returns:
            List of expiry dates (YYYYMMDD)
        """
        if not self.connected:
            return []

        try:
            contract = Future(symbol=symbol, exchange=exchange, currency=currency)
            details = self.ib.reqContractDetails(contract)

            expiries = [d.contract.lastTradeDateOrContractMonth for d in details]
            return sorted(expiries)
        except Exception as e:
            print(f"Error getting futures chain: {str(e)}")
            return []

    def get_options_chain(
        self,
        underlying: str,
        exchange: str = 'SMART',
        currency: str = 'USD'
    ) -> pd.DataFrame:
        """
        Get options chain for an underlying

        Args:
            underlying: Underlying symbol
            exchange: Exchange
            currency: Currency

        Returns:
            DataFrame with available strikes and expiries
        """
        if not self.connected:
            return pd.DataFrame()

        try:
            stock = Stock(underlying, exchange, currency)
            chains = self.ib.reqSecDefOptParams(stock.symbol, '', stock.secType, stock.conId)

            if not chains:
                return pd.DataFrame()

            chain_data = []
            for chain in chains:
                for expiry in chain.expirations:
                    for strike in chain.strikes:
                        chain_data.append({
                            'underlying': underlying,
                            'expiry': expiry,
                            'strike': strike,
                            'exchange': chain.exchange
                        })

            return pd.DataFrame(chain_data)
        except Exception as e:
            print(f"Error getting options chain: {str(e)}")
            return pd.DataFrame()


class IBKRDataFetcherMock:
    """
    Mock IBKR data fetcher for testing without IBKR connection
    Uses approximations and simulated data
    """

    def __init__(self):
        self.connected = False
        print("Using Mock IBKR Data Fetcher (no real connection)")

    def connect(self) -> bool:
        """Simulated connection"""
        self.connected = True
        print("✓ Mock connection established")
        return True

    def disconnect(self):
        """Simulated disconnection"""
        self.connected = False

    def get_historical_data(
        self,
        symbol: str,
        contract_type: str,  # 'future' or 'option'
        start_date: str,
        end_date: str
    ) -> pd.DataFrame:
        """
        Generate simulated historical data

        Args:
            symbol: Contract symbol
            contract_type: 'future' or 'option'
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD)

        Returns:
            DataFrame with simulated data
        """
        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        # Generate random walk prices
        np.random.seed(hash(symbol) % 2**32)
        base_price = 100.0 if contract_type == 'future' else 5.0
        returns = np.random.normal(0.0001, 0.02, len(dates))
        prices = base_price * np.exp(np.cumsum(returns))

        df = pd.DataFrame({
            'date': dates,
            'open': prices * (1 + np.random.uniform(-0.01, 0.01, len(dates))),
            'high': prices * (1 + np.random.uniform(0, 0.02, len(dates))),
            'low': prices * (1 + np.random.uniform(-0.02, 0, len(dates))),
            'close': prices,
            'volume': np.random.randint(1000, 10000, len(dates))
        })

        return df

    def get_option_greeks(self, symbol: str, strike: float, days_to_expiry: int) -> Dict:
        """
        Approximate option Greeks using Black-Scholes approximations

        Args:
            symbol: Option symbol
            strike: Strike price
            days_to_expiry: Days until expiration

        Returns:
            Dictionary with approximate Greeks
        """
        # Simplified approximations
        time_to_expiry = days_to_expiry / 365.0

        return {
            'delta': 0.5 + np.random.uniform(-0.3, 0.3),
            'gamma': 0.05 * np.exp(-time_to_expiry),
            'theta': -0.01 * strike / time_to_expiry if time_to_expiry > 0 else 0,
            'vega': 0.1 * strike * np.sqrt(time_to_expiry),
            'implied_vol': 0.20 + np.random.uniform(-0.05, 0.05)
        }

    def get_current_price(self, symbol: str, contract_type: str) -> float:
        """
        Get simulated current price

        Args:
            symbol: Contract symbol
            contract_type: 'future' or 'option'

        Returns:
            Simulated price
        """
        np.random.seed(hash(symbol) % 2**32)
        base = 100.0 if contract_type == 'future' else 5.0
        return base * (1 + np.random.uniform(-0.1, 0.1))


def test_ibkr_connection():
    """Test IBKR connection"""
    print("Testing IBKR Data Fetcher")
    print("=" * 60)

    if not IBKR_AVAILABLE:
        print("\nUsing Mock Data Fetcher (ib_insync not installed)")
        fetcher = IBKRDataFetcherMock()
        fetcher.connect()

        # Test mock data
        print("\n1. Testing mock historical data:")
        df = fetcher.get_historical_data('ES', 'future', '2024-01-01', '2024-01-31')
        print(f"   Retrieved {len(df)} days of data")
        print(f"   Price range: ${df['close'].min():.2f} - ${df['close'].max():.2f}")

        print("\n2. Testing mock Greeks:")
        greeks = fetcher.get_option_greeks('SPY', 450, 30)
        print(f"   Delta: {greeks['delta']:.3f}")
        print(f"   Gamma: {greeks['gamma']:.3f}")
        print(f"   Theta: {greeks['theta']:.3f}")

        fetcher.disconnect()
    else:
        print("\nAttempting to connect to IBKR...")
        print("Note: This requires IB Gateway or TWS to be running")

        fetcher = IBKRDataFetcher()
        if fetcher.connect():
            print("\n✓ Successfully connected to IBKR")
            print("  You can now fetch real futures and options data")
            fetcher.disconnect()
        else:
            print("\n✗ Could not connect to IBKR")
            print("  Using Mock Data Fetcher instead")
            fetcher = IBKRDataFetcherMock()
            fetcher.connect()
            fetcher.disconnect()

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_ibkr_connection()
