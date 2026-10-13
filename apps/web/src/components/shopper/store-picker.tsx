"use client";

import React, { useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { MapPin, Navigation, Check, Store as StoreIcon, ShieldAlert, Sparkles } from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { queryKeys } from "@/lib/query-keys";
import { useLocationStore } from "@/stores/location-store";
import { useStoreSelectionStore } from "@/stores/store-selection-store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";

interface StoreNearbyItem {
  id: string;
  name: string;
  address: string;
  city: string;
  distance_km: number;
  is_active: boolean;
  total_skus?: number;
  available_aisles?: number[];
  categories?: string[];
}

const DEMO_LOCATIONS = [
  { name: "Bengaluru (Indiranagar)", lat: 12.9719, lng: 77.6412, city: "Bengaluru" },
  { name: "Mumbai (Bandra West)", lat: 19.0596, lng: 72.8295, city: "Mumbai" },
  { name: "Delhi (Connaught Place)", lat: 28.6315, lng: 77.2167, city: "Delhi" },
  { name: "Hyderabad (Hitec City)", lat: 17.4486, lng: 78.3908, city: "Hyderabad" },
];

export function StorePicker(): React.JSX.Element {
  const { lat, lng, city, setLocation } = useLocationStore();
  const { selectedStoreIds, toggleStore, selectStores } = useStoreSelectionStore();

  const { data: stores, isLoading, error } = useQuery({
    queryKey: queryKeys.stores.nearby(lat ?? 12.9719, lng ?? 77.6412, 30),
    queryFn: async () => {
      const res = await apiClient.get<StoreNearbyItem[]>(
        `/api/v1/stores/nearby?lat=${lat ?? 12.9719}&lng=${lng ?? 77.6412}&radius_km=30`
      );
      return res;
    },
    enabled: lat !== null && lng !== null,
  });

  // Automatically select the closest store by default if none selected
  useEffect(() => {
    if (stores && stores.length > 0 && selectedStoreIds.length === 0) {
      selectStores([stores[0].id]);
    }
  }, [stores, selectedStoreIds.length, selectStores]);

  const requestBrowserLocation = () => {
    if (navigator.geolocation) {
      navigator.geolocation.getCurrentPosition(
        (pos) => {
          setLocation(pos.coords.latitude, pos.coords.longitude, "My Location");
        },
        (err) => {
          console.warn("Geolocation denied, using Indiranagar", err);
          setLocation(12.9719, 77.6412, "Bengaluru");
        }
      );
    }
  };

  const handleSelectAll = () => {
    if (stores) {
      selectStores(stores.map((s) => s.id));
    }
  };

  return (
    <Card className="p-6 bg-card/60 backdrop-blur-md border-border/80 shadow-md">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-4 border-b border-border/60">
        <div>
          <div className="flex items-center gap-2">
            <MapPin className="w-5 h-5 text-primary animate-pulse" />
            <h2 className="text-xl font-bold tracking-tight">Select Physical Stores</h2>
            <Badge variant="accent">
              {selectedStoreIds.length} {selectedStoreIds.length === 1 ? "Store" : "Stores"} Selected
            </Badge>
          </div>
          <p className="text-sm text-muted-foreground mt-1">
            OmniMission searches real-time inventory and shelf coordinates across selected nearby branches.
          </p>
        </div>

        <div className="flex items-center gap-2 flex-wrap">
          <Button variant="outline" size="sm" onClick={requestBrowserLocation}>
            <Navigation className="w-3.5 h-3.5 mr-1.5 text-primary" />
            Detect GPS
          </Button>
          <Button variant="ghost" size="sm" onClick={handleSelectAll}>
            Select All Stores
          </Button>
        </div>
      </div>

      {/* Quick City Presets */}
      <div className="flex items-center gap-2 pt-4 flex-wrap">
        <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          Demo Cities:
        </span>
        {DEMO_LOCATIONS.map((loc) => {
          const isActive = city === loc.city;
          return (
            <button
              key={loc.name}
              type="button"
              onClick={() => setLocation(loc.lat, loc.lng, loc.city)}
              className={`px-3 py-1 rounded-full text-xs font-medium transition-all ${
                isActive
                  ? "bg-primary text-primary-foreground shadow-sm scale-105"
                  : "bg-muted/70 text-foreground hover:bg-muted"
              }`}
            >
              {loc.name}
            </button>
          );
        })}
      </div>

      {/* Store Cards Grid */}
      <div className="mt-5 grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
        {isLoading && (
          <div className="col-span-full py-8 text-center text-sm text-muted-foreground">
            <div className="inline-block w-6 h-6 border-2 border-primary border-t-transparent rounded-full animate-spin mb-2" />
            <p>Locating closest physical stores...</p>
          </div>
        )}

        {error && (
          <div className="col-span-full p-4 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-sm flex items-center gap-2">
            <ShieldAlert className="w-4 h-4 shrink-0" />
            <span>Could not load stores. Please ensure backend is reachable.</span>
          </div>
        )}

        {stores?.map((store) => {
          const isSelected = selectedStoreIds.includes(store.id);
          return (
            <div
              key={store.id}
              onClick={() => toggleStore(store.id)}
              className={`relative cursor-pointer p-4 rounded-xl border transition-all ${
                isSelected
                  ? "border-primary bg-primary/5 shadow-sm ring-1 ring-primary/40"
                  : "border-border/70 hover:border-border hover:bg-muted/30"
              }`}
            >
              <div className="flex items-start justify-between gap-3">
                <div className="flex items-center gap-2.5">
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center transition-colors ${
                      isSelected ? "bg-primary text-primary-foreground" : "bg-muted text-muted-foreground"
                    }`}
                  >
                    <StoreIcon className="w-4 h-4" />
                  </div>
                  <div>
                    <h4 className="font-semibold text-sm leading-tight text-foreground">
                      {store.name}
                    </h4>
                    <p className="text-xs text-muted-foreground mt-0.5">{store.address}</p>
                  </div>
                </div>

                <div
                  className={`w-5 h-5 rounded-md border flex items-center justify-center shrink-0 transition-colors ${
                    isSelected
                      ? "bg-primary border-primary text-primary-foreground"
                      : "border-muted-foreground/30 bg-background"
                  }`}
                >
                  {isSelected && <Check className="w-3.5 h-3.5 stroke-[3]" />}
                </div>
              </div>

              <div className="mt-3 pt-3 border-t border-border/40 flex items-center justify-between text-xs">
                <span className="font-semibold text-primary">
                  {store.distance_km < 1
                    ? `${Math.round(store.distance_km * 1000)} m away`
                    : `${store.distance_km.toFixed(1)} km away`}
                </span>
                <span className="text-muted-foreground">
                  {store.available_aisles?.length ?? 4} Aisles • {store.total_skus ?? 28} SKUs
                </span>
              </div>
            </div>
          );
        })}
      </div>
    </Card>
  );
}
