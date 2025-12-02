import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { DashboardStats } from '../../types';
import { mockApiService as apiService } from '../../services/mockApi';

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    const fetchDashboardData = async () => {
      try {
        const data = await apiService.getDashboardStats();
        setStats(data);
      } catch (error: any) {
        setError(error.message || 'Failed to load dashboard data');
      } finally {
        setLoading(false);
      }
    };

    fetchDashboardData();
  }, []);

  if (loading) {
    return (
      <div className="loading-spinner">
        <div className="spinner-border text-primary" role="status">
          <span className="visually-hidden">Loading...</span>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="alert alert-danger" role="alert">
        <i className="fas fa-exclamation-triangle me-2"></i>
        {error}
      </div>
    );
  }

  if (!stats) {
    return null;
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="h3 mb-0">
          <i className="fas fa-tachometer-alt me-2"></i>
          Dashboard
        </h1>
        <div>
          <Link to="/invoices/new" className="btn btn-primary me-2">
            <i className="fas fa-plus me-1"></i>New Invoice
          </Link>
          <Link to="/customers/new" className="btn btn-outline-primary">
            <i className="fas fa-user-plus me-1"></i>Add Customer
          </Link>
        </div>
      </div>

      {/* Statistics Cards */}
      <div className="row mb-4">
        <div className="col-xl-3 col-md-6 mb-4">
          <div className="stats-card">
            <div className="d-flex justify-content-between">
              <div>
                <h3 className="text-white">₹{stats.monthly_sales.toLocaleString()}</h3>
                <p className="text-white-50 mb-0">Monthly Sales</p>
              </div>
              <div className="align-self-center">
                <i className="fas fa-chart-line fa-2x text-white-50"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-xl-3 col-md-6 mb-4">
          <div className="stats-card">
            <div className="d-flex justify-content-between">
              <div>
                <h3 className="text-white">{stats.total_invoices}</h3>
                <p className="text-white-50 mb-0">Total Invoices</p>
              </div>
              <div className="align-self-center">
                <i className="fas fa-file-invoice fa-2x text-white-50"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-xl-3 col-md-6 mb-4">
          <div className="stats-card">
            <div className="d-flex justify-content-between">
              <div>
                <h3 className="text-white">{stats.total_products}</h3>
                <p className="text-white-50 mb-0">Products</p>
              </div>
              <div className="align-self-center">
                <i className="fas fa-box fa-2x text-white-50"></i>
              </div>
            </div>
          </div>
        </div>
        
        <div className="col-xl-3 col-md-6 mb-4">
          <div className="stats-card">
            <div className="d-flex justify-content-between">
              <div>
                <h3 className="text-white">{stats.total_customers}</h3>
                <p className="text-white-50 mb-0">Customers</p>
              </div>
              <div className="align-self-center">
                <i className="fas fa-users fa-2x text-white-50"></i>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="row">
        {/* Recent Invoices */}
        <div className="col-lg-8 mb-4">
          <div className="card">
            <div className="card-header d-flex justify-content-between align-items-center">
              <h5 className="mb-0">
                <i className="fas fa-clock me-2"></i>
                Recent Invoices
              </h5>
              <Link to="/invoices" className="btn btn-sm btn-outline-primary">
                View All
              </Link>
            </div>
            <div className="card-body">
              {stats.recent_invoices.length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-hover">
                    <thead>
                      <tr>
                        <th>Invoice #</th>
                        <th>Customer</th>
                        <th>Date</th>
                        <th>Amount</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.recent_invoices.map((invoice) => (
                        <tr key={invoice.id}>
                          <td>
                            <Link to={`/invoices/${invoice.id}`} className="text-decoration-none">
                              {invoice.invoice_number}
                            </Link>
                          </td>
                          <td>{invoice.customer?.name}</td>
                          <td>{new Date(invoice.invoice_date).toLocaleDateString()}</td>
                          <td>₹{invoice.total_amount.toLocaleString()}</td>
                          <td>
                            <span className={`badge bg-${invoice.status === 'paid' ? 'success' : 'warning'}`}>
                              {invoice.status}
                            </span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-muted text-center mb-0">No recent invoices</p>
              )}
            </div>
          </div>
        </div>

        {/* Low Stock Alerts */}
        <div className="col-lg-4 mb-4">
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="fas fa-exclamation-triangle me-2 text-warning"></i>
                Low Stock Alerts
              </h5>
            </div>
            <div className="card-body">
              {stats.low_stock_products.length > 0 ? (
                <div className="list-group list-group-flush">
                  {stats.low_stock_products.map((product) => (
                    <div key={product.id} className="list-group-item d-flex justify-content-between align-items-center">
                      <div>
                        <h6 className="mb-1">{product.name}</h6>
                        <small className="text-muted">SKU: {product.sku}</small>
                      </div>
                      <span className="badge bg-danger rounded-pill">
                        {product.stock_quantity} {product.unit}
                      </span>
                    </div>
                  ))}
                </div>
              ) : (
                <p className="text-muted text-center mb-0">No low stock alerts</p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Top Selling Products */}
      <div className="row">
        <div className="col-12">
          <div className="card">
            <div className="card-header">
              <h5 className="mb-0">
                <i className="fas fa-star me-2 text-warning"></i>
                Top Selling Products
              </h5>
            </div>
            <div className="card-body">
              {stats.top_selling_products.length > 0 ? (
                <div className="table-responsive">
                  <table className="table">
                    <thead>
                      <tr>
                        <th>Product</th>
                        <th>SKU</th>
                        <th>Price</th>
                        <th>Stock</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {stats.top_selling_products.map((product) => (
                        <tr key={product.id}>
                          <td>
                            <Link to={`/products/${product.id}`} className="text-decoration-none">
                              {product.name}
                            </Link>
                          </td>
                          <td>{product.sku}</td>
                          <td>₹{product.price.toLocaleString()}</td>
                          <td>
                            <span className={`badge bg-${product.stock_quantity > (product.min_stock_level || 0) ? 'success' : 'danger'}`}>
                              {product.stock_quantity} {product.unit}
                            </span>
                          </td>
                          <td>
                            <Link to={`/products/${product.id}/edit`} className="btn btn-sm btn-outline-primary">
                              <i className="fas fa-edit"></i>
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-muted text-center mb-0">No products data available</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Dashboard;
