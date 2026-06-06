import { useState } from "react";
import type { ProfileIn } from "./api/types";
import { Button } from "./components/ui/Button";
import { PurchaseEvaluator } from "./features/advisory/PurchaseEvaluator";
import { HealthSidebar } from "./features/analysis/HealthSidebar";
import { LoginScreen } from "./features/auth/LoginScreen";
import { ForecastSection } from "./features/forecasting/ForecastSection";
import { TransactionImport } from "./features/ingestion/TransactionImport";
import { ProfileBuilder } from "./features/profile/ProfileBuilder";
import { ActiveProfileProvider, useActiveProfile } from "./state/activeProfile";
import { AuthProvider, useAuth } from "./state/auth";

// ── shared wizard step indicator ──────────────────────────────────────────────

type WizardStep = "import" | "review";

function StepBubble({ n, active, done, label }: {
  n: number; active: boolean; done: boolean; label: string;
}) {
  return (
    <div className="flex items-center gap-2">
      <div className={`flex h-7 w-7 items-center justify-center rounded-full text-xs font-bold transition-colors ${
        done    ? "bg-emerald-500 text-white" :
        active  ? "bg-indigo-600 text-white"  :
                  "bg-slate-200 text-slate-400"
      }`}>
        {done ? "✓" : n}
      </div>
      <span className={`text-sm ${active ? "font-semibold text-slate-800" : "text-slate-400"}`}>
        {label}
      </span>
    </div>
  );
}

// ── setup wizard (first-time onboarding) ──────────────────────────────────────

function SetupWizard({
  step,
  extractedProfile,
  onExtracted,
  onSaved,
  onBack,
}: {
  step: WizardStep;
  extractedProfile: ProfileIn | null;
  onExtracted: (p: ProfileIn, cif?: string) => void;
  onSaved: (p: ProfileIn) => void;
  onBack: () => void;
}) {
  const emptyProfile: ProfileIn = {
    id: "", income: { salary: 0, secondary: 0, avg_bonus_monthly: 0, passive: 0 },
    risk: "MEDIUM", emergency_fund: 0, expenses: [], debts: [], assets: [], goals: [],
  };

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <div className="mb-8 flex items-center gap-3">
        <StepBubble n={1} active={step === "import"} done={step === "review"} label="Nhập file giao dịch" />
        <div className="h-px flex-1 bg-slate-200" />
        <StepBubble n={2} active={step === "review"} done={false} label="Xem lại hồ sơ" />
      </div>

      {step === "import" && (
        <div className="space-y-3">
          <TransactionImport onExtracted={onExtracted} />
          <div className="text-center">
            <button
              onClick={() => onExtracted(emptyProfile)}
              className="text-sm text-slate-400 underline underline-offset-2 hover:text-slate-600 transition-colors"
            >
              Bỏ qua — nhập thông tin thủ công
            </button>
          </div>
        </div>
      )}

      {step === "review" && (
        <div className="space-y-4">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors"
          >
            ← Quay lại nhập file
          </button>
          <ProfileBuilder
            initialProfile={extractedProfile?.income?.salary ? extractedProfile : null}
            mode="create"
            onSaved={onSaved}
          />
        </div>
      )}
    </div>
  );
}

// ── update wizard (same flow as setup, but saves to existing profile) ─────────

function UpdateWizard({
  step,
  currentProfile,
  extractedProfile,
  onExtracted,
  onSaved,
  onBack,
  onCancel,
}: {
  step: WizardStep;
  currentProfile: ProfileIn | null;
  extractedProfile: ProfileIn | null;
  onExtracted: (p: ProfileIn, cif?: string) => void;
  onSaved: (p: ProfileIn) => void;
  onBack: () => void;
  onCancel: () => void;
}) {
  // Merge: extracted values on top of current profile (preserves id + goals/debts
  // that can't be extracted from transactions)
  const reviewProfile: ProfileIn | null =
    extractedProfile && currentProfile
      ? { ...currentProfile, ...extractedProfile, id: currentProfile.id }
      : extractedProfile ?? currentProfile;

  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">Cập nhật hồ sơ tài chính</h2>
        <Button variant="ghost" onClick={onCancel}>Huỷ</Button>
      </div>

      <div className="mb-8 flex items-center gap-3">
        <StepBubble n={1} active={step === "import"} done={step === "review"} label="Nhập file giao dịch" />
        <div className="h-px flex-1 bg-slate-200" />
        <StepBubble n={2} active={step === "review"} done={false} label="Xem lại & lưu" />
      </div>

      {step === "import" && (
        <div className="space-y-3">
          <TransactionImport onExtracted={onExtracted} />
          <div className="text-center">
            <button
              onClick={() => onExtracted(currentProfile ?? { id: "", income: { salary: 0, secondary: 0, avg_bonus_monthly: 0, passive: 0 }, risk: "MEDIUM", emergency_fund: 0, expenses: [], debts: [], assets: [], goals: [] })}
              className="text-sm text-slate-400 underline underline-offset-2 hover:text-slate-600 transition-colors"
            >
              Bỏ qua — chỉnh sửa thủ công
            </button>
          </div>
        </div>
      )}

      {step === "review" && (
        <div className="space-y-4">
          <button
            onClick={onBack}
            className="flex items-center gap-1.5 text-sm text-slate-400 hover:text-slate-600 transition-colors"
          >
            ← Quay lại nhập file
          </button>
          <ProfileBuilder
            initialProfile={reviewProfile}
            mode="update"
            onSaved={onSaved}
          />
        </div>
      )}
    </div>
  );
}

// ── main shell ────────────────────────────────────────────────────────────────

function Shell() {
  const [setupStep, setSetupStep]         = useState<WizardStep>("import");
  const [extractedProfile, setExtractedProfile] = useState<ProfileIn | null>(null);
  const [savedProfile, setSavedProfile]   = useState<ProfileIn | null>(null);
  const [importedCif, setImportedCif]     = useState<string | null>(null);

  const [updating, setUpdating]               = useState(false);
  const [updateStep, setUpdateStep]           = useState<WizardStep>("import");
  const [updateExtracted, setUpdateExtracted] = useState<ProfileIn | null>(null);

  const [refreshKey, setRefreshKey] = useState(0);

  const { activeProfileId, setActiveProfileId, resetProfile } = useActiveProfile();
  const { logout } = useAuth();
  const hasProfile = Boolean(activeProfileId);

  // ── setup handlers ──────────────────────────────────────────────────────────

  function handleExtracted(p: ProfileIn, cif?: string) {
    setExtractedProfile(p);
    if (cif) setImportedCif(cif);
    setSetupStep("review");
  }

  function handleBackToImport() {
    setSetupStep("import");
    setExtractedProfile(null);
    setImportedCif(null);
  }

  function handleProfileNotFound() {
    resetProfile();
    setSavedProfile(null);
    setExtractedProfile(null);
    setImportedCif(null);
    setSetupStep("import");
    setUpdating(false);
  }

  // ── update handlers ─────────────────────────────────────────────────────────

  function handleStartUpdate() {
    setUpdateStep("import");
    setUpdateExtracted(null);
    setUpdating(true);
  }

  function handleUpdateExtracted(p: ProfileIn, cif?: string) {
    setUpdateExtracted(p);
    if (cif) setImportedCif(cif);
    setUpdateStep("review");
  }

  function handleUpdateSaved(profile: ProfileIn) {
    setSavedProfile(profile);
    setUpdating(false);
    setRefreshKey((k) => k + 1);
  }

  function handleCancelUpdate() {
    setUpdating(false);
  }

  // ── render ──────────────────────────────────────────────────────────────────

  return (
    <div className="min-h-screen bg-slate-50">
      <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 px-6 py-3 backdrop-blur-sm">
        <div className="mx-auto flex max-w-6xl items-center justify-between">
          <div>
            <span className="text-base font-bold text-slate-800">BNPL Assistant</span>
            <span className="ml-2 text-xs text-slate-400">Tư vấn tài chính cá nhân</span>
          </div>
          <Button variant="ghost" onClick={logout}>Đăng xuất</Button>
        </div>
      </header>

      {!hasProfile ? (
        <SetupWizard
          step={setupStep}
          extractedProfile={extractedProfile}
          onExtracted={handleExtracted}
          onSaved={(p) => {
            setSavedProfile(p);
            if (p.id) setActiveProfileId(p.id);
          }}
          onBack={handleBackToImport}
        />
      ) : updating ? (
        <UpdateWizard
          step={updateStep}
          currentProfile={savedProfile}
          extractedProfile={updateExtracted}
          onExtracted={handleUpdateExtracted}
          onSaved={handleUpdateSaved}
          onBack={() => { setUpdateStep("import"); setUpdateExtracted(null); }}
          onCancel={handleCancelUpdate}
        />
      ) : (
        <div className="mx-auto max-w-6xl px-4 py-6 space-y-5">
          <div className="flex flex-col gap-5 md:flex-row md:items-start">
            <aside className="w-full flex-shrink-0 md:w-72">
              <HealthSidebar
                key={refreshKey}
                profileId={activeProfileId!}
                onEditProfile={handleStartUpdate}
                onProfileNotFound={handleProfileNotFound}
              />
            </aside>
            <main className="min-w-0 flex-1">
              <PurchaseEvaluator key={refreshKey} profileId={activeProfileId!} />
            </main>
          </div>

          {importedCif && (
            <ForecastSection cif={importedCif} profileId={activeProfileId!} />
          )}
        </div>
      )}
    </div>
  );
}

// ── root ──────────────────────────────────────────────────────────────────────

function Gate() {
  const { token } = useAuth();
  if (!token) return <LoginScreen />;
  return (
    <ActiveProfileProvider>
      <Shell />
    </ActiveProfileProvider>
  );
}

export function App() {
  return (
    <AuthProvider>
      <Gate />
    </AuthProvider>
  );
}
