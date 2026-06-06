// frontend/src/App.tsx
import { useState } from "react";
import type { CifSeed } from "./api/types";
import { Button } from "./components/ui/Button";
import { AnalysisDashboard } from "./features/analysis/AnalysisDashboard";
import { PurchaseEvaluator } from "./features/advisory/PurchaseEvaluator";
import { CifImport } from "./features/ingestion/CifImport";
import { ProfileBuilder } from "./features/profile/ProfileBuilder";
import { ActiveProfileProvider, useActiveProfile } from "./state/activeProfile";

type Section = "import" | "profile" | "analysis" | "evaluate";

const TABS: { key: Section; label: string }[] = [
  { key: "import", label: "1. Nhập CIF" },
  { key: "profile", label: "2. Hồ sơ" },
  { key: "analysis", label: "3. Phân tích" },
  { key: "evaluate", label: "4. Đánh giá" },
];

function Shell() {
  const [section, setSection] = useState<Section>("import");
  const [seed, setSeed] = useState<CifSeed | null>(null);
  const { activeProfileId } = useActiveProfile();

  return (
    <div className="mx-auto max-w-4xl p-6">
      <h1 className="mb-1 text-2xl font-bold text-slate-800">BNPL Assistant</h1>
      <p className="mb-5 text-sm text-slate-500">Tư vấn tài chính cá nhân</p>

      <nav className="mb-6 flex flex-wrap gap-2">
        {TABS.map((t) => (
          <Button key={t.key}
            variant={section === t.key ? "primary" : "ghost"}
            onClick={() => setSection(t.key)}>
            {t.label}
          </Button>
        ))}
      </nav>

      {section === "import" && (
        <CifImport onSeed={(s) => { setSeed(s); setSection("profile"); }} />
      )}
      {section === "profile" && (
        <ProfileBuilder initialSeed={seed} onCreated={() => setSection("analysis")} />
      )}
      {section === "analysis" && (
        activeProfileId
          ? <AnalysisDashboard profileId={activeProfileId} />
          : <NoProfile />
      )}
      {section === "evaluate" && (
        activeProfileId
          ? <PurchaseEvaluator profileId={activeProfileId} />
          : <NoProfile />
      )}
    </div>
  );
}

function NoProfile() {
  return (
    <div className="rounded-lg border border-amber-200 bg-amber-50 px-4 py-3 text-sm text-amber-700">
      Chưa có hồ sơ. Hãy tạo hồ sơ ở bước 2 trước.
    </div>
  );
}

export function App() {
  return (
    <ActiveProfileProvider>
      <Shell />
    </ActiveProfileProvider>
  );
}
