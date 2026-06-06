// frontend/src/features/profile/ProfileBuilder.tsx
import { useState } from "react";
import { createProfile } from "../../api/endpoints";
import type { AssetIn, CifSeed, DebtIn, ExpenseIn } from "../../api/types";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { NumberInput } from "../../components/ui/NumberInput";
import { Select } from "../../components/ui/Select";
import { TextInput } from "../../components/ui/TextInput";
import { useAsync } from "../../hooks/useAsync";
import { useActiveProfile } from "../../state/activeProfile";
import {
  emptyForm, seedToForm, toProfileIn, type GoalFormRow, type ProfileFormState,
} from "./profileForm";

const CLASSES = [
  { value: "FIXED", label: "Cứng" },
  { value: "SEMI_FIXED", label: "Biến đổi" },
  { value: "DISCRETIONARY", label: "Tùy chọn" },
];
const PRIORITIES = [
  { value: "LOW", label: "Thấp" },
  { value: "MEDIUM", label: "Trung bình" },
  { value: "HIGH", label: "Cao" },
  { value: "VERY_HIGH", label: "Rất cao" },
];
const RISKS = [
  { value: "LOW", label: "Thấp" },
  { value: "MEDIUM", label: "Trung bình" },
  { value: "HIGH", label: "Cao" },
];

export function ProfileBuilder({
  initialSeed,
  onCreated,
}: {
  initialSeed: CifSeed | null;
  onCreated: () => void;
}) {
  const [form, setForm] = useState<ProfileFormState>(() =>
    initialSeed ? seedToForm(initialSeed) : emptyForm(),
  );
  const { setActiveProfileId } = useActiveProfile();
  const { run, loading, error } = useAsync(createProfile);

  const update = (patch: Partial<ProfileFormState>) => setForm((f) => ({ ...f, ...patch }));

  async function submit() {
    try {
      const { id } = await run(toProfileIn(form));
      setActiveProfileId(id);
      onCreated();
    } catch {
      /* error surfaced via `error` */
    }
  }

  return (
    <div className="space-y-4">
      {error && <ErrorBanner message={error} />}

      <Card title="Thu nhập (₫/tháng)">
        <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
          <Field label="Lương chính">
            <NumberInput ariaLabel="Lương chính" value={form.income.salary}
              onValueChange={(v) => update({ income: { ...form.income, salary: v } })} />
          </Field>
          <Field label="Thu nhập phụ">
            <NumberInput value={form.income.secondary}
              onValueChange={(v) => update({ income: { ...form.income, secondary: v } })} />
          </Field>
          <Field label="Thưởng/tháng">
            <NumberInput value={form.income.avg_bonus_monthly}
              onValueChange={(v) => update({ income: { ...form.income, avg_bonus_monthly: v } })} />
          </Field>
          <Field label="Thu nhập thụ động">
            <NumberInput value={form.income.passive}
              onValueChange={(v) => update({ income: { ...form.income, passive: v } })} />
          </Field>
        </div>
      </Card>

      <Card title="Quỹ khẩn cấp & Khẩu vị rủi ro">
        <div className="grid grid-cols-2 gap-3">
          <Field label="Quỹ khẩn cấp">
            <NumberInput value={form.emergency_fund}
              onValueChange={(v) => update({ emergency_fund: v })} />
          </Field>
          <Field label="Khẩu vị rủi ro">
            <Select value={form.risk} options={RISKS}
              onChange={(e) => update({ risk: e.target.value as ProfileFormState["risk"] })} />
          </Field>
        </div>
      </Card>

      <Card title="Chi tiêu định kỳ">
        <ListEditor<ExpenseIn>
          rows={form.expenses}
          onChange={(expenses) => update({ expenses })}
          empty={{ category: "", amount: 0, classification: "FIXED" }}
          addLabel="Thêm khoản chi"
          render={(row, set) => (
            <>
              <TextInput placeholder="Danh mục" value={row.category}
                onChange={(e) => set({ ...row, category: e.target.value })} />
              <NumberInput value={row.amount} onValueChange={(v) => set({ ...row, amount: v })} />
              <Select value={row.classification} options={CLASSES}
                onChange={(e) => set({ ...row, classification: e.target.value as typeof row.classification })} />
            </>
          )}
        />
      </Card>

      <Card title="Khoản nợ (trả/tháng)">
        <ListEditor<DebtIn>
          rows={form.debts}
          onChange={(debts) => update({ debts })}
          empty={{ name: "", monthly_payment: 0, balance: null, apr: 0, months_remaining: null, debt_type: "INSTALLMENT" }}
          addLabel="Thêm khoản nợ"
          render={(row, set) => (
            <>
              <TextInput placeholder="Tên khoản nợ" value={row.name}
                onChange={(e) => set({ ...row, name: e.target.value })} />
              <NumberInput value={row.monthly_payment}
                onValueChange={(v) => set({ ...row, monthly_payment: v })} />
              <Select value={row.debt_type}
                options={[
                  { value: "REVOLVING", label: "Tín dụng xoay vòng" },
                  { value: "INSTALLMENT", label: "Trả góp" },
                  { value: "SECURED", label: "Có tài sản đảm bảo" },
                ]}
                onChange={(e) => set({ ...row, debt_type: e.target.value as typeof row.debt_type })} />
            </>
          )}
        />
      </Card>

      <Card title="Tài sản thanh khoản">
        <ListEditor<AssetIn>
          rows={form.assets}
          onChange={(assets) => update({ assets })}
          empty={{ type: "CASH", value: 0, liquidity: "HIGH" }}
          addLabel="Thêm tài sản"
          render={(row, set) => (
            <>
              <Select value={row.type}
                options={[
                  { value: "CASH", label: "Tiền mặt" },
                  { value: "SAVINGS", label: "Tiết kiệm" },
                  { value: "OTHER", label: "Khác" },
                ]}
                onChange={(e) => set({ ...row, type: e.target.value as typeof row.type })} />
              <NumberInput value={row.value} onValueChange={(v) => set({ ...row, value: v })} />
              <Select value={row.liquidity}
                options={[
                  { value: "HIGH", label: "Cao" },
                  { value: "MEDIUM", label: "Trung bình" },
                  { value: "LOW", label: "Thấp" },
                ]}
                onChange={(e) => set({ ...row, liquidity: e.target.value as typeof row.liquidity })} />
            </>
          )}
        />
      </Card>

      <Card title="Mục tiêu tài chính">
        <ListEditor<GoalFormRow>
          rows={form.goals}
          onChange={(goals) => update({ goals })}
          empty={{ name: "", target_amount: 0, deadline: "2030-01-01", priority: "MEDIUM", savings_allocated: 0 }}
          addLabel="Thêm mục tiêu"
          render={(row, set) => (
            <>
              <TextInput placeholder="Tên mục tiêu" value={row.name}
                onChange={(e) => set({ ...row, name: e.target.value })} />
              <NumberInput value={row.target_amount}
                onValueChange={(v) => set({ ...row, target_amount: v })} />
              <input type="date" value={row.deadline}
                onChange={(e) => set({ ...row, deadline: e.target.value })}
                className="rounded-lg border border-slate-300 px-3 py-2 text-sm" />
              <Select value={row.priority} options={PRIORITIES}
                onChange={(e) => set({ ...row, priority: e.target.value as typeof row.priority })} />
            </>
          )}
        />
      </Card>

      <Button onClick={submit} disabled={loading}>
        {loading ? "Đang tạo…" : "Tạo hồ sơ"}
      </Button>
    </div>
  );
}

function ListEditor<T>({
  rows, onChange, empty, addLabel, render,
}: {
  rows: T[];
  onChange: (rows: T[]) => void;
  empty: T;
  addLabel: string;
  render: (row: T, set: (next: T) => void) => React.ReactNode;
}) {
  return (
    <div className="space-y-2">
      {rows.map((row, i) => (
        <div key={i} className="flex flex-wrap items-center gap-2">
          {render(row, (next) => onChange(rows.map((r, j) => (j === i ? next : r))))}
          <Button variant="ghost" onClick={() => onChange(rows.filter((_, j) => j !== i))}>
            Xóa
          </Button>
        </div>
      ))}
      <Button variant="ghost" onClick={() => onChange([...rows, { ...empty }])}>
        {addLabel}
      </Button>
    </div>
  );
}
