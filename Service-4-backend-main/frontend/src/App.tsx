import React, { useState, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Auth from './components/auth/Auth';
import Dashboard from './components/Dashboard';
import API_BASE_URL from './config/api';

// Import existing components
import Products from './components/products/Products';
import ProductForm from './components/products/ProductForm';
import ProductDetail from './components/products/ProductDetail';
import Inventory from './components/inventory/Inventory';
import Invoices from './components/invoices/Invoices';
import InvoiceForm from './components/invoices/InvoiceForm';
import InvoiceDetail from './components/invoices/InvoiceDetail';

// Import new components
import Customers from './components/customers/Customers';
import CustomerDetail from './components/customers/CustomerDetail';
import CustomerEdit from './components/customers/CustomerEdit';
import CustomerDashboard from './components/customer/CustomerDashboard';
import Orders from './components/orders/Orders';
import Reports from './components/reports/Reports';
import Sales from './components/sales/Sales';

const App: React.FC = () => {
  const [userType, setUserType] = useState<'admin' | 'customer' | null>(null);
  const [checkingAuth, setCheckingAuth] = useState(true);

  const handleLogin = (type: 'admin' | 'customer') => {
    setUserType(type);
  };

  const handleLogout = async () => {
    // Call logout endpoint to clear server session
    try {
      await fetch(`${API_BASE_URL}/auth/logout`, {
        method: 'POST',
        credentials: 'include'
      });
    } catch (error) {
      console.error('Logout request failed:', error);
      // Continue with logout even if request fails
    }
    
    // Clear local state
    setUserType(null);
  };

  // Check authentication with backend on app load
  useEffect(() => {
    const checkAuth = async () => {
      try {
        // Try admin check first
        const adminCheck = await fetch(`${API_BASE_URL}/auth/check`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (adminCheck.ok) {
          const adminData = await adminCheck.json().catch(() => ({ authenticated: false }));
          if (adminData.authenticated) {
            setUserType('admin');
            setCheckingAuth(false);
            return;
          }
        }

        // Try customer check
        const customerCheck = await fetch(`${API_BASE_URL}/customer-auth/profile`, {
          credentials: 'include',
          headers: {
            'Content-Type': 'application/json'
          }
        });

        if (customerCheck.ok) {
          const customerData = await customerCheck.json().catch(() => ({}));
          if (customerData && !customerData.error) {
            setUserType('customer');
            setCheckingAuth(false);
            return;
          }
        }

        // No valid session found
        setUserType(null);
      } catch (error) {
        console.error('Auth check error:', error);
        setUserType(null);
      } finally {
        setCheckingAuth(false);
      }
    };

    checkAuth();
  }, []);

  return (
    <Router>
      <div className="App">
        <Routes>
          {/* Public routes */}
          <Route 
            path="/" 
            element={
              !userType ? (
                <Auth onLogin={handleLogin} />
              ) : (
                <Navigate to={
                  userType === 'customer' ? '/customer-dashboard' :
                  '/dashboard'
                } />
              )
            } 
          />
          <Route 
            path="/login" 
            element={
              !userType ? (
                <Auth onLogin={handleLogin} />
              ) : (
                <Navigate to={
                  userType === 'customer' ? '/customer-dashboard' :
                  '/dashboard'
                } />
              )
            } 
          />

          {/* Protected Admin Routes */}
          <Route 
            path="/dashboard" 
            element={
              checkingAuth ? (
                <div className="min-h-screen flex items-center justify-center">
                  <div className="text-center">
                    <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                    <p className="text-gray-600">Verifying authentication...</p>
                  </div>
                </div>
              ) : userType === 'admin' ? (
                <Dashboard onLogout={handleLogout} />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          
          {/* Products Routes */}
          <Route 
            path="/products" 
            element={
              userType === 'admin' ? (
                <Products />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/products/new" 
            element={
              userType === 'admin' ? (
                <ProductForm />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/products/:id" 
            element={
              userType === 'admin' ? (
                <ProductDetail />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/products/:id/edit" 
            element={
              userType === 'admin' ? (
                <ProductForm />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />

          {/* Inventory Routes */}
          <Route 
            path="/inventory" 
            element={
              userType === 'admin' ? (
                <Inventory />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />

          {/* Customers Routes */}
          <Route 
            path="/customers" 
            element={
              userType === 'admin' ? (
                <Customers />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/customers/:id" 
            element={
              userType === 'admin' ? (
                <CustomerDetail />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/customers/:id/edit" 
            element={
              userType === 'admin' ? (
                <CustomerEdit />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />

          {/* Orders Routes */}
          <Route 
            path="/orders" 
            element={
              userType === 'admin' ? (
                <Orders />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />

          {/* Reports Routes */}
          <Route 
            path="/reports" 
            element={
              userType === 'admin' ? (
                <Reports />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />

          {/* Sales Routes */}
          <Route 
            path="/sales" 
            element={
              userType === 'admin' ? (
                <Sales />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />

          {/* Invoices Routes */}
          <Route 
            path="/invoices" 
            element={
              userType === 'admin' ? (
                <Invoices />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/invoices/new" 
            element={
              userType === 'admin' ? (
                <InvoiceForm />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/invoices/:id" 
            element={
              userType === 'admin' ? (
                <InvoiceDetail />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />
          <Route 
            path="/invoices/:id/edit" 
            element={
              userType === 'admin' ? (
                <InvoiceForm />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />

          {/* Customer Routes */}
          <Route 
            path="/customer-dashboard" 
            element={
              userType === 'customer' ? (
                <CustomerDashboard onLogout={handleLogout} />
              ) : (
                <Navigate to="/login" />
              )
            } 
          />


          {/* Test route to check if styling is working */}
          <Route 
            path="/test" 
            element={
              <div className="min-h-screen bg-gradient-to-br from-slate-900 via-purple-900 to-slate-900 flex items-center justify-center">
                <div className="backdrop-blur-xl bg-white/10 rounded-3xl shadow-2xl border border-white/20 p-8">
                  <h1 className="text-4xl font-bold text-white mb-4">🎉 Success!</h1>
                  <p className="text-gray-300 text-lg mb-6">Tailwind CSS is working perfectly!</p>
                  <div className="flex space-x-4">
                    <button className="bg-gradient-to-r from-blue-600 to-purple-600 text-white px-6 py-3 rounded-2xl font-semibold hover:from-blue-700 hover:to-purple-700 transition-all duration-300 transform hover:scale-105 shadow-lg">
                      Beautiful Button
                    </button>
                    <button className="bg-gradient-to-r from-green-600 to-emerald-600 text-white px-6 py-3 rounded-2xl font-semibold hover:from-green-700 hover:to-emerald-700 transition-all duration-300 transform hover:scale-105 shadow-lg">
                      Another Button
                    </button>
                  </div>
                </div>
              </div>
            } 
          />

          {/* Catch all route */}
          <Route path="*" element={<Navigate to="/" />} />
        </Routes>
      </div>
    </Router>
  );
};

export default App;
