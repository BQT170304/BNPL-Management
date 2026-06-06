import { useState } from "react";
import type { CifSeed, ProfileIn } from "./api/types";
import { Button } from "./components/ui/Button";
import { PurchaseEvaluator } from "./features/advisory/PurchaseEvaluator";
import { HealthSidebar } from "./features/analysis/HealthSidebar";
import { LoginScreen } from "./features/auth/LoginScreen";
import { CifImport } from "./features/ingestion/CifImport";
import { ProfileBuilder } from "./features/profile/ProfileBuilder";
import { ActiveProfileProvider, useActiveProfile } from "./state/activeProfile";
import { AuthProvider, useAuth } from "./state/auth";

// ── setup wizard ──────────────────────────────────────────────────────────────

type SetupStep = "import" | "profile";

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

function SetupWizard({
  step,
  seed,
  onSeed,
  onSaved,
}: {
  step: SetupStep;
  seed: CifSeed | null;
  onSeed: (s: CifSeed) => void;
  onSaved: (profile: ProfileIn) => void;
}) {
  return (
    <div className="mx-auto max-w-xl px-4 py-10">
      <div className="mb-8 flex items-center gap-3">
        <StepBubble n={1} active={step === "import"} done={step === "profile"} label="Dữ liệu ngân hàng" />
        <div className="h-px flex-1 bg-slate-200" />
        <StepBubble n={2} active={step === "profile"} done={false} label="Hồ sơ tài chính" />
      </div>
      {step === "import" && <CifImport onSeed={onSeed} />}
      {step === "profile" && <ProfileBuilder initialSeed={seed} mode="create" onSaved={onSaved} />}
    </div>
  );
}

// ── edit profile ──────────────────────────────────────────────────────────────

function EditProfileScreen({
  currentProfile,
  onSaved,
  onCancel,
}: {
  currentProfile: ProfileIn | null;
  onSaved: (profile: ProfileIn) => void;
  onCancel: () => void;
}) {
  return (
    <div className="mx-auto max-w-xl px-4 py-6">
      <div className="mb-6 flex items-center justify-between">
        <h2 className="text-lg font-semibold text-slate-800">Cập nhật hồ sơ tài chính</h2>
        <Button variant="ghost" onClick={onCancel}>Huỷ</Button>
      </div>
      <ProfileBuilder
        initialProfile={currentProfile}
        mode="update"
        onSaved={onSaved}
      />
    </div>
  );
}

// ── main shell ────────────────────────────────────────────────────────────────

function Shell() {
  const [setupStep, setSetupStep] = useState<SetupStep>("import");
  const [seed, setSeed] = useState<CifSeed | null>(null);
  const [savedProfile, setSavedProfile] = useState<ProfileIn | null>(null);
  const [editingProfile, setEditingProfile] = useState(false);
  const [refreshKey, setRefreshKey] = useState(0);

  const { activeProfileId } = useActiveProfile();
  const { logout } = useAuth();
  const hasProfile = Boolean(activeProfileId);

  function handleProfileSaved(profile: ProfileIn) {
    setSavedProfile(profile);
    setEditingProfile(false);
    setRefreshKey((k) => k + 1);
  }

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
          seed={seed}
          onSeed={(s) => { setSeed(s); setSetupStep("profile"); }}
          onSaved={(profile) => { setSavedProfile(profile); }}
        />
      ) : editingProfile ? (
        <EditProfileScreen
          currentProfile={savedProfile}
          onSaved={handleProfileSaved}
          onCancel={() => setEditingProfile(false)}
        />
      ) : (
        <div className="mx-auto max-w-6xl px-4 py-6">
          <div className="flex flex-col gap-5 md:flex-row md:items-start">
            <aside className="w-full flex-shrink-0 md:w-72">
              <HealthSidebar
                key={refreshKey}
                profileId={activeProfileId!}
                onEditProfile={() => setEditingProfile(true)}
              />
            </aside>
            <main className="min-w-0 flex-1">
              <PurchaseEvaluator key={refreshKey} profileId={activeProfileId!} />
            </main>
          </div>
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
