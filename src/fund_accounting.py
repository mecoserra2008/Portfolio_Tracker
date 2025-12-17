"""
Fund Accounting System
Tracks cash position, investor stakes, and calculates management/performance fees
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import os


class CashManager:
    """
    Manages cash position tracking including deposits and withdrawals
    """

    def __init__(self, deposits_withdrawals_csv: str = 'data/fund/client_deposits_withdrawals.csv'):
        """
        Initialize cash manager

        Args:
            deposits_withdrawals_csv: Path to deposits/withdrawals CSV
        """
        self.csv_path = deposits_withdrawals_csv
        self._ensure_csv_exists()
        self.transactions = self._load_transactions()

    def _ensure_csv_exists(self):
        """Create CSV file and directory if they don't exist"""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

        if not os.path.exists(self.csv_path):
            # Create with headers
            df = pd.DataFrame(columns=[
                'date',           # Transaction date (YYYY-MM-DD)
                'investor_id',    # Unique investor identifier
                'investor_name',  # Investor name
                'type',           # 'deposit' or 'withdrawal'
                'amount',         # Amount in BRL
                'currency',       # Currency (BRL, USD, EUR)
                'amount_brl',     # Amount converted to BRL
                'description'     # Optional description
            ])
            df.to_csv(self.csv_path, index=False)

    def _load_transactions(self) -> pd.DataFrame:
        """Load transactions from CSV"""
        df = pd.read_csv(self.csv_path)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df = df.sort_values('date')
        return df

    def add_transaction(self, date: str, investor_id: str, investor_name: str,
                       transaction_type: str, amount: float, currency: str = 'BRL',
                       description: str = '') -> None:
        """
        Add a deposit or withdrawal transaction

        Args:
            date: Transaction date (YYYY-MM-DD)
            investor_id: Unique investor identifier
            investor_name: Investor name
            transaction_type: 'deposit' or 'withdrawal'
            amount: Amount in specified currency
            currency: Currency code (BRL, USD, EUR)
            description: Optional description
        """
        # Convert to BRL if needed
        amount_brl = amount  # Simplified - in production, use real FX rates

        new_transaction = pd.DataFrame([{
            'date': pd.to_datetime(date),
            'investor_id': investor_id,
            'investor_name': investor_name,
            'type': transaction_type,
            'amount': amount,
            'currency': currency,
            'amount_brl': amount_brl,
            'description': description
        }])

        self.transactions = pd.concat([self.transactions, new_transaction], ignore_index=True)
        self.transactions = self.transactions.sort_values('date')
        self._save_transactions()

    def _save_transactions(self):
        """Save transactions to CSV"""
        self.transactions.to_csv(self.csv_path, index=False)

    def get_cash_position(self, as_of_date: str = None) -> float:
        """
        Get total cash position as of a specific date

        Args:
            as_of_date: Date to calculate cash position (default: today)

        Returns:
            Cash position in BRL
        """
        if as_of_date is None:
            as_of_date = datetime.now()
        else:
            as_of_date = pd.to_datetime(as_of_date)

        if self.transactions.empty:
            return 0.0

        relevant_txns = self.transactions[self.transactions['date'] <= as_of_date].copy()

        if relevant_txns.empty:
            return 0.0

        deposits = relevant_txns[relevant_txns['type'] == 'deposit']['amount_brl'].sum()
        withdrawals = relevant_txns[relevant_txns['type'] == 'withdrawal']['amount_brl'].sum()

        return deposits - withdrawals

    def get_cash_flow_history(self, start_date: str = None, end_date: str = None) -> pd.DataFrame:
        """
        Get cash flow history over time

        Args:
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with daily cash positions
        """
        if self.transactions.empty:
            return pd.DataFrame()

        if start_date:
            start_date = pd.to_datetime(start_date)
        else:
            start_date = self.transactions['date'].min()

        if end_date:
            end_date = pd.to_datetime(end_date)
        else:
            end_date = datetime.now()

        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        cash_history = []
        for date in dates:
            cash_pos = self.get_cash_position(date)
            cash_history.append({
                'date': date,
                'cash_position': cash_pos
            })

        return pd.DataFrame(cash_history)


class InvestorTracker:
    """
    Tracks individual investor stakes and allocations over time
    """

    def __init__(self, cash_manager: CashManager):
        """
        Initialize investor tracker

        Args:
            cash_manager: CashManager instance
        """
        self.cash_manager = cash_manager

    def get_investor_stakes(self, as_of_date: str = None) -> pd.DataFrame:
        """
        Calculate each investor's stake in the fund

        Args:
            as_of_date: Date to calculate stakes (default: today)

        Returns:
            DataFrame with investor stakes
        """
        if as_of_date is None:
            as_of_date = datetime.now()
        else:
            as_of_date = pd.to_datetime(as_of_date)

        txns = self.cash_manager.transactions

        if txns.empty:
            return pd.DataFrame()

        relevant_txns = txns[txns['date'] <= as_of_date].copy()

        if relevant_txns.empty:
            return pd.DataFrame()

        # Calculate net contribution per investor
        investor_stakes = []

        for investor_id in relevant_txns['investor_id'].unique():
            investor_txns = relevant_txns[relevant_txns['investor_id'] == investor_id]

            deposits = investor_txns[investor_txns['type'] == 'deposit']['amount_brl'].sum()
            withdrawals = investor_txns[investor_txns['type'] == 'withdrawal']['amount_brl'].sum()
            net_contribution = deposits - withdrawals

            investor_name = investor_txns['investor_name'].iloc[0]
            first_investment = investor_txns['date'].min()

            investor_stakes.append({
                'investor_id': investor_id,
                'investor_name': investor_name,
                'deposits': deposits,
                'withdrawals': withdrawals,
                'net_contribution': net_contribution,
                'first_investment_date': first_investment
            })

        df = pd.DataFrame(investor_stakes)

        if not df.empty:
            total_capital = df['net_contribution'].sum()
            df['stake_pct'] = (df['net_contribution'] / total_capital * 100) if total_capital > 0 else 0

        return df

    def get_investor_history(self, investor_id: str, start_date: str = None,
                            end_date: str = None) -> pd.DataFrame:
        """
        Get stake history for a specific investor

        Args:
            investor_id: Investor ID
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            DataFrame with daily stake evolution
        """
        txns = self.cash_manager.transactions
        investor_txns = txns[txns['investor_id'] == investor_id]

        if investor_txns.empty:
            return pd.DataFrame()

        if start_date:
            start_date = pd.to_datetime(start_date)
        else:
            start_date = investor_txns['date'].min()

        if end_date:
            end_date = pd.to_datetime(end_date)
        else:
            end_date = datetime.now()

        dates = pd.date_range(start=start_date, end=end_date, freq='D')

        history = []
        for date in dates:
            relevant = investor_txns[investor_txns['date'] <= date]
            deposits = relevant[relevant['type'] == 'deposit']['amount_brl'].sum()
            withdrawals = relevant[relevant['type'] == 'withdrawal']['amount_brl'].sum()
            net = deposits - withdrawals

            history.append({
                'date': date,
                'net_contribution': net,
                'deposits': deposits,
                'withdrawals': withdrawals
            })

        return pd.DataFrame(history)


class FeeCalculator:
    """
    Calculates management fees (2% annual) and performance fees (20%)
    """

    def __init__(self, payments_csv: str = 'data/fund/payments_to_company.csv'):
        """
        Initialize fee calculator

        Args:
            payments_csv: Path to payments CSV
        """
        self.csv_path = payments_csv
        self._ensure_csv_exists()
        self.payments = self._load_payments()
        self.high_water_marks = {}  # Track high water mark per investor

    def _ensure_csv_exists(self):
        """Create CSV file if it doesn't exist"""
        os.makedirs(os.path.dirname(self.csv_path), exist_ok=True)

        if not os.path.exists(self.csv_path):
            df = pd.DataFrame(columns=[
                'date',              # Payment date
                'investor_id',       # Investor ID (or 'ALL' for fund-level)
                'investor_name',     # Investor name
                'fee_type',          # 'management' or 'performance'
                'period_start',      # Fee calculation period start
                'period_end',        # Fee calculation period end
                'nav_start',         # NAV at period start
                'nav_end',           # NAV at period end
                'fee_rate',          # Fee rate (2% or 20%)
                'fee_amount',        # Fee amount in BRL
                'paid',              # Boolean: has fee been paid
                'payment_date'       # Actual payment date
            ])
            df.to_csv(self.csv_path, index=False)

    def _load_payments(self) -> pd.DataFrame:
        """Load payments from CSV"""
        df = pd.read_csv(self.csv_path)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
            df['period_start'] = pd.to_datetime(df['period_start'])
            df['period_end'] = pd.to_datetime(df['period_end'])
            if 'payment_date' in df.columns:
                df['payment_date'] = pd.to_datetime(df['payment_date'])
        return df

    def _save_payments(self):
        """Save payments to CSV"""
        self.payments.to_csv(self.csv_path, index=False)

    def calculate_management_fee(self, nav: float, period_days: int = 365) -> float:
        """
        Calculate 2% annual management fee

        Args:
            nav: Net Asset Value
            period_days: Number of days in period (for pro-rata calculation)

        Returns:
            Management fee amount
        """
        annual_rate = 0.02  # 2%
        daily_rate = annual_rate / 365
        return nav * daily_rate * period_days

    def calculate_performance_fee(self, nav_start: float, nav_end: float,
                                  high_water_mark: float = None) -> Tuple[float, float]:
        """
        Calculate 20% performance fee on gains above high water mark

        Args:
            nav_start: NAV at period start
            nav_end: NAV at period end
            high_water_mark: Previous high water mark (default: nav_start)

        Returns:
            Tuple of (fee_amount, new_high_water_mark)
        """
        if high_water_mark is None:
            high_water_mark = nav_start

        # Only charge performance fee if NAV exceeds high water mark
        if nav_end > high_water_mark:
            gain = nav_end - high_water_mark
            fee = gain * 0.20  # 20% of gains
            new_hwm = nav_end
        else:
            fee = 0.0
            new_hwm = high_water_mark

        return fee, new_hwm

    def record_fee_payment(self, date: str, investor_id: str, investor_name: str,
                          fee_type: str, period_start: str, period_end: str,
                          nav_start: float, nav_end: float, fee_amount: float,
                          paid: bool = False) -> None:
        """
        Record a fee payment

        Args:
            date: Fee calculation date
            investor_id: Investor ID
            investor_name: Investor name
            fee_type: 'management' or 'performance'
            period_start: Period start date
            period_end: Period end date
            nav_start: NAV at period start
            nav_end: NAV at period end
            fee_amount: Calculated fee amount
            paid: Whether fee has been paid
        """
        fee_rate = 0.02 if fee_type == 'management' else 0.20

        new_payment = pd.DataFrame([{
            'date': pd.to_datetime(date),
            'investor_id': investor_id,
            'investor_name': investor_name,
            'fee_type': fee_type,
            'period_start': pd.to_datetime(period_start),
            'period_end': pd.to_datetime(period_end),
            'nav_start': nav_start,
            'nav_end': nav_end,
            'fee_rate': fee_rate,
            'fee_amount': fee_amount,
            'paid': paid,
            'payment_date': pd.NaT
        }])

        self.payments = pd.concat([self.payments, new_payment], ignore_index=True)
        self._save_payments()

    def mark_fee_as_paid(self, payment_index: int, payment_date: str = None):
        """
        Mark a fee as paid

        Args:
            payment_index: Index of payment in DataFrame
            payment_date: Date payment was made (default: today)
        """
        if payment_date is None:
            payment_date = datetime.now()
        else:
            payment_date = pd.to_datetime(payment_date)

        self.payments.loc[payment_index, 'paid'] = True
        self.payments.loc[payment_index, 'payment_date'] = payment_date
        self._save_payments()

    def get_outstanding_fees(self) -> pd.DataFrame:
        """Get all unpaid fees"""
        if self.payments.empty:
            return pd.DataFrame()
        return self.payments[self.payments['paid'] == False].copy()

    def get_fee_summary(self, start_date: str = None, end_date: str = None) -> Dict:
        """
        Get summary of fees over a period

        Args:
            start_date: Start date (optional)
            end_date: End date (optional)

        Returns:
            Dictionary with fee summary
        """
        if self.payments.empty:
            return {
                'total_management_fees': 0.0,
                'total_performance_fees': 0.0,
                'total_fees': 0.0,
                'outstanding_fees': 0.0,
                'paid_fees': 0.0
            }

        df = self.payments.copy()

        if start_date:
            df = df[df['date'] >= pd.to_datetime(start_date)]
        if end_date:
            df = df[df['date'] <= pd.to_datetime(end_date)]

        management_fees = df[df['fee_type'] == 'management']['fee_amount'].sum()
        performance_fees = df[df['fee_type'] == 'performance']['fee_amount'].sum()
        total_fees = management_fees + performance_fees

        outstanding = df[df['paid'] == False]['fee_amount'].sum()
        paid = df[df['paid'] == True]['fee_amount'].sum()

        return {
            'total_management_fees': management_fees,
            'total_performance_fees': performance_fees,
            'total_fees': total_fees,
            'outstanding_fees': outstanding,
            'paid_fees': paid,
            'num_payments': len(df),
            'num_outstanding': len(df[df['paid'] == False])
        }


class FundAccountingSystem:
    """
    Integrated fund accounting system combining cash, investors, and fees
    """

    def __init__(self, data_dir: str = 'data/fund'):
        """
        Initialize fund accounting system

        Args:
            data_dir: Directory for fund data
        """
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)

        self.cash_manager = CashManager(
            deposits_withdrawals_csv=f'{data_dir}/client_deposits_withdrawals.csv'
        )
        self.investor_tracker = InvestorTracker(self.cash_manager)
        self.fee_calculator = FeeCalculator(
            payments_csv=f'{data_dir}/payments_to_company.csv'
        )

    def calculate_nav(self, portfolio_value: float, cash_position: float = None) -> float:
        """
        Calculate Net Asset Value (NAV)

        Args:
            portfolio_value: Current portfolio market value
            cash_position: Cash position (if None, calculated from cash_manager)

        Returns:
            NAV (portfolio value + cash - outstanding fees)
        """
        if cash_position is None:
            cash_position = self.cash_manager.get_cash_position()

        outstanding_fees = self.fee_calculator.get_outstanding_fees()
        total_outstanding = outstanding_fees['fee_amount'].sum() if not outstanding_fees.empty else 0.0

        nav = portfolio_value + cash_position - total_outstanding
        return nav

    def calculate_investor_nav(self, investor_id: str, total_nav: float) -> float:
        """
        Calculate an investor's share of NAV based on their stake

        Args:
            investor_id: Investor ID
            total_nav: Total fund NAV

        Returns:
            Investor's NAV
        """
        stakes = self.investor_tracker.get_investor_stakes()

        if stakes.empty:
            return 0.0

        investor_stake = stakes[stakes['investor_id'] == investor_id]

        if investor_stake.empty:
            return 0.0

        stake_pct = investor_stake['stake_pct'].iloc[0]
        return total_nav * (stake_pct / 100)

    def process_period_fees(self, period_start: str, period_end: str,
                           nav_start: float, nav_end: float,
                           calculate_management: bool = True,
                           calculate_performance: bool = True) -> Dict:
        """
        Calculate and record all fees for a period

        Args:
            period_start: Period start date
            period_end: Period end date
            nav_start: NAV at period start
            nav_end: NAV at period end (before fees)
            calculate_management: Whether to calculate management fees
            calculate_performance: Whether to calculate performance fees

        Returns:
            Dictionary with fee breakdown
        """
        period_start_dt = pd.to_datetime(period_start)
        period_end_dt = pd.to_datetime(period_end)
        period_days = (period_end_dt - period_start_dt).days

        results = {
            'period_start': period_start,
            'period_end': period_end,
            'period_days': period_days,
            'nav_start': nav_start,
            'nav_end': nav_end,
            'management_fee': 0.0,
            'performance_fee': 0.0,
            'total_fees': 0.0
        }

        # Calculate management fee (2% annual)
        if calculate_management:
            mgmt_fee = self.fee_calculator.calculate_management_fee(nav_end, period_days)
            results['management_fee'] = mgmt_fee

            self.fee_calculator.record_fee_payment(
                date=period_end,
                investor_id='FUND',
                investor_name='Fund Level',
                fee_type='management',
                period_start=period_start,
                period_end=period_end,
                nav_start=nav_start,
                nav_end=nav_end,
                fee_amount=mgmt_fee,
                paid=False
            )

        # Calculate performance fee (20% on gains above HWM)
        if calculate_performance:
            hwm = self.fee_calculator.high_water_marks.get('FUND', nav_start)
            perf_fee, new_hwm = self.fee_calculator.calculate_performance_fee(
                nav_start, nav_end, hwm
            )
            results['performance_fee'] = perf_fee
            self.fee_calculator.high_water_marks['FUND'] = new_hwm

            if perf_fee > 0:
                self.fee_calculator.record_fee_payment(
                    date=period_end,
                    investor_id='FUND',
                    investor_name='Fund Level',
                    fee_type='performance',
                    period_start=period_start,
                    period_end=period_end,
                    nav_start=nav_start,
                    nav_end=nav_end,
                    fee_amount=perf_fee,
                    paid=False
                )

        results['total_fees'] = results['management_fee'] + results['performance_fee']
        results['nav_after_fees'] = nav_end - results['total_fees']

        return results

    def get_fund_summary(self, as_of_date: str = None) -> Dict:
        """
        Get comprehensive fund summary

        Args:
            as_of_date: Date for summary (default: today)

        Returns:
            Dictionary with fund summary
        """
        cash_position = self.cash_manager.get_cash_position(as_of_date)
        investor_stakes = self.investor_tracker.get_investor_stakes(as_of_date)
        fee_summary = self.fee_calculator.get_fee_summary()

        return {
            'as_of_date': as_of_date or datetime.now().strftime('%Y-%m-%d'),
            'cash_position': cash_position,
            'num_investors': len(investor_stakes) if not investor_stakes.empty else 0,
            'total_capital_contributed': investor_stakes['deposits'].sum() if not investor_stakes.empty else 0.0,
            'total_capital_withdrawn': investor_stakes['withdrawals'].sum() if not investor_stakes.empty else 0.0,
            'net_capital': investor_stakes['net_contribution'].sum() if not investor_stakes.empty else 0.0,
            'fees': fee_summary,
            'investors': investor_stakes.to_dict('records') if not investor_stakes.empty else []
        }


def test_fund_accounting():
    """Test fund accounting system"""
    print("Testing Fund Accounting System")
    print("=" * 60)

    # Initialize system
    system = FundAccountingSystem()

    # Add some test transactions
    print("\n1. Adding test deposits...")
    print("-" * 60)
    system.cash_manager.add_transaction(
        date='2024-01-01',
        investor_id='INV001',
        investor_name='João Silva',
        transaction_type='deposit',
        amount=1000000.00,
        currency='BRL',
        description='Initial investment'
    )

    system.cash_manager.add_transaction(
        date='2024-06-01',
        investor_id='INV002',
        investor_name='Maria Santos',
        transaction_type='deposit',
        amount=500000.00,
        currency='BRL',
        description='Initial investment'
    )

    print("✓ Added 2 test deposits")

    # Get fund summary
    print("\n2. Fund Summary:")
    print("-" * 60)
    summary = system.get_fund_summary()
    print(f"Cash Position: R$ {summary['cash_position']:,.2f}")
    print(f"Number of Investors: {summary['num_investors']}")
    print(f"Total Capital: R$ {summary['total_capital_contributed']:,.2f}")

    print("\nInvestor Stakes:")
    for investor in summary['investors']:
        print(f"  {investor['investor_name']}: {investor['stake_pct']:.2f}% "
              f"(R$ {investor['net_contribution']:,.2f})")

    # Calculate fees
    print("\n3. Calculating fees for 2024...")
    print("-" * 60)
    fees = system.process_period_fees(
        period_start='2024-01-01',
        period_end='2024-12-31',
        nav_start=1000000.00,
        nav_end=1200000.00  # 20% gain
    )

    print(f"Period: {fees['period_start']} to {fees['period_end']}")
    print(f"NAV Start: R$ {fees['nav_start']:,.2f}")
    print(f"NAV End: R$ {fees['nav_end']:,.2f}")
    print(f"Management Fee (2%): R$ {fees['management_fee']:,.2f}")
    print(f"Performance Fee (20%): R$ {fees['performance_fee']:,.2f}")
    print(f"Total Fees: R$ {fees['total_fees']:,.2f}")
    print(f"NAV After Fees: R$ {fees['nav_after_fees']:,.2f}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_fund_accounting()
