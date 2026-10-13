"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import {
  ShoppingBag,
  ArrowLeft,
  Store,
  MapPin,
  Clock,
  ShieldCheck,
  CreditCard,
  QrCode,
  Building,
  Banknote,
  CheckCircle2,
  Loader2,
  AlertCircle,
  User,
  LogIn,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { formatInr } from "@/lib/utils";
import { useAuthStore } from "@/stores/auth-store";
import { useCartStore } from "@/stores/cart-store";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

export default function CheckoutPage(): React.JSX.Element {
  const router = useRouter();
  const { user, setAuth } = useAuthStore();
  const { cart, fetchCart, clearCart, isLoading: isCartLoading } = useCartStore();

  const [fulfillmentType, setFulfillmentType] = useState<"pickup" | "delivery">("pickup");
  const [pickupSlot, setPickupSlot] = useState("Today, within 30 mins");
  const [paymentMethod, setPaymentMethod] = useState("simulated_upi");
  const [isPlacingOrder, setIsPlacingOrder] = useState(false);
  const [orderError, setOrderError] = useState<string | null>(null);

  // Guest authentication form states
  const [authMode, setAuthMode] = useState<"register" | "login">("register");
  const [authEmail, setAuthEmail] = useState("");
  const [authName, setAuthName] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [isAuthenticating, setIsAuthenticating] = useState(false);
  const [authError, setAuthError] = useState<string | null>(null);

  useEffect(() => {
    fetchCart();
  }, [fetchCart]);

  const handleAuthSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!authEmail || !authPassword) {
      setAuthError("Email and password are required.");
      return;
    }

    setIsAuthenticating(true);
    setAuthError(null);

    try {
      if (authMode === "register") {
        const regRes = await apiClient.post<{ user: any; access_token: string }>(
          "/api/v1/auth/register",
          {
            email: authEmail.trim(),
            password: authPassword,
            full_name: authName.trim() || authEmail.split("@")[0],
          }
        );
        setAuth(regRes.user, regRes.access_token);
      } else {
        const loginRes = await apiClient.post<{ user: any; access_token: string }>(
          "/api/v1/auth/login",
          {
            email: authEmail.trim(),
            password: authPassword,
          }
        );
        setAuth(loginRes.user, loginRes.access_token);
      }
      // Refresh cart after login so any guest session items are bound
      await fetchCart();
    } catch (err) {
      console.error("Auth error during checkout", err);
      setAuthError(err instanceof Error ? err.message : "Authentication failed");
    } finally {
      setIsAuthenticating(false);
    }
  };

  const handlePlaceOrder = async () => {
    if (!user) {
      setOrderError("Please sign in or create an account to finalize your order.");
      return;
    }

    if (!cart || !cart.items || cart.items.length === 0) {
      setOrderError("Your cart is empty. Add items before placing an order.");
      return;
    }

    setIsPlacingOrder(true);
    setOrderError(null);

    try {
      const orderRes = await apiClient.post<{
        id: string;
        order_number: string;
        status: string;
        total_amount: number;
      }>("/api/v1/orders/checkout", {
        cart_id: cart.id,
        payment_method: paymentMethod,
        pickup_time_slot: pickupSlot,
      });

      // Clear local cart store and redirect to confirmation
      await clearCart();
      router.push(`/orders/${orderRes.id}`);
    } catch (err) {
      console.error("Failed to checkout", err);
      setOrderError(err instanceof Error ? err.message : "Order checkout failed. Please try again.");
    } finally {
      setIsPlacingOrder(false);
    }
  };

  const items = cart?.items || [];
  const subtotal = cart?.total_amount || 0;
  const taxes = 0; // GST included in MRP
  const fulfillmentFee = 0; // Free store pickup
  const total = subtotal + taxes + fulfillmentFee;

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col">
      {/* Checkout Header */}
      <header className="border-b border-border/80 bg-background/80 backdrop-blur-md">
        <div className="max-w-5xl mx-auto px-4 sm:px-6 h-16 flex items-center justify-between">
          <Link href="/shop" className="flex items-center gap-2 text-xs font-semibold text-muted-foreground hover:text-foreground">
            <ArrowLeft className="w-4 h-4" /> Back to Store
          </Link>
          <div className="flex items-center gap-2">
            <ShoppingBag className="w-4 h-4 text-primary" />
            <span className="font-extrabold text-sm tracking-tight">Express Checkout</span>
          </div>
          <span className="text-xs text-muted-foreground flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-emerald-500" /> Simulated Mode
          </span>
        </div>
      </header>

      <main className="flex-1 max-w-5xl w-full mx-auto px-4 sm:px-6 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
          {/* Left Column: Flow Options */}
          <div className="lg:col-span-7 space-y-6">
            {/* Step 1: Account / Guest Guard */}
            <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">
                    1
                  </span>
                  <h3 className="font-bold text-base text-foreground">Customer Details</h3>
                </div>
                {user && (
                  <Badge variant="accent" className="text-[10px]">
                    Logged In
                  </Badge>
                )}
              </div>

              {user ? (
                <div className="p-3 bg-muted/40 rounded-xl border border-border/40 flex items-center justify-between">
                  <div>
                    <h4 className="font-bold text-sm text-foreground">{user.full_name || "Customer"}</h4>
                    <p className="text-xs text-muted-foreground">{user.email}</p>
                  </div>
                  <CheckCircle2 className="w-5 h-5 text-emerald-500" />
                </div>
              ) : (
                <div className="space-y-4">
                  <div className="flex items-center gap-2 p-1 bg-muted/60 rounded-xl text-xs font-semibold">
                    <button
                      type="button"
                      onClick={() => setAuthMode("register")}
                      className={`flex-1 py-1.5 rounded-lg text-center transition-all ${
                        authMode === "register" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"
                      }`}
                    >
                      Instant Guest Signup
                    </button>
                    <button
                      type="button"
                      onClick={() => setAuthMode("login")}
                      className={`flex-1 py-1.5 rounded-lg text-center transition-all ${
                        authMode === "login" ? "bg-card text-foreground shadow-sm" : "text-muted-foreground"
                      }`}
                    >
                      Sign In with Password
                    </button>
                  </div>

                  <form onSubmit={handleAuthSubmit} className="space-y-3">
                    {authMode === "register" && (
                      <Input
                        placeholder="Full Name (e.g. John Doe)"
                        value={authName}
                        onChange={(e) => setAuthName(e.target.value)}
                        required
                        className="text-xs rounded-xl"
                      />
                    )}
                    <Input
                      type="email"
                      placeholder="Email address"
                      value={authEmail}
                      onChange={(e) => setAuthEmail(e.target.value)}
                      required
                      className="text-xs rounded-xl"
                    />
                    <Input
                      type="password"
                      placeholder="Password"
                      value={authPassword}
                      onChange={(e) => setAuthPassword(e.target.value)}
                      required
                      className="text-xs rounded-xl"
                    />

                    {authError && (
                      <p className="text-xs text-destructive font-medium flex items-center gap-1">
                        <AlertCircle className="w-3.5 h-3.5" /> {authError}
                      </p>
                    )}

                    <Button
                      type="submit"
                      disabled={isAuthenticating}
                      size="sm"
                      className="w-full text-xs rounded-xl"
                    >
                      {isAuthenticating ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin mr-1" />
                      ) : (
                        <User className="w-3.5 h-3.5 mr-1" />
                      )}
                      {authMode === "register" ? "Continue to Payment" : "Sign In & Continue"}
                    </Button>
                  </form>
                </div>
              )}
            </Card>

            {/* Step 2: Fulfillment Method */}
            <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 space-y-4">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">
                  2
                </span>
                <h3 className="font-bold text-base text-foreground">Fulfillment Method</h3>
              </div>

              <div className="grid grid-cols-2 gap-3">
                <button
                  type="button"
                  onClick={() => setFulfillmentType("pickup")}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    fulfillmentType === "pickup"
                      ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                      : "border-border/80 bg-card hover:border-border"
                  }`}
                >
                  <Store className="w-4 h-4 text-primary mb-1.5" />
                  <h4 className="font-bold text-xs text-foreground">In-Store Pickup</h4>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Pre-packed at physical store counter.
                  </p>
                  <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 mt-2 block">
                    FREE
                  </span>
                </button>

                <button
                  type="button"
                  onClick={() => setFulfillmentType("delivery")}
                  className={`p-3.5 rounded-xl border text-left transition-all ${
                    fulfillmentType === "delivery"
                      ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                      : "border-border/80 bg-card hover:border-border"
                  }`}
                >
                  <Clock className="w-4 h-4 text-primary mb-1.5" />
                  <h4 className="font-bold text-xs text-foreground">Express Delivery</h4>
                  <p className="text-[11px] text-muted-foreground mt-0.5">
                    Dispatched from store in 30 mins.
                  </p>
                  <span className="text-[10px] font-bold text-emerald-600 dark:text-emerald-400 mt-2 block">
                    FREE (Promo)
                  </span>
                </button>
              </div>

              {fulfillmentType === "pickup" && (
                <div className="space-y-2 pt-2">
                  <label className="text-xs font-semibold text-muted-foreground block">
                    Select Pickup Time Slot
                  </label>
                  <div className="grid grid-cols-1 sm:grid-cols-3 gap-2">
                    {["Today, within 30 mins", "Today, 5:00 - 6:00 PM", "Tomorrow morning"].map((slot) => (
                      <button
                        key={slot}
                        type="button"
                        onClick={() => setPickupSlot(slot)}
                        className={`p-2 rounded-xl text-center text-xs font-medium border transition-all ${
                          pickupSlot === slot
                            ? "bg-primary text-primary-foreground border-primary"
                            : "bg-muted/40 text-muted-foreground border-border hover:bg-muted"
                        }`}
                      >
                        {slot}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </Card>

            {/* Step 3: Payment Selection */}
            <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 space-y-4">
              <div className="flex items-center gap-2">
                <span className="w-6 h-6 rounded-full bg-primary/10 text-primary font-bold text-xs flex items-center justify-center">
                  3
                </span>
                <h3 className="font-bold text-base text-foreground">Payment Method (Simulated)</h3>
              </div>

              <div className="space-y-2">
                {[
                  {
                    id: "simulated_upi",
                    title: "UPI (Google Pay / PhonePe / Paytm / QR)",
                    desc: "Instant zero-fee payment simulation",
                    icon: QrCode,
                  },
                  {
                    id: "simulated_card",
                    title: "Credit or Debit Card",
                    desc: "Visa, Mastercard, RuPay",
                    icon: CreditCard,
                  },
                  {
                    id: "simulated_netbanking",
                    title: "Net Banking",
                    desc: "HDFC, ICICI, SBI, Axis",
                    icon: Building,
                  },
                  {
                    id: "cash_on_pickup",
                    title: "Pay at Store Counter",
                    desc: "Cash or Card upon physical pickup",
                    icon: Banknote,
                  },
                ].map((pm) => {
                  const Icon = pm.icon;
                  const isSelected = paymentMethod === pm.id;
                  return (
                    <button
                      key={pm.id}
                      type="button"
                      onClick={() => setPaymentMethod(pm.id)}
                      className={`w-full p-3 rounded-xl border flex items-center justify-between text-left transition-all ${
                        isSelected
                          ? "border-primary bg-primary/5 ring-1 ring-primary/30"
                          : "border-border/70 bg-card hover:border-border"
                      }`}
                    >
                      <div className="flex items-center gap-3">
                        <div className="w-8 h-8 rounded-lg bg-muted flex items-center justify-center text-primary">
                          <Icon className="w-4 h-4" />
                        </div>
                        <div>
                          <h4 className="font-bold text-xs text-foreground">{pm.title}</h4>
                          <p className="text-[11px] text-muted-foreground">{pm.desc}</p>
                        </div>
                      </div>
                      <span className={`w-4 h-4 rounded-full border flex items-center justify-center ${
                        isSelected ? "border-primary bg-primary text-white" : "border-muted-foreground"
                      }`}>
                        {isSelected && <span className="w-1.5 h-1.5 rounded-full bg-white" />}
                      </span>
                    </button>
                  );
                })}
              </div>
            </Card>
          </div>

          {/* Right Column: Order Summary & Place Button */}
          <div className="lg:col-span-5 space-y-6">
            <Card className="p-6 bg-card/70 backdrop-blur-md border-border/80 space-y-5 sticky top-24">
              <div className="flex items-center justify-between pb-3 border-b border-border/60">
                <h3 className="font-bold text-base text-foreground">Order Summary</h3>
                <Badge variant="secondary" className="text-xs">
                  {items.length} items
                </Badge>
              </div>

              {/* Items List preview with physical aisle badges */}
              <div className="max-h-60 overflow-y-auto space-y-2.5 pr-1">
                {items.length === 0 ? (
                  <p className="text-xs text-muted-foreground text-center py-4">Your cart is empty.</p>
                ) : (
                  items.map((item) => (
                    <div key={item.id} className="flex items-start justify-between text-xs py-1 border-b border-border/30 last:border-none">
                      <div className="min-w-0 flex-1 pr-2">
                        <span className="font-semibold text-foreground truncate block">
                          {item.product_name}
                        </span>
                        <div className="flex items-center gap-1.5 text-[10px] text-muted-foreground font-mono">
                          <MapPin className="w-2.5 h-2.5 text-primary" />
                          Aisle {item.aisle ?? 1} · Qty {item.qty}
                        </div>
                      </div>
                      <span className="font-bold text-foreground shrink-0">
                        {formatInr(item.subtotal)}
                      </span>
                    </div>
                  ))
                )}
              </div>

              {/* Price Breakdown */}
              <div className="space-y-2 pt-3 border-t border-border/60 text-xs">
                <div className="flex justify-between text-muted-foreground">
                  <span>Subtotal</span>
                  <span className="text-foreground font-semibold">{formatInr(subtotal)}</span>
                </div>
                <div className="flex justify-between text-muted-foreground">
                  <span>Taxes (GST Included)</span>
                  <span className="text-foreground font-semibold">₹0.00</span>
                </div>
                <div className="flex justify-between text-muted-foreground">
                  <span>Fulfillment Fee</span>
                  <span className="text-emerald-600 dark:text-emerald-400 font-bold">FREE</span>
                </div>
                <div className="flex justify-between text-base font-extrabold text-foreground pt-2 border-t border-border/60">
                  <span>Total Amount</span>
                  <span className="text-primary">{formatInr(total)}</span>
                </div>
              </div>

              {orderError && (
                <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-1.5">
                  <AlertCircle className="w-4 h-4 shrink-0" />
                  <span>{orderError}</span>
                </div>
              )}

              {/* Place Order CTA */}
              <Button
                onClick={handlePlaceOrder}
                disabled={isPlacingOrder || items.length === 0}
                className="w-full py-6 text-sm font-bold rounded-2xl shadow-lg gap-2"
              >
                {isPlacingOrder ? (
                  <>
                    <Loader2 className="w-4 h-4 animate-spin" /> Finalizing Order...
                  </>
                ) : (
                  <>
                    <CheckCircle2 className="w-4 h-4" /> Place Order ({formatInr(total)})
                  </>
                )}
              </Button>

              <p className="text-[10px] text-muted-foreground text-center">
                Simulated Google Hackathon environment. No real funds are debited.
              </p>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}
