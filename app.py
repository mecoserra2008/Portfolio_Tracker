"""
Flask API for Portfolio Tracker
Serves portfolio data to the Apoena Wealth dashboard
"""

from flask import Flask, jsonify, request
from flask_cors import CORS
from src.portfolio_aggregator import PortfolioAggregator
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests from the website

# Initialize portfolio aggregator
portfolio = None


def get_portfolio():
    """Lazy load portfolio aggregator"""
    global portfolio
    if portfolio is None:
        portfolio = PortfolioAggregator()
    return portfolio


@app.route('/')
def index():
    """API root endpoint"""
    return jsonify({
        'name': 'Apoena Wealth Portfolio Tracker API',
        'version': '3.0.0',
        'features': [
            'Real-time portfolio tracking',
            'Historical performance analysis',
            'Risk metrics calculation',
            'Benchmark comparison',
            'Multi-asset support (stocks, crypto, bonds)',
            'Fund accounting with NAV tracking',
            'Investor stake management',
            'Management and performance fee calculation',
            'Monthly performance heatmaps',
            'Cumulative returns comparison',
            'Alpha measurement and tracking'
        ],
        'endpoints': {
            # Portfolio endpoints
            '/api/portfolio/summary': 'Get consolidated portfolio summary',
            '/api/portfolio/positions': 'Get all positions',
            '/api/portfolio/stocks': 'Get stock portfolio data',
            '/api/portfolio/crypto': 'Get crypto portfolio data',
            '/api/portfolio/bonds': 'Get bond portfolio data',
            '/api/portfolio/top-performers': 'Get top performing assets',
            '/api/portfolio/allocation': 'Get allocation chart data',
            '/api/portfolio/report': 'Get complete portfolio report',

            # Historical performance endpoints
            '/api/portfolio/historical': 'Get historical portfolio performance (params: period, start_date, end_date)',
            '/api/portfolio/comparison': 'Compare portfolio to benchmark (params: benchmark, start_date, end_date)',

            # Historical data management
            '/api/historical/initialize': 'Initialize historical data (POST: start_date, batch_days)',
            '/api/historical/stats': 'Get historical database statistics',

            # Fund accounting endpoints
            '/api/fund/nav': 'Get fund NAV (params: as_of_date)',
            '/api/fund/investors': 'Get investor positions and stakes (params: as_of_date)',
            '/api/fund/fees/calculate': 'Calculate fees for period (POST: period_start, period_end)',
            '/api/fund/fees/summary': 'Get fee summary (params: start_date, end_date)',
            '/api/fund/cash/deposit': 'Record cash deposit (POST: date, investor_id, investor_name, amount, currency)',
            '/api/fund/cash/withdrawal': 'Record cash withdrawal (POST: date, investor_id, investor_name, amount, currency)',

            # Performance analytics endpoints
            '/api/analytics/heatmap': 'Get monthly performance heatmap (params: start_date, end_date, format)',
            '/api/analytics/cumulative-returns': 'Compare cumulative returns (params: symbols, start_date, end_date)',
            '/api/analytics/alpha': 'Get alpha analysis (params: benchmark, start_date, end_date)',
            '/api/analytics/dashboard': 'Get complete analytics dashboard (params: symbols, benchmark)',

            # System
            '/health': 'Health check'
        }
    })


@app.route('/api/portfolio/summary')
def get_summary():
    """Get consolidated portfolio summary"""
    try:
        base_currency = request.args.get('currency', 'BRL')
        p = get_portfolio()
        summary = p.get_consolidated_summary(base_currency=base_currency)
        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/positions')
def get_positions():
    """Get all positions across all asset types"""
    try:
        p = get_portfolio()
        positions = p.get_all_positions()
        return jsonify({
            'success': True,
            'data': positions,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/stocks')
def get_stocks():
    """Get stock portfolio data"""
    try:
        p = get_portfolio()
        stock_data = {
            'summary': p.stock_portfolio.get_portfolio_summary(),
            'positions': p.stock_portfolio.get_current_values().to_dict('records'),
            'transactions': p.stock_portfolio.get_transactions_history().to_dict('records')
        }
        return jsonify({
            'success': True,
            'data': stock_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/crypto')
def get_crypto():
    """Get crypto portfolio data"""
    try:
        currency = request.args.get('currency', 'BRL')
        p = get_portfolio()
        crypto_data = {
            'summary': p.crypto_portfolio.get_portfolio_summary(currency=currency),
            'positions': p.crypto_portfolio.get_current_values(currency=currency).to_dict('records'),
            'allocation': p.crypto_portfolio.get_allocation().to_dict('records'),
            'transactions': p.crypto_portfolio.get_transactions_history().to_dict('records')
        }
        return jsonify({
            'success': True,
            'data': crypto_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/bonds')
def get_bonds():
    """Get bond portfolio data"""
    try:
        p = get_portfolio()
        bond_data = {
            'summary': p.bond_portfolio.get_portfolio_summary(),
            'positions': p.bond_portfolio.get_current_values().to_dict('records'),
            'allocation_by_type': p.bond_portfolio.get_allocation_by_type().to_dict('records'),
            'allocation_by_indexer': p.bond_portfolio.get_allocation_by_indexer().to_dict('records'),
            'maturity_schedule': p.bond_portfolio.get_maturity_schedule().to_dict('records')
        }
        return jsonify({
            'success': True,
            'data': bond_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/top-performers')
def get_top_performers():
    """Get top performing assets"""
    try:
        n = int(request.args.get('limit', 10))
        p = get_portfolio()
        performers = p.get_top_performers(n=n).to_dict('records')
        return jsonify({
            'success': True,
            'data': performers,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/allocation')
def get_allocation():
    """Get allocation chart data"""
    try:
        p = get_portfolio()
        allocation = p.get_allocation_chart_data()
        return jsonify({
            'success': True,
            'data': allocation,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/report')
def get_report():
    """Get complete portfolio report"""
    try:
        p = get_portfolio()
        report = p.export_complete_report()
        return jsonify({
            'success': True,
            'data': report,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/historical')
def get_historical_performance():
    """Get historical portfolio performance"""
    try:
        period = request.args.get('period', '1Y')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        p = get_portfolio()
        history = p.get_historical_performance(
            start_date=start_date,
            end_date=end_date,
            period=period
        )

        return jsonify({
            'success': True,
            'data': history,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/portfolio/comparison')
def get_benchmark_comparison():
    """Get portfolio comparison to benchmark"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        benchmark = request.args.get('benchmark', '^BVSP')

        p = get_portfolio()
        comparison = p.get_performance_comparison(
            start_date=start_date,
            end_date=end_date,
            benchmark=benchmark
        )

        return jsonify({
            'success': True,
            'data': comparison,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/historical/initialize', methods=['POST'])
def initialize_historical_data():
    """Initialize historical data for all portfolio assets"""
    try:
        data = request.get_json() or {}
        start_date = data.get('start_date', '2020-01-01')
        batch_days = data.get('batch_days', 90)

        p = get_portfolio()
        stats = p.initialize_historical_data(
            start_date=start_date,
            batch_days=batch_days
        )

        return jsonify({
            'success': True,
            'data': stats,
            'message': 'Historical data initialization complete',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/historical/stats')
def get_historical_stats():
    """Get statistics about stored historical data"""
    try:
        p = get_portfolio()
        stats = p.historical_manager.get_database_stats()

        return jsonify({
            'success': True,
            'data': stats,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== Fund Accounting Endpoints =====

@app.route('/api/fund/nav')
def get_fund_nav():
    """Get fund NAV"""
    try:
        as_of_date = request.args.get('as_of_date')
        p = get_portfolio()
        nav_data = p.get_fund_nav(as_of_date)
        return jsonify({
            'success': True,
            'data': nav_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fund/investors')
def get_investors():
    """Get investor positions and stakes"""
    try:
        as_of_date = request.args.get('as_of_date')
        p = get_portfolio()
        investors_data = p.get_investor_positions(as_of_date)
        return jsonify({
            'success': True,
            'data': investors_data,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fund/fees/calculate', methods=['POST'])
def calculate_fees():
    """Calculate fees for a period"""
    try:
        data = request.get_json() or {}
        period_start = data.get('period_start')
        period_end = data.get('period_end')
        calc_management = data.get('calculate_management', True)
        calc_performance = data.get('calculate_performance', True)

        if not period_start or not period_end:
            return jsonify({
                'success': False,
                'error': 'period_start and period_end are required'
            }), 400

        p = get_portfolio()
        fees = p.calculate_period_fees(
            period_start,
            period_end,
            calc_management,
            calc_performance
        )

        return jsonify({
            'success': True,
            'data': fees,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fund/fees/summary')
def get_fees_summary():
    """Get fee summary"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        p = get_portfolio()
        summary = p.get_fee_summary(start_date, end_date)
        return jsonify({
            'success': True,
            'data': summary,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fund/cash/deposit', methods=['POST'])
def add_deposit():
    """Record a cash deposit"""
    try:
        data = request.get_json() or {}
        date = data.get('date')
        investor_id = data.get('investor_id')
        investor_name = data.get('investor_name')
        amount = data.get('amount')
        currency = data.get('currency', 'BRL')
        description = data.get('description', '')

        if not all([date, investor_id, investor_name, amount]):
            return jsonify({
                'success': False,
                'error': 'date, investor_id, investor_name, and amount are required'
            }), 400

        p = get_portfolio()
        p.fund_accounting.cash_manager.add_transaction(
            date=date,
            investor_id=investor_id,
            investor_name=investor_name,
            transaction_type='deposit',
            amount=float(amount),
            currency=currency,
            description=description
        )

        return jsonify({
            'success': True,
            'message': 'Deposit recorded successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/fund/cash/withdrawal', methods=['POST'])
def add_withdrawal():
    """Record a cash withdrawal"""
    try:
        data = request.get_json() or {}
        date = data.get('date')
        investor_id = data.get('investor_id')
        investor_name = data.get('investor_name')
        amount = data.get('amount')
        currency = data.get('currency', 'BRL')
        description = data.get('description', '')

        if not all([date, investor_id, investor_name, amount]):
            return jsonify({
                'success': False,
                'error': 'date, investor_id, investor_name, and amount are required'
            }), 400

        p = get_portfolio()
        p.fund_accounting.cash_manager.add_transaction(
            date=date,
            investor_id=investor_id,
            investor_name=investor_name,
            transaction_type='withdrawal',
            amount=float(amount),
            currency=currency,
            description=description
        )

        return jsonify({
            'success': True,
            'message': 'Withdrawal recorded successfully',
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


# ===== Performance Analytics Endpoints =====

@app.route('/api/analytics/heatmap')
def get_heatmap():
    """Get monthly performance heatmap"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        format_type = request.args.get('format', 'json')  # 'json' or 'html'

        p = get_portfolio()
        fig = p.get_monthly_performance_heatmap(start_date, end_date, chart_type='plotly')

        if fig is None:
            return jsonify({
                'success': False,
                'error': 'No data available for heatmap'
            }), 404

        if format_type == 'html':
            html = fig.to_html(full_html=True, include_plotlyjs='cdn')
            return html, 200, {'Content-Type': 'text/html'}
        else:
            return jsonify({
                'success': True,
                'data': fig.to_json(),
                'timestamp': datetime.now().isoformat()
            })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/cumulative-returns')
def get_cumulative_returns():
    """Get cumulative returns comparison"""
    try:
        symbols_str = request.args.get('symbols', '')
        symbols = [s.strip() for s in symbols_str.split(',') if s.strip()]
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        if not symbols:
            return jsonify({
                'success': False,
                'error': 'At least one symbol is required'
            }), 400

        p = get_portfolio()
        result = p.get_cumulative_returns_comparison(
            symbols,
            start_date=start_date,
            end_date=end_date
        )

        # Convert chart to JSON
        if result.get('chart'):
            result['chart'] = result['chart'].to_json()

        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/alpha')
def get_alpha():
    """Get alpha analysis"""
    try:
        benchmark = request.args.get('benchmark', '^BVSP')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        p = get_portfolio()
        result = p.get_alpha_analysis(benchmark, start_date, end_date)

        # Convert chart to JSON
        if result.get('chart'):
            result['chart'] = result['chart'].to_json()

        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/analytics/dashboard')
def get_analytics_dashboard():
    """Get complete analytics dashboard"""
    try:
        symbols_str = request.args.get('symbols', '')
        symbols = [s.strip() for s in symbols_str.split(',') if s.strip()] if symbols_str else None
        benchmark = request.args.get('benchmark', '^BVSP')

        p = get_portfolio()
        figures = p.generate_analytics_dashboard(symbols, benchmark_symbol=benchmark)

        # Convert figures to JSON
        result = {}
        for key, fig in figures.items():
            if fig:
                result[key] = fig.to_json()

        return jsonify({
            'success': True,
            'data': result,
            'timestamp': datetime.now().isoformat()
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat()
    })


if __name__ == '__main__':
    # Development server
    app.run(debug=True, host='0.0.0.0', port=5000)
