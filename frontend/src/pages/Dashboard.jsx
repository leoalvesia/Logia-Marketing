import { useNavigate } from "react-router-dom";
import {
    TrendingUp, Zap, Clock, BookOpen, ArrowRight,
    CheckCircle2, PenLine, Search, Palette, Send,
    AlertCircle,
} from "lucide-react";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ChannelBadge } from "@/components/ui/ChannelBadge";

// ── Mock data ──────────────────────────────────────────────────────────────────

const WEEKLY_POSTS = [3, 7, 5, 9, 4, 6, 8]; // últimos 7 dias
const TOTAL_WEEK = WEEKLY_POSTS.reduce((a, b) => a + b, 0);

const ACTIVE_PIPELINE = {
    id: "pl-42",
    topic: "IA Generativa para PMEs Brasileiras",
    state: "GENERATING_COPY",
    startedAt: "2026-03-06T14:30:00",
};

const NEXT_SCHEDULE = {
    date: "2026-03-07T10:00:00",
    channel: "instagram",
    copy: "Descubra como a IA está transformando o marketing B2B para pequenas empresas — resultados reais de quem já adotou 🚀",
};

const MONITORED_SOURCES = [
    { channel: "instagram", count: 12 },
    { channel: "linkedin", count: 8 },
    { channel: "youtube", count: 5 },
    { channel: "twitter", count: 18 },
    { channel: "email", count: 3 },
];

const ACTIVITY_FEED = [
    { id: 1, type: "PUBLISHED", icon: CheckCircle2, color: "#10B981", channel: "instagram", msg: "Post publicado", topic: "Automação de Marketing", time: "há 2h" },
    { id: 2, type: "GENERATED", icon: PenLine, color: "#6366F1", channel: "linkedin", msg: "Copy gerada", topic: "IA para Vendas B2B", time: "há 3h" },
    { id: 3, type: "RESEARCHING", icon: Search, color: "#3B82F6", channel: null, msg: "Pesquisa iniciada", topic: "Tendências Marketing 2026", time: "há 5h" },
    { id: 4, type: "PUBLISHED", icon: CheckCircle2, color: "#10B981", channel: "linkedin", msg: "Post publicado", topic: "ROI em Redes Sociais", time: "há 7h" },
    { id: 5, type: "ART", icon: Palette, color: "#EC4899", channel: "instagram", msg: "Arte gerada", topic: "Ferramentas SaaS para Consultores", time: "ontem" },
    { id: 6, type: "SCHEDULED", icon: Clock, color: "#F59E0B", channel: "twitter", msg: "Agendado para amanhã", topic: "Automação de Marketing", time: "ontem" },
    { id: 7, type: "PUBLISHED", icon: CheckCircle2, color: "#10B981", channel: "instagram", msg: "Post publicado", topic: "Ferramentas SaaS para Consultores", time: "2 dias" },
    { id: 8, type: "GENERATED", icon: PenLine, color: "#6366F1", channel: "email", msg: "Copy gerada", topic: "Email Marketing B2B", time: "2 dias" },
    { id: 9, type: "FAILED", icon: AlertCircle, color: "#EF4444", channel: "youtube", msg: "Erro ao publicar", topic: "YouTube Shorts — IA", time: "3 dias" },
    { id: 10, type: "PUBLISHED", icon: Send, color: "#10B981", channel: "linkedin", msg: "Post publicado", topic: "Gestão de Clientes Digitais", time: "3 dias" },
];

// ── Mini bar chart (SVG inline) ────────────────────────────────────────────────

function MiniBarChart({ values }) {
    const max = Math.max(...values, 1);
    const W = 80, H = 28, gap = 3;
    const barW = (W - gap * (values.length - 1)) / values.length;

    return (
        <svg width={W} height={H} viewBox={`0 0 ${W} ${H}`}>
            {values.map((v, i) => {
                const barH = Math.max(2, (v / max) * H);
                const isLast = i === values.length - 1;
                return (
                    <rect
                        key={i}
                        x={i * (barW + gap)}
                        y={H - barH}
                        width={barW}
                        height={barH}
                        rx={1.5}
                        fill={isLast ? "#6366F1" : "#2E2E2E"}
                    />
                );
            })}
        </svg>
    );
}

// ── Summary card ───────────────────────────────────────────────────────────────

function SummaryCard({ title, icon: Icon, iconColor, children, action, onAction }) {
    return (
        <div className="ds-card flex flex-col gap-3 min-h-[120px]">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                    <div
                        className="w-7 h-7 rounded-md flex items-center justify-center"
                        style={{ backgroundColor: `${iconColor}18`, border: `1px solid ${iconColor}25` }}
                    >
                        <Icon size={14} style={{ color: iconColor }} />
                    </div>
                    <span className="text-xs text-[#9CA3AF] font-medium">{title}</span>
                </div>
                {action && (
                    <button
                        onClick={onAction}
                        className="text-[10px] font-medium text-[#6366F1] hover:text-[#818CF8] transition-colors flex items-center gap-0.5"
                    >
                        {action} <ArrowRight size={10} />
                    </button>
                )}
            </div>
            {children}
        </div>
    );
}

// ── Helpers ───────────────────────────────────────────────────────────────────

function formatDate(iso) {
    const d = new Date(iso);
    return d.toLocaleDateString("pt-BR", { weekday: "short", day: "2-digit", month: "short", hour: "2-digit", minute: "2-digit" });
}

// ── Main component ─────────────────────────────────────────────────────────────

export default function Dashboard() {
    const navigate = useNavigate();

    return (
        <div className="p-5 md:p-6 space-y-6 max-w-5xl mx-auto animate-[fade-in_0.25s_ease-out]">

            {/* ── Section title ─────────────────────────────────── */}
            <div>
                <h1 className="text-xl font-bold text-[#F9FAFB]">Dashboard</h1>
                <p className="text-xs text-[#6B7280] mt-0.5">
                    {new Date().toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
                </p>
            </div>

            {/* ── 4 Summary cards ───────────────────────────────── */}
            <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-3">

                {/* 1 — Posts publicados */}
                <SummaryCard title="Posts esta semana" icon={TrendingUp} iconColor="#10B981">
                    <div className="flex items-end justify-between">
                        <div>
                            <p className="text-2xl font-bold text-[#F9FAFB]">{TOTAL_WEEK}</p>
                            <p className="text-[10px] text-[#6B7280]">últimos 7 dias</p>
                        </div>
                        <MiniBarChart values={WEEKLY_POSTS} />
                    </div>
                </SummaryCard>

                {/* 2 — Pipeline ativo */}
                <SummaryCard
                    title="Pipeline ativo"
                    icon={Zap}
                    iconColor="#6366F1"
                    action="Continuar"
                    onAction={() => navigate("/pipeline")}
                >
                    <div className="space-y-1.5">
                        <StatusBadge state={ACTIVE_PIPELINE.state} size="sm" />
                        <p className="text-xs text-[#9CA3AF] line-clamp-2 leading-snug">{ACTIVE_PIPELINE.topic}</p>
                    </div>
                </SummaryCard>

                {/* 3 — Próximo agendamento */}
                <SummaryCard title="Próximo agendamento" icon={Clock} iconColor="#F59E0B">
                    <div className="space-y-1.5">
                        <div className="flex items-center gap-2">
                            <ChannelBadge channel={NEXT_SCHEDULE.channel} size="xs" variant="icon" />
                            <span className="text-[10px] text-[#9CA3AF]">{formatDate(NEXT_SCHEDULE.date)}</span>
                        </div>
                        <p className="text-xs text-[#F9FAFB] line-clamp-2 leading-snug">{NEXT_SCHEDULE.copy}</p>
                    </div>
                </SummaryCard>

                {/* 4 — Fontes monitoradas */}
                <SummaryCard title="Fontes monitoradas" icon={BookOpen} iconColor="#3B82F6">
                    <div className="flex flex-wrap gap-1.5">
                        {MONITORED_SOURCES.map(({ channel, count }) => (
                            <div key={channel} className="flex items-center gap-1">
                                <ChannelBadge channel={channel} size="xs" variant="icon" />
                                <span className="text-[10px] font-mono text-[#9CA3AF]">{count}</span>
                            </div>
                        ))}
                    </div>
                    <p className="text-[10px] text-[#6B7280]">
                        {MONITORED_SOURCES.reduce((s, x) => s + x.count, 0)} fontes ativas
                    </p>
                </SummaryCard>
            </div>

            {/* ── Activity feed ─────────────────────────────────── */}
            <div>
                <h2 className="text-sm font-semibold text-[#F9FAFB] mb-3">Atividade recente</h2>
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-lg overflow-hidden divide-y divide-[#2E2E2E]">
                    {ACTIVITY_FEED.map(({ id, icon: Icon, color, channel, msg, topic, time }) => (
                        <div key={id} className="flex items-center gap-3 px-4 py-3 hover:bg-[#242424]/60 transition-colors">
                            {/* Icon */}
                            <div
                                className="shrink-0 w-7 h-7 rounded-md flex items-center justify-center"
                                style={{ backgroundColor: `${color}15`, border: `1px solid ${color}25` }}
                            >
                                <Icon size={13} style={{ color }} />
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-1.5 flex-wrap">
                                    <span className="text-xs font-medium text-[#F9FAFB]">{msg}</span>
                                    {channel && <ChannelBadge channel={channel} size="xs" variant="icon" />}
                                </div>
                                <p className="text-[11px] text-[#6B7280] truncate">{topic}</p>
                            </div>

                            {/* Time */}
                            <span className="shrink-0 text-[10px] text-[#4B5563] font-mono">{time}</span>
                        </div>
                    ))}
                </div>
            </div>
        </div>
    );
}
