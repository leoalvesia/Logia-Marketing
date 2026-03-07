/**
 * FeedbackDashboard — /admin/feedback
 *
 * Protegido por ADMIN_KEY (prompt na primeira visita, persistido em sessionStorage).
 * Mostra: NPS médio, gráfico de tendência, distribuição 0–10, bugs com status.
 */

import { useState, useEffect, useCallback } from "react";
import {
    TrendingUp, Bug, Star, Download, RefreshCw,
    CheckCircle2, Clock, AlertCircle, ChevronDown,
} from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "";

// ── Helpers ────────────────────────────────────────────────────────────────────

function npsCategory(score) {
    if (score >= 9) return { label: "Promotor", color: "#10B981" };
    if (score >= 7) return { label: "Neutro", color: "#F59E0B" };
    return { label: "Detrator", color: "#EF4444" };
}

function statusBadge(status) {
    const map = {
        new: { label: "Novo", color: "#6366F1", icon: AlertCircle },
        analyzing: { label: "Em análise", color: "#F59E0B", icon: Clock },
        resolved: { label: "Resolvido", color: "#10B981", icon: CheckCircle2 },
    };
    return map[status] || map.new;
}

// ── Gráfico de tendência NPS (SVG inline) ─────────────────────────────────────

function TrendChart({ trend }) {
    if (!trend?.length) {
        return (
            <div className="h-24 flex items-center justify-center text-xs text-[#6B7280]">
                Sem dados para exibir
            </div>
        );
    }

    const W = 400, H = 80, pad = 8;
    const values = trend.map((t) => t.avg);
    const maxVal = Math.max(...values, 10);
    const minVal = Math.min(...values, 0);
    const range = maxVal - minVal || 1;

    const points = values.map((v, i) => ({
        x: pad + (i / Math.max(values.length - 1, 1)) * (W - pad * 2),
        y: H - pad - ((v - minVal) / range) * (H - pad * 2),
    }));

    const pathD = points
        .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x.toFixed(1)} ${p.y.toFixed(1)}`)
        .join(" ");

    const areaD = `${pathD} L ${points[points.length - 1].x} ${H} L ${points[0].x} ${H} Z`;

    return (
        <svg viewBox={`0 0 ${W} ${H}`} className="w-full h-20" aria-label="Tendência NPS">
            <defs>
                <linearGradient id="trend-grad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#6366F1" stopOpacity="0.3" />
                    <stop offset="100%" stopColor="#6366F1" stopOpacity="0" />
                </linearGradient>
            </defs>
            <path d={areaD} fill="url(#trend-grad)" />
            <path d={pathD} fill="none" stroke="#6366F1" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
            {points.map((p, i) => (
                <circle key={i} cx={p.x} cy={p.y} r="3" fill="#6366F1" />
            ))}
        </svg>
    );
}

// ── Distribuição de notas (barras horizontais) ────────────────────────────────

function NpsDistribution({ distribution, total }) {
    return (
        <div className="space-y-1.5">
            {Array.from({ length: 11 }, (_, i) => 10 - i).map((score) => {
                const count = distribution?.[String(score)] || 0;
                const pct = total > 0 ? (count / total) * 100 : 0;
                const { color } = npsCategory(score);
                return (
                    <div key={score} className="flex items-center gap-2">
                        <span className="text-xs font-mono text-[#9CA3AF] w-4 text-right">{score}</span>
                        <div className="flex-1 h-4 bg-[#0F0F0F] rounded overflow-hidden">
                            <div
                                className="h-full rounded transition-all duration-500"
                                style={{ width: `${pct}%`, backgroundColor: color }}
                            />
                        </div>
                        <span className="text-xs text-[#6B7280] w-8 text-right">{count}</span>
                    </div>
                );
            })}
        </div>
    );
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function FeedbackDashboard() {
    const [adminKey, setAdminKey] = useState(
        () => sessionStorage.getItem("logia:admin_key") || ""
    );
    const [keyInput, setKeyInput] = useState("");
    const [authError, setAuthError] = useState("");

    const [npsStats, setNpsStats] = useState(null);
    const [npsList, setNpsList] = useState([]);
    const [bugs, setBugs] = useState([]);
    const [tab, setTab] = useState("nps"); // "nps" | "bugs"
    const [loading, setLoading] = useState(false);
    const [days, setDays] = useState(30);

    const headers = { "X-Admin-Key": adminKey };

    const fetchAll = useCallback(async () => {
        if (!adminKey) return;
        setLoading(true);
        try {
            const [statsR, npsR, bugsR] = await Promise.all([
                fetch(`${API_BASE}/feedback/nps/stats?days=${days}`, { headers }),
                fetch(`${API_BASE}/feedback/nps?per_page=20`, { headers }),
                fetch(`${API_BASE}/feedback/bugs?per_page=20`, { headers }),
            ]);

            if (statsR.status === 403) {
                setAdminKey("");
                sessionStorage.removeItem("logia:admin_key");
                setAuthError("Chave inválida.");
                setLoading(false);
                return;
            }

            setNpsStats(await statsR.json());
            setNpsList((await npsR.json()).items || []);
            setBugs((await bugsR.json()).items || []);
        } catch {
            // rede indisponível — manter dados anteriores
        }
        setLoading(false);
    }, [adminKey, days]); // eslint-disable-line react-hooks/exhaustive-deps

    useEffect(() => { fetchAll(); }, [fetchAll]);

    async function updateBugStatus(bugId, newStatus) {
        await fetch(`${API_BASE}/feedback/bugs/${bugId}`, {
            method: "PATCH",
            headers: { ...headers, "Content-Type": "application/json" },
            body: JSON.stringify({ status: newStatus }),
        });
        setBugs((prev) =>
            prev.map((b) => (b.id === bugId ? { ...b, status: newStatus } : b))
        );
    }

    function exportCsv(tipo) {
        const url = `${API_BASE}/feedback/export?tipo=${tipo}`;
        const a = document.createElement("a");
        a.href = url;
        a.setAttribute("download", "");
        // Adicionar header não é possível via link direto — abrir em nova aba
        // Workaround: fetch + blob
        fetch(url, { headers }).then((r) => r.blob()).then((blob) => {
            const blobUrl = URL.createObjectURL(blob);
            a.href = blobUrl;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(blobUrl);
        });
    }

    // ── Tela de autenticação ──────────────────────────────────────────────────

    if (!adminKey) {
        return (
            <main className="min-h-screen bg-[#0F0F0F] flex items-center justify-center p-4" aria-label="Admin — autenticação">
                <div className="w-full max-w-sm bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-6 space-y-4">
                    <h1 className="text-lg font-bold text-[#F9FAFB]">Dashboard de Feedback</h1>
                    <p className="text-sm text-[#9CA3AF]">Insira a chave de admin para continuar.</p>
                    <div className="space-y-2">
                        <label htmlFor="admin-key" className="block text-xs font-medium text-[#9CA3AF]">
                            Admin Key
                        </label>
                        <input
                            id="admin-key"
                            type="password"
                            value={keyInput}
                            onChange={(e) => setKeyInput(e.target.value)}
                            onKeyDown={(e) => {
                                if (e.key === "Enter") {
                                    sessionStorage.setItem("logia:admin_key", keyInput);
                                    setAdminKey(keyInput);
                                }
                            }}
                            placeholder="••••••••••••"
                            className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-md px-3 py-2 text-sm text-[#F9FAFB] focus:outline-none focus:border-[#6366F1]"
                        />
                    </div>
                    {authError && <p className="text-xs text-red-400">{authError}</p>}
                    <button
                        onClick={() => {
                            sessionStorage.setItem("logia:admin_key", keyInput);
                            setAdminKey(keyInput);
                            setAuthError("");
                        }}
                        className="w-full bg-[#4F46E5] hover:bg-[#4338CA] text-white text-sm font-semibold py-2.5 rounded-lg transition-colors"
                    >
                        Entrar
                    </button>
                </div>
            </main>
        );
    }

    // ── Dashboard ─────────────────────────────────────────────────────────────

    return (
        <main className="min-h-screen bg-[#0F0F0F] p-5 md:p-8 space-y-6 max-w-5xl mx-auto" aria-label="Dashboard de Feedback">
            {/* Header */}
            <div className="flex items-center justify-between flex-wrap gap-3">
                <div>
                    <h1 className="text-xl font-bold text-[#F9FAFB]">Feedback Dashboard</h1>
                    <p className="text-xs text-[#6B7280] mt-0.5">Administração interna — Logia</p>
                </div>
                <div className="flex items-center gap-2">
                    <select
                        value={days}
                        onChange={(e) => setDays(Number(e.target.value))}
                        aria-label="Período"
                        className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-lg px-2 py-1.5 text-xs text-[#F9FAFB] focus:outline-none"
                    >
                        <option value={7}>7 dias</option>
                        <option value={30}>30 dias</option>
                        <option value={90}>90 dias</option>
                    </select>
                    <button
                        onClick={fetchAll}
                        disabled={loading}
                        aria-label="Atualizar dados"
                        className="p-1.5 border border-[#2E2E2E] rounded-lg text-[#9CA3AF] hover:text-[#F9FAFB] transition-colors"
                    >
                        <RefreshCw size={14} className={loading ? "animate-spin" : ""} aria-hidden="true" />
                    </button>
                    <button
                        onClick={() => exportCsv(tab === "nps" ? "nps" : "bugs")}
                        className="flex items-center gap-1.5 text-xs text-[#9CA3AF] hover:text-[#F9FAFB] border border-[#2E2E2E] rounded-lg px-3 py-1.5 transition-colors"
                    >
                        <Download size={13} aria-hidden="true" />
                        Exportar CSV
                    </button>
                </div>
            </div>

            {/* KPI cards */}
            {npsStats && (
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {[
                        {
                            label: "NPS Score",
                            value: npsStats.nps_score != null ? `${npsStats.nps_score}` : "—",
                            sub: "Promotores − Detratores",
                            icon: TrendingUp,
                            color: "#6366F1",
                        },
                        {
                            label: "Média",
                            value: npsStats.avg_score != null ? `${npsStats.avg_score}/10` : "—",
                            sub: `${npsStats.total} respostas`,
                            icon: Star,
                            color: "#F59E0B",
                        },
                        {
                            label: "Promotores",
                            value: npsStats.promoters,
                            sub: "Score 9–10",
                            icon: CheckCircle2,
                            color: "#10B981",
                        },
                        {
                            label: "Detratores",
                            value: npsStats.detractors,
                            sub: "Score 0–6",
                            icon: AlertCircle,
                            color: "#EF4444",
                        },
                    ].map(({ label, value, sub, icon: Icon, color }) => (
                        <div key={label} className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4">
                            <div className="flex items-center gap-2 mb-2">
                                <div
                                    className="w-6 h-6 rounded-md flex items-center justify-center"
                                    style={{ backgroundColor: `${color}18`, border: `1px solid ${color}25` }}
                                >
                                    <Icon size={12} style={{ color }} aria-hidden="true" />
                                </div>
                                <span className="text-xs text-[#9CA3AF]">{label}</span>
                            </div>
                            <p className="text-2xl font-bold text-[#F9FAFB]">{value}</p>
                            <p className="text-[10px] text-[#6B7280] mt-0.5">{sub}</p>
                        </div>
                    ))}
                </div>
            )}

            {/* Tabs */}
            <div className="flex border-b border-[#2E2E2E]" role="tablist">
                {[
                    { id: "nps", label: "NPS", icon: TrendingUp },
                    { id: "bugs", label: "Bug Reports", icon: Bug },
                ].map(({ id, label, icon: Icon }) => (
                    <button
                        key={id}
                        role="tab"
                        aria-selected={tab === id}
                        onClick={() => setTab(id)}
                        className={`flex items-center gap-2 px-4 py-2.5 text-sm font-medium transition-colors -mb-px ${
                            tab === id
                                ? "text-[#F9FAFB] border-b-2 border-[#6366F1]"
                                : "text-[#6B7280] hover:text-[#9CA3AF]"
                        }`}
                    >
                        <Icon size={14} aria-hidden="true" />
                        {label}
                    </button>
                ))}
            </div>

            {/* Tab: NPS */}
            {tab === "nps" && (
                <div className="space-y-6">
                    <div className="grid md:grid-cols-2 gap-4">
                        {/* Tendência */}
                        <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 space-y-3">
                            <h2 className="text-xs font-semibold text-[#9CA3AF]">Tendência — últimos {days} dias</h2>
                            <TrendChart trend={npsStats?.trend} />
                        </div>
                        {/* Distribuição */}
                        <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 space-y-3">
                            <h2 className="text-xs font-semibold text-[#9CA3AF]">Distribuição de notas</h2>
                            <NpsDistribution
                                distribution={npsStats?.distribution}
                                total={npsStats?.total || 0}
                            />
                        </div>
                    </div>

                    {/* Lista de comentários */}
                    <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl overflow-hidden">
                        <div className="px-4 py-3 border-b border-[#2E2E2E]">
                            <h2 className="text-xs font-semibold text-[#9CA3AF]">Comentários recentes</h2>
                        </div>
                        <div className="divide-y divide-[#2E2E2E]">
                            {npsList.length === 0 && (
                                <p className="text-sm text-[#6B7280] text-center py-8">Nenhum comentário ainda</p>
                            )}
                            {npsList.map((item) => {
                                const { color } = npsCategory(item.score);
                                return (
                                    <div key={item.id} className="px-4 py-3 flex items-start gap-3">
                                        <div
                                            className="w-8 h-8 rounded-full flex items-center justify-center shrink-0 text-xs font-bold text-white"
                                            style={{ backgroundColor: color }}
                                        >
                                            {item.score}
                                        </div>
                                        <div className="flex-1 min-w-0">
                                            <p className="text-sm text-[#F9FAFB]">
                                                {item.comment || (
                                                    <span className="text-[#4B5563] italic">Sem comentário</span>
                                                )}
                                            </p>
                                            <p className="text-[10px] text-[#6B7280] mt-0.5">
                                                {new Date(item.created_at).toLocaleDateString("pt-BR")}
                                            </p>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            )}

            {/* Tab: Bugs */}
            {tab === "bugs" && (
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl overflow-hidden">
                    <div className="divide-y divide-[#2E2E2E]">
                        {bugs.length === 0 && (
                            <p className="text-sm text-[#6B7280] text-center py-8">Nenhum bug reportado ainda</p>
                        )}
                        {bugs.map((bug) => {
                            const { label, color, icon: Icon } = statusBadge(bug.status);
                            return (
                                <div key={bug.id} className="px-4 py-3 space-y-2">
                                    <div className="flex items-start justify-between gap-3">
                                        <p className="text-sm text-[#F9FAFB] flex-1 leading-snug">
                                            {bug.description}
                                        </p>
                                        {/* Status selector */}
                                        <div className="relative shrink-0">
                                            <select
                                                value={bug.status}
                                                onChange={(e) => updateBugStatus(bug.id, e.target.value)}
                                                aria-label={`Status do bug ${bug.id}`}
                                                className="appearance-none bg-[#0F0F0F] border rounded-lg text-xs px-2 py-1 pr-6 focus:outline-none cursor-pointer"
                                                style={{ borderColor: color, color }}
                                            >
                                                <option value="new">Novo</option>
                                                <option value="analyzing">Em análise</option>
                                                <option value="resolved">Resolvido</option>
                                            </select>
                                            <ChevronDown
                                                size={10}
                                                className="absolute right-1.5 top-1/2 -translate-y-1/2 pointer-events-none"
                                                style={{ color }}
                                                aria-hidden="true"
                                            />
                                        </div>
                                    </div>
                                    <div className="flex items-center gap-3 text-[10px] text-[#6B7280]">
                                        {bug.url && <span className="truncate max-w-[200px]">{bug.url}</span>}
                                        <span>{new Date(bug.created_at).toLocaleDateString("pt-BR")}</span>
                                        {bug.has_screenshot && (
                                            <span className="text-[#6366F1]">📷 screenshot</span>
                                        )}
                                        {bug.sentry_event_id && (
                                            <span className="font-mono">Sentry: {bug.sentry_event_id.slice(0, 8)}</span>
                                        )}
                                    </div>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}
        </main>
    );
}
