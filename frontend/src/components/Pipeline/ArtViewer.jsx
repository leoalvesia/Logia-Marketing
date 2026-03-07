import { useState } from "react";
import { Check, RefreshCw, ZoomIn, X } from "lucide-react";

const ART_TYPES = [
    { id: "square", label: "Estático 1:1", ratio: "1 / 1", desc: "Feed Instagram/LinkedIn" },
    { id: "story", label: "Estático 9:16", ratio: "9 / 16", desc: "Stories e Reels" },
    { id: "carousel", label: "Carrossel", ratio: "4 / 5", desc: "Múltiplos slides" },
    { id: "thumbnail", label: "Thumbnail", ratio: "16 / 9", desc: "YouTube e Shorts" },
];

// Mock art variations (in production these are URLs from the Art Agent)
const MOCK_ARTS = [
    { id: "a1", label: "Variação A", bg: "linear-gradient(135deg, #6366F1 0%, #8B5CF6 50%, #EC4899 100%)", text: "#fff" },
    { id: "a2", label: "Variação B", bg: "linear-gradient(135deg, #0F0F0F 0%, #1A1A1A 50%, #2E2E2E 100%)", text: "#6366F1" },
    { id: "a3", label: "Variação C", bg: "linear-gradient(135deg, #10B981 0%, #0891B2 50%, #6366F1 100%)", text: "#fff" },
];

function ArtCard({ art, typeRatio, selected, onSelect, onRegenerate, onZoom }) {
    return (
        <div
            className={[
                "group relative flex flex-col gap-2 rounded-xl border transition-all duration-200 p-3",
                selected
                    ? "border-[#6366F1] bg-[#6366F1]/8 shadow-[0_0_16px_rgba(99,102,241,0.15)]"
                    : "border-[#2E2E2E] bg-[#1A1A1A] hover:border-[#6366F1]/40",
            ].join(" ")}
        >
            {/* Art preview */}
            <div
                className="w-full rounded-lg overflow-hidden relative"
                style={{ aspectRatio: typeRatio, background: art.bg }}
            >
                {/* Mock content overlay */}
                <div className="absolute inset-0 flex flex-col items-center justify-center p-4 text-center">
                    <div className="w-10 h-10 rounded-full bg-white/10 backdrop-blur-sm mb-2 flex items-center justify-center">
                        <span className="text-lg">L</span>
                    </div>
                    <p className="text-[10px] font-semibold" style={{ color: art.text }}>
                        Logia Marketing
                    </p>
                    <p className="text-[9px] mt-0.5 opacity-70" style={{ color: art.text }}>
                        IA Generativa para PMEs
                    </p>
                </div>

                {/* Zoom btn */}
                <button
                    onClick={() => onZoom?.(art)}
                    className="absolute top-1.5 right-1.5 w-6 h-6 rounded-md bg-black/50 backdrop-blur-sm flex items-center justify-center opacity-0 group-hover:opacity-100 transition-opacity hover:bg-black/70"
                >
                    <ZoomIn size={11} className="text-white" />
                </button>
            </div>

            {/* Label */}
            <p className="text-[11px] text-[#9CA3AF] text-center font-medium">{art.label}</p>

            {/* Actions */}
            <div className="flex gap-1.5">
                <button
                    onClick={() => onSelect?.(art.id)}
                    className={[
                        "flex-1 flex items-center justify-center gap-1 text-[10px] font-semibold py-1.5 rounded-md transition-all",
                        selected
                            ? "bg-[#6366F1] text-white"
                            : "bg-[#242424] text-[#9CA3AF] hover:bg-[#6366F1]/20 hover:text-[#818CF8]",
                    ].join(" ")}
                >
                    {selected && <Check size={10} />}
                    {selected ? "Selecionado" : "Selecionar"}
                </button>

                <button
                    onClick={() => onRegenerate?.(art.id)}
                    title="Regenerar variação"
                    className="w-7 h-7 flex items-center justify-center rounded-md bg-[#242424] text-[#6B7280] hover:text-[#9CA3AF] hover:bg-[#2E2E2E] transition-colors"
                >
                    <RefreshCw size={11} />
                </button>
            </div>
        </div>
    );
}

function LightboxModal({ art, ratio, onClose }) {
    return (
        <div
            className="fixed inset-0 z-50 bg-black/80 backdrop-blur-sm flex items-center justify-center p-6"
            onClick={onClose}
        >
            <div
                className="relative rounded-2xl overflow-hidden shadow-2xl max-w-lg w-full"
                style={{ aspectRatio: ratio, background: art.bg }}
                onClick={(e) => e.stopPropagation()}
            >
                <div className="absolute inset-0 flex flex-col items-center justify-center p-8 text-center">
                    <div className="w-20 h-20 rounded-full bg-white/10 backdrop-blur-sm mb-4 flex items-center justify-center">
                        <span className="text-4xl">L</span>
                    </div>
                    <p className="text-2xl font-bold" style={{ color: art.text }}>Logia Marketing</p>
                    <p className="text-base mt-1 opacity-70" style={{ color: art.text }}>
                        IA Generativa para PMEs Brasileiras
                    </p>
                </div>

                <button
                    onClick={onClose}
                    className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/50 flex items-center justify-center hover:bg-black/70 transition-colors"
                >
                    <X size={14} className="text-white" />
                </button>
            </div>
        </div>
    );
}

export default function ArtViewer({ onApprove }) {
    const [selectedType, setSelectedType] = useState("square");
    const [selectedArtId, setSelectedArtId] = useState(null);
    const [zoomedArt, setZoomedArt] = useState(null);
    const [approving, setApproving] = useState(false);

    const currentType = ART_TYPES.find((t) => t.id === selectedType);

    async function handleApprove() {
        if (!selectedArtId) return;
        setApproving(true);
        try {
            await onApprove?.(selectedArtId);
        } finally {
            setApproving(false);
        }
    }

    return (
        <div className="space-y-5">
            <div>
                <h2 className="text-lg font-semibold text-[#F9FAFB]">Revise as artes</h2>
                <p className="text-sm text-[#9CA3AF] mt-0.5">
                    Selecione o formato e escolha a melhor variação gerada.
                </p>
            </div>

            {/* Format type selector */}
            <div className="flex gap-2 flex-wrap">
                {ART_TYPES.map((t) => (
                    <button
                        key={t.id}
                        onClick={() => setSelectedType(t.id)}
                        className={[
                            "flex flex-col px-3 py-2 rounded-lg border text-xs font-medium transition-all",
                            selectedType === t.id
                                ? "border-[#6366F1] bg-[#6366F1]/10 text-[#818CF8]"
                                : "border-[#2E2E2E] bg-[#1A1A1A] text-[#9CA3AF] hover:border-[#6366F1]/40",
                        ].join(" ")}
                    >
                        <span>{t.label}</span>
                        <span className="text-[10px] text-[#6B7280] font-normal">{t.desc}</span>
                    </button>
                ))}
            </div>

            {/* Art grid */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {MOCK_ARTS.map((art) => (
                    <ArtCard
                        key={art.id}
                        art={art}
                        typeRatio={currentType?.ratio ?? "1 / 1"}
                        selected={selectedArtId === art.id}
                        onSelect={setSelectedArtId}
                        onZoom={setZoomedArt}
                    />
                ))}
            </div>

            {/* Approve footer */}
            <div className="flex items-center justify-between gap-3 pt-2 border-t border-[#2E2E2E]">
                <p className="text-xs text-[#6B7280]">
                    {selectedArtId ? "Arte selecionada — pronto para aprovar" : "Selecione uma variação para aprovar"}
                </p>
                <button
                    onClick={handleApprove}
                    disabled={!selectedArtId || approving}
                    className="flex items-center gap-2 bg-[#10B981] hover:bg-[#059669] disabled:opacity-50 disabled:cursor-not-allowed text-white text-sm font-semibold px-5 py-2.5 rounded-lg transition-colors shadow-[0_0_16px_rgba(16,185,129,0.2)]"
                >
                    <Check size={16} />
                    {approving ? "Aprovando..." : "Aprovar Arte"}
                </button>
            </div>

            {/* Lightbox */}
            {zoomedArt && (
                <LightboxModal
                    art={zoomedArt}
                    ratio={currentType?.ratio ?? "1 / 1"}
                    onClose={() => setZoomedArt(null)}
                />
            )}
        </div>
    );
}
