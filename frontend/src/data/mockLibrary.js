/**
 * Mock data for Library and Calendar pages.
 * Replace with real API calls once the backend is connected.
 */

// ── Helpers ───────────────────────────────────────────────────────────────────

function daysAgo(n) {
    const d = new Date();
    d.setDate(d.getDate() - n);
    return d.toISOString();
}

function daysFromNow(n) {
    const d = new Date();
    d.setDate(d.getDate() + n);
    return d.toISOString();
}

const CHANNELS = ["instagram", "linkedin", "twitter", "youtube", "email"];
const STATUSES = ["draft", "approved", "published"];

// ── Copies ────────────────────────────────────────────────────────────────────

const COPY_SNIPPETS = [
    "✨ A IA generativa está transformando como as PMEs fazem marketing — e os números são impressionantes. Empresas que adotaram ferramentas de IA cresceram 3x mais rápido.",
    "🔍 Novo estudo da FGV revela: PMEs que adotam IA generativa crescem 3x mais rápido. ROI médio de 180% em 6 meses com ferramentas acessíveis.",
    "A IA generativa está transformando PMEs brasileiras: 180% ROI médio em 6 meses. E o custo? R$500/mês vs. R$50.000 em 2022.",
    "TÍTULO: IA no Marketing — Como PMEs Crescem 3x Mais Rápido (Dados FGV 2026). Descubra como implementar em 30 dias.",
    "Assunto: [Estudo] PMEs com IA crescem 3x mais. Olá, acabou de sair um estudo da FGV que mudou minha visão sobre o mercado.",
    "🚀 O LinkedIn favorece especialistas em 2026. Aprenda a triplicar seu alcance orgânico com as novas regras do algoritmo.",
    "ROI de redes sociais: as 5 métricas que realmente importam para consultores B2B. Pare de olhar para curtidas e comece a medir conversões.",
    "Automação de marketing sem equipe técnica: guia completo para consultores independentes. Do zero ao primeiro fluxo em um fim de semana.",
    "Email Marketing B2B: lista segmentada gera 760% mais receita. Como construir segmentos comportamentais sem ferramentas caras.",
    "Personal Branding: consultores com marca pessoal forte cobram 40% a mais. O framework de 5 pilares para quem começa do zero.",
    "YouTube Shorts para B2B: análise de 500 perfis mostra 3x mais leads qualificados. A produção simples que funciona melhor que profissional.",
    "ChatGPT para conteúdo: 12 prompts que economizam 8h/mês na criação. Testados por 1.000 criadores profissionais.",
    "SaaS para agências: stack de ferramentas por menos de R$1.000/mês que substitui soluções de R$10.000. Comparativo real.",
    "Tendências Q2 2026: queda do alcance no Instagram, crescimento do LinkedIn Creator Mode e retorno do podcast B2B.",
    "Consultoria digital: como estruturar seu serviço de marketing para recorrência. O modelo que gera receita previsível todo mês.",
    "Case real: agência cresceu 40% nas vendas com sequências de email automatizadas. O passo a passo completo.",
    "Métricas que importam: para de reportar vaidade e comece a mostrar impacto real no negócio do cliente.",
    "Reels ou carrossel? A análise de 1.200 posts B2B que responde de vez a questão do formato ideal.",
    "WhatsApp Business para consultores: como usar grupos, catálogos e automações para escalar sem equipe.",
    "Gestão de clientes digitais: o CRM simples que qualquer consultor pode usar de graça no Google Sheets.",
];

const TOPICS = [
    "IA Generativa para PMEs",
    "Automação de Marketing B2B",
    "ROI em Redes Sociais",
    "LinkedIn Algorithm 2026",
    "Email Marketing Segmentado",
    "YouTube Shorts B2B",
    "ChatGPT para Conteúdo",
    "SaaS para Agências",
    "Tendências Q2 2026",
    "Personal Branding",
];

export const MOCK_COPIES = Array.from({ length: 42 }, (_, i) => ({
    id: `c${i + 1}`,
    channel: CHANNELS[i % CHANNELS.length],
    status: STATUSES[i % STATUSES.length],
    content: COPY_SNIPPETS[i % COPY_SNIPPETS.length],
    topic: TOPICS[i % TOPICS.length],
    pipeline_id: `pl-${Math.floor(i / 5) + 1}`,
    created_at: daysAgo(i * 2),
    updated_at: daysAgo(i),
    char_count: 120 + i * 30,
}));

// ── Arts ──────────────────────────────────────────────────────────────────────

const ART_GRADIENTS = [
    "linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%)",
    "linear-gradient(135deg, #10B981 0%, #0891B2 50%, #6366F1 100%)",
    "linear-gradient(135deg, #F59E0B 0%, #EF4444 100%)",
    "linear-gradient(135deg, #0A66C2 0%, #1D4ED8 100%)",
    "linear-gradient(135deg, #EC4899 0%, #F43F5E 50%, #F59E0B 100%)",
    "linear-gradient(135deg, #111827 0%, #1F2937 50%, #374151 100%)",
    "linear-gradient(135deg, #059669 0%, #10B981 100%)",
    "linear-gradient(135deg, #7C3AED 0%, #6366F1 50%, #3B82F6 100%)",
    "linear-gradient(135deg, #DC2626 0%, #EF4444 100%)",
];

const ART_TYPES = ["square", "story", "carousel", "thumbnail"];

export const MOCK_ARTS = Array.from({ length: 18 }, (_, i) => ({
    id: `a${i + 1}`,
    type: ART_TYPES[i % ART_TYPES.length],
    gradient: ART_GRADIENTS[i % ART_GRADIENTS.length],
    topic: TOPICS[i % TOPICS.length],
    channel: CHANNELS[i % CHANNELS.length],
    pipeline_id: `pl-${Math.floor(i / 3) + 1}`,
    created_at: daysAgo(i * 3),
    url: null, // null = use gradient placeholder
}));

// ── Posts (copy + art paired) ─────────────────────────────────────────────────

const POST_CHANNEL_STATUSES = [
    { channels: ["instagram", "linkedin", "twitter"], statuses: ["published", "published", "published"] },
    { channels: ["instagram", "linkedin"], statuses: ["published", "draft"] },
    { channels: ["linkedin", "email"], statuses: ["published", "pending"] },
    { channels: ["instagram", "youtube"], statuses: ["scheduled", "scheduled"] },
    { channels: ["twitter"], statuses: ["published"] },
    { channels: ["email"], statuses: ["draft"] },
];

export const MOCK_POSTS = Array.from({ length: 12 }, (_, i) => ({
    id: `p${i + 1}`,
    topic: TOPICS[i % TOPICS.length],
    copy: COPY_SNIPPETS[i % COPY_SNIPPETS.length],
    artGradient: ART_GRADIENTS[i % ART_GRADIENTS.length],
    artType: ART_TYPES[i % ART_TYPES.length],
    pipeline_id: `pl-${i + 1}`,
    created_at: daysAgo(i * 4),
    channelStatuses: POST_CHANNEL_STATUSES[i % POST_CHANNEL_STATUSES.length],
}));

// ── Calendar events ───────────────────────────────────────────────────────────

const CAL_TOPICS = [
    "IA Generativa para PMEs",
    "Automação de Marketing",
    "LinkedIn 2026",
    "Email Segmentado",
    "YouTube Shorts",
    "Personal Branding",
    "ROI em Redes Sociais",
];

// Create a realistic schedule around the current month
function makeCalendarEvents() {
    const now = new Date();
    const year = now.getFullYear();
    const month = now.getMonth();

    const schedule = [
        // Week 1
        { day: 2, channel: "instagram", time: "09:00", topic: CAL_TOPICS[0] },
        { day: 3, channel: "linkedin", time: "11:00", topic: CAL_TOPICS[2] },
        { day: 5, channel: "twitter", time: "14:00", topic: CAL_TOPICS[0] },
        // Week 2
        { day: 8, channel: "instagram", time: "09:00", topic: CAL_TOPICS[1] },
        { day: 8, channel: "email", time: "10:00", topic: CAL_TOPICS[3] },
        { day: 10, channel: "linkedin", time: "11:00", topic: CAL_TOPICS[4] },
        { day: 12, channel: "youtube", time: "15:00", topic: CAL_TOPICS[4] },
        // Week 3
        { day: 15, channel: "instagram", time: "09:00", topic: CAL_TOPICS[5] },
        { day: 16, channel: "twitter", time: "12:00", topic: CAL_TOPICS[6] },
        { day: 17, channel: "linkedin", time: "11:00", topic: CAL_TOPICS[5] },
        { day: 19, channel: "email", time: "10:00", topic: CAL_TOPICS[3] },
        // Week 4
        { day: 22, channel: "instagram", time: "09:00", topic: CAL_TOPICS[6] },
        { day: 24, channel: "youtube", time: "15:00", topic: CAL_TOPICS[4] },
        { day: 25, channel: "linkedin", time: "11:00", topic: CAL_TOPICS[0] },
        { day: 26, channel: "twitter", time: "14:00", topic: CAL_TOPICS[1] },
        { day: 28, channel: "email", time: "10:00", topic: CAL_TOPICS[3] },
    ];

    return schedule
        .filter(({ day }) => day <= new Date(year, month + 1, 0).getDate())
        .map(({ day, channel, time, topic }, i) => ({
            id: `ev${i + 1}`,
            channel,
            topic,
            time,
            date: new Date(year, month, day),
            dateStr: `${year}-${String(month + 1).padStart(2, "0")}-${String(day).padStart(2, "0")}`,
        }));
}

export const MOCK_CALENDAR_EVENTS = makeCalendarEvents();

export default {
    copies: MOCK_COPIES,
    arts: MOCK_ARTS,
    posts: MOCK_POSTS,
    calendarEvents: MOCK_CALENDAR_EVENTS,
};
