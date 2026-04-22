import { createContext, useContext, type ReactNode } from "react";
import type { RootStore } from "./root.store";

const StoreContext = createContext<RootStore | null>(null);

interface StoreProviderProps {
  children: ReactNode;
  store: RootStore;
}

export function StoreProvider({ children, store }: StoreProviderProps) {
  return <StoreContext.Provider value={store}>{children}</StoreContext.Provider>;
}

export function useStores(): RootStore {
  const store = useContext(StoreContext);
  if (store === null) {
    throw new Error("useStores must be used within a StoreProvider");
  }
  return store;
}
