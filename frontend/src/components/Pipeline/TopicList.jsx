import { useState } from "react";
import { ExternalLink, Star } from "lucide-react";
import { ScoreBar } from "@/components/ui/ScoreBar";
import { ChannelBadge } from "@/components/ui/ChannelBadge";

// ── Mock topics (replaced by real data from store/API) ─────────────────────────
export const MOCK_TOPICS = [
    {
        id: "t1",
        title: "IA Generativa Está Transformando PMEs Brasileiras",
        summary: "Empresas de pequeno porte que adotam ferramentas de IA generativa crescem 3x mais rápido que concorrentes. Estudo da FGV aponta ROI médio de 180% em 6 meses.",
        score: 0.94,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.96 },
            { label: "Tendência", value: 0.92 },
            { label: "Relevância", value: 0.94 },
        ],
        channels: ["linkedin", "instagram"],
        sourceUrl: "https://fgv.br/pesquisa/ia-pme-brasil-2026",
        sourceLabel: "FGV Research",
    },
    {
        id: "t2",
        title: "Automação de Marketing: Guia Prático para Consultores",
        summary: "Como implementar fluxos de automação em clientes B2B sem equipe técnica. Case real: agência cresceu 40% nas vendas com sequências de email automatizadas.",
        score: 0.88,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.85 },
            { label: "Tendência", value: 0.91 },
            { label: "Relevância", value: 0.88 },
        ],
        channels: ["linkedin", "email"],
        sourceUrl: "https://hubspot.com/blog/marketing-automation-b2b",
        sourceLabel: "HubSpot Blog",
    },
    {
        id: "t3",
        title: "ROI de Redes Sociais: Como Medir o que Realmente Importa",
        summary: "Métricas de vaidade vs. métricas de negócio. Os 5 KPIs que todo consultor deve apresentar ao cliente para justificar o investimento em social media.",
        score: 0.82,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.80 },
            { label: "Tendência", value: 0.84 },
            { label: "Relevância", value: 0.82 },
        ],
        channels: ["instagram", "twitter"],
        sourceUrl: "https://sproutsocial.com/insights/social-media-roi",
        sourceLabel: "Sprout Social",
    },
    {
        id: "t4",
        title: "LinkedIn 2026: Algoritmo Favorece Conteúdo de Especialistas",
        summary: "Nova atualização do algoritmo do LinkedIn prioriza criadores com alta taxa de conclusão. Estratégias testadas que aumentaram alcance orgânico em 5x.",
        score: 0.79,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.82 },
            { label: "Tendência", value: 0.76 },
            { label: "Relevância", value: 0.79 },
        ],
        channels: ["linkedin"],
        sourceUrl: "https://linkedin.com/pulse/algorithm-update-2026",
        sourceLabel: "LinkedIn Official",
    },
    {
        id: "t5",
        title: "Email Marketing B2B: Segmentação que Gera Resultados",
        summary: "Lista segmentada gera 760% mais receita que campanhas massivas. Como construir segmentos comportamentais sem ferramenta cara — metodologia com Mailchimp e planilhas.",
        score: 0.77,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.74 },
            { label: "Tendência", value: 0.80 },
            { label: "Relevância", value: 0.77 },
        ],
        channels: ["email"],
        sourceUrl: "https://mailchimp.com/resources/email-segmentation-guide",
        sourceLabel: "Mailchimp",
    },
    {
        id: "t6",
        title: "Shorts e Reels no B2B: Funciona para Consultores?",
        summary: "Análise de 500 perfis B2B que migraram para vídeo curto. Resultado: 3x mais leads qualificados comparado a posts estáticos, mesmo com produção simples.",
        score: 0.74,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.78 },
            { label: "Tendência", value: 0.70 },
            { label: "Relevância", value: 0.74 },
        ],
        channels: ["instagram", "youtube"],
        sourceUrl: "https://youtube.com/creators/blog/shorts-b2b",
        sourceLabel: "YouTube Creators",
    },
    {
        id: "t7",
        title: "ChatGPT para Estratégia de Conteúdo: Prompts que Funcionam",
        summary: "Os 12 prompts mais eficazes para planejamento de conteúdo identificados por análise de 1.000 criadores profissionais. Ahorra 8h por mês na criação.",
        score: 0.71,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.73 },
            { label: "Tendência", value: 0.69 },
            { label: "Relevância", value: 0.71 },
        ],
        channels: ["twitter", "linkedin"],
        sourceUrl: "https://openai.com/blog/content-strategy-prompts",
        sourceLabel: "OpenAI Blog",
    },
    {
        id: "t8",
        title: "Personal Branding: O Diferencial de Consultores de Alta Performance",
        summary: "Consultores com marca pessoal forte cobram 40% a mais. O framework de 5 pilares usado por coaches e consultores que faturam 7 dígitos no marketing digital.",
        score: 0.68,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.72 },
            { label: "Tendência", value: 0.64 },
            { label: "Relevância", value: 0.68 },
        ],
        channels: ["instagram", "linkedin"],
        sourceUrl: "https://forbes.com/personal-branding-consultants",
        sourceLabel: "Forbes Business",
    },
    {
        id: "t9",
        title: "Ferramentas SaaS Essenciais para Agências de Marketing Digital",
        summary: "Stack de ferramentas que custa menos de R$1.000/mês e substitui solução enterprise de R$10.000. Comparativo real de 15 ferramentas com custo-benefício.",
        score: 0.62,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.60 },
            { label: "Tendência", value: 0.65 },
            { label: "Relevância", value: 0.61 },
        ],
        channels: ["twitter", "email"],
        sourceUrl: "https://g2.com/categories/marketing-automation",
        sourceLabel: "G2 Reviews",
    },
    {
        id: "t10",
        title: "Tendências de Marketing Digital para Q2 2026",
        summary: "Relatório trimestral de tendências: queda do alcance orgânico no Instagram, crescimento do LinkedIn Creator Mode e retorno do podcast B2B como canal de aquisição.",
        score: 0.58,
        scoreBreakdown: [
            { label: "Engajamento", value: 0.55 },
            { label: "Tendência", value: 0.62 },
            { label: "Relevância", value: 0.57 },
        ],
        channels: ["instagram", "linkedin", "twitter"],
        sourceUrl: "https://digitalmarketinginstitute.com/trends-q2-2026",
        sourceLabel: "DMI Report",
    },
];

export default function TopicList({ topics = MOCK_TOPICS, onSelect, loadingId }) {
    return (
        <div className="space-y-5">
            <div>
                <h2 className="text-lg font-semibold text-[#F9FAFB]">Escolha um tema</h2>
                <p className="text-sm text-[#9CA3AF] mt-0.5">
                    O Orquestrador encontrou {topics.length} temas relevantes para o seu nicho.
                </p>
            </div>

            <div className="space-y-3">
                {topics.map((topic, i) => (
                    <TopicCard
                        key={topic.id}
                        topic={topic}
                        index={i}
                        isFirst={i === 0}
                        onSelect={onSelect}
                        isLoading={loadingId === topic.id}
                    />
                ))}
            </div>
        </div>
    );
}

function TopicCard({ topic, index, isFirst, onSelect, isLoading }) {
    const delay = `${index * 50}ms`;

    return (
        <div
            style={{ animationDelay: delay }}
            className="group relative bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 hover:border-[#6366F1]/40 hover:bg-[#1E1E2A] transition-all duration-200 animate-[fade-in_0.35s_ease-out_both]"
        >
            {/* Recommended badge */}
            {isFirst && (
                <div className="absolute -top-2.5 left-4">
                    <span className="inline-flex items-center gap-1 bg-[#6366F1] text-white text-[10px] font-semibold px-2 py-0.5 rounded-full shadow-[0_0_12px_rgba(99,102,241,0.4)]">
                        <Star size={9} fill="currentColor" /> Recomendado
                    </span>
                </div>
            )}

            <div className="flex gap-4">
                {/* Rank number */}
                <div className="shrink-0 w-7 h-7 rounded-md bg-[#242424] border border-[#2E2E2E] flex items-center justify-center mt-0.5">
                    <span className="text-[11px] font-mono text-[#6B7280]">#{index + 1}</span>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 space-y-2.5">
                    {/* Title */}
                    <h3 className="text-sm font-semibold text-[#F9FAFB] leading-snug">
                        {topic.title}
                    </h3>

                    {/* Summary */}
                    <p className="text-xs text-[#9CA3AF] leading-relaxed line-clamp-3">
                        {topic.summary}
                    </p>

                    {/* Score bar */}
                    <ScoreBar
                        score={topic.score}
                        label="Relevância"
                        breakdown={topic.scoreBreakdown}
                        size="sm"
                    />

                    {/* Footer row */}
                    <div className="flex items-center justify-between gap-2 flex-wrap">
                        <div className="flex items-center gap-2 flex-wrap">
                            {/* Source link */}
                            <a
                                href={topic.sourceUrl}
                                target="_blank"
                                rel="noopener noreferrer"
                                onClick={(e) => e.stopPropagation()}
                                className="inline-flex items-center gap-1 text-[10px] text-[#6366F1] hover:text-[#818CF8] transition-colors"
                            >
                                <ExternalLink size={10} />
                                {topic.sourceLabel}
                            </a>

                            {/* Channel badges */}
                            <div className="flex gap-1">
                                {topic.channels.map((ch) => (
                                    <ChannelBadge key={ch} channel={ch} size="xs" variant="icon" />
                                ))}
                            </div>
                        </div>

                        {/* CTA */}
                        <button
                            onClick={() => onSelect?.(topic.id)}
                            disabled={isLoading}
                            className="shrink-0 flex items-center gap-1.5 bg-[#6366F1]/10 hover:bg-[#6366F1] border border-[#6366F1]/40 hover:border-[#6366F1] text-[#818CF8] hover:text-white text-xs font-semibold px-3 py-1.5 rounded-lg transition-all duration-200 disabled:opacity-50"
                        >
                            {isLoading ? (
                                <span className="w-3 h-3 rounded-full border-2 border-[#818CF8] border-t-transparent animate-spin" />
                            ) : null}
                            {isLoading ? "Iniciando..." : "Usar este tema"}
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
