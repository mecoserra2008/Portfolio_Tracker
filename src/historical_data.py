"""
Historical Data Manager
Fetches, stores, and retrieves historical price data with batch processing
"""

import pandas as pd
import numpy as np
import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import time
import os
from .market_data import MarketDataFetcher


class HistoricalDataManager:
    """
    Manages historical price data with:
    - Batch fetching to overcome API limits
    - SQLite storage for persistence
    - Incremental updates (only fetch missing data)
    - Support for stocks, crypto, and indices
    """

    def __init__(self, db_path: str = 'data/historical_data.db'):
        """
        Initialize historical data manager

        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = db_path
        self.market_data = MarketDataFetcher()
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with required tables"""
        os.makedirs(os.path.dirname(self.db_path) if os.path.dirname(self.db_path) else '.', exist_ok=True)

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Price history table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS price_history (
                symbol TEXT NOT NULL,
                date DATE NOT NULL,
                open REAL,
                high REAL,
                low REAL,
                close REAL,
                adj_close REAL,
                volume INTEGER,
                dividend REAL DEFAULT 0,
                split REAL DEFAULT 1,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                PRIMARY KEY (symbol, date)
            )
        ''')

        # Metadata table to track last update
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS symbol_metadata (
                symbol TEXT PRIMARY KEY,
                first_date DATE,
                last_date DATE,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                total_records INTEGER DEFAULT 0
            )
        ''')

        # Index for faster queries
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_date
            ON price_history(date)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_price_symbol_date
            ON price_history(symbol, date DESC)
        ''')

        conn.commit()
        conn.close()

    def _get_date_ranges_to_fetch(self, symbol: str, start_date: str, end_date: str) -> List[Tuple[str, str]]:
        """
        Determine which date ranges need to be fetched
        Returns list of (start, end) date tuples to fetch
        """
        conn = sqlite3.connect(self.db_path)

        # Get existing data range for symbol
        query = '''
            SELECT MIN(date), MAX(date)
            FROM price_history
            WHERE symbol = ?
        '''
        result = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()

        existing_start = result.iloc[0, 0]
        existing_end = result.iloc[0, 1]

        ranges = []

        if pd.isna(existing_start):
            # No data exists, fetch everything
            ranges.append((start_date, end_date))
        else:
            # Fetch data before existing range
            if start_date < existing_start:
                ranges.append((start_date, existing_start))

            # Fetch data after existing range
            if end_date > existing_end:
                ranges.append((existing_end, end_date))

        return ranges

    def fetch_historical_data(
        self,
        symbol: str,
        start_date: str,
        end_date: str = None,
        force_refresh: bool = False,
        batch_days: int = 100
    ) -> pd.DataFrame:
        """
        Fetch historical data with batch processing

        Args:
            symbol: Stock/crypto symbol
            start_date: Start date (YYYY-MM-DD)
            end_date: End date (YYYY-MM-DD), default is today
            force_refresh: If True, re-fetch all data
            batch_days: Number of days per batch (to avoid API limits)

        Returns:
            DataFrame with historical price data
        """
        if end_date is None:
            end_date = datetime.now().strftime('%Y-%m-%d')

        # If force refresh, delete existing data
        if force_refresh:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('DELETE FROM price_history WHERE symbol = ?', (symbol,))
            cursor.execute('DELETE FROM symbol_metadata WHERE symbol = ?', (symbol,))
            conn.commit()
            conn.close()

        # Determine what needs to be fetched
        ranges_to_fetch = self._get_date_ranges_to_fetch(symbol, start_date, end_date)

        if not ranges_to_fetch:
            print(f"✓ {symbol}: All data already cached")
            return self.get_historical_data(symbol, start_date, end_date)

        # Fetch data in batches
        for range_start, range_end in ranges_to_fetch:
            self._fetch_and_store_range(symbol, range_start, range_end, batch_days)

        return self.get_historical_data(symbol, start_date, end_date)

    def _fetch_and_store_range(self, symbol: str, start_date: str, end_date: str, batch_days: int):
        """
        Fetch and store data for a date range in batches

        Args:
            symbol: Symbol to fetch
            start_date: Start date
            end_date: End date
            batch_days: Days per batch
        """
        start = pd.Timestamp(start_date)
        end = pd.Timestamp(end_date)

        current = start
        total_records = 0

        print(f"Fetching {symbol} from {start_date} to {end_date}...")

        while current < end:
            batch_end = min(current + timedelta(days=batch_days), end)

            batch_start_str = current.strftime('%Y-%m-%d')
            batch_end_str = batch_end.strftime('%Y-%m-%d')

            print(f"  Batch: {batch_start_str} to {batch_end_str}", end=' ')

            try:
                # Fetch data from Yahoo Finance
                df = self.market_data.get_stock_data(symbol, batch_start_str, batch_end_str)

                if not df.empty:
                    # Store in database
                    records_stored = self._store_price_data(symbol, df)
                    total_records += records_stored
                    print(f"✓ ({records_stored} records)")
                else:
                    print("✗ (no data)")

                # Rate limiting: sleep between batches
                time.sleep(0.5)  # 500ms delay between batches

            except Exception as e:
                print(f"✗ Error: {str(e)}")

            current = batch_end + timedelta(days=1)

        print(f"✓ Total: {total_records} records stored for {symbol}")

    def _store_price_data(self, symbol: str, df: pd.DataFrame) -> int:
        """
        Store price data in database

        Args:
            symbol: Symbol
            df: DataFrame with price data

        Returns:
            Number of records stored
        """
        conn = sqlite3.connect(self.db_path)

        # Prepare data for insertion
        df_db = df.copy()
        df_db['symbol'] = symbol
        df_db['date'] = df_db['Date'].dt.strftime('%Y-%m-%d')
        df_db = df_db.rename(columns={
            'Open': 'open',
            'High': 'high',
            'Low': 'low',
            'Close': 'close',
            'Adj Close': 'adj_close',
            'Volume': 'volume',
            'Dividend': 'dividend',
            'Split': 'split'
        })

        # Select relevant columns
        columns = ['symbol', 'date', 'open', 'high', 'low', 'close', 'adj_close',
                   'volume', 'dividend', 'split']
        df_db = df_db[columns]

        # Insert or replace records
        df_db.to_sql('price_history', conn, if_exists='append', index=False,
                     method='multi', chunksize=1000)

        # Update metadata
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO symbol_metadata (symbol, first_date, last_date, total_records, last_updated)
            SELECT
                ?,
                MIN(date),
                MAX(date),
                COUNT(*),
                CURRENT_TIMESTAMP
            FROM price_history
            WHERE symbol = ?
        ''', (symbol, symbol))

        conn.commit()
        records_count = len(df_db)
        conn.close()

        return records_count

    def get_historical_data(
        self,
        symbol: str,
        start_date: str = None,
        end_date: str = None
    ) -> pd.DataFrame:
        """
        Retrieve historical data from database

        Args:
            symbol: Symbol to retrieve
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with historical data
        """
        conn = sqlite3.connect(self.db_path)

        query = 'SELECT * FROM price_history WHERE symbol = ?'
        params = [symbol]

        if start_date:
            query += ' AND date >= ?'
            params.append(start_date)

        if end_date:
            query += ' AND date <= ?'
            params.append(end_date)

        query += ' ORDER BY date ASC'

        df = pd.read_sql_query(query, conn, params=params)
        conn.close()

        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])

        return df

    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get most recent price for a symbol"""
        conn = sqlite3.connect(self.db_path)

        query = '''
            SELECT close
            FROM price_history
            WHERE symbol = ?
            ORDER BY date DESC
            LIMIT 1
        '''

        result = pd.read_sql_query(query, conn, params=(symbol,))
        conn.close()

        if not result.empty:
            return float(result.iloc[0, 0])
        return None

    def bulk_fetch(
        self,
        symbols: List[str],
        start_date: str,
        end_date: str = None,
        batch_days: int = 100
    ):
        """
        Fetch historical data for multiple symbols

        Args:
            symbols: List of symbols
            start_date: Start date
            end_date: End date
            batch_days: Days per batch
        """
        print(f"\n{'='*60}")
        print(f"Bulk fetching {len(symbols)} symbols")
        print(f"{'='*60}\n")

        for i, symbol in enumerate(symbols, 1):
            print(f"[{i}/{len(symbols)}] {symbol}")
            try:
                self.fetch_historical_data(symbol, start_date, end_date,
                                          batch_days=batch_days)
            except Exception as e:
                print(f"  ✗ Error: {str(e)}")

            # Rate limiting between symbols
            if i < len(symbols):
                time.sleep(1)  # 1 second between symbols

        print(f"\n{'='*60}")
        print("Bulk fetch complete!")
        print(f"{'='*60}\n")

    def get_database_stats(self) -> Dict:
        """Get statistics about stored data"""
        conn = sqlite3.connect(self.db_path)

        # Symbol count
        symbol_count = pd.read_sql_query(
            'SELECT COUNT(DISTINCT symbol) as count FROM price_history',
            conn
        ).iloc[0, 0]

        # Total records
        total_records = pd.read_sql_query(
            'SELECT COUNT(*) as count FROM price_history',
            conn
        ).iloc[0, 0]

        # Date range
        date_range = pd.read_sql_query(
            'SELECT MIN(date) as min_date, MAX(date) as max_date FROM price_history',
            conn
        ).iloc[0]

        # Per-symbol stats
        symbol_stats = pd.read_sql_query('''
            SELECT
                symbol,
                COUNT(*) as records,
                MIN(date) as first_date,
                MAX(date) as last_date
            FROM price_history
            GROUP BY symbol
            ORDER BY records DESC
        ''', conn)

        conn.close()

        return {
            'total_symbols': int(symbol_count),
            'total_records': int(total_records),
            'date_range': {
                'start': date_range['min_date'],
                'end': date_range['max_date']
            },
            'symbols': symbol_stats.to_dict('records')
        }

    def clear_old_data(self, days_to_keep: int = 365):
        """
        Remove old data to save space

        Args:
            days_to_keep: Number of days to retain
        """
        cutoff_date = (datetime.now() - timedelta(days=days_to_keep)).strftime('%Y-%m-%d')

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute('DELETE FROM price_history WHERE date < ?', (cutoff_date,))
        deleted = cursor.rowcount

        conn.commit()
        conn.close()

        print(f"Deleted {deleted} records older than {cutoff_date}")

        return deleted


def test_historical_data_manager():
    """Test historical data manager"""
    print("Testing Historical Data Manager")
    print("=" * 60)

    manager = HistoricalDataManager()

    # Test with a few symbols
    test_symbols = ['AAPL', 'PETR4.SA', 'BTC-USD']
    start_date = '2024-01-01'

    print("\n1. Fetching historical data for test symbols...")
    print("-" * 60)

    for symbol in test_symbols:
        print(f"\nFetching {symbol}...")
        try:
            df = manager.fetch_historical_data(
                symbol,
                start_date,
                batch_days=90  # 90 days per batch
            )
            print(f"  Retrieved {len(df)} records")
            if not df.empty:
                print(f"  Date range: {df['date'].min()} to {df['date'].max()}")
                print(f"  Latest price: ${df.iloc[-1]['close']:.2f}")
        except Exception as e:
            print(f"  Error: {str(e)}")

    # Get database stats
    print("\n2. Database Statistics:")
    print("-" * 60)
    stats = manager.get_database_stats()
    print(f"Total symbols: {stats['total_symbols']}")
    print(f"Total records: {stats['total_records']}")
    print(f"Date range: {stats['date_range']['start']} to {stats['date_range']['end']}")

    print("\nPer-symbol stats:")
    for sym_stat in stats['symbols']:
        print(f"  {sym_stat['symbol']}: {sym_stat['records']} records "
              f"({sym_stat['first_date']} to {sym_stat['last_date']})")

    # Test retrieval
    print("\n3. Testing data retrieval...")
    print("-" * 60)
    test_symbol = 'AAPL'
    retrieved = manager.get_historical_data(test_symbol, '2024-06-01', '2024-06-30')
    if not retrieved.empty:
        print(f"Retrieved {len(retrieved)} records for {test_symbol} in June 2024")
        print(retrieved.head())

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_historical_data_manager()
