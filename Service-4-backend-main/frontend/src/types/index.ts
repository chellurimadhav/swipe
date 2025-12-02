export interface User {
  id: number;
  username: string;
  email: string;
  business_name: string;
  gst_number: string;
  business_address: string;
  business_phone: string;
  business_email: string;
  business_state: string;
  business_pincode: string;
  created_at: string;
  is_active: boolean;
}

export interface Customer {
  id: number;
  user_id: number;
  name: string;
  gstin?: string;
  email?: string;
  phone: string;
  billing_address: string;
  shipping_address?: string;
  state: string;
  pincode: string;
  created_at: string;
  is_active: boolean;
}

export interface Product {
  id: number;
  name: string;
  description: string;
  price: number;
  image_url: string;
  stock_quantity: number;
  created_at: string;
  updated_at: string;
  is_active: boolean;
  sku?: string;
  unit?: string;
  min_stock_level?: number;
}

export interface InvoiceItem {
  id: number;
  invoice_id: number;
  product_id: number;
  quantity: number;
  unit_price: number;
  total: number;
  product?: Product;
}

export interface Invoice {
  id: number;
  invoice_number: string;
  invoice_date: string;
  business_name: string;
  business_address: string;
  business_phone: string;
  customer_name: string;
  customer_address: string;
  customer_phone: string;
  subtotal: number;
  total_amount: number;
  notes?: string;
  created_at: string;
  updated_at: string;
  items?: InvoiceItem[];
  custom_columns?: { [key: string]: string };
  customer?: Customer;
  status?: string;
}

export interface StockMovement {
  id: number;
  product_id: number;
  movement_type: string;
  quantity: number;
  reference?: string;
  notes?: string;
  created_at: string;
}

export interface GSTReport {
  id: number;
  user_id: number;
  report_type: string;
  period_month: number;
  period_year: number;
  total_taxable_value: number;
  total_cgst: number;
  total_sgst: number;
  total_igst: number;
  report_data?: any;
  created_at: string;
  user?: User;
}

export interface DashboardStats {
  monthly_sales: number;
  total_invoices: number;
  total_products: number;
  total_customers: number;
  recent_invoices: Invoice[];
  low_stock_products: Product[];
  top_selling_products: Product[];
}

export interface SalesChartData {
  labels: string[];
  datasets: {
    label: string;
    data: number[];
    backgroundColor: string;
    borderColor: string;
  }[];
}

export interface LoginForm {
  username: string;
  password: string;
  remember_me: boolean;
}

export interface RegisterForm {
  username: string;
  email: string;
  password: string;
  confirm_password: string;
  business_name: string;
  gst_number: string;
  business_address: string;
  business_phone: string;
  business_email: string;
  business_state: string;
  business_pincode: string;
}

export interface CustomerForm {
  name: string;
  gstin: string;
  email: string;
  phone: string;
  billing_address: string;
  shipping_address: string;
  state: string;
  pincode: string;
}

export interface ProductForm {
  name: string;
  description: string;
  price: number;
  stock_quantity: number;
  image_url: string;
}

export interface InvoiceForm {
  business_name: string;
  business_address: string;
  business_phone: string;
  customer_name: string;
  customer_address: string;
  customer_phone: string;
  invoice_date: string;
  notes: string;
  items: {
    product_id: number;
    quantity: number;
    unit_price: number;
  }[];
  custom_columns?: { [key: string]: string };
}
