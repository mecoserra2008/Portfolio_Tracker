"""
Performance Analytics
Monthly performance heatmaps, cumulative return comparisons, and alpha calculations
"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from typing import Dict, List, Optional
from .portfolio_performance import PortfolioPerformanceCalculator


class PerformanceAnalytics:
    """
    Advanced performance analytics including heatmaps, cumulative returns, and alpha
    """

    def __init__(self, performance_calculator: PortfolioPerformanceCalculator = None):
        """
        Initialize performance analytics

        Args:
            performance_calculator: PortfolioPerformanceCalculator instance
        """
        self.performance_calculator = performance_calculator or PortfolioPerformanceCalculator()

    def calculate_monthly_returns(self, performance_df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate monthly returns from daily performance data

        Args:
            performance_df: DataFrame with daily performance data

        Returns:
            DataFrame with monthly returns
        """
        if performance_df.empty:
            return pd.DataFrame()

        df = performance_df.copy()
        df['date'] = pd.to_datetime(df['date'])
        df = df.set_index('date')

        # Resample to month-end
        monthly = df['total_value'].resample('M').last()

        # Calculate monthly returns
        monthly_returns = monthly.pct_change() * 100

        # Create DataFrame with year and month
        result = pd.DataFrame({
            'date': monthly_returns.index,
            'year': monthly_returns.index.year,
            'month': monthly_returns.index.month,
            'month_name': monthly_returns.index.strftime('%b'),
            'return_pct': monthly_returns.values
        })

        return result

    def create_monthly_returns_heatmap_plotly(
        self,
        monthly_returns: pd.DataFrame,
        title: str = 'Monthly Portfolio Returns (%)'
    ) -> go.Figure:
        """
        Create interactive monthly returns heatmap using Plotly

        Args:
            monthly_returns: DataFrame with monthly returns
            title: Chart title

        Returns:
            Plotly Figure object
        """
        if monthly_returns.empty:
            return go.Figure()

        # Pivot data for heatmap
        pivot = monthly_returns.pivot(
            index='year',
            columns='month',
            values='return_pct'
        )

        # Month names for x-axis
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']

        # Create heatmap
        fig = go.Figure(data=go.Heatmap(
            z=pivot.values,
            x=month_names,
            y=pivot.index,
            colorscale='RdYlGn',
            zmid=0,  # Center colorscale at 0
            text=np.round(pivot.values, 2),
            texttemplate='%{text}%',
            textfont={"size": 10},
            colorbar=dict(title='Return %'),
            hoverongaps=False,
            hovertemplate='Year: %{y}<br>Month: %{x}<br>Return: %{z:.2f}%<extra></extra>'
        ))

        fig.update_layout(
            title=title,
            xaxis_title='Month',
            yaxis_title='Year',
            height=400 + len(pivot) * 30,  # Dynamic height based on years
            font=dict(size=12)
        )

        return fig

    def create_monthly_returns_heatmap_seaborn(
        self,
        monthly_returns: pd.DataFrame,
        title: str = 'Monthly Portfolio Returns (%)',
        figsize: tuple = (12, 8),
        save_path: str = None
    ) -> plt.Figure:
        """
        Create monthly returns heatmap using Seaborn

        Args:
            monthly_returns: DataFrame with monthly returns
            title: Chart title
            figsize: Figure size
            save_path: Path to save figure (optional)

        Returns:
            Matplotlib Figure object
        """
        if monthly_returns.empty:
            fig, ax = plt.subplots(figsize=figsize)
            ax.text(0.5, 0.5, 'No data available', ha='center', va='center')
            return fig

        # Pivot data for heatmap
        pivot = monthly_returns.pivot(
            index='year',
            columns='month',
            values='return_pct'
        )

        # Month names for columns
        month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun',
                      'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
        pivot.columns = [month_names[i-1] for i in pivot.columns]

        # Create figure
        fig, ax = plt.subplots(figsize=figsize)

        # Create heatmap
        sns.heatmap(
            pivot,
            annot=True,
            fmt='.2f',
            cmap='RdYlGn',
            center=0,
            cbar_kws={'label': 'Return (%)'},
            linewidths=0.5,
            linecolor='gray',
            ax=ax
        )

        ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
        ax.set_xlabel('Month', fontsize=12)
        ax.set_ylabel('Year', fontsize=12)

        plt.tight_layout()

        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight')

        return fig

    def calculate_cumulative_returns(
        self,
        performance_df: pd.DataFrame,
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Calculate cumulative returns for the portfolio

        Args:
            performance_df: DataFrame with daily performance data
            normalize: If True, start at 100

        Returns:
            DataFrame with cumulative returns
        """
        if performance_df.empty:
            return pd.DataFrame()

        df = performance_df.copy()

        if normalize:
            # Normalize to 100 at start
            df['cumulative_value'] = (df['total_value'] / df['total_value'].iloc[0]) * 100
        else:
            df['cumulative_value'] = df['total_value']

        return df[['date', 'cumulative_value', 'cumulative_return']]

    def compare_cumulative_returns(
        self,
        portfolio_performance: pd.DataFrame,
        asset_symbols: List[str],
        asset_names: Dict[str, str] = None,
        normalize: bool = True
    ) -> pd.DataFrame:
        """
        Compare portfolio cumulative returns with individual assets

        Args:
            portfolio_performance: Portfolio performance DataFrame
            asset_symbols: List of asset symbols to compare
            asset_names: Dictionary mapping symbols to display names
            normalize: If True, normalize all to 100 at start

        Returns:
            DataFrame with comparison data
        """
        if portfolio_performance.empty:
            return pd.DataFrame()

        start_date = portfolio_performance['date'].min().strftime('%Y-%m-%d')
        end_date = portfolio_performance['date'].max().strftime('%Y-%m-%d')

        # Start with portfolio data
        comparison = portfolio_performance[['date', 'total_value']].copy()
        comparison = comparison.rename(columns={'total_value': 'Portfolio'})
        comparison['date'] = pd.to_datetime(comparison['date'])

        # Add each asset
        for symbol in asset_symbols:
            try:
                # Get historical data for asset
                asset_data = self.performance_calculator.historical_manager.get_historical_data(
                    symbol, start_date, end_date
                )

                if not asset_data.empty:
                    asset_name = asset_names.get(symbol, symbol) if asset_names else symbol
                    asset_data['date'] = pd.to_datetime(asset_data['date'])

                    # Merge with comparison
                    comparison = comparison.merge(
                        asset_data[['date', 'close']].rename(columns={'close': asset_name}),
                        on='date',
                        how='left'
                    )
            except Exception as e:
                print(f"Warning: Could not load data for {symbol}: {str(e)}")

        # Normalize if requested
        if normalize:
            for col in comparison.columns:
                if col != 'date':
                    comparison[col] = (comparison[col] / comparison[col].iloc[0]) * 100

        return comparison

    def create_cumulative_return_chart(
        self,
        comparison_df: pd.DataFrame,
        title: str = 'Cumulative Returns Comparison',
        height: int = 600
    ) -> go.Figure:
        """
        Create interactive cumulative return comparison chart

        Args:
            comparison_df: Comparison DataFrame
            title: Chart title
            height: Chart height

        Returns:
            Plotly Figure
        """
        if comparison_df.empty:
            return go.Figure()

        fig = go.Figure()

        # Add a line for each asset/portfolio
        for col in comparison_df.columns:
            if col != 'date':
                fig.add_trace(go.Scatter(
                    x=comparison_df['date'],
                    y=comparison_df[col],
                    mode='lines',
                    name=col,
                    line=dict(width=2 if col == 'Portfolio' else 1),
                    hovertemplate='%{y:.2f}<extra></extra>'
                ))

        fig.update_layout(
            title=title,
            xaxis_title='Date',
            yaxis_title='Indexed Value (Base = 100)',
            height=height,
            hovermode='x unified',
            legend=dict(
                orientation="v",
                yanchor="top",
                y=0.99,
                xanchor="left",
                x=0.01,
                bgcolor="rgba(255, 255, 255, 0.8)"
            )
        )

        return fig

    def calculate_alpha(
        self,
        portfolio_returns: pd.Series,
        benchmark_returns: pd.Series,
        risk_free_rate: float = 0.0
    ) -> Dict:
        """
        Calculate alpha (excess return vs benchmark)

        Args:
            portfolio_returns: Portfolio returns series
            benchmark_returns: Benchmark returns series
            risk_free_rate: Risk-free rate (annualized %)

        Returns:
            Dictionary with alpha metrics
        """
        # Align series
        aligned = pd.DataFrame({
            'portfolio': portfolio_returns,
            'benchmark': benchmark_returns
        }).dropna()

        if aligned.empty or len(aligned) < 2:
            return {}

        # Calculate metrics
        port_returns = aligned['portfolio']
        bench_returns = aligned['benchmark']

        # Excess returns
        excess_returns = port_returns - bench_returns

        # Alpha (simple): average excess return annualized
        alpha_simple = excess_returns.mean() * 252  # Annualized

        # Beta (portfolio sensitivity to benchmark)
        covariance = np.cov(port_returns, bench_returns)[0, 1]
        benchmark_variance = np.var(bench_returns)
        beta = covariance / benchmark_variance if benchmark_variance > 0 else 0

        # Jensen's Alpha: portfolio_return - (rf + beta * (benchmark_return - rf))
        port_annual_return = port_returns.mean() * 252
        bench_annual_return = bench_returns.mean() * 252
        jensens_alpha = port_annual_return - (risk_free_rate + beta * (bench_annual_return - risk_free_rate))

        # Information Ratio: alpha / tracking error
        tracking_error = excess_returns.std() * np.sqrt(252)
        information_ratio = alpha_simple / tracking_error if tracking_error > 0 else 0

        # Win rate (% of days portfolio outperformed)
        win_rate = (excess_returns > 0).sum() / len(excess_returns) * 100

        return {
            'alpha_simple': alpha_simple,
            'jensens_alpha': jensens_alpha,
            'beta': beta,
            'information_ratio': information_ratio,
            'tracking_error': tracking_error,
            'win_rate': win_rate,
            'correlation': port_returns.corr(bench_returns),
            'avg_excess_return': excess_returns.mean(),
            'total_excess_return': excess_returns.sum()
        }

    def create_alpha_visualization(
        self,
        portfolio_performance: pd.DataFrame,
        benchmark_performance: pd.DataFrame,
        title: str = 'Alpha Analysis'
    ) -> go.Figure:
        """
        Create visualization showing alpha over time

        Args:
            portfolio_performance: Portfolio performance DataFrame
            benchmark_performance: Benchmark performance DataFrame
            title: Chart title

        Returns:
            Plotly Figure with subplots
        """
        if portfolio_performance.empty or benchmark_performance.empty:
            return go.Figure()

        # Merge data
        merged = portfolio_performance[['date', 'daily_return', 'cumulative_return']].copy()
        merged['date'] = pd.to_datetime(merged['date'])

        benchmark_performance['date'] = pd.to_datetime(benchmark_performance['date'])

        merged = merged.merge(
            benchmark_performance[['date', 'benchmark_return', 'benchmark_cumulative']],
            on='date',
            how='inner'
        )

        # Calculate excess returns
        merged['excess_return'] = merged['daily_return'] - merged['benchmark_return']
        merged['cumulative_alpha'] = merged['cumulative_return'] - merged['benchmark_cumulative']

        # Create subplots
        fig = make_subplots(
            rows=2, cols=1,
            subplot_titles=(
                'Cumulative Returns (Portfolio vs Benchmark)',
                'Cumulative Alpha (Excess Return)'
            ),
            vertical_spacing=0.12,
            row_heights=[0.5, 0.5]
        )

        # Top chart: Cumulative returns
        fig.add_trace(
            go.Scatter(
                x=merged['date'],
                y=merged['cumulative_return'],
                mode='lines',
                name='Portfolio',
                line=dict(color='blue', width=2),
                hovertemplate='Portfolio: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )

        fig.add_trace(
            go.Scatter(
                x=merged['date'],
                y=merged['benchmark_cumulative'],
                mode='lines',
                name='Benchmark',
                line=dict(color='gray', width=2),
                hovertemplate='Benchmark: %{y:.2f}%<extra></extra>'
            ),
            row=1, col=1
        )

        # Bottom chart: Alpha
        colors = ['green' if x >= 0 else 'red' for x in merged['cumulative_alpha']]

        fig.add_trace(
            go.Scatter(
                x=merged['date'],
                y=merged['cumulative_alpha'],
                mode='lines',
                name='Alpha',
                line=dict(color='green', width=2),
                fill='tozeroy',
                fillcolor='rgba(0, 255, 0, 0.2)',
                hovertemplate='Alpha: %{y:.2f}%<extra></extra>'
            ),
            row=2, col=1
        )

        # Add zero line
        fig.add_hline(y=0, line_dash="dash", line_color="gray", row=2, col=1)

        fig.update_xaxes(title_text="Date", row=2, col=1)
        fig.update_yaxes(title_text="Cumulative Return (%)", row=1, col=1)
        fig.update_yaxes(title_text="Cumulative Alpha (%)", row=2, col=1)

        fig.update_layout(
            title=title,
            height=800,
            hovermode='x unified',
            showlegend=True,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        return fig

    def create_performance_dashboard(
        self,
        portfolio_performance: pd.DataFrame,
        comparison_assets: List[str] = None,
        asset_names: Dict[str, str] = None,
        benchmark_symbol: str = '^BVSP'
    ) -> Dict[str, go.Figure]:
        """
        Create comprehensive performance dashboard

        Args:
            portfolio_performance: Portfolio performance DataFrame
            comparison_assets: List of asset symbols to compare
            asset_names: Dictionary mapping symbols to names
            benchmark_symbol: Benchmark symbol for alpha calculation

        Returns:
            Dictionary of Plotly figures
        """
        figures = {}

        # 1. Monthly Returns Heatmap
        monthly_returns = self.calculate_monthly_returns(portfolio_performance)
        figures['heatmap'] = self.create_monthly_returns_heatmap_plotly(monthly_returns)

        # 2. Cumulative Returns Comparison
        if comparison_assets:
            comparison_df = self.compare_cumulative_returns(
                portfolio_performance,
                comparison_assets,
                asset_names
            )
            figures['cumulative_comparison'] = self.create_cumulative_return_chart(comparison_df)

        # 3. Alpha Analysis
        benchmark_comparison = self.performance_calculator.compare_to_benchmark(
            portfolio_performance,
            benchmark_symbol
        )

        if 'benchmark_return' in benchmark_comparison.columns:
            figures['alpha'] = self.create_alpha_visualization(
                benchmark_comparison,
                benchmark_comparison,
                title=f'Alpha Analysis vs {benchmark_symbol}'
            )

        return figures

    def export_analytics_report(
        self,
        portfolio_performance: pd.DataFrame,
        benchmark_symbol: str = '^BVSP',
        output_path: str = 'reports/performance_analytics.html'
    ) -> str:
        """
        Export complete analytics report as HTML

        Args:
            portfolio_performance: Portfolio performance DataFrame
            benchmark_symbol: Benchmark symbol
            output_path: Path to save HTML report

        Returns:
            Path to saved report
        """
        import os
        os.makedirs(os.path.dirname(output_path), exist_ok=True)

        # Generate all figures
        monthly_returns = self.calculate_monthly_returns(portfolio_performance)
        heatmap_fig = self.create_monthly_returns_heatmap_plotly(monthly_returns)

        benchmark_comparison = self.performance_calculator.compare_to_benchmark(
            portfolio_performance,
            benchmark_symbol
        )

        alpha_fig = self.create_alpha_visualization(
            benchmark_comparison,
            benchmark_comparison
        )

        # Calculate alpha metrics
        alpha_metrics = {}
        if 'daily_return' in benchmark_comparison.columns and 'benchmark_return' in benchmark_comparison.columns:
            alpha_metrics = self.calculate_alpha(
                benchmark_comparison['daily_return'],
                benchmark_comparison['benchmark_return']
            )

        # Create HTML
        html_content = f"""
        <html>
        <head>
            <title>Portfolio Performance Analytics</title>
            <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                h1 {{ color: #2c3e50; }}
                h2 {{ color: #34495e; margin-top: 40px; }}
                .metric {{ display: inline-block; margin: 10px 20px; }}
                .metric-label {{ font-weight: bold; color: #7f8c8d; }}
                .metric-value {{ font-size: 24px; color: #2c3e50; }}
                .section {{ margin-bottom: 60px; }}
            </style>
        </head>
        <body>
            <h1>Portfolio Performance Analytics Report</h1>
            <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>

            <div class="section">
                <h2>Alpha Metrics vs {benchmark_symbol}</h2>
                <div class="metric">
                    <div class="metric-label">Alpha (Simple)</div>
                    <div class="metric-value">{alpha_metrics.get('alpha_simple', 0):.2f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Jensen's Alpha</div>
                    <div class="metric-value">{alpha_metrics.get('jensens_alpha', 0):.2f}%</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Beta</div>
                    <div class="metric-value">{alpha_metrics.get('beta', 0):.2f}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Information Ratio</div>
                    <div class="metric-value">{alpha_metrics.get('information_ratio', 0):.2f}</div>
                </div>
            </div>

            <div class="section">
                <h2>Monthly Returns Heatmap</h2>
                {heatmap_fig.to_html(full_html=False, include_plotlyjs=False)}
            </div>

            <div class="section">
                <h2>Alpha Analysis</h2>
                {alpha_fig.to_html(full_html=False, include_plotlyjs=False)}
            </div>
        </body>
        </html>
        """

        with open(output_path, 'w') as f:
            f.write(html_content)

        return output_path


def test_performance_analytics():
    """Test performance analytics"""
    print("Testing Performance Analytics")
    print("=" * 60)

    # This test requires historical data
    print("\nNote: This test requires populated historical database")
    print("Run historical data initialization first")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    test_performance_analytics()
