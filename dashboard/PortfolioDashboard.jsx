/**
 * Portfolio Dashboard Component for Apoena Wealth
 * Displays comprehensive portfolio tracking with stocks, crypto, and bonds
 */

import React, { useState, useEffect } from 'react';
import {
  PieChart, Pie, Cell, BarChart, Bar, LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

// Configuration
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:5000/api';
const COLORS = {
  primary: '#0A4D3C',
  secondary: '#10B981',
  accent: '#34D399',
  gold: '#D4AF37',
  red: '#EF4444',
  gray: '#6B7280'
};

const CHART_COLORS = ['#0A4D3C', '#10B981', '#34D399', '#D4AF37', '#60A5FA', '#F59E0B'];


// Utility function to format currency
const formatCurrency = (value, currency = 'BRL') => {
  return new Intl.NumberFormat('pt-BR', {
    style: 'currency',
    currency: currency
  }).format(value);
};

// Utility function to format percentage
const formatPercent = (value) => {
  const formatted = value.toFixed(2);
  return value >= 0 ? `+${formatted}%` : `${formatted}%`;
};


/**
 * Summary Card Component
 */
const SummaryCard = ({ title, value, subValue, trend, icon }) => (
  <div className="bg-white p-6 rounded-lg shadow-md hover:shadow-lg transition-shadow">
    <div className="flex items-center justify-between mb-2">
      <h3 className="text-sm font-medium text-gray-600">{title}</h3>
      {icon && <span className="text-2xl">{icon}</span>}
    </div>
    <div className="text-3xl font-bold text-gray-900 mb-1">{value}</div>
    {subValue && (
      <div className={`text-sm ${trend >= 0 ? 'text-green-600' : 'text-red-600'}`}>
        {subValue}
      </div>
    )}
  </div>
);


/**
 * Position Table Component
 */
const PositionTable = ({ positions, type }) => {
  if (!positions || positions.length === 0) {
    return <div className="text-gray-500 text-center py-8">No positions found</div>;
  }

  const renderStockRow = (pos, idx) => (
    <tr key={idx} className="hover:bg-gray-50">
      <td className="px-4 py-3 border-b">{pos.Symbol}</td>
      <td className="px-4 py-3 border-b text-right">{pos.Quantity.toFixed(2)}</td>
      <td className="px-4 py-3 border-b text-right">{formatCurrency(pos['Avg Cost'])}</td>
      <td className="px-4 py-3 border-b text-right">{formatCurrency(pos['Current Price'])}</td>
      <td className="px-4 py-3 border-b text-right font-semibold">{formatCurrency(pos['Market Value'])}</td>
      <td className={`px-4 py-3 border-b text-right font-semibold ${pos['Unrealized P&L'] >= 0 ? 'text-green-600' : 'text-red-600'}`}>
        {formatPercent(pos['Unrealized P&L %'])}
      </td>
    </tr>
  );

  const renderCryptoRow = (pos, idx) => (
    <tr key={idx} className="hover:bg-gray-50">
      <td className="px-4 py-3 border-b">{pos.Symbol}</td>
      <td className="px-4 py-3 border-b text-right">{pos.Quantity.toFixed(6)}</td>
      <td className="px-4 py-3 border-b text-right">{formatCurrency(pos['Avg Cost'])}</td>
      <td className="px-4 py-3 border-b text-right">{formatCurrency(pos['Current Price'])}</td>
      <td className="px-4 py-3 border-b text-right font-semibold">{formatCurrency(pos['Market Value'])}</td>
      <td className={`px-4 py-3 border-b text-right font-semibold ${pos['Total P&L'] >= 0 ? 'text-green-600' : 'text-red-600'}`}>
        {formatPercent(pos['Total P&L %'])}
      </td>
    </tr>
  );

  const renderBondRow = (pos, idx) => (
    <tr key={idx} className="hover:bg-gray-50">
      <td className="px-4 py-3 border-b text-sm">{pos.Título}</td>
      <td className="px-4 py-3 border-b">{pos.Indexador}</td>
      <td className="px-4 py-3 border-b text-right">{formatCurrency(pos['Valor Investido'])}</td>
      <td className="px-4 py-3 border-b text-right font-semibold">{formatCurrency(pos['Valor Atual'])}</td>
      <td className="px-4 py-3 border-b text-right">
        {pos.Vencimento ? new Date(pos.Vencimento).toLocaleDateString('pt-BR') : 'N/A'}
      </td>
      <td className={`px-4 py-3 border-b text-right font-semibold ${pos['P&L'] >= 0 ? 'text-green-600' : 'text-red-600'}`}>
        {formatPercent(pos['P&L %'])}
      </td>
    </tr>
  );

  const headers = {
    stocks: ['Symbol', 'Quantity', 'Avg Cost', 'Current Price', 'Market Value', 'P&L %'],
    crypto: ['Symbol', 'Quantity', 'Avg Cost', 'Current Price', 'Market Value', 'P&L %'],
    bonds: ['Bond', 'Indexer', 'Invested', 'Current Value', 'Maturity', 'P&L %']
  };

  const renderRow = {
    stocks: renderStockRow,
    crypto: renderCryptoRow,
    bonds: renderBondRow
  };

  return (
    <div className="overflow-x-auto">
      <table className="min-w-full bg-white">
        <thead className="bg-gray-100">
          <tr>
            {headers[type].map((header, idx) => (
              <th
                key={idx}
                className={`px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider ${
                  idx > 1 ? 'text-right' : ''
                }`}
              >
                {header}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {positions.map((pos, idx) => renderRow[type](pos, idx))}
        </tbody>
      </table>
    </div>
  );
};


/**
 * Main Portfolio Dashboard Component
 */
const PortfolioDashboard = () => {
  const [portfolioData, setPortfolioData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  // Fetch portfolio data
  useEffect(() => {
    const fetchPortfolioData = async () => {
      try {
        setLoading(true);
        const response = await fetch(`${API_BASE_URL}/portfolio/report`);
        const result = await response.json();

        if (result.success) {
          setPortfolioData(result.data);
          setError(null);
        } else {
          setError(result.error || 'Failed to fetch portfolio data');
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchPortfolioData();
    // Refresh every 5 minutes
    const interval = setInterval(fetchPortfolioData, 5 * 60 * 1000);
    return () => clearInterval(interval);
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-gray-600">Loading portfolio data...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-xl text-red-600">Error: {error}</div>
      </div>
    );
  }

  if (!portfolioData) {
    return null;
  }

  const { summary, stocks, crypto, bonds, top_performers, chart_data } = portfolioData;

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-emerald-800 to-emerald-600 text-white py-8 px-6">
        <div className="max-w-7xl mx-auto">
          <h1 className="text-4xl font-bold mb-2">Portfolio Dashboard</h1>
          <p className="text-emerald-100">Real-time portfolio tracking and analytics</p>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-6 py-8">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <SummaryCard
            title="Total Portfolio Value"
            value={formatCurrency(summary.total_portfolio_value)}
            subValue={formatPercent(summary.total_return_pct)}
            trend={summary.total_return_pct}
            icon="💼"
          />
          <SummaryCard
            title="Total P&L"
            value={formatCurrency(summary.total_pnl)}
            trend={summary.total_pnl}
            icon="📈"
          />
          <SummaryCard
            title="Stocks"
            value={formatCurrency(summary.asset_allocation.stocks.value)}
            subValue={`${summary.asset_allocation.stocks.allocation_pct.toFixed(1)}% of portfolio`}
            trend={summary.asset_allocation.stocks.return_pct}
            icon="📊"
          />
          <SummaryCard
            title="Crypto"
            value={formatCurrency(summary.asset_allocation.crypto.value)}
            subValue={`${summary.asset_allocation.crypto.allocation_pct.toFixed(1)}% of portfolio`}
            trend={summary.asset_allocation.crypto.return_pct}
            icon="₿"
          />
        </div>

        {/* Asset Allocation Chart */}
        <div className="bg-white p-6 rounded-lg shadow-md mb-8">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">Asset Allocation</h2>
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Pie Chart */}
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={chart_data.asset_allocation}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, value }) => `${name}: ${formatCurrency(value)}`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {chart_data.asset_allocation.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={CHART_COLORS[index % CHART_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCurrency(value)} />
              </PieChart>
            </ResponsiveContainer>

            {/* Bond Type Allocation */}
            {chart_data.bond_type_allocation && chart_data.bond_type_allocation.length > 0 && (
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={chart_data.bond_type_allocation}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                  <YAxis />
                  <Tooltip formatter={(value) => formatCurrency(value)} />
                  <Bar dataKey="value" fill={COLORS.primary} />
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
        </div>

        {/* Tabs */}
        <div className="mb-4">
          <nav className="flex space-x-4">
            {['overview', 'stocks', 'crypto', 'bonds'].map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 font-medium rounded-lg transition-colors ${
                  activeTab === tab
                    ? 'bg-emerald-600 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                }`}
              >
                {tab.charAt(0).toUpperCase() + tab.slice(1)}
              </button>
            ))}
          </nav>
        </div>

        {/* Tab Content */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Top Performers */}
            <div className="bg-white p-6 rounded-lg shadow-md">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Top 10 Performers</h2>
              <div className="overflow-x-auto">
                <table className="min-w-full">
                  <thead className="bg-gray-100">
                    <tr>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Asset</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase">Type</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase">Value</th>
                      <th className="px-4 py-3 text-right text-xs font-semibold text-gray-700 uppercase">P&L %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {top_performers.slice(0, 10).map((perf, idx) => (
                      <tr key={idx} className="hover:bg-gray-50">
                        <td className="px-4 py-3 border-b">{perf.Asset}</td>
                        <td className="px-4 py-3 border-b">
                          <span className="px-2 py-1 text-xs rounded-full bg-emerald-100 text-emerald-800">
                            {perf.Type}
                          </span>
                        </td>
                        <td className="px-4 py-3 border-b text-right">{formatCurrency(perf.Value)}</td>
                        <td className={`px-4 py-3 border-b text-right font-semibold ${
                          perf['P&L %'] >= 0 ? 'text-green-600' : 'text-red-600'
                        }`}>
                          {formatPercent(perf['P&L %'])}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </div>
        )}

        {activeTab === 'stocks' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Stock Portfolio</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Total Value</div>
                <div className="text-2xl font-bold">{formatCurrency(stocks.summary.total_market_value)}</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Total P&L</div>
                <div className={`text-2xl font-bold ${stocks.summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(stocks.summary.total_pnl)}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Return</div>
                <div className={`text-2xl font-bold ${stocks.summary.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(stocks.summary.total_return_pct)}
                </div>
              </div>
            </div>
            <PositionTable positions={stocks.positions} type="stocks" />
          </div>
        )}

        {activeTab === 'crypto' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Crypto Portfolio</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Total Value</div>
                <div className="text-2xl font-bold">{formatCurrency(crypto.summary.total_market_value)}</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Total P&L</div>
                <div className={`text-2xl font-bold ${crypto.summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(crypto.summary.total_pnl)}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Return</div>
                <div className={`text-2xl font-bold ${crypto.summary.total_return_pct >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatPercent(crypto.summary.total_return_pct)}
                </div>
              </div>
            </div>
            <PositionTable positions={crypto.positions} type="crypto" />
          </div>
        )}

        {activeTab === 'bonds' && (
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">Bond Portfolio</h2>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Total Value</div>
                <div className="text-2xl font-bold">{formatCurrency(bonds.summary.total_current_value)}</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Total P&L</div>
                <div className={`text-2xl font-bold ${bonds.summary.total_pnl >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(bonds.summary.total_pnl)}
                </div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Active Bonds</div>
                <div className="text-2xl font-bold">{bonds.summary.num_active_bonds}</div>
              </div>
              <div className="bg-gray-50 p-4 rounded-lg">
                <div className="text-sm text-gray-600 mb-1">Maturing in 30 days</div>
                <div className="text-2xl font-bold text-orange-600">{bonds.summary.bonds_maturing_30days}</div>
              </div>
            </div>
            <PositionTable positions={bonds.positions} type="bonds" />
          </div>
        )}

        {/* Footer */}
        <div className="mt-8 text-center text-sm text-gray-500">
          <p>Last updated: {new Date(portfolioData.generated_at).toLocaleString('pt-BR')}</p>
          <p className="mt-2">Apoena Wealth Management - Portfolio Tracker</p>
        </div>
      </div>
    </div>
  );
};

export default PortfolioDashboard;
