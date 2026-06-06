import type { ExplanationOut } from "../../api/types";
import { Card } from "../../components/ui/Card";

const SECTIONS = [
  { key: "payment_recommendation" as const, title: "Nên trả thẳng hay trả góp?" },
  { key: "goal_delay_summary" as const,     title: "Ảnh hưởng đến mục tiêu tài chính" },
  { key: "emergency_fund_assessment" as const, title: "Quỹ khẩn cấp" },
  { key: "balanced_option_summary" as const,   title: "Phương án cân bằng nhất" },
];

export function ExplanationPanel({ data }: { data: ExplanationOut }) {
  return (
    <Card title={`Giải thích chi tiết ${data.source === "llm" ? "(AI)" : ""}`}>
      <div className="space-y-4">
        {SECTIONS.map(({ key, title }) => (
          <div key={key}>
            <p className="mb-1 text-xs font-semibold uppercase tracking-wide text-slate-400">{title}</p>
            <p className="text-sm text-slate-700 leading-relaxed">{data[key]}</p>
          </div>
        ))}
      </div>
    </Card>
  );
}
