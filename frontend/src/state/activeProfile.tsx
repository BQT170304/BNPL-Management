import { createContext, useCallback, useContext, useState, type ReactNode } from "react";

const KEY = "bnpl.activeProfileId";

interface Ctx {
  activeProfileId: string | null;
  setActiveProfileId: (id: string) => void;
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
  return (
    <ActiveProfileContext.Provider value={{ activeProfileId, setActiveProfileId }}>
      {children}
    </ActiveProfileContext.Provider>
  );
}

export function useActiveProfile(): Ctx {
  const ctx = useContext(ActiveProfileContext);
  if (!ctx) throw new Error("useActiveProfile must be used within ActiveProfileProvider");
  return ctx;
}
