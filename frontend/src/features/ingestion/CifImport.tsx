// frontend/src/features/ingestion/CifImport.tsx
import { useState } from "react";
import { getCifSeed } from "../../api/endpoints";
import type { CifSeed } from "../../api/types";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { Select } from "../../components/ui/Select";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";

const DEMO_CIF = "10000327";

export function CifImport({ onSeed }: { onSeed: (seed: CifSeed) => void }) {
  const seedCall = useAsync(getCifSeed);
  const [strategy, setStrategy] = useState<"latest" | "average">("latest");

  async function use() {
    const seed = await seedCall.run(DEMO_CIF, strategy).catch(() => null);
    if (seed) onSeed(seed);
  }

  return (
    <div className="space-y-4">
      {seedCall.error && <ErrorBanner message={seedCall.error} />}
      <Card title="Nhập dữ liệu từ CIF ngân hàng">
        <p className="mb-3 text-sm text-slate-600">
          Dùng dữ liệu CIF mặc định <strong>{DEMO_CIF}</strong> để khởi tạo hồ sơ.
        </p>
        <div className="grid grid-cols-1 gap-3 md:grid-cols-2">
          <Field label="Cách tính">
            <Select value={strategy}
              onChange={(e) => setStrategy(e.target.value as "latest" | "average")}
              options={[
                { value: "latest", label: "Tháng gần nhất" },
                { value: "average", label: "Trung bình" },
              ]} />
          </Field>
          <div className="flex items-end">
            <Button onClick={use} disabled={seedCall.loading}>
              {seedCall.loading ? "Đang lấy…" : "Dùng dữ liệu này"}
            </Button>
          </div>
        </div>
        {seedCall.data && (
          <p className="mt-3 text-sm text-slate-600">
            Thu nhập {formatVnd(seedCall.data.income)} · Chi tiêu{" "}
            {formatVnd(seedCall.data.expense)} · Nợ {formatVnd(seedCall.data.debt_payment)}
          </p>
        )}
      </Card>
    </div>
  );
}
