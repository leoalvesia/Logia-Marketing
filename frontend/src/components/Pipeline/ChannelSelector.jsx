import { useState } from "react";
import { Zap } from "lucide-react";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { usePipelineStore } from "@/stores/pipelineStore";

const CHANNELS = [
    {
        id: "instagram",
        name: "Instagram",
        desc: "Carrossel, reels e stories",
        maxChars: 2200,
    },
    {
        id: "linkedin",
        name: "LinkedIn",
        desc: "Artigos longos e posts profissionais",
        maxChars: 3000,
    },
    {
        id: "twitter",
        name: "Twitter / X",
        desc: "Threads curtas e impactantes",
        maxChars: 280,
    },
    {
        id: "youtube",
        name: "YouTube",
        desc: "Descrição + título + thumbnail",
        maxChars: 5000,
    },
    {
        id: "email",
        name: "E-mail",
        desc: "Newsletter e sequências de nurturing",
        maxChars: null,
    },
];

export default function ChannelSelector({ onStart, loading }) {
    const selectedChannels = usePipelineStore((s) => s.selectedChannels);
    const toggleChannel = usePipelineStore((s) => s.toggleChannel);

    const isSelected = (id) => selectedChannels.includes(id);
    const canStart = selectedChannels.length >= 1;

    return (
        <div className="space-y-6 max-w-2xl mx-auto">
            <div>
                <h2 className="text-lg font-semibold text-[#F9FAFB]">Selecione os canais</h2>
                <p className="text-sm text-[#9CA3AF] mt-0.5">
                    Escolha onde o conteúdo será publicado. Cada canal gera uma copy otimizada.
                </p>
            </div>

            {/* Channel cards grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-3">
                {CHANNELS.map(({ id, name, desc, maxChars }, i) => {
                    const selected = isSelected(id);
                    return (
                        <button
                            key={id}
                            onClick={() => toggleChannel(id)}
                            style={{ animationDelay: `${i * 60}ms` }}
                            className={[
                                "relative text-left rounded-xl border p-4 transition-all duration-200 animate-[fade-in_0.3s_ease-out_both]",
                                "hover:border-[#6366F1]/50 hover:bg-[#242424]",
                                selected
                                    ? "border-[#6366F1] bg-[#6366F1]/10 shadow-[0_0_16px_rgba(99,102,241,0.2)]"
                                    : "border-[#2E2E2E] bg-[#1A1A1A]",
                            ].join(" ")}
                        >
                            {/* Selected checkmark */}
                            {selected && (
                                <span className="absolute top-3 right-3 w-5 h-5 rounded-full bg-[#6366F1] flex items-center justify-center">
                                    <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                                        <path d="M1 4l3 3 5-6" stroke="white" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" />
                                    </svg>
                                </span>
                            )}

                            {/* Channel badge (icon) */}
                            <ChannelBadge channel={id} size="lg" variant="icon" />

                            <div className="mt-3 space-y-0.5">
                                <p className={`text-sm font-semibold ${selected ? "text-[#F9FAFB]" : "text-[#E5E7EB]"}`}>
                                    {name}
                                </p>
                                <p className="text-xs text-[#9CA3AF]">{desc}</p>
                                {maxChars && (
                                    <p className="text-[10px] font-mono text-[#6B7280]">
                                        máx. {maxChars.toLocaleString()} chars
                                    </p>
                                )}
                            </div>
                        </button>
                    );
                })}
            </div>

            {/* Footer */}
            <div className="flex items-center justify-between pt-2">
                <p className="text-xs text-[#6B7280]">
                    {selectedChannels.length === 0
                        ? "Selecione ao menos 1 canal"
                        : `${selectedChannels.length} canal${selectedChannels.length > 1 ? "is" : ""} selecionado${selectedChannels.length > 1 ? "s" : ""}`}
                </p>

                <button
                    onClick={onStart}
                    disabled={!canStart || loading}
                    className={[
                        "flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-semibold transition-all duration-200",
                        canStart && !loading
                            ? "bg-[#6366F1] hover:bg-[#4F46E5] text-white shadow-[0_0_16px_rgba(99,102,241,0.3)] hover:shadow-[0_0_24px_rgba(99,102,241,0.4)]"
                            : "bg-[#2E2E2E] text-[#4B5563] cursor-not-allowed",
                    ].join(" ")}
                >
                    <Zap size={16} className={loading ? "animate-spin" : ""} />
                    {loading ? "Iniciando..." : "Iniciar Pesquisa"}
                </button>
            </div>
        </div>
    );
}
