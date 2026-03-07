import { useState } from "react";
import { StatusBadge } from "../components/ui/StatusBadge";
import { ChannelBadge, ChannelBadgeList } from "../components/ui/ChannelBadge";
import { ScoreBar } from "../components/ui/ScoreBar";
import { AgentCard, AgentGrid } from "../components/ui/AgentCard";

const STATES = [
    "RESEARCHING",
    "ORCHESTRATING",
    "AWAITING_SELECTION",
    "GENERATING_COPY",
    "COPY_REVIEW",
    "GENERATING_ART",
    "ART_REVIEW",
    "SCHEDULED",
    "PUBLISHING",
    "PUBLISHED",
    "FAILED",
];

const CHANNELS = ["instagram", "linkedin", "twitter", "youtube", "email"];

const SCORE_EXAMPLES = [
    { score: 0.92, label: "Relevância", breakdown: [{ label: "Engagement", value: 0.95 }, { label: "Alcance", value: 0.88 }, { label: "Conversão", value: 0.93 }] },
    { score: 0.55, label: "Competição", breakdown: [{ label: "Diferenciação", value: 0.60 }, { label: "Oportunidade", value: 0.50 }] },
    { score: 0.22, label: "SEO Score", breakdown: [{ label: "Keywords", value: 0.18 }, { label: "Backlinks", value: 0.26 }] },
];

const DEMO_AGENTS = [
    { agent: "research", status: "done", startedAt: new Date(Date.now() - 45000), chunks: ["Análise de mercado concluída. Identificados 12 temas de alto potencial no segmento B2B.\n\nTop temas:\n1. Automação de marketing\n2. IA generativa para PMEs\n3. ROI em redes sociais"] },
    { agent: "copy_instagram", status: "running", startedAt: new Date(Date.now() - 18000), chunks: ["✨ Descubra como a IA está transformando o marketing B2B...\n\n", "Empresas que adotam automação crescem 3x mais rápido 🚀\n\n", "Swipe para ver os dados →"] },
    { agent: "copy_linkedin", status: "idle", startedAt: null, chunks: [] },
    { agent: "art", status: "error", startedAt: new Date(Date.now() - 5000), chunks: [], error: "API timeout após 110s. Limite de soft_time_limit atingido." },
];

function Section({ title, children }) {
    return (
        <section className="space-y-4">
            <h2 className="text-lg font-semibold text-[#F9FAFB] border-b border-[#2E2E2E] pb-2">{title}</h2>
            {children}
        </section>
    );
}

function Token({ name, value, swatch }) {
    return (
        <div className="flex items-center gap-3 py-1.5">
            {swatch && (
                <span
                    className="w-6 h-6 rounded-md border border-[#2E2E2E] flex-shrink-0"
                    style={{ backgroundColor: value }}
                />
            )}
            <code className="text-xs font-mono text-[#818CF8]">{name}</code>
            <span className="text-xs text-[#6B7280]">{value}</span>
        </div>
    );
}

export default function DesignSystemDemo() {
    const [agentStates] = useState(DEMO_AGENTS);

    return (
        <div className="min-h-screen bg-[#0F0F0F] text-[#F9FAFB] font-sans">
            {/* Header */}
            <div className="border-b border-[#2E2E2E] bg-[#1A1A1A] px-8 py-6">
                <p className="text-xs font-mono text-[#6366F1] uppercase tracking-widest mb-1">Logia Marketing Platform</p>
                <h1 className="text-3xl font-bold">Design System</h1>
                <p className="text-[#9CA3AF] text-sm mt-1">Tokens, componentes e padrões visuais</p>
            </div>

            <div className="max-w-5xl mx-auto px-8 py-10 space-y-12">

                {/* ── 1. Color Tokens ─────────────────────────────────── */}
                <Section title="1. Color Tokens">
                    <div className="grid grid-cols-2 md:grid-cols-3 gap-x-8 gap-y-0 bg-[#1A1A1A] rounded-lg border border-[#2E2E2E] p-4">
                        <Token name="primary" value="#6366F1" swatch />
                        <Token name="primary-dark" value="#4F46E5" swatch />
                        <Token name="secondary" value="#10B981" swatch />
                        <Token name="danger" value="#EF4444" swatch />
                        <Token name="warning" value="#F59E0B" swatch />
                        <Token name="background" value="#0F0F0F" swatch />
                        <Token name="surface" value="#1A1A1A" swatch />
                        <Token name="surface-elevated" value="#242424" swatch />
                        <Token name="border" value="#2E2E2E" swatch />
                        <Token name="text-primary" value="#F9FAFB" swatch />
                        <Token name="text-secondary" value="#9CA3AF" swatch />
                        <Token name="text-muted" value="#6B7280" swatch />
                    </div>
                </Section>

                {/* ── 2. Typography ─────────────────────────────────────── */}
                <Section title="2. Typography">
                    <div className="bg-[#1A1A1A] rounded-lg border border-[#2E2E2E] p-6 space-y-3">
                        <p className="font-sans text-3xl font-bold">Inter — Heading 3xl/bold</p>
                        <p className="font-sans text-xl font-semibold text-[#9CA3AF]">Inter — Subheading xl/semibold</p>
                        <p className="font-sans text-base">Inter — Body text base/regular</p>
                        <p className="font-sans text-sm text-[#9CA3AF]">Inter — Label sm/regular</p>
                        <p className="font-sans text-xs text-[#6B7280]">Inter — Caption xs</p>
                        <hr className="border-[#2E2E2E]" />
                        <p className="font-mono text-base text-[#818CF8]">JetBrains Mono — código e terminais</p>
                        <p className="font-mono text-sm text-[#6B7280]">const pipeline = await start({"{ nicho: 'marketing' }"})</p>
                    </div>
                </Section>

                {/* ── 3. StatusBadge ────────────────────────────────────── */}
                <Section title="3. StatusBadge">
                    <div className="bg-[#1A1A1A] rounded-lg border border-[#2E2E2E] p-6">
                        <div className="flex flex-wrap gap-3">
                            {STATES.map((s) => (
                                <StatusBadge key={s} state={s} />
                            ))}
                        </div>
                        <p className="text-xs text-[#6B7280] mt-4 font-mono">
                            Props: <span className="text-[#818CF8]">state</span> | <span className="text-[#818CF8]">size</span> ("sm" | "md") | <span className="text-[#818CF8]">pulse</span> (boolean)
                        </p>
                    </div>

                    <div className="bg-[#1A1A1A] rounded-lg border border-[#2E2E2E] p-4">
                        <p className="text-xs text-[#6B7280] mb-3">Size variants</p>
                        <div className="flex items-center gap-3 flex-wrap">
                            <StatusBadge state="RESEARCHING" size="sm" />
                            <StatusBadge state="RESEARCHING" size="md" />
                            <StatusBadge state="GENERATING_COPY" size="sm" />
                            <StatusBadge state="GENERATING_COPY" size="md" />
                            <StatusBadge state="PUBLISHED" size="sm" />
                            <StatusBadge state="PUBLISHED" size="md" />
                        </div>
                    </div>
                </Section>

                {/* ── 4. ChannelBadge ────────────────────────────────────── */}
                <Section title="4. ChannelBadge">
                    <div className="bg-[#1A1A1A] rounded-lg border border-[#2E2E2E] p-6 space-y-4">
                        <div>
                            <p className="text-xs text-[#6B7280] mb-2 font-mono">variant="badge" (default)</p>
                            <div className="flex flex-wrap gap-2">
                                {CHANNELS.map((ch) => <ChannelBadge key={ch} channel={ch} />)}
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-[#6B7280] mb-2 font-mono">variant="pill"</p>
                            <div className="flex flex-wrap gap-2">
                                {CHANNELS.map((ch) => <ChannelBadge key={ch} channel={ch} variant="pill" />)}
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-[#6B7280] mb-2 font-mono">variant="icon"</p>
                            <div className="flex flex-wrap gap-2">
                                {CHANNELS.map((ch) => <ChannelBadge key={ch} channel={ch} variant="icon" />)}
                            </div>
                        </div>
                        <div>
                            <p className="text-xs text-[#6B7280] mb-2 font-mono">ChannelBadgeList (multi-canal)</p>
                            <ChannelBadgeList channels={["instagram", "linkedin", "twitter"]} />
                        </div>
                    </div>
                </Section>

                {/* ── 5. ScoreBar ──────────────────────────────────────────── */}
                <Section title="5. ScoreBar">
                    <div className="bg-[#1A1A1A] rounded-lg border border-[#2E2E2E] p-6 space-y-5">
                        {SCORE_EXAMPLES.map((ex) => (
                            <ScoreBar key={ex.label} score={ex.score} label={ex.label} breakdown={ex.breakdown} />
                        ))}
                        <p className="text-xs text-[#6B7280] font-mono mt-2">
                            Hover nas barras para ver breakdown do score · Gradiente vermelho→amarelo→verde
                        </p>
                    </div>
                </Section>

                {/* ── 6. AgentCard ─────────────────────────────────────────── */}
                <Section title="6. AgentCard">
                    <AgentGrid agents={agentStates} />
                    <p className="text-xs text-[#6B7280] font-mono">
                        Statuses: idle · running (com elapsed timer + shimmer bar) · done · error (com retry)
                    </p>
                </Section>

                {/* ── 7. Shadows + Glows ─────────────────────────────────── */}
                <Section title="7. Shadows &amp; Glows">
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                        {["shadow-sm", "shadow-md", "shadow-lg", "shadow-[0_0_20px_rgba(99,102,241,0.3)]"].map((s, i) => (
                            <div key={i} className={`bg-[#1A1A1A] rounded-lg border border-[#2E2E2E] p-4 text-center ${s}`}>
                                <p className="text-xs text-[#6B7280] font-mono">{["sm", "md", "lg", "glow-primary"][i]}</p>
                            </div>
                        ))}
                    </div>
                </Section>

                {/* ── 8. Animations ──────────────────────────────────────── */}
                <Section title="8. Animations">
                    <div className="flex flex-wrap gap-4 bg-[#1A1A1A] p-6 rounded-lg border border-[#2E2E2E]">
                        <div className="flex flex-col items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-[#6366F1] animate-[pulse-glow_2s_ease-in-out_infinite]" />
                            <p className="text-xs text-[#6B7280] font-mono">pulse-glow</p>
                        </div>
                        <div className="flex flex-col items-center gap-2">
                            <div className="w-8 h-8 rounded-full bg-[#10B981] animate-[pulse-glow-green_2s_ease-in-out_infinite]" />
                            <p className="text-xs text-[#6B7280] font-mono">pulse-glow-green</p>
                        </div>
                        <div className="flex flex-col items-center gap-2">
                            <span className="font-mono text-[#F9FAFB] text-lg">▌<span className="animate-[cursor-blink_1s_step-end_infinite]">|</span></span>
                            <p className="text-xs text-[#6B7280] font-mono">cursor-blink</p>
                        </div>
                        <div className="flex flex-col items-center gap-2">
                            <div className="animate-[fade-in_0.2s_ease-out] bg-[#242424] rounded px-3 py-1 border border-[#2E2E2E]">
                                <p className="text-xs text-[#9CA3AF] font-mono">fade-in</p>
                            </div>
                            <p className="text-xs text-[#6B7280] font-mono">fade-in</p>
                        </div>
                    </div>
                </Section>

            </div>
        </div>
    );
}
