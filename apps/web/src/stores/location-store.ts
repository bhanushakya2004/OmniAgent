import { create } from "zustand";
import { persist } from "zustand/middleware";

interface LocationState {
  lat: number | null;
  lng: number | null;
  city: string | null;
  permission: "prompt" | "granted" | "denied";
  setLocation: (lat: number, lng: number, city?: string) => void;
  setPermission: (permission: "prompt" | "granted" | "denied") => void;
  resetLocation: () => void;
}

export const useLocationStore = create<LocationState>()(
  persist(
    (set) => ({
      lat: 12.9719, // Default to Bengaluru Indiranagar for golden demo
      lng: 77.6412,
      city: "Bengaluru",
      permission: "prompt",
      setLocation: (lat, lng, city = "Detected Location") => set({ lat, lng, city }),
      setPermission: (permission) => set({ permission }),
      resetLocation: () => set({ lat: null, lng: null, city: null, permission: "prompt" }),
    }),
    {
      name: "omni-location-storage",
    }
  )
);
