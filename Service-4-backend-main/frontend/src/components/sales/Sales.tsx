import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import API_BASE_URL from '../../config/api';

interface Invoice {
  id: number | string;
  invoice_number: string;
  customer_id: number | string;
  customer_name: string;
  customer_email: string;
  customer_phone: string;
  invoice_date: string;
  due_date: string;
  status: string;
  subtotal: number;
  cgst_amount: number;
  sgst_amount: number;
  igst_amount: number;
  total_amount: number;
  notes: string;
  items: any[];
  order_id?: number | string;
  created_at: string;
  created_by?: string;
}

interface SalesSummary {
  total_sales: number;
  total_paid: number;
  total_pending: number;
  total_cancelled: number;
  total_purchases: number;
  total_expenses: number;
}

const Sales: React.FC = () => {
  const navigate = useNavigate();
  const [invoices, setInvoices] = useState<Invoice[]>([]);
  const [summary, setSummary] = useState<SalesSummary>({
    total_sales: 0,
    total_paid: 0,
    total_pending: 0,
    total_cancelled: 0,
    total_purchases: 0,
    total_expenses: 0
  });
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState<'all' | 'pending' | 'paid' | 'cancelled' | 'done' | 'drafts'>('all');
  const [updatingStatus, setUpdatingStatus] = useState<number | null>(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('this_month');
  const [currentPage, setCurrentPage] = useState(1);
  const [itemsPerPage, setItemsPerPage] = useState(100);
  const [selectedInvoice, setSelectedInvoice] = useState<Invoice | null>(null);
  const [showActionsMenu, setShowActionsMenu] = useState<number | null>(null);
  const [showCreateSaleModal, setShowCreateSaleModal] = useState(false);
  const [customers, setCustomers] = useState<any[]>([]);
  const [products, setProducts] = useState<any[]>([]);
  const [saleForm, setSaleForm] = useState({
    customer_id: '',
    customer_name: '',
    customer_phone: '',
    invoice_date: new Date().toISOString().split('T')[0],
    items: [] as Array<{ product_id: number; product_name: string; quantity: number; unit_price: number; gst_rate: number; total: number }>,
    notes: '',
    status: 'pending' as 'pending' | 'draft'
  });
  const [selectedProduct, setSelectedProduct] = useState<any>(null);
  const [productSearch, setProductSearch] = useState('');
  const [showProductDropdown, setShowProductDropdown] = useState(false);
  const [productsLoading, setProductsLoading] = useState(false);
  const [creatingSale, setCreatingSale] = useState(false);

  const getDateRange = () => {
    if (dateFilter === 'all') {
      return null;
    }
    
    const now = new Date();
    
    switch (dateFilter) {
      case 'this_month':
        // Include today and all of this month - be more inclusive
        const startOfMonth = new Date(now.getFullYear(), now.getMonth(), 1, 0, 0, 0, 0);
        // End date should be end of current month, or today if we're in the current month
        const endOfMonth = new Date(now.getFullYear(), now.getMonth() + 1, 0, 23, 59, 59, 999);
        // Always use end of month to include all invoices created this month
        return {
          start: startOfMonth,
          end: endOfMonth
        };
      case 'last_month':
        return {
          start: new Date(now.getFullYear(), now.getMonth() - 1, 1, 0, 0, 0, 0),
          end: new Date(now.getFullYear(), now.getMonth(), 0, 23, 59, 59, 999)
        };
      case 'this_year':
        return {
          start: new Date(now.getFullYear(), 0, 1, 0, 0, 0, 0),
          end: new Date(now.getFullYear(), 11, 31, 23, 59, 59, 999)
        };
      default:
        return null;
    }
  };

  useEffect(() => {
    fetchSalesData();
  }, [dateFilter]);

  useEffect(() => {
    if (showCreateSaleModal) {
      fetchCustomers();
      // Always fetch products when modal opens, even if we have some cached
      setProducts([]); // Clear existing products to show loading state
      fetchProducts();
      // Reset form when modal opens
      setProductSearch('');
      setShowProductDropdown(false);
    } else {
      // Reset when modal closes
      setProductSearch('');
      setShowProductDropdown(false);
      setProductsLoading(false);
    }
  }, [showCreateSaleModal]);

  const fetchCustomers = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/admin/customers`, {
        credentials: 'include'
      });
      if (response.ok) {
        const data = await response.json();
        setCustomers(data.customers || []);
      }
    } catch (error) {
      console.error('Failed to load customers:', error);
    }
  };

  const fetchProducts = async () => {
    try {
      setProductsLoading(true);
      console.log('Fetching products for sales from:', `${API_BASE_URL}/products/`);
      const response = await fetch(`${API_BASE_URL}/products/`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      console.log('Products response status:', response.status);
      const responseText = await response.text();
      console.log('Products response text (first 500 chars):', responseText.substring(0, 500));
      
      let data;
      try {
        data = JSON.parse(responseText);
      } catch (parseError) {
        console.error('Failed to parse JSON response:', parseError);
        console.error('Response text:', responseText);
        alert(`Server returned invalid JSON. Check console for details.`);
        setProducts([]);
        setProductsLoading(false);
        return;
      }
      
      console.log('Products response data:', data);
      if (response.ok) {
        if (data.success) {
          const productsList = data.products || [];
          console.log(`Loaded ${productsList.length} products for sales`);
          if (productsList.length === 0) {
            console.warn('API returned success but no products in array');
            console.warn('Full response:', data);
          }
          setProducts(productsList);
        } else {
          console.error('API returned success=false:', data.error || 'Unknown error');
          alert(`Failed to load products: ${data.error || 'Unknown error'}`);
          setProducts([]);
        }
      } else {
        console.error('HTTP error response:', response.status, data);
        alert(`Failed to load products: ${data.error || response.statusText}`);
        setProducts([]);
      }
    } catch (error: any) {
      console.error('Failed to load products for sales:', error);
      alert(`Error loading products: ${error.message || 'Network error'}`);
      setProducts([]);
    } finally {
      setProductsLoading(false);
    }
  };

  const fetchSalesData = async () => {
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE_URL}/invoices/`, {
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });
      
      if (response.ok) {
        const data = await response.json();
        console.log('Fetched invoices response:', data);
        const invoicesData = (data.invoices || []).map((inv: any) => {
          // Ensure ID is always set and is a string
          // Try multiple possible ID fields
          const invoiceId = inv.id || inv._id || inv.invoice_id || null;
          
          if (!invoiceId) {
            console.warn('Invoice missing ID:', inv);
            console.warn('Available fields:', Object.keys(inv));
          }
          
          // Ensure created_at is set (use invoice_date as fallback)
          const createdAt = inv.created_at || inv.invoice_date || new Date().toISOString();
          
          return {
            ...inv,
            id: invoiceId ? String(invoiceId) : null,
            created_at: createdAt
          };
        }).filter((inv: any) => inv.id); // Filter out invoices without IDs
        
        console.log('Loaded invoices:', invoicesData.length);
        if (invoicesData.length > 0) {
          console.log('Sample invoice:', invoicesData[0]);
          console.log('All invoices:', invoicesData.map((inv: any) => ({ 
            number: inv.invoice_number, 
            created_at: inv.created_at,
            invoice_date: inv.invoice_date,
            status: inv.status,
            id: inv.id
          })));
        } else {
          console.warn('No invoices loaded! Check backend logs.');
        }
        setInvoices(invoicesData);
        
        // Calculate summary based on date filter
        const dateRange = getDateRange();
        let filteredForSummary = invoicesData;
        
        if (dateRange) {
          filteredForSummary = invoicesData.filter((inv: Invoice) => {
            const invoiceDate = new Date(inv.created_at);
            return invoiceDate >= dateRange.start && invoiceDate <= dateRange.end;
          });
        }
        
        const totalSales = filteredForSummary.reduce((sum: number, inv: Invoice) => sum + inv.total_amount, 0);
        const totalPaid = filteredForSummary
          .filter((inv: Invoice) => inv.status.toLowerCase() === 'paid')
          .reduce((sum: number, inv: Invoice) => sum + inv.total_amount, 0);
        const totalPending = filteredForSummary
          .filter((inv: Invoice) => inv.status.toLowerCase() === 'pending')
          .reduce((sum: number, inv: Invoice) => sum + inv.total_amount, 0);
        const totalCancelled = filteredForSummary
          .filter((inv: Invoice) => inv.status.toLowerCase() === 'cancelled')
          .reduce((sum: number, inv: Invoice) => sum + inv.total_amount, 0);
        const totalDone = filteredForSummary
          .filter((inv: Invoice) => inv.status.toLowerCase() === 'done')
          .reduce((sum: number, inv: Invoice) => sum + inv.total_amount, 0);
        
        setSummary({
          total_sales: totalSales,
          total_paid: totalPaid,
          total_pending: totalPending,
          total_cancelled: totalCancelled,
          total_purchases: 0, // Can be added later if purchase tracking is implemented
          total_expenses: 0 // Can be added later if expense tracking is implemented
        });
      }
    } catch (error) {
      console.error('Failed to load sales data:', error);
    } finally {
      setLoading(false);
    }
  };

  const formatCurrency = (amount: number) => {
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2
    }).format(amount);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-IN', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffInSeconds = Math.floor((now.getTime() - date.getTime()) / 1000);
    
    if (diffInSeconds < 60) return `${diffInSeconds} seconds ago`;
    if (diffInSeconds < 3600) return `${Math.floor(diffInSeconds / 60)} minutes ago`;
    if (diffInSeconds < 86400) return `${Math.floor(diffInSeconds / 3600)} hours ago`;
    if (diffInSeconds < 2592000) return `${Math.floor(diffInSeconds / 86400)} days ago`;
    return formatDate(dateString);
  };

  const getStatusColor = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return 'bg-yellow-100 text-yellow-800 border-yellow-200';
      case 'paid':
        return 'bg-green-100 text-green-800 border-green-200';
      case 'cancelled':
        return 'bg-gray-100 text-gray-800 border-gray-200';
      case 'done':
        return 'bg-purple-100 text-purple-800 border-purple-200';
      case 'draft':
        return 'bg-blue-100 text-blue-800 border-blue-200';
      default:
        return 'bg-gray-100 text-gray-800 border-gray-200';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status.toLowerCase()) {
      case 'pending':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-12a1 1 0 10-2 0v4a1 1 0 00.293.707l2.828 2.829a1 1 0 101.415-1.415L11 9.586V6z" clipRule="evenodd" />
          </svg>
        );
      case 'paid':
        return (
          <svg className="w-4 h-4" fill="currentColor" viewBox="0 0 20 20">
            <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
          </svg>
        );
      default:
        return null;
    }
  };

  const getPaymentMode = (invoice: Invoice): string => {
    // Since payment mode is not in the current model, we'll use a default
    // This can be enhanced when payment tracking is added
    return invoice.status.toLowerCase() === 'paid' ? 'Online' : 'Pending';
  };

  const filteredInvoices = invoices.filter(invoice => {
    // Filter by tab
    if (activeTab === 'all') {
      // Show all except drafts
      if (invoice.status && invoice.status.toLowerCase() === 'draft') return false;
    } else if (activeTab === 'drafts') {
      if (!invoice.status || invoice.status.toLowerCase() !== 'draft') return false;
    } else if (activeTab === 'done') {
      if (!invoice.status || invoice.status.toLowerCase() !== 'done') return false;
    } else {
      if (!invoice.status || invoice.status.toLowerCase() !== activeTab) return false;
    }
    
    // Filter by date range
    const dateRange = getDateRange();
    if (dateRange) {
      // Use created_at if available, otherwise use invoice_date
      const invoiceDateStr = invoice.created_at || invoice.invoice_date;
      if (!invoiceDateStr) {
        // If no date available, include it (shouldn't happen, but be safe)
        console.warn('Invoice missing date:', invoice.invoice_number);
        return true;
      }
      const invoiceDate = new Date(invoiceDateStr);
      // Check if date is valid
      if (isNaN(invoiceDate.getTime())) {
        console.warn('Invalid date for invoice:', invoice.invoice_number, invoiceDateStr);
        return true; // Include invoices with invalid dates
      }
      // Compare dates - be more inclusive by comparing timestamps
      // Include invoices that fall within the range (inclusive of start and end)
      if (invoiceDate < dateRange.start || invoiceDate > dateRange.end) {
        // Only log if it's clearly outside the range
        if (invoiceDate < dateRange.start) {
          console.log(`Invoice ${invoice.invoice_number} filtered out (before range): ${invoiceDate} < ${dateRange.start}`);
        } else {
          console.log(`Invoice ${invoice.invoice_number} filtered out (after range): ${invoiceDate} > ${dateRange.end}`);
        }
        return false;
      }
    }
    
    // Filter by search term
    if (searchTerm) {
      const searchLower = searchTerm.toLowerCase();
      return (
        (invoice.invoice_number && invoice.invoice_number.toLowerCase().includes(searchLower)) ||
        (invoice.customer_name && invoice.customer_name.toLowerCase().includes(searchLower)) ||
        (invoice.customer_email && invoice.customer_email.toLowerCase().includes(searchLower))
      );
    }
    
    return true;
  });
  
  console.log(`Filtered invoices: ${filteredInvoices.length} out of ${invoices.length} total, activeTab: ${activeTab}, dateFilter: ${dateFilter}`);

  const paginatedInvoices = filteredInvoices.slice(
    (currentPage - 1) * itemsPerPage,
    currentPage * itemsPerPage
  );

  const totalPages = Math.ceil(filteredInvoices.length / itemsPerPage);

  const handleDeleteInvoice = async (invoice: Invoice) => {
    if (!invoice || !invoice.id) {
      alert('Invalid invoice');
      return;
    }

    if (!confirm(`Are you sure you want to delete invoice ${invoice.invoice_number}? This action cannot be undone.`)) {
      return;
    }

    try {
      const invoiceId = typeof invoice.id === 'string' ? invoice.id : String(invoice.id);
      const response = await fetch(`${API_BASE_URL}/invoices/${invoiceId}`, {
        method: 'DELETE',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json'
        }
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          alert('Invoice deleted successfully');
          // Refresh the sales data
          fetchSalesData();
        } else {
          alert('Failed to delete invoice: ' + (data.error || 'Unknown error'));
        }
      } else {
        const errorData = await response.json().catch(() => ({ error: response.statusText }));
        alert('Failed to delete invoice: ' + (errorData.error || 'Unknown error'));
      }
    } catch (error: any) {
      console.error('Failed to delete invoice:', error);
      alert('Failed to delete invoice: ' + (error.message || 'Network error'));
    }
  };

  const handleUpdateStatus = async (invoice: Invoice, newStatus: string) => {
    // Validate invoice ID
    if (!invoice || !invoice.id || invoice.id === 'None' || invoice.id === 'undefined') {
      console.error('Invalid invoice ID:', invoice);
      alert('Error: Invoice ID is missing. Please refresh the page and try again.');
      return;
    }
    
    setUpdatingStatus(invoice.id as number);
    try {
      // Convert invoice ID to string for MongoDB ObjectId compatibility
      const invoiceId = invoice.id ? (typeof invoice.id === 'string' ? invoice.id : String(invoice.id)) : null;
      
      if (!invoiceId || invoiceId === 'None' || invoiceId === 'undefined' || invoiceId === 'null') {
        console.error('Invalid invoice ID after conversion:', invoiceId, 'Original:', invoice.id);
        alert('Error: Invalid invoice ID. Please refresh the page and try again.');
        setUpdatingStatus(null);
        return;
      }
      
      console.log('Updating invoice status:', { invoiceId, newStatus, invoice });
      
      const response = await fetch(`${API_BASE_URL}/invoices/${invoiceId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify({ status: newStatus })
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // Refresh sales data
          await fetchSalesData();
          alert(`Sale status updated to ${newStatus}`);
        } else {
          alert('Failed to update status: ' + (data.error || 'Unknown error'));
        }
      } else {
        // Try alternative endpoint
        const altResponse = await fetch(`${API_BASE_URL}/invoices/${invoiceId}/status`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          credentials: 'include',
          body: JSON.stringify({ status: newStatus })
        });

        if (altResponse.ok) {
          const altData = await altResponse.json();
          if (altData.success) {
            await fetchSalesData();
            alert(`Sale status updated to ${newStatus}`);
          } else {
            alert('Failed to update status: ' + (altData.error || 'Unknown error'));
          }
        } else {
          const errorData = await altResponse.json().catch(() => ({ error: altResponse.statusText }));
          alert('Failed to update status: ' + (errorData.error || `HTTP ${altResponse.status}`));
        }
      }
    } catch (error: any) {
      console.error('Error updating status:', error);
      alert('Error updating status: ' + (error.message || 'Unknown error'));
    } finally {
      setUpdatingStatus(null);
      setShowActionsMenu(null);
    }
  };

  const handleDownloadInvoice = (invoice: Invoice) => {
    window.open(`${API_BASE_URL}/invoices/${invoice.id}/pdf`, '_blank');
  };

  const getDateRangeLabel = () => {
    switch (dateFilter) {
      case 'this_month':
        return 'This Month';
      case 'last_month':
        return 'Last Month';
      case 'this_year':
        return 'This Year';
      case 'all':
        return 'All Time';
      default:
        return 'This Month';
    }
  };

  const handleAddProductToSale = (product?: any) => {
    // Use passed product or fall back to selectedProduct state
    const productToAdd = product || selectedProduct;
    
    if (!productToAdd || !productToAdd.id) {
      alert('Please select a valid product');
      return;
    }
    
    // Convert product ID to string for consistency (handle both string and number IDs)
    const productId = typeof productToAdd.id === 'string' ? productToAdd.id : String(productToAdd.id);
    
    // Check if product already exists in items (handle both string and number IDs)
    const existingItemIndex = saleForm.items.findIndex(item => {
      if (!item || !item.product_id) return false;
      const itemId = typeof item.product_id === 'string' ? item.product_id : String(item.product_id);
      return itemId === productId;
    });
    
    const unitPrice = productToAdd.price || 0;
    const gstRate = productToAdd.gst_rate || 18;
    const quantity = 1;
    const subtotal = unitPrice * quantity;
    const gstAmount = (subtotal * gstRate) / 100;
    const total = subtotal + gstAmount;

    if (existingItemIndex >= 0) {
      // Update existing item
      const updatedItems = [...saleForm.items];
      if (updatedItems[existingItemIndex]) {
        updatedItems[existingItemIndex].quantity += quantity;
        updatedItems[existingItemIndex].total = updatedItems[existingItemIndex].unit_price * updatedItems[existingItemIndex].quantity * (1 + gstRate / 100);
        setSaleForm({ ...saleForm, items: updatedItems });
      }
    } else {
      // Add new item
      setSaleForm({
        ...saleForm,
        items: [
          ...saleForm.items,
          {
            product_id: productId,
            product_name: productToAdd.name || 'Unknown Product',
            quantity: quantity,
            unit_price: unitPrice,
            gst_rate: gstRate,
            total: total
          }
        ]
      });
    }
    setSelectedProduct(null);
    setProductSearch('');
    setShowProductDropdown(false);
  };

  const handleRemoveItem = (index: number) => {
    const updatedItems = saleForm.items.filter((_, i) => i !== index);
    setSaleForm({ ...saleForm, items: updatedItems });
  };

  const handleUpdateItemQuantity = (index: number, quantity: number) => {
    if (quantity <= 0) {
      handleRemoveItem(index);
      return;
    }
    const updatedItems = [...saleForm.items];
    const item = updatedItems[index];
    const subtotal = item.unit_price * quantity;
    const gstAmount = (subtotal * item.gst_rate) / 100;
    item.quantity = quantity;
    item.total = subtotal + gstAmount;
    setSaleForm({ ...saleForm, items: updatedItems });
  };

  const calculateTotal = () => {
    return saleForm.items.reduce((sum, item) => sum + item.total, 0);
  };

  const handleCreateSale = async () => {
    if (!saleForm.customer_id && !saleForm.customer_name) {
      alert('Please select or enter a customer name');
      return;
    }
    if (saleForm.items.length === 0) {
      alert('Please add at least one product');
      return;
    }

    setCreatingSale(true);
    try {
      // Validate and filter items to ensure all required fields are present
      const validItems = saleForm.items
        .filter(item => item && item.product_id && item.quantity > 0 && item.unit_price >= 0)
        .map(item => ({
          product_id: item.product_id,
          quantity: item.quantity,
          unit_price: item.unit_price,
          total: item.total || (item.unit_price * item.quantity)
        }));
      
      if (validItems.length === 0) {
        alert('Please add at least one valid product');
        setCreatingSale(false);
        return;
      }

      const invoiceData = {
        customer_id: saleForm.customer_id ? parseInt(saleForm.customer_id) : null,
        customer_name: saleForm.customer_name || '',
        customer_phone: saleForm.customer_phone || '',
        invoice_date: saleForm.invoice_date,
        notes: saleForm.notes || '',
        status: saleForm.status || 'pending',
        items: validItems,
        total_amount: calculateTotal()
      };

      const response = await fetch(`${API_BASE_URL}/invoices/`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        credentials: 'include',
        body: JSON.stringify(invoiceData)
      });

      if (response.ok) {
        const data = await response.json();
        if (data.success) {
          // Reset form
          setSaleForm({
            customer_id: '',
            customer_name: '',
            customer_phone: '',
            invoice_date: new Date().toISOString().split('T')[0],
            items: [],
            notes: '',
            status: 'pending'
          });
          setShowCreateSaleModal(false);
          // Refresh sales data with a delay to ensure database has updated
          // Also reset date filter to 'all' temporarily to ensure new sale is visible
          const previousFilter = dateFilter;
          if (dateFilter !== 'all') {
            setDateFilter('all');
          }
          setTimeout(() => {
            fetchSalesData();
            // Restore previous filter after a moment
            if (previousFilter !== 'all') {
              setTimeout(() => {
                setDateFilter(previousFilter);
              }, 1000);
            }
          }, 1000);
          alert(saleForm.status === 'draft' ? 'Draft saved successfully!' : 'Sale created successfully!');
        } else {
          alert('Failed to create sale: ' + (data.error || 'Unknown error'));
        }
      } else {
        let errorMessage = 'Unknown error';
        try {
          const errorData = await response.json();
          errorMessage = errorData.error || errorData.message || `HTTP ${response.status}: ${response.statusText}`;
        } catch (parseError) {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`;
        }
        console.error('Failed to create sale:', errorMessage);
        alert('Failed to create sale: ' + errorMessage);
      }
    } catch (error: any) {
      console.error('Error creating sale:', error);
      alert('Error creating sale: ' + error.message);
    } finally {
      setCreatingSale(false);
    }
  };

  const filteredProductsForSale = productSearch
    ? products.filter(product =>
        product.name.toLowerCase().includes(productSearch.toLowerCase()) ||
        (product.description && product.description.toLowerCase().includes(productSearch.toLowerCase()))
      )
    : products; // Show all products when search is empty

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Loading sales data...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center space-x-3">
              <div className="h-10 w-10 bg-blue-600 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-white" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
              </div>
              <div>
                <h1 className="text-2xl font-semibold text-gray-900">Sales</h1>
                <p className="text-sm text-gray-500">Track and manage your sales transactions</p>
              </div>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => setShowCreateSaleModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                <span>Create Sale</span>
              </button>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
        {/* Summary Cards */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Sales</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(summary.total_sales)}</p>
                <p className="text-xs text-gray-500 mt-1">Showing data for {getDateRangeLabel()}</p>
              </div>
              <div className="h-12 w-12 bg-blue-100 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8c-1.657 0-3 .895-3 2s1.343 2 3 2 3 .895 3 2-1.343 2-3 2m0-8c1.11 0 2.08.402 2.599 1M12 8V7m0 1v8m0 0v1m0-1c-1.11 0-2.08-.402-2.599-1M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Purchases</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(summary.total_purchases)}</p>
                <p className="text-xs text-gray-500 mt-1">Showing data for {getDateRangeLabel()}</p>
              </div>
              <div className="h-12 w-12 bg-green-100 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M16 11V7a4 4 0 00-8 0v4M5 9h14l1 12H4L5 9z" />
                </svg>
              </div>
            </div>
          </div>
          
          <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium text-gray-600">Expenses</p>
                <p className="text-2xl font-bold text-gray-900 mt-1">{formatCurrency(summary.total_expenses)}</p>
                <p className="text-xs text-gray-500 mt-1">Showing data for {getDateRangeLabel()}</p>
              </div>
              <div className="h-12 w-12 bg-red-100 rounded-lg flex items-center justify-center">
                <svg className="h-6 w-6 text-red-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17 9V7a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2m2 4h10a2 2 0 002-2v-6a2 2 0 00-2-2H9a2 2 0 00-2 2v6a2 2 0 002 2zm7-5a2 2 0 11-4 0 2 2 0 014 0z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Sales Section Header */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 p-6 mb-6">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center space-x-2">
              <h2 className="text-xl font-semibold text-gray-900">Sales</h2>
              <svg className="h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14.752 11.168l-3.197-2.132A1 1 0 0010 9.87v4.263a1 1 0 001.555.832l3.197-2.132a1 1 0 000-1.664z" />
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <div className="flex items-center space-x-3">
              <button
                onClick={() => navigate('/reports')}
                className="bg-green-600 hover:bg-green-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors flex items-center space-x-2"
              >
                <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
                </svg>
                <span>View Reports</span>
              </button>
              <button
                onClick={() => setShowCreateSaleModal(true)}
                className="bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-lg text-sm font-medium transition-colors"
              >
                + Create Sale
              </button>
            </div>
          </div>

          {/* Tabs */}
          <div className="flex items-center space-x-1 mb-4 border-b border-gray-200">
            <button
              onClick={() => setActiveTab('all')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'all'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              All Transactions ({invoices.filter(i => i.status.toLowerCase() !== 'draft').length})
            </button>
            <button
              onClick={() => setActiveTab('pending')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'pending'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Pending ({invoices.filter(i => i.status.toLowerCase() === 'pending').length})
            </button>
            <button
              onClick={() => setActiveTab('paid')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'paid'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Paid ({invoices.filter(i => i.status.toLowerCase() === 'paid').length})
            </button>
            <button
              onClick={() => setActiveTab('cancelled')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'cancelled'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Cancelled ({invoices.filter(i => i.status.toLowerCase() === 'cancelled').length})
            </button>
            <button
              onClick={() => setActiveTab('done')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'done'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Done ({invoices.filter(i => i.status.toLowerCase() === 'done').length})
            </button>
            <button
              onClick={() => setActiveTab('drafts')}
              className={`px-4 py-2 text-sm font-medium transition-colors ${
                activeTab === 'drafts'
                  ? 'text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              Drafts ({invoices.filter(i => i.status.toLowerCase() === 'draft').length})
            </button>
          </div>

          {/* Search and Filters */}
          <div className="flex items-center space-x-4 mb-4">
            <div className="flex-1">
              <div className="relative">
                <svg className="absolute left-3 top-3 h-5 w-5 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
                </svg>
                <input
                  type="text"
                  placeholder="Search by transaction, customers, invoice #..."
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>
            </div>
            <select
              value={dateFilter}
              onChange={(e) => setDateFilter(e.target.value)}
              className="px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            >
              <option value="this_month">This Month</option>
              <option value="last_month">Last Month</option>
              <option value="this_year">This Year</option>
              <option value="all">All Time</option>
            </select>
          </div>
        </div>

        {/* Transactions Table */}
        <div className="bg-white rounded-lg shadow-sm border border-gray-200 overflow-hidden">
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Amount
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Mode
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Bill #
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Customer
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Date Created time
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {paginatedInvoices.length === 0 ? (
                  <tr>
                    <td colSpan={7} className="px-6 py-12 text-center">
                      <div className="text-gray-500">
                        <svg className="mx-auto h-12 w-12 text-gray-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                        </svg>
                        <p className="text-lg font-medium">No transactions found</p>
                        <p className="text-sm mt-1">Try adjusting your filters or create a new invoice</p>
                      </div>
                    </td>
                  </tr>
                ) : (
                  paginatedInvoices.map((invoice) => {
                    // Ensure invoice has a valid ID for key and actions
                    const invoiceKey = invoice.id || invoice.invoice_number || `invoice-${Math.random()}`;
                    return (
                    <tr key={invoiceKey} className="hover:bg-gray-50">
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm font-semibold text-gray-900">
                          {formatCurrency(invoice.total_amount)}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${getStatusColor(invoice.status)}`}>
                          {getStatusIcon(invoice.status)}
                          <span className="ml-1">{invoice.status}</span>
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{getPaymentMode(invoice)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{invoice.invoice_number}</div>
                        {invoice.created_by && (
                          <div className="text-xs text-gray-500">by {invoice.created_by}</div>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-sm text-gray-900">{invoice.customer_name}</div>
                        {invoice.customer_email && (
                          <div className="text-xs text-gray-500 truncate max-w-xs">{invoice.customer_email}</div>
                        )}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">{formatDate(invoice.created_at)}</div>
                        <div className="text-xs text-gray-500">{formatTimeAgo(invoice.created_at)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                        <div className="flex items-center justify-end space-x-2">
                          <div className="relative">
                            <button
                              onClick={() => setShowActionsMenu(showActionsMenu === invoiceKey ? null : invoiceKey)}
                              className="text-gray-600 hover:text-gray-900 p-1 rounded hover:bg-gray-100 transition-colors"
                            >
                              <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                                <path d="M10 6a2 2 0 110-4 2 2 0 010 4zM10 12a2 2 0 110-4 2 2 0 010 4zM10 18a2 2 0 110-4 2 2 0 010 4z" />
                              </svg>
                            </button>
                            {showActionsMenu === invoiceKey && (
                              <div className="absolute right-0 mt-2 w-56 bg-white rounded-md shadow-lg z-10 border border-gray-200">
                                <div className="py-1">
                                  <button
                                    onClick={() => {
                                      navigate(`/invoices/${invoice.id}/edit`);
                                      setShowActionsMenu(null);
                                    }}
                                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                  >
                                    Edit
                                  </button>
                                  <button
                                    onClick={() => {
                                      handleDeleteInvoice(invoice);
                                      setShowActionsMenu(null);
                                    }}
                                    className="block w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50"
                                  >
                                    Delete
                                  </button>
                                  <button
                                    onClick={() => {
                                      handleDownloadInvoice(invoice);
                                      setShowActionsMenu(null);
                                    }}
                                    className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100"
                                  >
                                    Download PDF
                                  </button>
                                  <div className="border-t border-gray-200 my-1"></div>
                                  <div className="px-2 py-1 text-xs font-semibold text-gray-500 uppercase">Change Status</div>
                                  {invoice.status.toLowerCase() !== 'pending' && (
                                    <button
                                      onClick={() => handleUpdateStatus(invoice, 'pending')}
                                      disabled={updatingStatus === invoice.id || !invoice.id}
                                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                                    >
                                      {updatingStatus === invoice.id ? 'Updating...' : 'Mark as Pending'}
                                    </button>
                                  )}
                                  {invoice.status.toLowerCase() !== 'paid' && (
                                    <button
                                      onClick={() => handleUpdateStatus(invoice, 'paid')}
                                      disabled={updatingStatus === invoice.id || !invoice.id}
                                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                                    >
                                      {updatingStatus === invoice.id ? 'Updating...' : 'Mark as Paid'}
                                    </button>
                                  )}
                                  {invoice.status.toLowerCase() !== 'cancelled' && (
                                    <button
                                      onClick={() => handleUpdateStatus(invoice, 'cancelled')}
                                      disabled={updatingStatus === invoice.id || !invoice.id}
                                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                                    >
                                      {updatingStatus === invoice.id ? 'Updating...' : 'Mark as Cancelled'}
                                    </button>
                                  )}
                                  {invoice.status.toLowerCase() !== 'done' && (
                                    <button
                                      onClick={() => handleUpdateStatus(invoice, 'done')}
                                      disabled={updatingStatus === invoice.id || !invoice.id}
                                      className="block w-full text-left px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 disabled:opacity-50"
                                    >
                                      {updatingStatus === invoice.id ? 'Updating...' : 'Mark as Done'}
                                    </button>
                                  )}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      </td>
                    </tr>
                    );
                  })
                )}
              </tbody>
            </table>
          </div>

          {/* Summary and Pagination */}
          <div className="bg-gray-50 px-6 py-4 border-t border-gray-200">
            <div className="flex items-center justify-between">
              <div className="flex items-center space-x-6">
                <div>
                  <span className="text-sm font-medium text-gray-700">Total </span>
                  <span className="text-sm font-bold text-gray-900">{formatCurrency(summary.total_sales)}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">Paid </span>
                  <span className="text-sm font-bold text-green-600">{formatCurrency(summary.total_paid)}</span>
                </div>
                <div>
                  <span className="text-sm font-medium text-gray-700">Pending </span>
                  <span className="text-sm font-bold text-yellow-600">{formatCurrency(summary.total_pending)}</span>
                </div>
              </div>
              <div className="flex items-center space-x-4">
                <div className="flex items-center space-x-2">
                  <button
                    onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
                    disabled={currentPage === 1}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    &lt;
                  </button>
                  {Array.from({ length: Math.min(5, totalPages) }, (_, i) => {
                    let pageNum;
                    if (totalPages <= 5) {
                      pageNum = i + 1;
                    } else if (currentPage <= 3) {
                      pageNum = i + 1;
                    } else if (currentPage >= totalPages - 2) {
                      pageNum = totalPages - 4 + i;
                    } else {
                      pageNum = currentPage - 2 + i;
                    }
                    return (
                      <button
                        key={pageNum}
                        onClick={() => setCurrentPage(pageNum)}
                        className={`px-3 py-1 border rounded-lg text-sm font-medium transition-colors ${
                          currentPage === pageNum
                            ? 'bg-blue-600 text-white border-blue-600'
                            : 'border-gray-300 text-gray-700 hover:bg-gray-50'
                        }`}
                      >
                        {pageNum}
                      </button>
                    );
                  })}
                  <button
                    onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
                    disabled={currentPage === totalPages}
                    className="px-3 py-1 border border-gray-300 rounded-lg text-sm text-gray-700 hover:bg-gray-50 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    &gt;
                  </button>
                </div>
                <select
                  value={itemsPerPage}
                  onChange={(e) => {
                    setItemsPerPage(Number(e.target.value));
                    setCurrentPage(1);
                  }}
                  className="px-3 py-1 border border-gray-300 rounded-lg text-sm text-gray-700 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                >
                  <option value={25}>25 / page</option>
                  <option value={50}>50 / page</option>
                  <option value={100}>100 / page</option>
                  <option value={200}>200 / page</option>
                </select>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Create Sale Modal */}
      {showCreateSaleModal && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4 overflow-y-auto">
          <div className="bg-white rounded-lg shadow-xl border border-gray-200 p-6 max-w-4xl w-full max-h-[90vh] overflow-y-auto">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-semibold text-gray-900">Create New Sale</h2>
              <button
                onClick={() => {
                  setShowCreateSaleModal(false);
                  setSaleForm({
                    customer_id: '',
                    customer_name: '',
                    customer_phone: '',
                    invoice_date: new Date().toISOString().split('T')[0],
                    items: [],
                    notes: '',
                    status: 'pending'
                  });
                }}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>

            <div className="space-y-6">
              {/* Customer Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Customer</label>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <select
                      value={saleForm.customer_id}
                      onChange={(e) => {
                        const customer = customers.find(c => c.id === parseInt(e.target.value));
                        setSaleForm({
                          ...saleForm,
                          customer_id: e.target.value,
                          customer_name: customer ? customer.name : '',
                          customer_phone: customer ? customer.phone : ''
                        });
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="">Select Customer</option>
                      {customers.map(customer => (
                        <option key={customer.id} value={customer.id}>{customer.name}</option>
                      ))}
                    </select>
                  </div>
                  <div>
                    <input
                      type="text"
                      placeholder="Or enter customer name"
                      value={saleForm.customer_name}
                      onChange={(e) => setSaleForm({ ...saleForm, customer_name: e.target.value, customer_id: '' })}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                  </div>
                </div>
                {saleForm.customer_id && (
                  <input
                    type="text"
                    placeholder="Phone (optional)"
                    value={saleForm.customer_phone}
                    onChange={(e) => setSaleForm({ ...saleForm, customer_phone: e.target.value })}
                    className="mt-2 w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </div>

              {/* Invoice Date */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Invoice Date</label>
                <input
                  type="date"
                  value={saleForm.invoice_date}
                  onChange={(e) => setSaleForm({ ...saleForm, invoice_date: e.target.value })}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                />
              </div>

              {/* Add Products */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Add Products</label>
                <div className="flex space-x-2 mb-4">
                  <div className="flex-1 relative">
                    <input
                      type="text"
                      placeholder="Search products or click to see all..."
                      value={productSearch}
                      onChange={(e) => {
                        setProductSearch(e.target.value);
                        setShowProductDropdown(true); // Show dropdown when typing
                      }}
                      onFocus={() => {
                        setShowProductDropdown(true); // Show dropdown on focus
                        // Always try to load products when user focuses on search
                        if (products.length === 0 && !productsLoading) {
                          fetchProducts();
                        }
                      }}
                      onBlur={(e) => {
                        // Delay hiding dropdown to allow click events
                        setTimeout(() => setShowProductDropdown(false), 200);
                      }}
                      className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                    />
                    {showProductDropdown && (
                      <div className="absolute z-10 w-full mt-1 bg-white border border-gray-300 rounded-lg shadow-lg max-h-60 overflow-y-auto">
                        {productsLoading ? (
                          <div className="px-4 py-2 text-sm text-gray-500">Loading products...</div>
                        ) : products.length === 0 ? (
                          <div className="px-4 py-2 text-sm text-gray-500">No products available. Please add products to inventory first.</div>
                        ) : filteredProductsForSale.length > 0 ? (
                          filteredProductsForSale.map(product => (
                            <button
                              key={product.id}
                              type="button"
                              onMouseDown={(e) => {
                                e.preventDefault(); // Prevent onBlur from firing before onClick
                                // Pass product directly to avoid React state update timing issues
                                handleAddProductToSale(product);
                              }}
                              className="w-full text-left px-4 py-2 hover:bg-gray-100 flex items-center justify-between"
                            >
                              <div>
                                <div className="font-medium text-gray-900">{product.name}</div>
                                <div className="text-sm text-gray-500">₹{product.price || 0} | Stock: {product.stock_quantity || 0}</div>
                              </div>
                              <svg className="h-5 w-5 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                              </svg>
                            </button>
                          ))
                        ) : productSearch ? (
                          <div className="px-4 py-2 text-sm text-gray-500">No products found matching "{productSearch}"</div>
                        ) : (
                          <div className="px-4 py-2 text-sm text-gray-500">No products available. Please add products to inventory first.</div>
                        )}
                      </div>
                    )}
                  </div>
                </div>

                {/* Selected Items */}
                {saleForm.items.length > 0 && (
                  <div className="border border-gray-200 rounded-lg overflow-hidden">
                    <table className="min-w-full divide-y divide-gray-200">
                      <thead className="bg-gray-50">
                        <tr>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Product</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Price</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Qty</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">GST</th>
                          <th className="px-4 py-3 text-left text-xs font-medium text-gray-500 uppercase">Total</th>
                          <th className="px-4 py-3 text-right text-xs font-medium text-gray-500 uppercase">Action</th>
                        </tr>
                      </thead>
                      <tbody className="bg-white divide-y divide-gray-200">
                        {saleForm.items.map((item, index) => (
                          <tr key={index}>
                            <td className="px-4 py-3 text-sm text-gray-900">{item.product_name}</td>
                            <td className="px-4 py-3 text-sm text-gray-900">{formatCurrency(item.unit_price)}</td>
                            <td className="px-4 py-3">
                              <input
                                type="number"
                                min="1"
                                value={item.quantity}
                                onChange={(e) => handleUpdateItemQuantity(index, parseInt(e.target.value) || 1)}
                                className="w-20 px-2 py-1 border border-gray-300 rounded text-gray-900 focus:outline-none focus:ring-2 focus:ring-blue-500"
                              />
                            </td>
                            <td className="px-4 py-3 text-sm text-gray-900">{item.gst_rate}%</td>
                            <td className="px-4 py-3 text-sm font-semibold text-gray-900">{formatCurrency(item.total)}</td>
                            <td className="px-4 py-3 text-right">
                              <button
                                onClick={() => handleRemoveItem(index)}
                                className="text-red-600 hover:text-red-900"
                              >
                                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                </svg>
                              </button>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

              {/* Notes */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">Notes (Optional)</label>
                <textarea
                  value={saleForm.notes}
                  onChange={(e) => setSaleForm({ ...saleForm, notes: e.target.value })}
                  rows={3}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="Add any additional notes..."
                />
              </div>

              {/* Total and Actions */}
              <div className="border-t border-gray-200 pt-4">
                <div className="flex items-center justify-between mb-4">
                  <span className="text-lg font-semibold text-gray-900">Total:</span>
                  <span className="text-2xl font-bold text-gray-900">{formatCurrency(calculateTotal())}</span>
                </div>
                <div className="flex items-center space-x-4">
                  <label className="block text-sm font-medium text-gray-700">Initial Status:</label>
                  <select
                    value={saleForm.status}
                    onChange={(e) => setSaleForm({ ...saleForm, status: e.target.value as any })}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-900 bg-white focus:outline-none focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="pending">Pending</option>
                    <option value="paid">Paid</option>
                    <option value="done">Done</option>
                    <option value="draft">Draft</option>
                  </select>
                </div>
                <div className="flex items-center justify-end space-x-3 mt-6">
                  <button
                    onClick={() => {
                      setShowCreateSaleModal(false);
                      setSaleForm({
                        customer_id: '',
                        customer_name: '',
                        customer_phone: '',
                        invoice_date: new Date().toISOString().split('T')[0],
                        items: [],
                        notes: '',
                        status: 'pending'
                      });
                    }}
                    className="px-4 py-2 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                  >
                    Cancel
                  </button>
                  <button
                    onClick={handleCreateSale}
                    disabled={creatingSale || saleForm.items.length === 0}
                    className="px-6 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                  >
                    {creatingSale ? (
                      <>
                        <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                        <span>Creating...</span>
                      </>
                    ) : (
                      <span>Create Sale</span>
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Sales;

