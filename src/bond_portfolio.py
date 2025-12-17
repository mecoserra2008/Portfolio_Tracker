"""
Bond Portfolio Calculator
Handles Brazilian bonds with IPCA indexation, coupons, and maturity tracking
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from .market_data import MarketDataFetcher


class BondPortfolio:
    """
    Manages bond portfolio calculations including:
    - Multiple bond types (CDB, LCA, CRI, Tesouro, NTN-B, LTN, LFT, COE)
    - IPCA indexation for inflation-linked bonds
    - Coupon payment tracking
    - Face value and market value tracking
    - Maturity tracking
    - Realized and unrealized P&L
    """

    def __init__(self, bonds_dir: str = 'data/bonds', market_data: MarketDataFetcher = None):
        """
        Initialize bond portfolio

        Args:
            bonds_dir: Directory containing bond CSV files
            market_data: MarketDataFetcher instance (optional)
        """
        self.bonds_dir = bonds_dir
        self.market_data = market_data or MarketDataFetcher()

        # Load all bond types
        self.bonds = self._load_all_bonds()

        # Get IPCA data
        self.ipca_data = None

    def _load_all_bonds(self) -> pd.DataFrame:
        """Load all bond files and combine them"""
        bond_files = {
            'Emissão Bancária': 'emissao_bancaria.csv',
            'Crédito Privado': 'credito_privado.csv',
            'Tesouro': 'tesouro.csv',
            'Títulos Públicos': 'titulos_publicos.csv',
            'COE': 'coe.csv'
        }

        all_bonds = []

        for bond_type, filename in bond_files.items():
            try:
                filepath = f"{self.bonds_dir}/{filename}"
                df = pd.read_csv(filepath)
                df['Tipo de Título'] = bond_type
                all_bonds.append(df)
            except Exception as e:
                print(f"Warning: Could not load {filename}: {str(e)}")

        if not all_bonds:
            return pd.DataFrame()

        combined = pd.concat(all_bonds, ignore_index=True)

        # Standardize date columns
        date_columns = ['Data de Aplicação / Resgate', 'Vencimento']
        for col in date_columns:
            if col in combined.columns:
                combined[col] = pd.to_datetime(combined[col], errors='coerce')

        return combined

    def _load_ipca_data(self, start_date: str = None, end_date: str = None):
        """Load IPCA data from Bacen"""
        if self.ipca_data is None:
            if start_date is None:
                start_date = '2020-01-01'  # Get last few years
            if end_date is None:
                end_date = datetime.now().strftime('%Y-%m-%d')

            self.ipca_data = self.market_data.get_ipca(start_date, end_date)

        return self.ipca_data

    def _calculate_ipca_adjustment(self, base_value: float, start_date: pd.Timestamp,
                                   end_date: pd.Timestamp = None) -> float:
        """
        Calculate IPCA adjustment between two dates

        Args:
            base_value: Initial value
            start_date: Start date
            end_date: End date (default: today)

        Returns:
            Adjusted value
        """
        if end_date is None:
            end_date = pd.Timestamp.now()

        # Load IPCA data
        ipca = self._load_ipca_data()

        if ipca is None or ipca.empty:
            print("Warning: IPCA data not available, using 5% annual approximation")
            years = (end_date - start_date).days / 365.25
            adjustment_factor = (1.05 ** years)  # Approximate 5% annual
            return base_value * adjustment_factor

        # Filter IPCA for date range
        ipca_filtered = ipca[(ipca['Date'] >= start_date) & (ipca['Date'] <= end_date)]

        if ipca_filtered.empty:
            return base_value

        # Calculate cumulative IPCA
        # IPCA values are monthly percentages
        cumulative_factor = 1.0
        for ipca_value in ipca_filtered['IPCA']:
            cumulative_factor *= (1 + ipca_value / 100)

        return base_value * cumulative_factor

    def _parse_indexador(self, indexador: str, percentual: str) -> Dict:
        """
        Parse bond indexer information

        Args:
            indexador: Index name (e.g., 'IPCA', 'CDI', 'Prefixado', 'SELIC')
            percentual: Percentage over index (e.g., '5.50%', 'IPCA + 6%')

        Returns:
            Dictionary with index type and rate
        """
        if pd.isna(indexador):
            return {'type': 'Prefixado', 'rate': 0}

        indexador = str(indexador).upper()

        result = {
            'type': indexador,
            'rate': 0
        }

        # Parse percentage
        if pd.notna(percentual):
            percentual_str = str(percentual)
            # Extract number from string like "6.00%" or "IPCA + 6%"
            import re
            numbers = re.findall(r'[\d.]+', percentual_str)
            if numbers:
                result['rate'] = float(numbers[-1])  # Take last number

        return result

    def _calculate_bond_value(self, bond: pd.Series, valuation_date: pd.Timestamp = None) -> Dict:
        """
        Calculate current value of a bond

        Args:
            bond: Bond row from DataFrame
            valuation_date: Date to value the bond (default: today)

        Returns:
            Dictionary with bond valuation details
        """
        if valuation_date is None:
            valuation_date = pd.Timestamp.now()

        # Extract bond characteristics
        titulo = bond.get('Título ', 'Unknown')
        quantidade = bond.get('Quantidade', 0)
        preco_unitario = bond.get('Preço Unitário ', 0)
        valor_investido = bond.get('Valor investido ', 0)
        indexador = bond.get('Indexador', 'Prefixado')
        percentual = bond.get('Percentual Indexado ', '0%')
        data_aplicacao = bond.get('Data de Aplicação / Resgate')
        vencimento = bond.get('Vencimento')
        tipo_titulo = bond.get('Tipo de Título', 'Unknown')

        # Parse indexer
        index_info = self._parse_indexador(indexador, percentual)

        # Calculate current value based on bond type and indexer
        current_value = valor_investido  # Default

        if pd.notna(data_aplicacao) and index_info['type'] in ['IPCA', 'NTN-B']:
            # Apply IPCA adjustment
            current_value = self._calculate_ipca_adjustment(
                valor_investido,
                pd.Timestamp(data_aplicacao),
                valuation_date
            )
            # Add fixed rate component (compounded annually)
            if index_info['rate'] > 0:
                years = (valuation_date - pd.Timestamp(data_aplicacao)).days / 365.25
                rate_factor = (1 + index_info['rate'] / 100) ** years
                current_value *= rate_factor

        elif index_info['type'] in ['CDI', 'SELIC', 'LFT']:
            # For CDI/SELIC linked, use approximate rate
            # In production, would fetch actual CDI/SELIC rates
            if pd.notna(data_aplicacao):
                years = (valuation_date - pd.Timestamp(data_aplicacao)).days / 365.25
                # Approximate CDI at 13.75% p.a., SELIC at 11.75% p.a.
                base_rate = 13.75 if index_info['type'] == 'CDI' else 11.75
                total_rate = base_rate * (index_info['rate'] / 100) if index_info['rate'] > 0 else base_rate
                current_value = valor_investido * ((1 + total_rate / 100) ** years)

        elif index_info['type'] in ['PREFIXADO', 'LTN']:
            # For prefixado, use the fixed rate
            if pd.notna(data_aplicacao) and index_info['rate'] > 0:
                years = (valuation_date - pd.Timestamp(data_aplicacao)).days / 365.25
                current_value = valor_investido * ((1 + index_info['rate'] / 100) ** years)

        # Check if bond has matured
        is_matured = pd.notna(vencimento) and valuation_date >= pd.Timestamp(vencimento)

        # Calculate P&L
        unrealized_pnl = current_value - valor_investido
        unrealized_pnl_pct = (unrealized_pnl / valor_investido * 100) if valor_investido > 0 else 0

        # Calculate days to maturity
        days_to_maturity = None
        if pd.notna(vencimento) and not is_matured:
            days_to_maturity = (pd.Timestamp(vencimento) - valuation_date).days

        return {
            'Título': titulo,
            'Tipo': tipo_titulo,
            'Quantidade': quantidade,
            'Valor Investido': valor_investido,
            'Valor Atual': current_value,
            'Indexador': indexador,
            'Taxa': index_info['rate'],
            'Data Aplicação': data_aplicacao,
            'Vencimento': vencimento,
            'Dias até Vencimento': days_to_maturity,
            'Maturado': is_matured,
            'P&L': unrealized_pnl,
            'P&L %': unrealized_pnl_pct
        }

    def get_current_values(self, valuation_date: pd.Timestamp = None) -> pd.DataFrame:
        """
        Get current values of all bonds

        Args:
            valuation_date: Date to value bonds (default: today)

        Returns:
            DataFrame with bond valuations
        """
        if self.bonds.empty:
            return pd.DataFrame()

        results = []

        for _, bond in self.bonds.iterrows():
            valuation = self._calculate_bond_value(bond, valuation_date)
            results.append(valuation)

        df = pd.DataFrame(results)

        # Filter out zero quantity positions
        df = df[df['Quantidade'] != 0]

        # Sort by current value descending
        if not df.empty:
            df = df.sort_values('Valor Atual', ascending=False)

        return df

    def get_portfolio_summary(self) -> Dict:
        """
        Get bond portfolio summary

        Returns:
            Dictionary with summary metrics
        """
        df = self.get_current_values()

        if df.empty:
            return {
                'total_invested': 0,
                'total_current_value': 0,
                'total_pnl': 0,
                'total_return_pct': 0,
                'num_bonds': 0,
                'bonds_maturing_30days': 0,
                'bonds_maturing_90days': 0
            }

        # Count bonds maturing soon
        active_bonds = df[~df['Maturado']]
        bonds_30days = len(active_bonds[active_bonds['Dias até Vencimento'] <= 30]) if not active_bonds.empty else 0
        bonds_90days = len(active_bonds[active_bonds['Dias até Vencimento'] <= 90]) if not active_bonds.empty else 0

        return {
            'total_invested': df['Valor Investido'].sum(),
            'total_current_value': df['Valor Atual'].sum(),
            'total_pnl': df['P&L'].sum(),
            'total_return_pct': (df['P&L'].sum() / df['Valor Investido'].sum() * 100) if df['Valor Investido'].sum() > 0 else 0,
            'num_bonds': len(df),
            'num_active_bonds': len(active_bonds),
            'bonds_maturing_30days': bonds_30days,
            'bonds_maturing_90days': bonds_90days
        }

    def get_allocation_by_type(self) -> pd.DataFrame:
        """Get allocation by bond type"""
        df = self.get_current_values()

        if df.empty:
            return df

        allocation = df.groupby('Tipo').agg({
            'Valor Atual': 'sum',
            'P&L': 'sum'
        }).reset_index()

        total_value = allocation['Valor Atual'].sum()
        allocation['Alocação %'] = (allocation['Valor Atual'] / total_value * 100)

        allocation = allocation.sort_values('Valor Atual', ascending=False)

        return allocation

    def get_allocation_by_indexer(self) -> pd.DataFrame:
        """Get allocation by indexer type"""
        df = self.get_current_values()

        if df.empty:
            return df

        allocation = df.groupby('Indexador').agg({
            'Valor Atual': 'sum',
            'P&L': 'sum'
        }).reset_index()

        total_value = allocation['Valor Atual'].sum()
        allocation['Alocação %'] = (allocation['Valor Atual'] / total_value * 100)

        allocation = allocation.sort_values('Valor Atual', ascending=False)

        return allocation

    def get_maturity_schedule(self) -> pd.DataFrame:
        """Get bonds grouped by maturity date"""
        df = self.get_current_values()

        if df.empty:
            return df

        # Filter active bonds only
        active = df[~df['Maturado']].copy()

        if active.empty:
            return pd.DataFrame()

        # Group by year-month of maturity
        active['Mês Vencimento'] = pd.to_datetime(active['Vencimento']).dt.to_period('M')

        schedule = active.groupby('Mês Vencimento').agg({
            'Valor Atual': 'sum',
            'Título': 'count'
        }).reset_index()

        schedule.columns = ['Mês', 'Valor a Vencer', 'Quantidade']
        schedule = schedule.sort_values('Mês')

        return schedule

    def to_dict(self) -> Dict:
        """Export bond portfolio to dictionary format"""
        return {
            'positions': self.get_current_values().to_dict('records'),
            'summary': self.get_portfolio_summary(),
            'allocation_by_type': self.get_allocation_by_type().to_dict('records'),
            'allocation_by_indexer': self.get_allocation_by_indexer().to_dict('records'),
            'maturity_schedule': self.get_maturity_schedule().to_dict('records')
        }


def test_bond_portfolio():
    """Test bond portfolio calculator"""
    print("Testing Bond Portfolio Calculator")
    print("=" * 80)

    # Initialize portfolio
    portfolio = BondPortfolio()

    # Get current values
    print("\n1. Current Bond Holdings:")
    print("-" * 80)
    current = portfolio.get_current_values()
    if not current.empty:
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', 200)
        print(current.to_string())
    else:
        print("   No bonds found")

    # Get summary
    print("\n2. Bond Portfolio Summary:")
    print("-" * 80)
    summary = portfolio.get_portfolio_summary()
    for key, value in summary.items():
        if 'pct' in key or 'return' in key:
            print(f"   {key}: {value:.2f}%")
        elif isinstance(value, float):
            print(f"   {key}: R$ {value:,.2f}")
        else:
            print(f"   {key}: {value}")

    # Allocation by type
    print("\n3. Allocation by Bond Type:")
    print("-" * 80)
    by_type = portfolio.get_allocation_by_type()
    if not by_type.empty:
        print(by_type.to_string())

    # Allocation by indexer
    print("\n4. Allocation by Indexer:")
    print("-" * 80)
    by_indexer = portfolio.get_allocation_by_indexer()
    if not by_indexer.empty:
        print(by_indexer.to_string())

    # Maturity schedule
    print("\n5. Maturity Schedule:")
    print("-" * 80)
    schedule = portfolio.get_maturity_schedule()
    if not schedule.empty:
        print(schedule.to_string())

    print("\n" + "=" * 80)


if __name__ == '__main__':
    test_bond_portfolio()
