"""
Market Data Module - Fetches stock, crypto, and economic data
"""

import requests
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import json


class MarketDataFetcher:
    """Fetches market data from various sources"""

    def __init__(self):
        self.yahoo_base_url = "https://query1.finance.yahoo.com/v8/finance/chart/"
        self.bacen_base_url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs"

    def get_stock_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Fetch stock data from Yahoo Finance

        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL', 'PETR4.SA')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format

        Returns:
            DataFrame with columns: Date, Open, High, Low, Close, Volume, Adj Close
        """
        try:
            # Convert dates to timestamps
            if start_date:
                start_ts = int(pd.Timestamp(start_date).timestamp())
            else:
                start_ts = int((datetime.now() - timedelta(days=365)).timestamp())

            if end_date:
                end_ts = int(pd.Timestamp(end_date).timestamp())
            else:
                end_ts = int(datetime.now().timestamp())

            # Build Yahoo Finance API URL
            url = f"{self.yahoo_base_url}{symbol}"
            params = {
                'period1': start_ts,
                'period2': end_ts,
                'interval': '1d',
                'events': 'div,split'
            }

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"Warning: Could not fetch data for {symbol}. Status: {response.status_code}")
                return pd.DataFrame()

            data = response.json()

            if 'chart' not in data or 'result' not in data['chart'] or not data['chart']['result']:
                print(f"Warning: No data available for {symbol}")
                return pd.DataFrame()

            result = data['chart']['result'][0]

            # Extract price data
            timestamps = result['timestamp']
            quote = result['indicators']['quote'][0]

            df = pd.DataFrame({
                'Date': pd.to_datetime(timestamps, unit='s'),
                'Open': quote['open'],
                'High': quote['high'],
                'Low': quote['low'],
                'Close': quote['close'],
                'Volume': quote['volume']
            })

            # Add adjusted close if available
            if 'adjclose' in result['indicators']:
                df['Adj Close'] = result['indicators']['adjclose'][0]['adjclose']
            else:
                df['Adj Close'] = df['Close']

            # Extract dividends and splits
            events = result.get('events', {})
            dividends = events.get('dividends', {})
            splits = events.get('splits', {})

            # Add dividend and split columns
            df['Dividend'] = 0.0
            df['Split'] = 1.0

            for ts, div_data in dividends.items():
                date = pd.to_datetime(int(ts), unit='s')
                df.loc[df['Date'] == date, 'Dividend'] = div_data['amount']

            for ts, split_data in splits.items():
                date = pd.to_datetime(int(ts), unit='s')
                df.loc[df['Date'] == date, 'Split'] = split_data['numerator'] / split_data['denominator']

            df = df.sort_values('Date').reset_index(drop=True)

            return df

        except Exception as e:
            print(f"Error fetching data for {symbol}: {str(e)}")
            return pd.DataFrame()

    def get_current_price(self, symbol: str) -> Optional[float]:
        """Get current price for a symbol"""
        try:
            df = self.get_stock_data(symbol)
            if df.empty:
                return None
            return float(df.iloc[-1]['Close'])
        except Exception as e:
            print(f"Error getting current price for {symbol}: {str(e)}")
            return None

    def get_crypto_data(self, symbol: str, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Fetch cryptocurrency data from Yahoo Finance

        Args:
            symbol: Crypto symbol (e.g., 'BTC-USD', 'ETH-USD')
            start_date: Start date in 'YYYY-MM-DD' format
            end_date: End date in 'YYYY-MM-DD' format

        Returns:
            DataFrame with price data
        """
        # Crypto symbols in Yahoo Finance use -USD suffix
        if not symbol.endswith('-USD'):
            symbol = f"{symbol}-USD"

        return self.get_stock_data(symbol, start_date, end_date)

    def get_ipca(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Fetch IPCA (Brazilian inflation index) from Banco Central do Brasil

        IPCA Series Code: 433

        Args:
            start_date: Start date in 'DD/MM/YYYY' format
            end_date: End date in 'DD/MM/YYYY' format

        Returns:
            DataFrame with Date and IPCA value
        """
        try:
            # IPCA series code in BCB API
            ipca_code = 433

            # Format dates for BCB API (DD/MM/YYYY)
            if start_date and '-' in start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            if end_date and '-' in end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')

            # Build URL
            url = f"{self.bacen_base_url}/{ipca_code}/dados"
            params = {}
            if start_date:
                params['dataInicial'] = start_date
            if end_date:
                params['dataFinal'] = end_date

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"Warning: Could not fetch IPCA data. Status: {response.status_code}")
                return pd.DataFrame()

            data = response.json()

            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['valor'] = pd.to_numeric(df['valor'])
            df = df.rename(columns={'data': 'Date', 'valor': 'IPCA'})

            return df.sort_values('Date').reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching IPCA data: {str(e)}")
            return pd.DataFrame()

    def get_selic(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Fetch SELIC rate (Brazilian interest rate) from Banco Central do Brasil

        SELIC Series Code: 11

        Args:
            start_date: Start date in 'DD/MM/YYYY' format
            end_date: End date in 'DD/MM/YYYY' format

        Returns:
            DataFrame with Date and SELIC value
        """
        try:
            selic_code = 11

            # Format dates for BCB API
            if start_date and '-' in start_date:
                start_date = datetime.strptime(start_date, '%Y-%m-%d').strftime('%d/%m/%Y')
            if end_date and '-' in end_date:
                end_date = datetime.strptime(end_date, '%Y-%m-%d').strftime('%d/%m/%Y')

            url = f"{self.bacen_base_url}/{selic_code}/dados"
            params = {}
            if start_date:
                params['dataInicial'] = start_date
            if end_date:
                params['dataFinal'] = end_date

            response = requests.get(url, params=params)

            if response.status_code != 200:
                print(f"Warning: Could not fetch SELIC data. Status: {response.status_code}")
                return pd.DataFrame()

            data = response.json()

            df = pd.DataFrame(data)
            df['data'] = pd.to_datetime(df['data'], format='%d/%m/%Y')
            df['valor'] = pd.to_numeric(df['valor'])
            df = df.rename(columns={'data': 'Date', 'valor': 'SELIC'})

            return df.sort_values('Date').reset_index(drop=True)

        except Exception as e:
            print(f"Error fetching SELIC data: {str(e)}")
            return pd.DataFrame()

    def get_exchange_rate(self, from_currency: str, to_currency: str = 'USD') -> Optional[float]:
        """
        Get current exchange rate

        Args:
            from_currency: Source currency code (e.g., 'BRL', 'EUR')
            to_currency: Target currency code (default: 'USD')

        Returns:
            Exchange rate or None if not available
        """
        try:
            if from_currency == to_currency:
                return 1.0

            symbol = f"{from_currency}{to_currency}=X"
            price = self.get_current_price(symbol)

            if price is None and to_currency == 'USD':
                # Try reverse rate
                symbol = f"{to_currency}{from_currency}=X"
                reverse_price = self.get_current_price(symbol)
                if reverse_price and reverse_price > 0:
                    price = 1.0 / reverse_price

            return price

        except Exception as e:
            print(f"Error getting exchange rate {from_currency}/{to_currency}: {str(e)}")
            return None


# Convenience function
def test_market_data():
    """Test market data fetcher"""
    fetcher = MarketDataFetcher()

    print("Testing Market Data Fetcher")
    print("=" * 60)

    # Test stock data
    print("\n1. Fetching AAPL stock data...")
    aapl = fetcher.get_stock_data('AAPL', start_date='2024-01-01')
    if not aapl.empty:
        print(f"   Retrieved {len(aapl)} days of data")
        print(f"   Latest price: ${aapl.iloc[-1]['Close']:.2f}")

    # Test Brazilian stock
    print("\n2. Fetching PETR4.SA (Petrobras) data...")
    petr4 = fetcher.get_stock_data('PETR4.SA', start_date='2024-01-01')
    if not petr4.empty:
        print(f"   Retrieved {len(petr4)} days of data")
        print(f"   Latest price: R$ {petr4.iloc[-1]['Close']:.2f}")

    # Test crypto
    print("\n3. Fetching BTC-USD data...")
    btc = fetcher.get_crypto_data('BTC', start_date='2024-01-01')
    if not btc.empty:
        print(f"   Retrieved {len(btc)} days of data")
        print(f"   Latest price: ${btc.iloc[-1]['Close']:.2f}")

    # Test IPCA
    print("\n4. Fetching IPCA data...")
    ipca = fetcher.get_ipca(start_date='2024-01-01')
    if not ipca.empty:
        print(f"   Retrieved {len(ipca)} months of data")
        print(f"   Latest IPCA: {ipca.iloc[-1]['IPCA']:.2f}%")

    # Test exchange rate
    print("\n5. Fetching BRL/USD exchange rate...")
    brl_usd = fetcher.get_exchange_rate('BRL', 'USD')
    if brl_usd:
        print(f"   BRL/USD: {brl_usd:.4f}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_market_data()
