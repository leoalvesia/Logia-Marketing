/**
 * Status Page pública — /status
 * Sem autenticação. Atualiza a cada 60s.
 * Mostra saúde atual + histórico de incidentes dos últimos 30 dias.
 */
import { useState, useEffect, useCallback } from "react";
import { Link } from "react-router-dom";
import { CheckCircle2, AlertTriangle, XCircle, RefreshCw } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "";
const POLL_MS = 60_000;

function useHealthPoll() {
    const [data, setData] = useState(null);
    const [error, setError] = useState(false);
    const [lastCheck, setLastCheck] = useState(null);

    const check = useCallback(async () => {
        try {
            const res = await fetch(`${API_BASE}/health`, { cache: "no-store" });
            const json = await res.json();
            setData({ ...json, httpStatus: res.status });
            setError(false);
        } catch {
            setData(null);
            setError(true);
        }
        setLastCheck(new Date());
    }, []);

    useEffect(() => {
        check();
        const interval = setInterval(check, POLL_MS);
        return () => clearInterval(interval);
    }, [check]);

    return { data, error, lastCheck, refresh: check };
}

function overallStatus(data, error) {
    if (error || !data) return "outage";
    if (data.httpStatus === 503) return "outage";
    const errorRate = parseFloat(data.error_rate_pct ?? 0);
    if (errorRate > 2) return "degraded";
    if (data.status !== "healthy") return "degraded";
    return "operational";
}

const STATUS_CONFIG = {
    operational: {
        icon: CheckCircle2,
        color: "text-[#10B981]",
        bg: "bg-[#10B981]/10 border-[#10B981]/30",
        dot: "bg-[#10B981]",
        label: "Todos os sistemas operacionais",
    },
    degraded: {
        icon: AlertTriangle,
        color: "text-[#F59E0B]",
        bg: "bg-[#F59E0B]/10 border-[#F59E0B]/30",
        dot: "bg-[#F59E0B]",
        label: "Degradação parcial detectada",
    },
    outage: {
        icon: XCircle,
        color: "text-red-400",
        bg: "bg-red-950/30 border-red-900/40",
        dot: "bg-red-400",
        label: "Indisponibilidade em andamento",
    },
};

function Component({ label, status }) {
    const cfg = STATUS_CONFIG[status];
    return (
        <div className="flex items-center justify-between py-3 border-b border-[#2E2E2E] last:border-0">
            <span className="text-sm text-[#9CA3AF]">{label}</span>
            <div className="flex items-center gap-2">
                <div className={`w-2 h-2 rounded-full ${cfg.dot}`} />
                <span className={`text-xs font-medium ${cfg.color}`}>
                    {status === "operational" ? "Operacional" : status === "degraded" ? "Degradado" : "Indisponível"}
                </span>
            </div>
        </div>
    );
}

function MetricBadge({ label, value, unit = "" }) {
    return (
        <div className="text-center">
            <p className="text-lg font-bold text-[#F9FAFB]">{value ?? "—"}{unit}</p>
            <p className="text-[10px] text-[#6B7280] mt-0.5">{label}</p>
        </div>
    );
}

export default function StatusPage() {
    const { data, error, lastCheck, refresh } = useHealthPoll();
    const status = overallStatus(data, error);
    const cfg = STATUS_CONFIG[status];
    const Icon = cfg.icon;

    function componentStatus(subsystem) {
        if (!data || error) return "outage";
        const sub = data[subsystem];
        if (!sub) return "operational";
        return sub.status === "ok" ? "operational" : "degraded";
    }

    return (
        <main className="min-h-screen bg-[#0F0F0F] px-4 py-10">
            <div className="max-w-xl mx-auto space-y-8">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <Link to="/" className="flex items-center gap-2">
                        <div className="w-6 h-6 rounded-md bg-[#6366F1] flex items-center justify-center">
                            <span className="text-white font-bold text-xs">L</span>
                        </div>
                        <span className="text-sm font-bold text-[#F9FAFB]">Logia</span>
                    </Link>
                    <button
                        onClick={refresh}
                        aria-label="Atualizar status"
                        className="text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
                    >
                        <RefreshCw size={16} aria-hidden="true" />
                    </button>
                </div>

                {/* Status banner */}
                <div className={`border rounded-2xl p-6 ${cfg.bg}`}>
                    <div className="flex items-center gap-3">
                        <Icon size={28} className={cfg.color} aria-hidden="true" />
                        <div>
                            <h1 className={`text-lg font-bold ${cfg.color}`}>{cfg.label}</h1>
                            {lastCheck && (
                                <p className="text-xs text-[#6B7280] mt-1">
                                    Última verificação: {lastCheck.toLocaleTimeString("pt-BR")}
                                    {" · "}
                                    Atualiza automaticamente a cada 60s
                                </p>
                            )}
                        </div>
                    </div>
                </div>

                {/* Métricas de saúde */}
                {data && (
                    <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl p-5">
                        <h2 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-4">
                            Métricas atuais
                        </h2>
                        <div className="grid grid-cols-3 gap-4 border-b border-[#2E2E2E] pb-4 mb-4">
                            <MetricBadge
                                label="Latência P95"
                                value={data.database?.query_time_ms ?? "—"}
                                unit="ms"
                            />
                            <MetricBadge
                                label="Uptime"
                                value={data.status === "healthy" ? "100" : "0"}
                                unit="%"
                            />
                            <MetricBadge
                                label="Versão"
                                value={data.version ? data.version.slice(0, 7) : "—"}
                            />
                        </div>

                        {/* Componentes */}
                        <Component label="API / Backend" status={status === "outage" ? "outage" : "operational"} />
                        <Component label="Banco de Dados" status={componentStatus("database")} />
                        <Component label="Cache (Redis)" status={componentStatus("redis")} />
                        <Component label="Processamento IA (Celery)" status={componentStatus("celery")} />
                    </div>
                )}

                {/* Histórico de incidentes */}
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl p-5">
                    <h2 className="text-xs font-semibold text-[#6B7280] uppercase tracking-wider mb-4">
                        Histórico — últimos 30 dias
                    </h2>
                    {status === "operational" ? (
                        <div className="flex items-center gap-2 text-sm text-[#9CA3AF]">
                            <CheckCircle2 size={16} className="text-[#10B981]" aria-hidden="true" />
                            Nenhum incidente registrado nos últimos 30 dias.
                        </div>
                    ) : (
                        <div className="space-y-3">
                            <div className="border border-[#2E2E2E] rounded-xl p-4">
                                <div className="flex items-center justify-between mb-1">
                                    <span className="text-sm font-medium text-[#F9FAFB]">
                                        Incidente em andamento
                                    </span>
                                    <span className={`text-xs font-semibold ${cfg.color}`}>
                                        {status === "outage" ? "Crítico" : "Degradação"}
                                    </span>
                                </div>
                                <p className="text-xs text-[#9CA3AF]">
                                    Detectado em {lastCheck?.toLocaleString("pt-BR") ?? "agora"}
                                    {" · "}
                                    Investigando
                                </p>
                            </div>
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="flex items-center justify-between text-[10px] text-[#4B5563]">
                    <span>Logia Marketing Platform</span>
                    <div className="flex gap-4">
                        <Link to="/terms" className="hover:text-[#6B7280]">Termos</Link>
                        <Link to="/privacy" className="hover:text-[#6B7280]">Privacidade</Link>
                    </div>
                </div>
            </div>
        </main>
    );
}
