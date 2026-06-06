import { useEffect } from "react";
import { ApiError } from "../../api/client";
import { getAlerts, getAnalysis } from "../../api/endpoints";
import { useAsync } from "../../hooks/useAsync";
import { formatVnd } from "../../lib/money";

const ALERT_DOT: Record<string, string> = {
  INFO: "bg-sky-400",
  WARNING: "bg-amber-400",
  CRITICAL: "bg-red-500",
};

const DTI_COLOR: Record<string, string> = {
  SAFE: "text-emerald-300",
  ACCEPTABLE: "text-blue-300",
  WARNING: "text-amber-300",
  DANGER: "text-red-300",
};

const EFR_COLOR = (efr: number) =>
  efr >= 3 ? "text-emerald-300" : efr >= 1 ? "text-amber-300" : "text-red-300";

export function HealthSidebar({
  profileId,
  onEditProfile,
  onProfileNotFound,
}: {
  profileId: string;
  onEditProfile?: () => void;
  onProfileNotFound?: () => void;
}) {
  const metricsAsync = useAsync(getAnalysis);
  const alertsAsync  = useAsync(getAlerts);

  useEffect(() => {
    metricsAsync.run(profileId).catch((e) => {
      if (e instanceof ApiError && e.status === 404) onProfileNotFound?.();
    });
    alertsAsync.run(profileId).catch(() => undefined);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [profileId]);

  const m      = metricsAsync.data;
  const alerts = alertsAsync.data?.alerts ?? [];

  return (
    <div className="flex flex-col gap-3">
      {/* Hero card */}
      <div className="rounded-2xl bg-gradient-to-br from-indigo-600 to-violet-700 p-4 text-white shadow-md">
        <div className="flex items-center justify-between">
          <p className="text-[11px] font-semibold uppercase tracking-widest opacity-60">
            Sức khoẻ tài chính
          </p>
          {onEditProfile && (
            <button
              onClick={onEditProfile}
              className="rounded-md px-2 py-0.5 text-[11px] font-medium text-white/70 hover:bg-white/15 hover:text-white transition-colors"
            >
              Sửa hồ sơ
            </button>
          )}
        </div>

        {m ? (
          <>
            <div className="mt-3">
              <p className="text-xs opacity-70">Tiền còn lại / tháng</p>
              <p className={`text-2xl font-bold leading-tight ${m.ncf < 0 ? "text-red-300" : ""}`}>
                {formatVnd(m.ncf)}
              </p>
            </div>

            <div className="mt-3 flex justify-between text-xs">
              <div>
                <p className="opacity-60">Tiết kiệm</p>
                <p className="font-bold text-base">{m.saving_rate.toFixed(0)}%</p>
              </div>
              <div className="text-right">
                <p className="opacity-60">Tỷ lệ nợ</p>
                <p className={`font-bold text-base ${DTI_COLOR[m.dti_band] ?? ""}`}>
                  {m.dti.toFixed(0)}%
                </p>
              </div>
              <div className="text-right">
                <p className="opacity-60">Dự phòng</p>
                <p className={`font-bold text-base ${EFR_COLOR(m.efr)}`}>
                  {m.efr.toFixed(1)} th
                </p>
              </div>
              <div className="text-right">
                <p className="opacity-60">Rủi ro</p>
                <p className="font-bold text-base">{m.pgrs.toFixed(0)}</p>
              </div>
            </div>
          </>
        ) : metricsAsync.error ? (
          <div className="mt-3">
            <p className="text-sm text-red-200">Không tải được dữ liệu</p>
            <p className="mt-1 text-xs text-white/60">{metricsAsync.error}</p>
          </div>
        ) : (
          <div className="mt-3 space-y-2">
            <div className="h-7 animate-pulse rounded-lg bg-white/15" />
            <div className="h-4 animate-pulse rounded bg-white/10" />
          </div>
        )}
      </div>

      {/* Alerts */}
      {alerts.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-slate-400">
            Cảnh báo
          </p>
          <div className="space-y-2.5">
            {alerts.map((a) => (
              <div key={a.code} className="flex items-start gap-2">
                <span className={`mt-1.5 h-1.5 w-1.5 flex-shrink-0 rounded-full ${ALERT_DOT[a.level]}`} />
                <div>
                  <p className="text-xs font-medium leading-snug text-slate-700">{a.message}</p>
                  <p className="text-xs text-slate-400">{a.recommendation}</p>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Goals */}
      {m && m.goals.length > 0 && (
        <div className="rounded-xl border border-slate-200 bg-white p-3">
          <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-slate-400">
            Mục tiêu
          </p>
          <div className="space-y-2.5">
            {m.goals.map((g) => {
              const onTrack = g.gat <= g.months_remaining;
              return (
                <div key={g.goal_id}>
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-1.5">
                      <span
                        className={`h-2 w-2 rounded-full ${onTrack ? "bg-emerald-400" : "bg-amber-400"}`}
                      />
                      <span className="text-xs font-medium text-slate-700">{g.name}</span>
                    </div>
                    <span className="text-xs text-slate-400">{g.months_remaining} tháng</span>
                  </div>
                  <p className="mt-0.5 pl-3.5 text-xs text-slate-400">
                    còn thiếu {formatVnd(g.gap)} · {formatVnd(g.monthly_allocated)}/th
                  </p>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
