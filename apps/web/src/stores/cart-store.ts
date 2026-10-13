import { create } from "zustand";
import { apiClient } from "@/lib/api-client";
import { Cart, CartItem } from "@/types/commerce";

interface CartState {
  cart: Cart | null;
  isOpen: boolean;
  isLoading: boolean;
  error: string | null;

  // Drawer controls
  openCart: () => void;
  closeCart: () => void;
  toggleCart: () => void;

  // Cart operations
  fetchCart: () => Promise<void>;
  addItem: (storeId: string, productId: string, qty?: number, notes?: string) => Promise<void>;
  updateItemQty: (itemId: string, qty: number) => Promise<void>;
  removeItem: (itemId: string) => Promise<void>;
  clearCart: () => Promise<void>;
  setCart: (cart: Cart | null) => void;
}

export const useCartStore = create<CartState>((set, get) => ({
  cart: null,
  isOpen: false,
  isLoading: false,
  error: null,

  openCart: () => set({ isOpen: true }),
  closeCart: () => set({ isOpen: false }),
  toggleCart: () => set((state) => ({ isOpen: !state.isOpen })),
  setCart: (cart) => set({ cart }),

  fetchCart: async () => {
    set({ isLoading: true, error: null });
    try {
      const data = await apiClient<Cart>("/api/v1/cart");
      set({ cart: data, isLoading: false });
    } catch (err) {
      console.error("Failed to load cart", err);
      set({ isLoading: false, error: err instanceof Error ? err.message : "Failed to load cart" });
    }
  },

  addItem: async (storeId: string, productId: string, qty = 1, notes?: string) => {
    set({ isLoading: true, error: null });
    try {
      const updated = await apiClient<Cart>("/api/v1/cart/items", {
        method: "POST",
        body: JSON.stringify({
          store_id: storeId,
          product_id: productId,
          qty,
          notes,
        }),
      });
      set({ cart: updated, isLoading: false, isOpen: true });
    } catch (err) {
      console.error("Failed to add item to cart", err);
      set({ isLoading: false, error: err instanceof Error ? err.message : "Failed to add item" });
      throw err;
    }
  },

  updateItemQty: async (itemId: string, qty: number) => {
    try {
      const updated = await apiClient<Cart>(`/api/v1/cart/items/${itemId}`, {
        method: "PATCH",
        body: JSON.stringify({ qty }),
      });
      set({ cart: updated });
    } catch (err) {
      console.error("Failed to update cart item qty", err);
      throw err;
    }
  },

  removeItem: async (itemId: string) => {
    try {
      const updated = await apiClient<Cart>(`/api/v1/cart/items/${itemId}`, {
        method: "DELETE",
      });
      set({ cart: updated });
    } catch (err) {
      console.error("Failed to remove item from cart", err);
      throw err;
    }
  },

  clearCart: async () => {
    try {
      const updated = await apiClient<Cart>("/api/v1/cart", {
        method: "DELETE",
      });
      set({ cart: updated });
    } catch (err) {
      console.error("Failed to clear cart", err);
      throw err;
    }
  },
}));
