"use client";

import React, { useState, useEffect, useCallback } from "react";
import {
  Search,
  MapPin,
  CheckCircle,
  Plus,
  Loader2,
  Tag,
  Sparkles,
  SlidersHorizontal,
  X,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { formatInr } from "@/lib/utils";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCartStore } from "@/stores/cart-store";
import { useStoreSelectionStore } from "@/stores/store-selection-store";

export interface SearchCandidate {
  product_id: string;
  store_id: string;
  name: string;
  brand: string;
  category: string;
  size_label?: string | null;
  is_travel_size: boolean;
  dietary_tags: string[];
  price: number | string;
  mrp: number | string;
  stock_qty: number;
  aisle: number;
  bay: number;
  shelf: number;
  score: number;
  match_method: string;
}

const DIETARY_OPTIONS = [
  { id: "eggless", label: "Eggless" },
  { id: "vegetarian", label: "Vegetarian" },
  { id: "vegan", label: "Vegan" },
  { id: "gluten_free", label: "Gluten-Free" },
  { id: "organic", label: "Organic" },
];

export function CatalogSearchView(): React.JSX.Element {
  const [query, setQuery] = useState("");
  const [selectedDietary, setSelectedDietary] = useState<string[]>([]);
  const [travelSizeOnly, setTravelSizeOnly] = useState(false);
  const [inStockOnly, setInStockOnly] = useState(true);
  const [results, setResults] = useState<SearchCandidate[]>([]);
  const [loading, setLoading] = useState(false);
  const [addingId, setAddingId] = useState<string | null>(null);

  const selectedStoreIds = useStoreSelectionStore((state) => state.selectedStoreIds);
  const addItem = useCartStore((state) => state.addItem);

  const executeSearch = useCallback(
    async (searchQuery: string) => {
      if (!searchQuery.trim()) {
        setResults([]);
        return;
      }

      setLoading(true);
      try {
        const params = new URLSearchParams();
        params.set("q", searchQuery);

        // Store IDs
        if (selectedStoreIds.length > 0) {
          selectedStoreIds.forEach((sid) => params.append("store_ids", sid));
        } else {
          // Default to Indiranagar store if none selected
          params.append("store_ids", "11111111-1111-1111-1111-111111111111");
        }

        selectedDietary.forEach((dt) => params.append("dietary_tags", dt));
        if (travelSizeOnly) params.set("is_travel_size", "true");
        params.set("in_stock_only", inStockOnly ? "true" : "false");
        params.set("limit", "24");

        const hits = await apiClient<SearchCandidate[]>(`/api/v1/catalog/search?${params.toString()}`);
        setResults(hits || []);
      } catch (err) {
        console.error("Search query failed", err);
        setResults([]);
      } finally {
        setLoading(false);
      }
    },
    [selectedStoreIds, selectedDietary, travelSizeOnly, inStockOnly]
  );

  // Debounced search on query change
  useEffect(() => {
    const timer = setTimeout(() => {
      executeSearch(query);
    }, 250);
    return () => clearTimeout(timer);
  }, [query, executeSearch]);

  const toggleDietary = (tag: string) => {
    setSelectedDietary((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag]
    );
  };

  const handleAddToCart = async (item: SearchCandidate) => {
    setAddingId(item.product_id);
    try {
      await addItem(item.store_id, item.product_id, 1);
    } finally {
      setAddingId(null);
    }
  };

  return (
    <div className="space-y-6">
      {/* Search Input Bar */}
      <div className="relative">
        <Search className="absolute left-4 top-1/2 -translate-y-1/2 w-5 h-5 text-muted-foreground pointer-events-none" />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search items, ingredients, brands (e.g. strawberry, maida, almond milk, shampoo)..."
          className="pl-12 pr-10 py-6 text-base rounded-2xl bg-card border-border/80 shadow-sm focus-visible:ring-primary"
        />
        {query && (
          <button
            onClick={() => setQuery("")}
            className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground p-1"
          >
            <X className="w-4 h-4" />
          </button>
        )}
      </div>

      {/* Filter Chips */}
      <div className="flex flex-wrap items-center gap-2 text-xs">
        <span className="text-muted-foreground font-semibold flex items-center gap-1 mr-1">
          <SlidersHorizontal className="w-3.5 h-3.5" /> Filters:
        </span>

        {DIETARY_OPTIONS.map((opt) => {
          const active = selectedDietary.includes(opt.id);
          return (
            <button
              key={opt.id}
              onClick={() => toggleDietary(opt.id)}
              className={`px-3 py-1.5 rounded-full font-medium transition-all ${
                active
                  ? "bg-primary text-primary-foreground shadow-sm"
                  : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
              }`}
            >
              {opt.label}
            </button>
          );
        })}

        <button
          onClick={() => setTravelSizeOnly((prev) => !prev)}
          className={`px-3 py-1.5 rounded-full font-medium transition-all ${
            travelSizeOnly
              ? "bg-accent text-accent-foreground shadow-sm"
              : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          Travel Size
        </button>

        <button
          onClick={() => setInStockOnly((prev) => !prev)}
          className={`px-3 py-1.5 rounded-full font-medium transition-all ${
            inStockOnly
              ? "bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border border-emerald-500/30"
              : "bg-muted/60 text-muted-foreground hover:bg-muted hover:text-foreground"
          }`}
        >
          In Stock Only
        </button>
      </div>

      {/* Results Section */}
      <div>
        {loading ? (
          <div className="flex flex-col items-center justify-center p-12 space-y-3">
            <Loader2 className="w-8 h-8 animate-spin text-primary" />
            <p className="text-sm text-muted-foreground font-medium">
              Searching physical inventory & shelf locations...
            </p>
          </div>
        ) : query && results.length === 0 ? (
          <div className="text-center p-12 bg-muted/20 rounded-2xl border border-dashed border-border space-y-3">
            <Tag className="w-10 h-10 mx-auto text-muted-foreground stroke-1" />
            <h4 className="font-bold text-base text-foreground">No matching products found</h4>
            <p className="text-xs text-muted-foreground max-w-sm mx-auto">
              We couldn't find items matching &ldquo;{query}&rdquo; in the selected physical stores.
              Try adjusting your dietary filters or switch to <strong>Ask AI</strong> for intelligent recipe mapping.
            </p>
          </div>
        ) : results.length > 0 ? (
          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {results.map((hit) => {
              const priceNum = typeof hit.price === "string" ? parseFloat(hit.price) : hit.price;
              const mrpNum = typeof hit.mrp === "string" ? parseFloat(hit.mrp) : hit.mrp;
              const hasDiscount = mrpNum > priceNum;
              const isAdding = addingId === hit.product_id;

              return (
                <Card
                  key={`${hit.store_id}-${hit.product_id}`}
                  className="p-4 bg-card/70 border-border/80 hover:border-border hover:shadow-md transition-all flex flex-col justify-between space-y-3"
                >
                  <div className="space-y-2">
                    <div className="flex items-start justify-between gap-2">
                      <div className="min-w-0">
                        <span className="text-[11px] font-semibold text-muted-foreground uppercase tracking-wider block">
                          {hit.brand}
                        </span>
                        <h4 className="font-bold text-sm text-foreground leading-snug line-clamp-2">
                          {hit.name}
                        </h4>
                      </div>
                      <Badge variant="secondary" className="text-[10px] shrink-0">
                        {hit.category}
                      </Badge>
                    </div>

                    {/* Physical Location Badge */}
                    <div className="flex items-center gap-1.5 text-xs text-muted-foreground pt-1">
                      <span className="inline-flex items-center gap-1 font-mono text-[11px] px-2 py-0.5 rounded bg-muted/80 text-foreground/90 font-medium">
                        <MapPin className="w-3 h-3 text-primary" />
                        Aisle {hit.aisle} · Bay {hit.bay} · Shelf {hit.shelf}
                      </span>
                    </div>

                    {/* Tags */}
                    <div className="flex flex-wrap gap-1 pt-1">
                      {hit.dietary_tags.map((tag) => (
                        <Badge
                          key={tag}
                          variant="outline"
                          className="text-[9px] uppercase tracking-wide bg-background/50"
                        >
                          {tag.replace("_", " ")}
                        </Badge>
                      ))}
                      {hit.is_travel_size && (
                        <Badge variant="accent" className="text-[9px]">
                          Travel Size
                        </Badge>
                      )}
                      <span className="text-[10px] text-emerald-600 dark:text-emerald-400 font-semibold ml-auto">
                        {hit.stock_qty} in stock
                      </span>
                    </div>
                  </div>

                  {/* Price & Add to Cart */}
                  <div className="pt-3 border-t border-border/60 flex items-center justify-between">
                    <div>
                      <div className="flex items-baseline gap-1.5">
                        <span className="font-extrabold text-base text-foreground">
                          {formatInr(priceNum)}
                        </span>
                        {hasDiscount && (
                          <span className="text-xs text-muted-foreground line-through">
                            {formatInr(mrpNum)}
                          </span>
                        )}
                      </div>
                      {hit.size_label && (
                        <span className="text-[10px] text-muted-foreground block">
                          {hit.size_label}
                        </span>
                      )}
                    </div>

                    <Button
                      size="sm"
                      onClick={() => handleAddToCart(hit)}
                      disabled={isAdding || hit.stock_qty <= 0}
                      className="gap-1.5 text-xs rounded-xl shadow-sm"
                    >
                      {isAdding ? (
                        <Loader2 className="w-3.5 h-3.5 animate-spin" />
                      ) : (
                        <Plus className="w-3.5 h-3.5" />
                      )}
                      Add
                    </Button>
                  </div>
                </Card>
              );
            })}
          </div>
        ) : (
          /* Initial Empty state with quick suggestions */
          <div className="p-8 text-center bg-muted/20 rounded-2xl border border-dashed border-border space-y-4">
            <div className="w-12 h-12 rounded-2xl bg-primary/10 flex items-center justify-center text-primary mx-auto">
              <Search className="w-6 h-6" />
            </div>
            <div className="space-y-1">
              <h4 className="font-bold text-base text-foreground">
                Search 350+ products across 7 physical stores
              </h4>
              <p className="text-xs text-muted-foreground max-w-md mx-auto">
                Explore real inventory with live shelf coordinates. Or click any quick search below:
              </p>
            </div>
            <div className="flex flex-wrap justify-center gap-2 pt-2">
              {[
                "Strawberry",
                "Maida flour",
                "Condensed milk",
                "Almond milk",
                "Travel shampoo",
                "Tortilla chips",
                "Dark chocolate",
              ].map((term) => (
                <button
                  key={term}
                  onClick={() => setQuery(term)}
                  className="px-3 py-1.5 rounded-xl bg-card border border-border/70 hover:border-primary text-xs text-muted-foreground hover:text-foreground transition-all"
                >
                  {term}
                </button>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
