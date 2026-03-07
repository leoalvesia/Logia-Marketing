import { useState } from "react";
import { Plus, X, ChevronRight, Instagram, Linkedin, Twitter, Youtube } from "lucide-react";

const PLATFORM_ICONS = {
    instagram: Instagram,
    linkedin: Linkedin,
    twitter: Twitter,
    youtube: Youtube,
};

function suggestProfiles(nicho) {
    const lower = nicho.toLowerCase();
    const suggestions = [];

    if (lower.includes("marketing") || lower.includes("agência")) {
        suggestions.push(
            { platform: "instagram", handle: "neilpatel" },
            { platform: "linkedin", handle: "gary-vaynerchuk" },
        );
    } else if (lower.includes("dentist") || lower.includes("clínica") || lower.includes("saúde")) {
        suggestions.push(
            { platform: "instagram", handle: "drdental_br" },
            { platform: "youtube", handle: "odontologia_moderna" },
        );
    } else if (lower.includes("coach") || lower.includes("carreira")) {
        suggestions.push(
            { platform: "linkedin", handle: "brene-brown" },
            { platform: "instagram", handle: "coach_carreira_br" },
        );
    } else {
        suggestions.push(
            { platform: "instagram", handle: "hubspot" },
            { platform: "linkedin", handle: "marketing-land" },
        );
    }
    return suggestions;
}

export default function OnboardingProfiles({ onNext, onBack, data }) {
    const suggested = suggestProfiles(data.nicho || "");
    const [profiles, setProfiles] = useState(suggested);
    const [input, setInput] = useState("");
    const [platform, setPlatform] = useState("instagram");

    const canAdvance = profiles.length >= 2;

    function addProfile() {
        const handle = input.replace(/^@/, "").trim();
        if (!handle) return;
        if (profiles.some((p) => p.platform === platform && p.handle === handle)) return;
        setProfiles([...profiles, { platform, handle }]);
        setInput("");
    }

    function removeProfile(idx) {
        setProfiles(profiles.filter((_, i) => i !== idx));
    }

    function handleNext() {
        onNext({ profiles });
    }

    return (
        <div className="space-y-6 animate-[fade-in_0.3s_ease-out]">
            <div>
                <h2 className="text-xl font-bold text-[#F9FAFB] mb-1">Perfis monitorados</h2>
                <p className="text-sm text-[#9CA3AF]">
                    Adicione concorrentes ou referências do seu nicho. A IA monitora o conteúdo
                    deles para gerar ideias para você.
                </p>
            </div>

            {/* Lista atual */}
            <div className="space-y-2">
                {profiles.map((p, idx) => {
                    const Icon = PLATFORM_ICONS[p.platform] || Instagram;
                    return (
                        <div
                            key={idx}
                            className="flex items-center gap-3 bg-[#1A1A1A] border border-[#2E2E2E] rounded-lg px-3 py-2.5"
                        >
                            <Icon size={16} className="text-[#6366F1] flex-shrink-0" aria-hidden="true" />
                            <span className="text-sm text-[#F9FAFB] flex-1">
                                @{p.handle}
                                <span className="text-[#6B7280] ml-1 text-xs">({p.platform})</span>
                            </span>
                            <button
                                type="button"
                                onClick={() => removeProfile(idx)}
                                aria-label={`Remover @${p.handle}`}
                                className="text-[#6B7280] hover:text-red-400 transition-colors"
                            >
                                <X size={14} aria-hidden="true" />
                            </button>
                        </div>
                    );
                })}

                {profiles.length === 0 && (
                    <p className="text-sm text-[#6B7280] text-center py-4">
                        Nenhum perfil adicionado ainda
                    </p>
                )}
            </div>

            {/* Input de adição */}
            <div className="space-y-2">
                <p className="text-xs font-medium text-[#9CA3AF]">Adicionar perfil</p>
                <div className="flex gap-2">
                    {/* Seletor de plataforma */}
                    <select
                        value={platform}
                        onChange={(e) => setPlatform(e.target.value)}
                        aria-label="Selecionar plataforma"
                        className="bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-2 py-2 text-sm text-[#F9FAFB] focus:outline-none focus:border-[#6366F1]"
                    >
                        <option value="instagram">Instagram</option>
                        <option value="linkedin">LinkedIn</option>
                        <option value="twitter">Twitter</option>
                        <option value="youtube">YouTube</option>
                    </select>

                    <input
                        type="text"
                        value={input}
                        onChange={(e) => setInput(e.target.value)}
                        onKeyDown={(e) => e.key === "Enter" && addProfile()}
                        placeholder="@handle ou nome do canal"
                        aria-label="Handle do perfil"
                        className="flex-1 bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                    />

                    <button
                        type="button"
                        onClick={addProfile}
                        disabled={!input.trim()}
                        aria-label="Adicionar perfil"
                        className="px-3 py-2 bg-[#6366F1]/20 border border-[#6366F1]/40 rounded-lg text-[#6366F1] hover:bg-[#6366F1]/30 disabled:opacity-40 transition-colors"
                    >
                        <Plus size={16} aria-hidden="true" />
                    </button>
                </div>
            </div>

            {!canAdvance && (
                <p className="text-xs text-[#F59E0B] text-center">
                    Adicione pelo menos 2 perfis para continuar
                </p>
            )}

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
