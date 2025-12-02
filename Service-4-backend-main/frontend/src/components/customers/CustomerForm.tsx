import React from 'react';
import { Link } from 'react-router-dom';

const CustomerForm: React.FC = () => {
  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-4">
        <h1 className="h3 mb-0">
          <i className="fas fa-user-plus me-2"></i>
          Add Customer
        </h1>
        <Link to="/customers" className="btn btn-outline-secondary">
          <i className="fas fa-arrow-left me-1"></i>Back
        </Link>
      </div>
      
      <div className="card">
        <div className="card-body text-center py-5">
          <i className="fas fa-user-plus fa-3x text-muted mb-3"></i>
          <h4>Customer Form</h4>
          <p className="text-muted">This feature will be implemented soon.</p>
          <Link to="/customers" className="btn btn-primary">
            <i className="fas fa-arrow-left me-1"></i>Back to Customers
          </Link>
        </div>
      </div>
    </div>
  );
};

export default CustomerForm;

