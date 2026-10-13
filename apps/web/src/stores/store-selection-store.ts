import { create } from "zustand";
import { persist } from "zustand/middleware";

interface StoreSelectionState {
  selectedStoreIds: string[];
  toggleStore: (storeId: string) => void;
  selectStores: (storeIds: string[]) => void;
  clearSelection: () => void;
  isSelected: (storeId: string) => boolean;
}

export const useStoreSelectionStore = create<StoreSelectionState>()(
  persist(
    (set, get) => ({
      selectedStoreIds: [],
      toggleStore: (storeId: string) => {
        const current = get().selectedStoreIds;
        if (current.includes(storeId)) {
          set({ selectedStoreIds: current.filter((id) => id !== storeId) });
        } else {
          set({ selectedStoreIds: [...current, storeId] });
        }
      },
      selectStores: (storeIds: string[]) => set({ selectedStoreIds: storeIds }),
      clearSelection: () => set({ selectedStoreIds: [] }),
      isSelected: (storeId: string) => get().selectedStoreIds.includes(storeId),
    }),
    {
      name: "omni-selected-stores",
    }
  )
);
