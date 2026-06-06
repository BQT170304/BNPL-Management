// frontend/src/App.tsx
import { useState } from "react";
import type { CifSeed } from "./api/types";
import { Button } from "./components/ui/Button";
import { AnalysisDashboard } from "./features/analysis/AnalysisDashboard";
import { PurchaseEvaluator } from "./features/advisory/PurchaseEvaluator";
import { LoginScreen } from "./features/auth/LoginScreen";
import { CashflowForecast } from "./features/forecast/CashflowForecast";
import { CifImport } from "./features/ingestion/CifImport";
import { ProfileBuilder } from "./features/profile/ProfileBuilder";
import { ActiveProfileProvider, useActiveProfile } from "./state/activeProfile";
import { AuthProvider, useAuth } from "./state/auth";

type Section = "import" | "profile" | "analysis" | "evaluate" | "forecast";

const USERNAME = "nguyenvana";

const TABS: { key: Section; label: string }[] = [
  { key: "import", label: "1. Nhập CIF" },
  { key: "profile", label: "2. Hồ sơ" },
  { key: "analysis", label: "3. Phân tích" },
  { key: "evaluate", label: "4. Đánh giá" },
  { key: "forecast", label: "5. Dự báo" },
];

function Shell() {
  const [section, setSection] = useState<Section>("import");
  const [seed, setSeed] = useState<CifSeed | null>(null);
  const { activeProfileId } = useActiveProfile();
  const { logout } = useAuth();

  return (
    <div className="mx-auto min-h-screen max-w-5xl px-5 py-6 sm:px-6 lg:px-8">
      <div className="mb-6 flex flex-col gap-4 rounded-card bg-bnpl-navy p-5 text-white shadow-bnpl-soft sm:flex-row sm:items-start sm:justify-between">
        <div>
          <p className="mb-2 font-mono text-xs font-medium uppercase tracking-[0.08em] text-bnpl-amber">
            Responsible Wealth Director
          </p>
          <h1 className="mb-1 text-3xl font-extrabold leading-tight tracking-normal">BNPL Assistant</h1>
          <p className="max-w-2xl text-sm leading-6 text-slate-200">
            Tư vấn tài chính cá nhân với góc nhìn kiểm soát rủi ro trước khi mua trả sau.
          </p>
        </div>
        <div className="flex items-center gap-3 text-sm text-slate-200">
          <span className="font-mono text-xs uppercase tracking-[0.08em]">{USERNAME}</span>
          <Button
            variant="ghost"
            className="border-white/20 bg-white/10 text-white hover:bg-white/15 hover:text-white"
            onClick={logout}
          >
            Đăng xuất
          </Button>
        </div>
      </div>

      <nav className="mb-6 flex flex-wrap gap-2 rounded-card bg-white p-2 shadow-bnpl">
        {TABS.map((t) => (
          <Button
            key={t.key}
            variant={section === t.key ? "primary" : "ghost"}
            className="min-h-12"
            onClick={() => setSection(t.key)}
          >
            {t.label}
          </Button>
        ))}
      </nav>

      {section === "import" && (
        <CifImport
          onSeed={(s) => {
            setSeed(s);
            setSection("profile");
          }}
        />
      )}
      {section === "profile" && <ProfileBuilder initialSeed={seed} onCreated={() => setSection("analysis")} />}
      {section === "analysis" && (activeProfileId ? <AnalysisDashboard profileId={activeProfileId} /> : <NoProfile />)}
      {section === "evaluate" && (activeProfileId ? <PurchaseEvaluator profileId={activeProfileId} /> : <NoProfile />)}
      {section === "forecast" && <CashflowForecast />}
    </div>
  );
}

function Gate() {
  const { token } = useAuth();
  if (!token) return <LoginScreen />;
  return (
    <ActiveProfileProvider>
      <Shell />
    </ActiveProfileProvider>
  );
}

function NoProfile() {
  return (
    <div className="rounded-card border border-bnpl-orange/30 bg-orange-50 px-4 py-3 text-sm text-amber-800 shadow-bnpl">
      Chưa có hồ sơ. Hãy tạo hồ sơ ở bước 2 trước.
    </div>
  );
}

export function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  );
}
