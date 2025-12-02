import { User, Customer, Product, GSTReport, DashboardStats, SalesChartData, LoginForm, RegisterForm, CustomerForm, ProductForm } from '../types';
import API_BASE_URL from '../config/api';

class ApiService {
  private baseUrl = API_BASE_URL;

  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    const config: RequestInit = {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      credentials: 'include',
      ...options,
    };

    // Add auth token if available
    const token = localStorage.getItem('authToken');
    if (token) {
      config.headers = {
        ...config.headers,
        'Authorization': `Bearer ${token}`,
      };
    }

    const response = await fetch(url, config);
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Authentication methods
  async login(credentials: LoginForm): Promise<{ user: User; token: string }> {
    return this.request<{ user: User; token: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(userData: RegisterForm): Promise<{ user: User; token: string }> {
    return this.request<{ user: User; token: string }>('/auth/register', {
      method: 'POST',
      body: JSON.stringify(userData),
    });
  }

  async logout(): Promise<void> {
    return this.request<void>('/auth/logout', {
      method: 'POST',
    });
  }

  async getCurrentUser(): Promise<User> {
    return this.request<User>('/auth/me');
  }

  // Dashboard methods
  async getDashboardStats(): Promise<DashboardStats> {
    return this.request<DashboardStats>('/dashboard/stats');
  }

  async getSalesChartData(): Promise<SalesChartData> {
    return this.request<SalesChartData>('/dashboard/sales-chart');
  }

  // Customer methods
  async getCustomers(): Promise<Customer[]> {
    return this.request<Customer[]>('/customers');
  }

  async getCustomer(id: number): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}`);
  }

  async createCustomer(customerData: CustomerForm): Promise<Customer> {
    return this.request<Customer>('/customers', {
      method: 'POST',
      body: JSON.stringify(customerData),
    });
  }

  async updateCustomer(id: number, customerData: CustomerForm): Promise<Customer> {
    return this.request<Customer>(`/customers/${id}`, {
      method: 'PUT',
      body: JSON.stringify(customerData),
    });
  }

  async deleteCustomer(id: number): Promise<void> {
    return this.request<void>(`/customers/${id}`, {
      method: 'DELETE',
    });
  }

  // Product methods
  async getProducts(search?: string, category?: string): Promise<Product[]> {
    const params = new URLSearchParams();
    if (search) params.append('search', search);
    if (category) params.append('category', category);
    
    const queryString = params.toString();
    const endpoint = queryString ? `/products?${queryString}` : '/products';
    
    const response = await this.request<{ success: boolean; products: Product[] }>(endpoint);
    return response.products;
  }

  async getProduct(id: number): Promise<Product> {
    const response = await this.request<{ success: boolean; product: Product }>(`/products/${id}`);
    return response.product;
  }

  async createProduct(productData: ProductForm): Promise<{ success: boolean; message: string; product: { id: number; name: string; sku: string } }> {
    return this.request<{ success: boolean; message: string; product: { id: number; name: string; sku: string } }>('/products', {
      method: 'POST',
      body: JSON.stringify(productData),
    });
  }

  async updateProduct(id: number, productData: ProductForm): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/products/${id}`, {
      method: 'PUT',
      body: JSON.stringify(productData),
    });
  }

  async deleteProduct(id: number): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/products/${id}`, {
      method: 'DELETE',
    });
  }

  // Inventory methods
  async getInventory(): Promise<{ inventory: any[]; summary: any }> {
    const response = await this.request<{ success: boolean; inventory: any[]; summary: any }>('/inventory');
    return {
      inventory: response.inventory,
      summary: response.summary
    };
  }

  async addStockMovement(productId: number, movementData: { movement_type: 'in' | 'out' | 'adjustment'; quantity: number; reference?: string; notes?: string }): Promise<{ success: boolean; message: string; new_stock: number }> {
    return this.request<{ success: boolean; message: string; new_stock: number }>(`/products/${productId}/stock`, {
      method: 'POST',
      body: JSON.stringify(movementData),
    });
  }

  // Image upload
  async uploadImage(file: File): Promise<{ success: boolean; image_url: string; filename: string }> {
    const formData = new FormData();
    formData.append('image', file);

    const token = localStorage.getItem('authToken');
    const response = await fetch(`${this.baseUrl}/upload-image`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }

    return response.json();
  }

  // Order methods
  async getOrders(): Promise<any[]> {
    const response = await this.request<{ success: boolean; orders: any[] }>('/admin/orders');
    return response.orders || [];
  }

  async getCustomerOrders(): Promise<any[]> {
    const response = await this.request<{ success: boolean; orders: any[] }>('/customers/orders');
    return response.orders || [];
  }

  async createOrder(orderData: any): Promise<{ success: boolean; message: string; order: any }> {
    return this.request<{ success: boolean; message: string; order: any }>('/customers/orders', {
      method: 'POST',
      body: JSON.stringify(orderData),
    });
  }

  async updateOrderStatus(orderId: number, status: string): Promise<{ success: boolean; message: string }> {
    return this.request<{ success: boolean; message: string }>(`/admin/orders/${orderId}/status`, {
      method: 'PUT',
      body: JSON.stringify({ status }),
    });
  }

  // Invoice methods
  async getInvoices(): Promise<any[]> {
    const response = await this.request<{ success: boolean; invoices: any[] }>('/invoices');
    return response.invoices || [];
  }

  async getCustomerInvoices(): Promise<any[]> {
    const response = await this.request<{ success: boolean; invoices: any[] }>('/customer-invoices');
    return response.invoices || [];
  }

  async getInvoice(invoiceId: number): Promise<any> {
    const response = await this.request<{ success: boolean; invoice: any }>(`/invoices/${invoiceId}`);
    return response.invoice;
  }

  // GST Reports methods
  async getGSTReports(): Promise<GSTReport[]> {
    return this.request<GSTReport[]>('/gst/reports');
  }

  // General Reports methods
  async getReports(): Promise<any> {
    return this.request<any>('/reports');
  }
}

const apiService = new ApiService();
export { apiService };
