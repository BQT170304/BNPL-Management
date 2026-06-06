// frontend/src/features/ingestion/CifImport.tsx
import { useEffect, useState } from "react";
import { getCifSeed, listCifs } from "../../api/endpoints";
import type { CifSeed } from "../../api/types";
import { Button } from "../../components/ui/Button";
import { Card } from "../../components/ui/Card";
import { ErrorBanner } from "../../components/ui/ErrorBanner";
import { Field } from "../../components/ui/Field";
import { Select } from "../../components/ui/Select";
import { Spinner } from "../../components/ui/Spinner";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";

export function CifImport({ onSeed }: { onSeed: (seed: CifSeed) => void }) {
  const list = useAsync(listCifs);
  const seedCall = useAsync(getCifSeed);
  const [cif, setCif] = useState("");
  const [strategy, setStrategy] = useState<"latest" | "average">("latest");

  useEffect(() => {
    list.run().then((cifs) => setCif(cifs[0] ?? "")).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  async function use() {
    if (!cif) return;
    const seed = await seedCall.run(cif, strategy).catch(() => null);
    if (seed) onSeed(seed);
  }

  if (list.loading) return <Spinner />;

  return (
    <div className="space-y-4">
      {(list.error || seedCall.error) && (
        <ErrorBanner message={list.error ?? seedCall.error ?? ""} />
      )}
      <Card title="Nhập dữ liệu từ CIF ngân hàng">
        <div className="grid grid-cols-1 gap-3 md:grid-cols-3">
          <Field label="Chọn CIF">
            <Select value={cif} onChange={(e) => setCif(e.target.value)}
              options={(list.data ?? []).map((c) => ({ value: c, label: c }))} />
          </Field>
          <Field label="Cách tính">
            <Select value={strategy}
              onChange={(e) => setStrategy(e.target.value as "latest" | "average")}
              options={[
                { value: "latest", label: "Tháng gần nhất" },
                { value: "average", label: "Trung bình" },
              ]} />
          </Field>
          <div className="flex items-end">
            <Button onClick={use} disabled={!cif || seedCall.loading}>
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
