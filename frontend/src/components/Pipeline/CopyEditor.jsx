import { useState, useRef, useEffect } from "react";
import { RefreshCw, Check, Save } from "lucide-react";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { usePipelineStore } from "@/stores/pipelineStore";

// Char limits per channel (null = unlimited)
const CHAR_LIMITS = {
    instagram: 2200,
    linkedin: 3000,
    twitter: 280,
    youtube: 5000,
    email: null,
};

// Initial copy content per channel (populated from store/ws in production)
const INITIAL_COPY = {
    instagram: `✨ A IA generativa está transformando como as PMEs fazem marketing — e os números são impressionantes.

Empresas que adotaram ferramentas de IA cresceram 3x mais rápido que concorrentes em 2025.

ROI médio de 180% em 6 meses? Isso é real, e temos os dados para provar.

Swipe para ver os 5 cases mais impactantes 👉

#MarketingDigital #InteligenciaArtificial #PME #Automação #BusinessGrowth`,

    linkedin: `🔍 Novo estudo da FGV revela: PMEs que adotam IA generativa crescem 3x mais rápido

Após analisar 500 pequenas e médias empresas brasileiras, os pesquisadores da Fundação Getulio Vargas encontraram um padrão consistente: a adoção de ferramentas de IA generativa está correlacionada com crescimento acelerado e redução significativa de custos operacionais.

**Os números:**
→ 180% de ROI médio em 6 meses
→ 65% de redução no tempo de criação de conteúdo
→ 3x mais leads qualificados vs. concorrentes tradicionais

O estudo aponta que a barreira de entrada nunca foi tão baixa. Ferramentas que custavam R$50.000/mês em 2022 hoje estão acessíveis por menos de R$500/mês.

Para consultores e agências de marketing: esta é a conversa que seus clientes ainda não estão tendo, mas deveriam.

Qual tem sido sua experiência com IA generativa em projetos com clientes? Compartilhe nos comentários.`,

    twitter: `A IA generativa está transformando PMEs brasileiras:

📊 180% ROI médio em 6 meses
⚡ 3x mais crescimento vs. concorrentes
💡 65% menos tempo criando conteúdo

E o custo? R$500/mês vs. R$50.000 em 2022.

A barreira nunca foi tão baixa. 🧵 (1/5)`,

    youtube: `TÍTULO: IA no Marketing: Como PMEs Brasileiras Crescem 3x Mais Rápido (Dados FGV 2026)

DESCRIÇÃO:
Neste vídeo, analisamos o novo estudo da FGV que revelou algo surpreendente: empresas que adotaram IA generativa crescem 3x mais rápido que concorrentes.

O que você vai aprender:
✅ Os 5 cases mais impactantes do estudo
✅ Ferramentas acessíveis para PMEs (< R$500/mês)
✅ Como apresentar ROI de IA para clientes conservadores
✅ Framework de implementação em 30 dias

CAPÍTULOS:
00:00 - Introdução
02:30 - Os dados do estudo FGV
08:15 - 5 cases reais de PMEs brasileiras
15:40 - Stack de ferramentas recomendada
22:10 - Como vender IA para clientes resistentes
28:00 - Próximos passos`,

    email: `Assunto: [Estudo Exclusivo] PMEs com IA crescem 3x mais — os dados que você precisa ver

Olá {{nome}},

Acabou de sair um estudo da FGV que mudou minha visão sobre o mercado de consultoria de marketing.

**O que eles descobriram:**

Das 500 PMEs brasileiras analisadas entre 2024 e 2026, aquelas que adotaram ferramentas de IA generativa nos fluxos de marketing cresceram, em média, 3x mais que as que não adotaram.

ROI médio: 180% em 6 meses.

Eu sei, parece exagerado. Por isso separei os 3 cases mais verificáveis do estudo para você analisar.

→ [Case 1: E-commerce de moda — 420% ROI]
→ [Case 2: Agência B2B — 280% mais leads qualificados]
→ [Case 3: Consultoria de RH — time de 2 virou time de 8 em produtividade]

A pergunta que fica: quantos dos seus clientes atuais já estão aproveitando isso?

Nos vemos quinta,
[Assinatura]

P.S. Semana que vem vou compartilhar o framework exato que uso para apresentar ROI de IA para clientes inicialmente céticos. Fique de olho.`,
};

function CharCounter({ count, limit }) {
    if (!limit) return (
        <span className="text-[10px] font-mono text-[#6B7280]">{count} chars</span>
    );

    const pct = count / limit;
    const color = pct > 0.95 ? "#EF4444" : pct > 0.8 ? "#F59E0B" : "#10B981";

    return (
        <span className="text-[10px] font-mono" style={{ color }}>
            {count} / {limit}
        </span>
    );
}

function ChannelEditor({ channel, onRegenerate, regenerating, streamingText }) {
    const limit = CHAR_LIMITS[channel];
    const initialContent = INITIAL_COPY[channel] ?? "";

    const copies = usePipelineStore((s) => s.copies);
    const storeContent = copies[channel]?.content;

    const [content, setContent] = useState(storeContent ?? initialContent);
    const textareaRef = useRef(null);
    const liveText = regenerating && streamingText ? streamingText : content;

    // Auto-resize textarea
    useEffect(() => {
        const el = textareaRef.current;
        if (!el) return;
        el.style.height = "auto";
        el.style.height = `${el.scrollHeight}px`;
    }, [liveText]);

    return (
        <div className="space-y-3">
            {/* Toolbar */}
            <div className="flex items-center justify-between">
                <CharCounter count={liveText.length} limit={limit} />
                <button
                    onClick={() => onRegenerate?.(channel)}
                    disabled={regenerating}
                    className="flex items-center gap-1.5 text-xs text-[#9CA3AF] hover:text-[#6366F1] transition-colors disabled:opacity-50"
                >
                    <RefreshCw size={12} className={regenerating ? "animate-spin" : ""} />
                    {regenerating ? "Gerando..." : "Regenerar"}
                </button>
            </div>

            {/* Textarea */}
            <div className="relative">
                <textarea
                    ref={textareaRef}
                    value={regenerating && streamingText ? streamingText : content}
                    onChange={(e) => !regenerating && setContent(e.target.value)}
                    readOnly={regenerating}
                    className={[
                        "w-full min-h-[200px] resize-none bg-[#0F0F0F] border rounded-lg px-4 py-3",
                        "text-sm text-[#F9FAFB] font-mono leading-relaxed",
                        "focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/30",
                        "transition-colors placeholder:text-[#4B5563]",
                        regenerating ? "border-[#6366F1]/40 cursor-wait" : "border-[#2E2E2E]",
                    ].join(" ")}
                    placeholder="Copy gerada pelo agente aparecerá aqui..."
                />

                {/* Streaming cursor overlay */}
                {regenerating && (
                    <div className="absolute bottom-3 right-3">
                        <span className="inline-block w-1.5 h-4 bg-[#6366F1] animate-[cursor-blink_1s_step-end_infinite]" />
                    </div>
                )}

                {/* Limit bar */}
                {limit && (
                    <div className="mt-1.5 h-0.5 w-full bg-[#2E2E2E] rounded-full overflow-hidden">
                        <div
                            className="h-full rounded-full transition-all duration-300"
                            style={{
                                width: `${Math.min(100, (liveText.length / limit) * 100)}%`,
                                background: liveText.length > limit * 0.95 ? "#EF4444"
                                    : liveText.length > limit * 0.8 ? "#F59E0B"
                                        : "#10B981",
                            }}
                        />
                    </div>
                )}
            </div>
        </div>
    );
}

export default function CopyEditor({ channels = ["instagram", "linkedin"], pipelineId, onApprove }) {
    const [activeChannel, setActiveChannel] = useState(channels[0]);
    const [regenerating, setRegenerating] = useState({});
    const [approving, setApproving] = useState(false);
    const streamingChunks = usePipelineStore((s) => s.streamingChunks);

    async function handleRegenerate(channel) {
        setRegenerating((r) => ({ ...r, [channel]: true }));
        // In production: call pipelineApi to regenerate single channel
        await new Promise((r) => setTimeout(r, 3000));
        setRegenerating((r) => ({ ...r, [channel]: false }));
    }

    async function handleApprove() {
        setApproving(true);
        try {
            await onApprove?.(pipelineId);
        } finally {
            setApproving(false);
        }
    }

    return (
        <div className="space-y-5">
            <div>
                <h2 className="text-lg font-semibold text-[#F9FAFB]">Revise as copies</h2>
                <p className="text-sm text-[#9CA3AF] mt-0.5">
                    Edite, regenere e aprove o conteúdo gerado para cada canal.
                </p>
            </div>

            {/* Channel tabs */}
            <div className="flex gap-2 border-b border-[#2E2E2E] pb-0 flex-wrap">
                {channels.map((ch) => (
                    <button
                        key={ch}
                        onClick={() => setActiveChannel(ch)}
                        className={[
                            "flex items-center gap-1.5 px-3 py-2 text-xs font-medium border-b-2 -mb-px transition-all",
                            activeChannel === ch
                                ? "border-[#6366F1] text-[#F9FAFB]"
                                : "border-transparent text-[#6B7280] hover:text-[#9CA3AF]",
                        ].join(" ")}
                    >
                        <ChannelBadge channel={ch} size="xs" variant="icon" />
                        <span className="capitalize">{ch === "twitter" ? "X" : ch.charAt(0).toUpperCase() + ch.slice(1)}</span>
                        {regenerating[ch] && (
                            <span className="w-1.5 h-1.5 rounded-full bg-[#6366F1] animate-pulse" />
                        )}
                    </button>
                ))}
            </div>

            {/* Active channel editor */}
            <ChannelEditor
                key={activeChannel}
                channel={activeChannel}
                onRegenerate={handleRegenerate}
                regenerating={!!regenerating[activeChannel]}
                streamingText={streamingChunks[activeChannel] ?? ""}
            />

            {/* Footer actions */}
            <div className="flex items-center justify-between gap-3 pt-2 border-t border-[#2E2E2E]">
                <button className="flex items-center gap-2 text-sm text-[#9CA3AF] hover:text-[#F9FAFB] transition-colors">
                    <Save size={14} />
                    Salvar Rascunho
                </button>

                <button
                    onClick={handleApprove}
                    disabled={approving}
                    className="flex items-center gap-2 bg-[#10B981] hover:bg-[#059669] disabled:opacity-60 text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors shadow-[0_0_16px_rgba(16,185,129,0.25)]"
                >
                    <Check size={16} />
                    {approving ? "Aprovando..." : "Aprovar Todas"}
                </button>
            </div>
        </div>
    );
}
