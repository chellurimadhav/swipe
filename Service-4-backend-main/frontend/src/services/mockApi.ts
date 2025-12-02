import { User, Customer, Product, Invoice, GSTReport, DashboardStats, SalesChartData, LoginForm, RegisterForm, CustomerForm, ProductForm, InvoiceForm } from '../types';

// Mock data - Empty for user to add their own products
const mockProducts: Product[] = [];

// Mock invoices - Empty for user to create their own
const mockInvoices: Invoice[] = [];

// Mock orders - Empty for user to create their own
const mockOrders: any[] = [];

class MockApiService {
  private delay(ms: number = 500): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // Authentication methods
  async login(_credentials: LoginForm): Promise<{ user: User; token: string }> {
    await this.delay();
    return {
      user: {
        id: 1,
        username: 'demo',
        email: 'demo@example.com',
        business_name: 'Demo Business',
        gst_number: '22AAAAA0000A1Z5',
        business_address: '123 Demo Street, Demo City',
        business_phone: '9876543210',
        business_email: 'demo@example.com',
        business_state: 'Maharashtra',
        business_pincode: '400001',
        created_at: '2024-01-01',
        is_active: true
      },
      token: 'mock-token-123'
    };
  }

  async register(userData: RegisterForm): Promise<{ user: User; token: string }> {
    await this.delay();
    return this.login({ username: userData.username, password: userData.password, remember_me: false });
  }

  async logout(): Promise<void> {
    await this.delay();
  }

  async getCurrentUser(): Promise<User> {
    await this.delay();
    return {
      id: 1,
      username: 'demo',
      email: 'demo@example.com',
      business_name: 'Demo Business',
      gst_number: '22AAAAA0000A1Z5',
      business_address: '123 Demo Street, Demo City',
      business_phone: '9876543210',
      business_email: 'demo@example.com',
      business_state: 'Maharashtra',
      business_pincode: '400001',
      created_at: '2024-01-01',
      is_active: true
    };
  }

  // Dashboard methods
  async getDashboardStats(): Promise<DashboardStats> {
    await this.delay();
    return {
      monthly_sales: 125000,
      total_invoices: 45,
      total_products: mockProducts.length,
      total_customers: 12,
      recent_invoices: [],
      low_stock_products: [],
      top_selling_products: []
    };
  }

  async getSalesChartData(): Promise<SalesChartData> {
    await this.delay();
    return {
      labels: ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun'],
      datasets: [{
        label: 'Sales',
        data: [65000, 59000, 80000, 81000, 56000, 125000],
        backgroundColor: 'rgba(54, 162, 235, 0.2)',
        borderColor: 'rgba(54, 162, 235, 1)'
      }]
    };
  }

  // Customer methods
  async getCustomers(): Promise<Customer[]> {
    await this.delay();
    return [];
  }

  async getCustomer(_id: number): Promise<Customer> {
    await this.delay();
    throw new Error('Customer not found');
  }

  async createCustomer(_customerData: CustomerForm): Promise<Customer> {
    await this.delay();
    throw new Error('Not implemented');
  }

  async updateCustomer(_id: number, _customerData: CustomerForm): Promise<Customer> {
    await this.delay();
    throw new Error('Not implemented');
  }

  async deleteCustomer(_id: number): Promise<void> {
    await this.delay();
    throw new Error('Not implemented');
  }

  // Product methods
  async getProducts(search?: string): Promise<Product[]> {
    await this.delay();
    let filteredProducts = [...mockProducts];
    
    if (search) {
      filteredProducts = filteredProducts.filter(product =>
        product.name.toLowerCase().includes(search.toLowerCase()) ||
        product.description.toLowerCase().includes(search.toLowerCase())
      );
    }
    
    return filteredProducts;
  }

  async getProduct(id: number): Promise<Product> {
    await this.delay();
    const product = mockProducts.find(p => p.id === id);
    if (!product) {
      throw new Error('Product not found');
    }
    return product;
  }

  async createProduct(productData: ProductForm): Promise<{ success: boolean; message: string; product: { id: number; name: string } }> {
    await this.delay();
    const newProduct: Product = {
      id: mockProducts.length + 1,
      name: productData.name,
      description: productData.description,
      price: productData.price,
      image_url: productData.image_url,
      stock_quantity: productData.stock_quantity || 0, // Use the stock quantity from form
      is_active: true,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString()
    };
    
    mockProducts.push(newProduct);
    
    return {
      success: true,
      message: 'Product added to inventory successfully',
      product: {
        id: newProduct.id,
        name: newProduct.name
      }
    };
  }

  async updateProduct(id: number, productData: ProductForm): Promise<{ success: boolean; message: string }> {
    await this.delay();
    const index = mockProducts.findIndex(p => p.id === id);
    if (index === -1) {
      throw new Error('Product not found');
    }
    
    mockProducts[index] = {
      ...mockProducts[index],
      name: productData.name,
      description: productData.description,
      price: productData.price,
      image_url: productData.image_url,
      updated_at: new Date().toISOString()
    };
    
    return {
      success: true,
      message: 'Product updated successfully'
    };
  }

  async deleteProduct(id: number): Promise<{ success: boolean; message: string }> {
    await this.delay();
    const index = mockProducts.findIndex(p => p.id === id);
    if (index === -1) {
      throw new Error('Product not found');
    }
    
    mockProducts.splice(index, 1);
    
    return {
      success: true,
      message: 'Product deleted successfully'
    };
  }

  // Inventory methods
  async getInventory(): Promise<{ inventory: any[]; summary: any }> {
    await this.delay();
    const inventory = mockProducts.map(product => ({
      id: product.id,
      name: product.name,
      sku: `SKU-${product.id.toString().padStart(3, '0')}`,
      category: 'Electronics',
      stock_quantity: product.stock_quantity,
      min_stock_level: 5,
      price: product.price,
      total_value: product.price * product.stock_quantity,
      status: product.stock_quantity === 0 ? 'out_of_stock' : 
              product.stock_quantity <= 5 ? 'low_stock' : 'in_stock'
    }));
    
    const summary = {
      total_products: inventory.length,
      total_value: inventory.reduce((sum, item) => sum + item.total_value, 0),
      low_stock_count: inventory.filter(item => item.status === 'low_stock').length,
      out_of_stock_count: inventory.filter(item => item.status === 'out_of_stock').length
    };
    
    return { inventory, summary };
  }

  async addStockMovement(productId: number, movementData: { movement_type: 'in' | 'out' | 'adjustment'; quantity: number; reference?: string; notes?: string }): Promise<{ success: boolean; message: string; new_stock: number }> {
    await this.delay();
    const product = mockProducts.find(p => p.id === productId);
    if (!product) {
      throw new Error('Product not found');
    }
    
    if (movementData.movement_type === 'in') {
      product.stock_quantity += movementData.quantity;
    } else if (movementData.movement_type === 'out') {
      if (product.stock_quantity < movementData.quantity) {
        throw new Error('Insufficient stock');
      }
      product.stock_quantity -= movementData.quantity;
    } else {
      product.stock_quantity = movementData.quantity;
    }
    
    return {
      success: true,
      message: 'Stock movement recorded successfully',
      new_stock: product.stock_quantity
    };
  }

  // Image upload
  async uploadImage(file: File): Promise<{ success: boolean; image_url: string; filename: string }> {
    await this.delay();
    // Simulate file upload
    const filename = `uploaded_${Date.now()}_${file.name}`;
    const image_url = `/uploads/${filename}`;
    
    return {
      success: true,
      image_url,
      filename
    };
  }

  // Invoice methods
  async getInvoices(): Promise<Invoice[]> {
    await this.delay();
    return [...mockInvoices];
  }

  async getInvoice(id: number): Promise<Invoice> {
    await this.delay();
    const invoice = mockInvoices.find(inv => inv.id === id);
    if (!invoice) {
      throw new Error('Invoice not found');
    }
    return invoice;
  }

  async createInvoice(invoiceData: InvoiceForm): Promise<{ success: boolean; message: string; invoice: Invoice }> {
    await this.delay();
    const newInvoice: Invoice = {
      id: Date.now(),
      invoice_number: `INV-${Date.now()}`,
      invoice_date: invoiceData.invoice_date,
      business_name: invoiceData.business_name,
      business_address: invoiceData.business_address,
      business_phone: invoiceData.business_phone,
      customer_name: invoiceData.customer_name,
      customer_address: invoiceData.customer_address,
      customer_phone: invoiceData.customer_phone,
      subtotal: invoiceData.items.reduce((sum: number, item: any) => sum + (item.quantity * item.unit_price), 0),
      total_amount: invoiceData.items.reduce((sum: number, item: any) => sum + (item.quantity * item.unit_price), 0),
             notes: invoiceData.notes,
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      items: invoiceData.items.map((item: any) => ({
        id: Date.now() + Math.random(),
        invoice_id: Date.now(),
        product_id: item.product_id,
        quantity: item.quantity,
        unit_price: item.unit_price,
        total: item.quantity * item.unit_price
      })),
      custom_columns: invoiceData.custom_columns
    };
    
    mockInvoices.push(newInvoice);
    
    return {
      success: true,
      message: 'Invoice created successfully',
      invoice: newInvoice
    };
  }

  async updateInvoice(_id: number, _invoiceData: InvoiceForm): Promise<{ success: boolean; message: string }> {
    await this.delay();
    return {
      success: true,
      message: 'Invoice updated successfully'
    };
  }

  async deleteInvoice(id: number): Promise<void> {
    await this.delay();
    const index = mockInvoices.findIndex(inv => inv.id === id);
    if (index === -1) {
      throw new Error('Invoice not found');
    }
    mockInvoices.splice(index, 1);
  }

  // GST Reports methods
  async getGSTReports(): Promise<GSTReport[]> {
    await this.delay();
    return [];
  }

  // General Reports methods
  async getReports(): Promise<any> {
    await this.delay();
    return {};
  }

  // Order methods
  async getOrders(): Promise<any[]> {
    await this.delay();
    return [...mockOrders];
  }

  async getCustomerOrders(): Promise<any[]> {
    await this.delay();
    return [...mockOrders];
  }

  async createOrder(orderData: any): Promise<{ success: boolean; message: string; order: any }> {
    await this.delay();
    const newOrder = {
      id: Date.now(),
      order_number: `ORD-${Date.now()}`,
      customer_id: 1,
      customer_name: 'Demo Customer',
      customer_email: 'customer@example.com',
      customer_phone: '9876543210',
      order_date: new Date().toISOString(),
      status: 'pending',
      total_amount: orderData.total_amount || 0,
      notes: orderData.notes || '',
      items: orderData.items.map((item: any) => ({
        id: Date.now() + Math.random(),
        product_id: item.product_id,
        product_name: 'Demo Product',
        quantity: item.quantity,
        unit_price: item.unit_price,
        total: item.quantity * item.unit_price
      })),
      created_at: new Date().toISOString()
    };
    
    mockOrders.push(newOrder);
    
    return {
      success: true,
      message: 'Order created successfully',
      order: newOrder
    };
  }

  async updateOrderStatus(orderId: number, status: string): Promise<{ success: boolean; message: string }> {
    await this.delay();
    const order = mockOrders.find(o => o.id === orderId);
    if (order) {
      order.status = status;
      return {
        success: true,
        message: 'Order status updated successfully'
      };
    }
    throw new Error('Order not found');
  }
}

const mockApiService = new MockApiService();
export { mockApiService };
