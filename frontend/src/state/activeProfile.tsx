import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

const KEY = "bnpl.activeProfileId";

interface Ctx {
  activeProfileId: string | null;
  setActiveProfileId: (id: string) => void;
  resetProfile: () => void;
}

const ActiveProfileContext = createContext<Ctx | null>(null);

export function ActiveProfileProvider({ children }: { children: ReactNode }) {
  const [activeProfileId, setId] = useState<string | null>(
    () => localStorage.getItem(KEY),
  );
  const setActiveProfileId = useCallback((id: string) => {
    localStorage.setItem(KEY, id);
    setId(id);
  }, []);
  const resetProfile = useCallback(() => {
    localStorage.removeItem(KEY);
    setId(null);
  }, []);
  return (
    <ActiveProfileContext.Provider value={{ activeProfileId, setActiveProfileId, resetProfile }}>
      {children}
    </ActiveProfileContext.Provider>
  );
}

export function useActiveProfile(): Ctx {
  const ctx = useContext(ActiveProfileContext);
  if (!ctx) throw new Error("useActiveProfile must be used within ActiveProfileProvider");
  return ctx;
}
