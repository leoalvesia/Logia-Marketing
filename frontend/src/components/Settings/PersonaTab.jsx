import { useState, useRef } from "react";
import { useSettingsStore } from "@/stores/settingsStore";
import { useToast } from "@/components/ui/Toast";
import { X, Plus, Save } from "lucide-react";

const TONES = [
    { value: "professional", label: "Profissional", emoji: "👔", desc: "Formal, dados e autoridade" },
    { value: "casual", label: "Casual", emoji: "😊", desc: "Amigável, próximo e direto" },
    { value: "technical", label: "Técnico", emoji: "⚙️", desc: "Aprofundado e preciso" },
    { value: "inspirational", label: "Inspiracional", emoji: "🚀", desc: "Motivador e aspiracional" },
];

export default function PersonaTab() {
    const persona = useSettingsStore((s) => s.persona);
    const updatePersona = useSettingsStore((s) => s.updatePersona);
    const addKeyword = useSettingsStore((s) => s.addKeyword);
    const removeKeyword = useSettingsStore((s) => s.removeKeyword);
    const toast = useToast();

    const [saving, setSaving] = useState(false);
    const [kwInput, setKwInput] = useState("");
    const tagInputRef = useRef();

    function handleAddKeyword(e) {
        e.preventDefault();
        const kw = kwInput.trim().toLowerCase();
        if (!kw) return;
        addKeyword(kw);
        setKwInput("");
    }

    async function handleSave() {
        setSaving(true);
        await new Promise((r) => setTimeout(r, 700));
        setSaving(false);
        toast({ type: "success", title: "Salvo com sucesso", description: "Nicho e persona atualizados." });
    }

    const charCountNicho = persona.nicho.length;
    const charCountPersona = persona.persona.length;

    return (
        <section aria-label="Configurações de nicho e persona" className="space-y-6">

            {/* Nicho description */}
            <div className="space-y-1.5">
                <label htmlFor="nicho-textarea" className="text-xs font-medium text-[#9CA3AF]">
                    Descreva seu nicho
                </label>
                <div className="relative">
                    <textarea
                        id="nicho-textarea"
                        rows={3}
                        value={persona.nicho}
                        onChange={(e) => updatePersona({ nicho: e.target.value })}
                        maxLength={300}
                        placeholder="Ex.: Consultor de IA para PMEs brasileiras..."
                        aria-describedby="nicho-help nicho-count"
                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-xl px-4 py-3 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] leading-relaxed resize-none
                       focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/30 transition-colors"
                    />
                    <span
                        id="nicho-count"
                        aria-live="polite"
                        aria-label={`${charCountNicho} de 300 caracteres`}
                        className={`absolute bottom-2.5 right-3 text-[10px] font-mono ${charCountNicho > 270 ? "text-amber-400" : "text-[#4B5563]"}`}
                    >
                        {charCountNicho}/300
                    </span>
                </div>
                <p id="nicho-help" className="text-[10px] text-[#4B5563]">
                    Use para o orquestrador filtrar temas relevantes para o seu mercado.
                </p>
            </div>

            {/* Persona description */}
            <div className="space-y-1.5">
                <label htmlFor="persona-textarea" className="text-xs font-medium text-[#9CA3AF]">
                    Descreva sua persona ideal
                </label>
                <div className="relative">
                    <textarea
                        id="persona-textarea"
                        rows={3}
                        value={persona.persona}
                        onChange={(e) => updatePersona({ persona: e.target.value })}
                        maxLength={300}
                        placeholder="Ex.: Gestores de marketing de médias empresas, 30-50 anos, buscam automatizar processos..."
                        aria-describedby="persona-help persona-count"
                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-xl px-4 py-3 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] leading-relaxed resize-none
                       focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/30 transition-colors"
                    />
                    <span
                        id="persona-count"
                        aria-live="polite"
                        aria-label={`${charCountPersona} de 300 caracteres`}
                        className={`absolute bottom-2.5 right-3 text-[10px] font-mono ${charCountPersona > 270 ? "text-amber-400" : "text-[#4B5563]"}`}
                    >
                        {charCountPersona}/300
                    </span>
                </div>
                <p id="persona-help" className="text-[10px] text-[#4B5563]">
                    Usado para adaptar o tom e linguagem de toda a copy gerada.
                </p>
            </div>

            {/* Keywords */}
            <div className="space-y-2">
                <p className="text-xs font-medium text-[#9CA3AF]">Palavras-chave do nicho</p>
                <form
                    onSubmit={handleAddKeyword}
                    className="flex gap-2"
                    role="search"
                    aria-label="Adicionar palavra-chave"
                >
                    <input
                        ref={tagInputRef}
                        type="text"
                        value={kwInput}
                        onChange={(e) => setKwInput(e.target.value)}
                        placeholder="Ex.: automação, ia, b2b..."
                        aria-label="Nova palavra-chave"
                        className="flex-1 bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-xs text-[#F9FAFB] placeholder:text-[#4B5563]
                       focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/30 transition-colors"
                    />
                    <button
                        type="submit"
                        aria-label="Adicionar palavra-chave"
                        disabled={!kwInput.trim()}
                        className="flex items-center gap-1.5 bg-[#6366F1] hover:bg-[#4F46E5] disabled:opacity-50 text-white text-xs font-semibold px-3 py-2 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                    >
                        <Plus size={13} aria-hidden="true" />
                    </button>
                </form>

                {/* Tag list */}
                {persona.keywords.length > 0 ? (
                    <div
                        role="list"
                        aria-label="Palavras-chave adicionadas"
                        className="flex flex-wrap gap-2"
                    >
                        {persona.keywords.map((kw) => (
                            <div
                                key={kw}
                                role="listitem"
                                className="flex items-center gap-1.5 bg-[#6366F1]/15 border border-[#6366F1]/30 rounded-full px-3 py-1"
                            >
                                <span className="text-xs text-[#818CF8] font-medium">{kw}</span>
                                <button
                                    onClick={() => removeKeyword(kw)}
                                    aria-label={`Remover palavra-chave "${kw}"`}
                                    className="text-[#6B7280] hover:text-red-400 transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1] rounded-full"
                                >
                                    <X size={11} aria-hidden="true" />
                                </button>
                            </div>
                        ))}
                    </div>
                ) : (
                    <p className="text-xs text-[#4B5563]">Nenhuma palavra-chave adicionada.</p>
                )}
            </div>

            {/* Tone of voice */}
            <fieldset>
                <legend className="text-xs font-medium text-[#9CA3AF] mb-3">Tom de voz</legend>
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                    {TONES.map((t) => (
                        <label
                            key={t.value}
                            className={[
                                "relative flex flex-col gap-1 p-3 rounded-xl border cursor-pointer transition-all group",
                                "focus-within:ring-2 focus-within:ring-[#6366F1]/50",
                                persona.tone === t.value
                                    ? "border-[#6366F1] bg-[#6366F1]/10"
                                    : "border-[#2E2E2E] bg-[#1A1A1A] hover:border-[#6366F1]/40",
                            ].join(" ")}
                        >
                            <input
                                type="radio"
                                name="tone"
                                value={t.value}
                                checked={persona.tone === t.value}
                                onChange={() => updatePersona({ tone: t.value })}
                                className="sr-only"
                                aria-label={t.label}
                            />
                            <span className="text-xl" aria-hidden="true">{t.emoji}</span>
                            <span className={`text-xs font-semibold ${persona.tone === t.value ? "text-[#818CF8]" : "text-[#F9FAFB]"}`}>
                                {t.label}
                            </span>
                            <span className="text-[9px] text-[#6B7280] leading-tight">{t.desc}</span>
                            {persona.tone === t.value && (
                                <div className="absolute top-2 right-2 w-2 h-2 rounded-full bg-[#6366F1]" aria-hidden="true" />
                            )}
                        </label>
                    ))}
                </div>
            </fieldset>

            {/* Save */}
            <div className="flex justify-end">
                <button
                    onClick={handleSave}
                    disabled={saving}
                    aria-label="Salvar configurações de nicho e persona"
                    aria-busy={saving}
                    className="flex items-center gap-2 bg-[#6366F1] hover:bg-[#4F46E5] disabled:opacity-60 text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-all focus-visible:outline-2 focus-visible:outline-[#6366F1] shadow-[0_0_14px_rgba(99,102,241,0.3)]"
                >
                    {saving ? (
                        <>
                            <span className="w-4 h-4 rounded-full border-2 border-white/40 border-t-white animate-spin" aria-hidden="true" />
                            Salvando...
                        </>
                    ) : (
                        <>
                            <Save size={15} aria-hidden="true" />
                            Salvar
                        </>
                    )}
                </button>
            </div>
        </section>
    );
}
