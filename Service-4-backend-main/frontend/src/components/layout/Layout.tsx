import React, { useState } from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { useAuth } from '../../contexts/AuthContext';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const { user, logout } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const handleLogout = async () => {
    try {
      await logout();
      navigate('/login');
    } catch (error) {
      console.error('Logout failed:', error);
    }
  };

  const isActive = (path: string) => {
    return location.pathname.startsWith(path);
  };

  return (
    <div className="container-fluid">
      <div className="row">
        {/* Sidebar */}
        <nav className={`col-md-3 col-lg-2 d-md-block sidebar collapse ${sidebarOpen ? 'show' : ''}`}>
          <div className="position-sticky pt-3">
            <div className="text-center mb-4">
              <h4 className="text-white">GST Billing</h4>
              <small className="text-white-50">{user?.business_name}</small>
            </div>
            
            <ul className="nav flex-column">
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/dashboard') ? 'active' : ''}`} 
                  to="/dashboard"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-tachometer-alt"></i> Dashboard
                </Link>
              </li>
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/customers') ? 'active' : ''}`} 
                  to="/customers"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-users"></i> Customers
                </Link>
              </li>
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/products') ? 'active' : ''}`} 
                  to="/products"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-box"></i> Products Catalog
                </Link>
              </li>
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/inventory') ? 'active' : ''}`} 
                  to="/inventory"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-warehouse"></i> Inventory Management
                </Link>
              </li>
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/shop') ? 'active' : ''}`} 
                  to="/products"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-shopping-bag"></i> Shop
                </Link>
              </li>
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/invoices') ? 'active' : ''}`} 
                  to="/invoices"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-file-invoice"></i> Invoices
                </Link>
              </li>
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/gst') ? 'active' : ''}`} 
                  to="/gst"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-receipt"></i> GST Reports
                </Link>
              </li>
              <li className="nav-item">
                <Link 
                  className={`nav-link ${isActive('/reports') ? 'active' : ''}`} 
                  to="/reports"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-chart-bar"></i> Reports
                </Link>
              </li>
            </ul>
            
            <hr className="text-white-50" />
            
            <ul className="nav flex-column">
              <li className="nav-item">
                <Link 
                  className="nav-link" 
                  to="/profile"
                  onClick={() => setSidebarOpen(false)}
                >
                  <i className="fas fa-user-cog"></i> Profile
                </Link>
              </li>
              <li className="nav-item">
                <button 
                  className="nav-link btn btn-link text-start w-100" 
                  onClick={handleLogout}
                >
                  <i className="fas fa-sign-out-alt"></i> Logout
                </button>
              </li>
            </ul>
          </div>
        </nav>
        
        {/* Main content */}
        <main className="col-md-9 ms-sm-auto col-lg-10 px-md-4 main-content">
          {/* Top navbar */}
          <nav className="navbar navbar-expand-lg navbar-light bg-white shadow-sm rounded mb-4">
            <div className="container-fluid">
              <button 
                className="navbar-toggler d-md-none" 
                type="button" 
                onClick={() => setSidebarOpen(!sidebarOpen)}
              >
                <span className="navbar-toggler-icon"></span>
              </button>
              
              <div className="navbar-nav ms-auto">
                <div className="nav-item dropdown">
                  <a className="nav-link dropdown-toggle" href="#" id="navbarDropdown" role="button" data-bs-toggle="dropdown">
                    <i className="fas fa-user-circle"></i> {user?.username}
                  </a>
                  <ul className="dropdown-menu">
                    <li><Link className="dropdown-item" to="/profile">Profile</Link></li>
                    <li><hr className="dropdown-divider" /></li>
                    <li><button className="dropdown-item" onClick={handleLogout}>Logout</button></li>
                  </ul>
                </div>
              </div>
            </div>
          </nav>
          
          {/* Page content */}
          {children}
        </main>
      </div>
    </div>
  );
};

export default Layout;
