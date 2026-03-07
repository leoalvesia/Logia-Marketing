/**
 * ProductionDashboard — painel de saúde de produção.
 * Rota: /admin (protegida por ADMIN_KEY via sessionStorage)
 * Polling: 30s automático para GET /admin/metrics
 */
import { useState, useEffect, useCallback, useRef } from "react";
import {
    Activity, Users, Zap, DollarSign,
    RefreshCw, AlertTriangle, CheckCircle2,
    TrendingUp, Server, Database,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "";
const POLL_MS = 30_000;
const SK_KEY = "logia:admin_key";

// ── Auth ────────────────────────────────────────────────────────────────────

function useAdminAuth() {
    const [key, setKey] = useState(() => sessionStorage.getItem(SK_KEY) || "");
    const [authed, setAuthed] = useState(false);
    const [checking, setChecking] = useState(false);
    const [inputKey, setInputKey] = useState("");

    const verify = useCallback(async (k) => {
        setChecking(true);
        try {
            const res = await fetch(`${API_BASE}/admin/metrics`, {
                headers: { "X-Admin-Key": k },
            });
            if (res.status === 403 || res.status === 401) {
                sessionStorage.removeItem(SK_KEY);
                setKey("");
                setAuthed(false);
            } else {
                sessionStorage.setItem(SK_KEY, k);
                setKey(k);
                setAuthed(true);
            }
        } catch {
            setAuthed(false);
        }
        setChecking(false);
    }, []);

    useEffect(() => {
        if (key) verify(key);
    }, []);

    return { key, authed, checking, inputKey, setInputKey, verify };
}

// ── Data fetcher ─────────────────────────────────────────────────────────────

function useMetrics(key) {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [lastUpdate, setLastUpdate] = useState(null);
    const intervalRef = useRef(null);

    const fetch_ = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/admin/metrics`, {
                headers: { "X-Admin-Key": key },
            });
            if (!res.ok) throw new Error(`HTTP ${res.status}`);
            const json = await res.json();
            setData(json);
            setError(null);
            setLastUpdate(new Date());
        } catch (e) {
            setError(e.message);
        }
        setLoading(false);
    }, [key]);

    useEffect(() => {
        if (!key) return;
        fetch_();
        intervalRef.current = setInterval(fetch_, POLL_MS);
        return () => clearInterval(intervalRef.current);
    }, [key, fetch_]);

    return { data, loading, error, lastUpdate, refresh: fetch_ };
}

// ── Primitivos visuais ───────────────────────────────────────────────────────

function KpiCard({ icon: Icon, label, value, sub, accent = "#6366F1", alert = false }) {
    return (
        <div className={`bg-[#1A1A1A] border rounded-xl p-4 space-y-2 ${alert ? "border-red-900/60" : "border-[#2E2E2E]"}`}>
            <div className="flex items-center justify-between">
                <span className="text-xs text-[#6B7280]">{label}</span>
                <Icon size={14} style={{ color: accent }} aria-hidden="true" />
            </div>
            <p className="text-2xl font-bold text-[#F9FAFB] tabular-nums">{value ?? "—"}</p>
            {sub && <p className="text-[10px] text-[#6B7280]">{sub}</p>}
        </div>
    );
}

function SectionTitle({ icon: Icon, title }) {
    return (
        <div className="flex items-center gap-2 mb-4 mt-8 first:mt-0">
            <Icon size={16} className="text-[#6366F1]" aria-hidden="true" />
            <h2 className="text-sm font-semibold text-[#F9FAFB]">{title}</h2>
        </div>
    );
}

function HBar({ label, value, max, color = "#6366F1" }) {
    const pct = max > 0 ? Math.min((value / max) * 100, 100) : 0;
    return (
        <div className="space-y-1">
            <div className="flex justify-between text-xs">
                <span className="text-[#9CA3AF] capitalize">{label}</span>
                <span className="text-[#F9FAFB] tabular-nums">{value}</span>
            </div>
            <div className="h-1.5 bg-[#2E2E2E] rounded-full overflow-hidden">
                <div className="h-full rounded-full transition-all" style={{ width: `${pct}%`, background: color }} />
            </div>
        </div>
    );
}

function MiniLineChart({ data, field = "count", color = "#6366F1" }) {
    if (!data?.length) return <div className="h-16 flex items-center justify-center text-xs text-[#4B5563]">Sem dados</div>;
    const values = data.map((d) => d[field]);
    const max = Math.max(...values, 1);
    const W = 260, H = 48, PAD = 4;
    const pts = values.map((v, i) => {
        const x = PAD + (i / (values.length - 1 || 1)) * (W - PAD * 2);
        const y = PAD + (1 - v / max) * (H - PAD * 2);
        return `${x},${y}`;
    });
    const area = `${PAD},${H} ${pts.join(" ")} ${W - PAD},${H}`;
    return (
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full" aria-hidden="true">
            <defs>
                <linearGradient id="grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor={color} stopOpacity="0.3" />
                    <stop offset="100%" stopColor={color} stopOpacity="0" />
                </linearGradient>
            </defs>
            <polygon points={area} fill="url(#grad)" />
            <polyline points={pts.join(" ")} fill="none" stroke={color} strokeWidth="1.5" strokeLinejoin="round" />
        </svg>
    );
}

function PieChart({ data, colors }) {
    if (!data || Object.keys(data).length === 0)
        return <div className="h-24 flex items-center justify-center text-xs text-[#4B5563]">Sem dados</div>;

    const total = Object.values(data).reduce((a, b) => a + b, 0) || 1;
    const entries = Object.entries(data);
    const PALETTE = colors || ["#6366F1", "#10B981", "#F59E0B", "#EC4899", "#3B82F6"];

    let cumPct = 0;
    const slices = entries.map(([label, value], i) => {
        const pct = value / total;
        const startAngle = cumPct * 2 * Math.PI - Math.PI / 2;
        cumPct += pct;
        const endAngle = cumPct * 2 * Math.PI - Math.PI / 2;
        const R = 40, CX = 50, CY = 50;
        const x1 = CX + R * Math.cos(startAngle);
        const y1 = CY + R * Math.sin(startAngle);
        const x2 = CX + R * Math.cos(endAngle);
        const y2 = CY + R * Math.sin(endAngle);
        const large = pct > 0.5 ? 1 : 0;
        const color = PALETTE[i % PALETTE.length];
        return { label, value, pct, path: `M${CX},${CY} L${x1},${y1} A${R},${R} 0 ${large},1 ${x2},${y2} Z`, color };
    });

    return (
        <div className="flex items-center gap-4">
            <svg viewBox="0 0 100 100" className="w-24 h-24 flex-shrink-0" aria-hidden="true">
                {slices.map((s, i) => <path key={i} d={s.path} fill={s.color} />)}
            </svg>
            <div className="space-y-1.5 min-w-0">
                {slices.map((s, i) => (
                    <div key={i} className="flex items-center gap-1.5 text-xs">
                        <div className="w-2 h-2 rounded-full flex-shrink-0" style={{ background: s.color }} />
                        <span className="text-[#9CA3AF] capitalize truncate">{s.label}</span>
                        <span className="text-[#F9FAFB] tabular-nums ml-auto pl-2">{s.value}</span>
                    </div>
                ))}
            </div>
        </div>
    );
}

// ── Login gate ───────────────────────────────────────────────────────────────

function LoginGate({ auth }) {
    return (
        <main className="min-h-screen bg-[#0F0F0F] flex items-center justify-center p-4">
            <div className="w-full max-w-sm bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl p-6 space-y-4">
                <div className="flex items-center gap-2">
                    <Server size={16} className="text-[#6366F1]" />
                    <h1 className="text-sm font-semibold text-[#F9FAFB]">Admin Dashboard</h1>
                </div>
                <p className="text-xs text-[#9CA3AF]">Acesso restrito. Insira a ADMIN_KEY.</p>
                <input
                    type="password"
                    value={auth.inputKey}
                    onChange={(e) => auth.setInputKey(e.target.value)}
                    onKeyDown={(e) => e.key === "Enter" && auth.verify(auth.inputKey)}
                    placeholder="ADMIN_KEY"
                    autoFocus
                    className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] font-mono focus:outline-none focus:border-[#6366F1]"
                />
                <button
                    onClick={() => auth.verify(auth.inputKey)}
                    disabled={auth.checking || !auth.inputKey}
                    className="w-full bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 text-white text-sm font-semibold py-2.5 rounded-xl transition-colors"
                >
                    {auth.checking ? "Verificando..." : "Entrar"}
                </button>
            </div>
        </main>
    );
}

// ── Dashboard ────────────────────────────────────────────────────────────────

function Dashboard({ metrics, lastUpdate, refresh, loading }) {
    const { system, users, product, costs } = metrics;

    const errorAlert = system.error_rate_1h_pct > 2;

    const channelMax = Math.max(...Object.values(product.copies_by_channel || {}), 1);
    const totalPubs = Object.values(product.publications_by_channel || {}).reduce((a, b) => a + b, 0);

    return (
        <main className="min-h-screen bg-[#0F0F0F] text-[#F9FAFB] px-4 py-8 max-w-4xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div className="flex items-center gap-3">
                    <div className="w-7 h-7 rounded-lg bg-[#6366F1] flex items-center justify-center">
                        <Server size={14} className="text-white" aria-hidden="true" />
                    </div>
                    <div>
                        <h1 className="text-sm font-bold text-[#F9FAFB]">Production Dashboard</h1>
                        {lastUpdate && (
                            <p className="text-[10px] text-[#4B5563]">
                                Atualizado {lastUpdate.toLocaleTimeString("pt-BR")} · polling 30s
                            </p>
                        )}
                    </div>
                </div>
                <button
                    onClick={refresh}
                    disabled={loading}
                    aria-label="Atualizar métricas"
                    className="text-[#6B7280] hover:text-[#9CA3AF] transition-colors disabled:opacity-40"
                >
                    <RefreshCw size={16} className={loading ? "animate-spin" : ""} aria-hidden="true" />
                </button>
            </div>

            {/* ── SEÇÃO: SISTEMA ── */}
            <SectionTitle icon={Activity} title="Sistema" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <KpiCard
                    icon={CheckCircle2}
                    label="Uptime 24h"
                    value={`${system.uptime_24h_pct}%`}
                    sub={`7d: ${system.uptime_7d_pct}% · 30d: ${system.uptime_30d_pct}%`}
                    accent="#10B981"
                />
                <KpiCard
                    icon={AlertTriangle}
                    label="Error rate 1h"
                    value={`${system.error_rate_1h_pct}%`}
                    accent={errorAlert ? "#EF4444" : "#10B981"}
                    alert={errorAlert}
                />
                <KpiCard
                    icon={Activity}
                    label="Latência P95"
                    value={`${system.latency_ms?.p95 ?? "—"}ms`}
                    sub={`P50: ${system.latency_ms?.p50 ?? "—"}ms · P99: ${system.latency_ms?.p99 ?? "—"}ms`}
                />
                <KpiCard
                    icon={Server}
                    label="WebSockets ativos"
                    value={system.ws_connections}
                />
            </div>

            {/* Celery queues */}
            <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 space-y-3">
                <p className="text-xs font-medium text-[#6B7280]">Celery Queues</p>
                {Object.entries(system.celery_queues || {}).map(([q, len]) => (
                    <HBar
                        key={q}
                        label={q}
                        value={len}
                        max={Math.max(...Object.values(system.celery_queues), 50)}
                        color={len > 20 ? "#EF4444" : len > 10 ? "#F59E0B" : "#10B981"}
                    />
                ))}
            </div>

            {/* ── SEÇÃO: USUÁRIOS ── */}
            <SectionTitle icon={Users} title="Usuários" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <KpiCard icon={Users} label="Total cadastrados" value={users.total} />
                <KpiCard icon={Users} label="Ativos hoje" value={users.active_today} accent="#10B981" />
                <KpiCard icon={Users} label="Ativos esta semana" value={users.active_this_week} />
                <KpiCard
                    icon={TrendingUp}
                    label="Onboarding completo"
                    value={`${users.onboarding_completion_pct}%`}
                    accent={users.onboarding_completion_pct >= 70 ? "#10B981" : "#F59E0B"}
                />
            </div>

            {users.signups_last_14d?.length > 0 && (
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4">
                    <p className="text-xs font-medium text-[#6B7280] mb-3">Novos cadastros — últimos 14 dias</p>
                    <MiniLineChart data={users.signups_last_14d} field="count" color="#6366F1" />
                    <div className="flex justify-between mt-1">
                        <span className="text-[9px] text-[#4B5563]">{users.signups_last_14d[0]?.day}</span>
                        <span className="text-[9px] text-[#4B5563]">{users.signups_last_14d.at(-1)?.day}</span>
                    </div>
                </div>
            )}

            {/* ── SEÇÃO: PRODUTO ── */}
            <SectionTitle icon={Zap} title="Produto" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <KpiCard icon={Zap} label="Pipelines hoje" value={product.pipelines_today} />
                <KpiCard icon={Zap} label="Esta semana" value={product.pipelines_this_week} />
                <KpiCard
                    icon={CheckCircle2}
                    label="Taxa de conclusão"
                    value={`${product.completion_rate_pct}%`}
                    accent={product.completion_rate_pct >= 30 ? "#10B981" : "#EF4444"}
                    alert={product.completion_rate_pct < 30 && product.pipelines_this_week >= 5}
                />
                <KpiCard
                    icon={Activity}
                    label="Tempo médio pipeline"
                    value={product.avg_pipeline_minutes ? `${product.avg_pipeline_minutes}min` : "—"}
                />
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                {/* Copies por canal */}
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 space-y-3">
                    <p className="text-xs font-medium text-[#6B7280]">Copies geradas por canal (7d)</p>
                    {Object.entries(product.copies_by_channel || {}).length === 0
                        ? <p className="text-xs text-[#4B5563]">Sem dados</p>
                        : Object.entries(product.copies_by_channel).map(([ch, val]) => (
                            <HBar key={ch} label={ch} value={val} max={channelMax} />
                        ))
                    }
                </div>

                {/* Publicações por canal — pizza */}
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4">
                    <p className="text-xs font-medium text-[#6B7280] mb-3">
                        Publicações por canal (7d) · total: {totalPubs}
                    </p>
                    <PieChart data={product.publications_by_channel} />
                </div>
            </div>

            {/* ── SEÇÃO: CUSTOS IA ── */}
            <SectionTitle icon={DollarSign} title="Custos IA" />
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
                <KpiCard
                    icon={DollarSign}
                    label="Hoje"
                    value={`$${costs.today_usd?.toFixed(4)}`}
                    accent={costs.today_usd > costs.alert_threshold_usd ? "#EF4444" : "#10B981"}
                    alert={costs.today_usd > costs.alert_threshold_usd}
                />
                <KpiCard icon={DollarSign} label="Este mês" value={`$${costs.month_usd?.toFixed(2)}`} />
                <KpiCard
                    icon={TrendingUp}
                    label="Projeção fim do mês"
                    value={`$${costs.month_projection_usd?.toFixed(2)}`}
                    sub={`Alerta: $${costs.alert_threshold_usd}/dia`}
                />
                <KpiCard
                    icon={Zap}
                    label="Custo por publicação"
                    value={costs.cost_per_publication ? `$${costs.cost_per_publication?.toFixed(4)}` : "—"}
                />
            </div>

            {/* Tabela por agente */}
            {costs.by_agent?.length > 0 && (
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl overflow-hidden">
                    <table className="w-full text-xs">
                        <thead>
                            <tr className="border-b border-[#2E2E2E] text-left">
                                <th className="px-4 py-3 text-[#6B7280] font-medium">Agente</th>
                                <th className="px-4 py-3 text-[#6B7280] font-medium text-right">Tokens</th>
                                <th className="px-4 py-3 text-[#6B7280] font-medium text-right">Calls</th>
                                <th className="px-4 py-3 text-[#6B7280] font-medium text-right">Custo USD</th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-[#2E2E2E]">
                            {costs.by_agent.map((a) => (
                                <tr key={a.agent} className="hover:bg-[#242424]">
                                    <td className="px-4 py-2.5 text-[#F9FAFB] font-mono">{a.agent}</td>
                                    <td className="px-4 py-2.5 text-[#9CA3AF] text-right tabular-nums">
                                        {a.tokens?.toLocaleString()}
                                    </td>
                                    <td className="px-4 py-2.5 text-[#9CA3AF] text-right tabular-nums">
                                        {a.calls}
                                    </td>
                                    <td className="px-4 py-2.5 text-[#F9FAFB] text-right tabular-nums font-medium">
                                        ${a.cost_usd?.toFixed(4)}
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                </div>
            )}

            <div className="mt-8 text-center text-[10px] text-[#4B5563]">
                Logia Admin · dados atualizados em tempo real · polling a cada 30s
            </div>
        </main>
    );
}

// ── Root export ──────────────────────────────────────────────────────────────

export default function ProductionDashboard() {
    const auth = useAdminAuth();
    const { data, loading, error, lastUpdate, refresh } = useMetrics(auth.key);

    if (!auth.authed) return <LoginGate auth={auth} />;
    if (loading && !data)
        return (
            <div className="min-h-screen bg-[#0F0F0F] flex items-center justify-center">
                <p className="text-sm text-[#6B7280]">Carregando métricas...</p>
            </div>
        );
    if (error && !data)
        return (
            <div className="min-h-screen bg-[#0F0F0F] flex items-center justify-center">
                <p className="text-sm text-red-400">Erro ao carregar métricas: {error}</p>
            </div>
        );

    return <Dashboard metrics={data} lastUpdate={lastUpdate} refresh={refresh} loading={loading} />;
}
