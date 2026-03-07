import { useState } from "react";
import { ChevronRight } from "lucide-react";

const EXEMPLOS = [
    "Consultor de IA",
    "Agência de Marketing",
    "Dentista",
    "Coach de Carreira",
    "Nutricionista",
    "Advogado",
];

const TONS = [
    {
        id: "profissional",
        label: "Profissional",
        preview: "Os dados indicam um crescimento expressivo no setor, exigindo estratégias bem fundamentadas.",
    },
    {
        id: "descontraido",
        label: "Descontraído",
        preview: "Olha só esses números! O mercado tá bombando e a gente precisa aproveitar essa onda. 🚀",
    },
    {
        id: "inspirador",
        label: "Inspirador",
        preview: "Cada desafio é uma oportunidade disfarçada. O momento de crescer é agora — juntos chegamos lá.",
    },
    {
        id: "direto",
        label: "Direto ao ponto",
        preview: "Mercado cresceu 40%. Ação necessária: revisar estratégia e executar até sexta.",
    },
];

export default function OnboardingNicho({ onNext, onBack, onChange, data }) {
    const [nicho, setNicho] = useState(data.nicho || "");
    const [persona, setPersona] = useState(data.persona || "");
    const [tom, setTom] = useState(data.tom || "");

    const canAdvance = nicho.trim().length >= 5 && tom;

    function handleNext() {
        onChange({ nicho: nicho.trim(), persona: persona.trim(), tom });
        onNext();
    }

    return (
        <div className="space-y-6 animate-[fade-in_0.3s_ease-out]">
            <div>
                <h2 className="text-xl font-bold text-[#F9FAFB] mb-1">Seu negócio</h2>
                <p className="text-sm text-[#9CA3AF]">
                    Essas informações guiam os agentes de IA na hora de criar seu conteúdo.
                </p>
            </div>

            {/* Nicho */}
            <div className="space-y-2">
                <label htmlFor="nicho" className="block text-xs font-medium text-[#9CA3AF]">
                    Descreva seu negócio / nicho em uma frase
                </label>
                <input
                    id="nicho"
                    type="text"
                    value={nicho}
                    onChange={(e) => setNicho(e.target.value)}
                    placeholder="Ex: Consultora de marketing digital para clínicas odontológicas"
                    className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2.5 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                />
                {/* Exemplos clicáveis */}
                <div className="flex flex-wrap gap-2 pt-1">
                    {EXEMPLOS.map((ex) => (
                        <button
                            key={ex}
                            type="button"
                            onClick={() => setNicho(ex)}
                            className="text-xs px-2.5 py-1 rounded-full border border-[#2E2E2E] text-[#9CA3AF] hover:border-[#6366F1]/60 hover:text-[#C7D2FE] transition-colors"
                        >
                            {ex}
                        </button>
                    ))}
                </div>
            </div>

            {/* Cliente ideal */}
            <div className="space-y-2">
                <label htmlFor="persona" className="block text-xs font-medium text-[#9CA3AF]">
                    Quem é seu cliente ideal?{" "}
                    <span className="text-[#6B7280] font-normal">(opcional)</span>
                </label>
                <textarea
                    id="persona"
                    value={persona}
                    onChange={(e) => setPersona(e.target.value)}
                    placeholder="Ex: Donos de clínicas odontológicas, 35-55 anos, que querem mais pacientes via redes sociais"
                    rows={2}
                    className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2.5 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors resize-none"
                />
            </div>

            {/* Tom de voz */}
            <div className="space-y-2">
                <p className="text-xs font-medium text-[#9CA3AF]">Tom de voz</p>
                <div className="grid grid-cols-2 gap-2">
                    {TONS.map((t) => (
                        <button
                            key={t.id}
                            type="button"
                            onClick={() => setTom(t.id)}
                            aria-pressed={tom === t.id}
                            className={`p-3 rounded-lg border text-left transition-all ${
                                tom === t.id
                                    ? "border-[#6366F1] bg-[#6366F1]/10 ring-1 ring-[#6366F1]/40"
                                    : "border-[#2E2E2E] hover:border-[#3E3E3E]"
                            }`}
                        >
                            <p className="text-xs font-semibold text-[#F9FAFB] mb-1">{t.label}</p>
                            <p className="text-[10px] text-[#9CA3AF] line-clamp-2">{t.preview}</p>
                        </button>
                    ))}
                </div>
            </div>

            {/* Navegação */}
            <div className="flex gap-3 pt-2">
                <button
                    type="button"
                    onClick={onBack}
                    className="flex-1 py-2.5 rounded-xl border border-[#2E2E2E] text-[#9CA3AF] text-sm hover:border-[#3E3E3E] transition-colors"
                >
                    Voltar
                </button>
                <button
                    type="button"
                    onClick={handleNext}
                    disabled={!canAdvance}
                    className="flex-[2] flex items-center justify-center gap-2 bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 text-white text-sm font-semibold py-2.5 rounded-xl transition-colors"
                >
                    Continuar <ChevronRight size={16} aria-hidden="true" />
                </button>
            </div>
        </div>
    );
}
