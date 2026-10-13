/**
 * Core commerce and physical retail domain models.
 */

export interface CartItem {
  id: string;
  store_id: string;
  store_name?: string | null;
  product_id: string;
  sku: string;
  product_name: string;
  product_brand?: string | null;
  unit_price: number;
  qty: number;
  subtotal: number;
  aisle?: number | null;
  bay?: number | null;
  shelf?: number | null;
  notes?: string | null;
}

export interface Cart {
  id: string;
  user_id?: string | null;
  guest_session_id?: string | null;
  store_id?: string | null;
  status: string;
  total_items: number;
  total_amount: number;
  items: CartItem[];
  created_at?: string;
  updated_at?: string;
}

export interface OrderItem {
  id: string;
  product_id: string;
  sku: string;
  product_name: string;
  unit_price: number;
  qty: number;
  subtotal: number;
  aisle?: number | null;
  bay?: number | null;
  shelf?: number | null;
}

export interface Order {
  id: string;
  user_id: string;
  store_id: string;
  store_name?: string | null;
  status: string;
  total_amount: number;
  payment_status: string;
  payment_method: string;
  pickup_time_slot?: string | null;
  items: OrderItem[];
  created_at: string;
  updated_at?: string;
}

export interface CatalogProduct {
  id: string;
  sku: string;
  name: string;
  brand: string;
  description: string;
  department: string;
  category: string;
  price: number;
  mrp: number;
  unit: string;
  dietary_flags: string[];
  attributes: Record<string, unknown>;
  is_travel_friendly: boolean;
  store_id?: string;
  store_name?: string;
  in_stock?: boolean;
  stock_quantity?: number;
  aisle?: number;
  bay?: number;
  shelf?: number;
  score?: number;
}
