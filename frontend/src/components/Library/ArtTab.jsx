import { useState } from "react";
import { Download, RefreshCw, Repeat2, X, ZoomIn } from "lucide-react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { MOCK_ARTS } from "@/data/mockLibrary";

const TYPE_CONFIG = {
  square: { label: "1:1", ratio: "1/1" },
  story: { label: "9:16", ratio: "9/16" },
  carousel: { label: "Carrossel", ratio: "4/5" },
  thumbnail: { label: "Thumb", ratio: "16/9" },
};

const ART_TYPE_LABELS = {
  square: "Estático 1:1",
  story: "Estático 9:16",
  carousel: "Carrossel",
  thumbnail: "Thumbnail",
};

// ── Skeletons ─────────────────────────────────────────────────────────────────

function ArtSkeleton() {
  return (
    <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
      {Array.from({ length: 9 }).map((_, i) => (
        <div key={i} className="aspect-square bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl animate-pulse" />
      ))}
    </div>
  );
}

// ── Lightbox ──────────────────────────────────────────────────────────────────

function Lightbox({ art, onClose }) {
  return (
    <div
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex flex-col items-center justify-center p-6 gap-4"
      onClick={onClose}
    >
      {/* Header */}
      <div className="flex items-center justify-between w-full max-w-xl" onClick={(e) => e.stopPropagation()}>
        <div className="space-y-0.5">
          <p className="text-sm font-semibold text-[#F9FAFB]">{art.topic}</p>
          <p className="text-xs text-[#9CA3AF]">{ART_TYPE_LABELS[art.type]} · {new Date(art.created_at).toLocaleDateString("pt-BR")}</p>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-full bg-[#2E2E2E] flex items-center justify-center hover:bg-[#3E3E3E] transition-colors"
        >
          <X size={14} className="text-[#9CA3AF]" />
        </button>
      </div>

      {/* Zoomed image */}
      <div
        className="rounded-2xl overflow-hidden shadow-2xl"
        style={{ width: "min(500px, 90vw)", aspectRatio: TYPE_CONFIG[art.type]?.ratio ?? "1/1" }}
        onClick={(e) => e.stopPropagation()}
      >
        <TransformWrapper>
          <TransformComponent>
            <div
              className="w-full h-full flex items-center justify-center"
              style={{ background: art.gradient, aspectRatio: TYPE_CONFIG[art.type]?.ratio ?? "1/1", width: "min(500px, 90vw)" }}
            >
              <div className="text-center text-white/80 space-y-1">
                <div className="w-16 h-16 rounded-full bg-white/10 mx-auto flex items-center justify-center text-2xl">L</div>
                <p className="text-sm font-semibold">Logia Marketing</p>
                <p className="text-xs opacity-70">{art.topic}</p>
              </div>
            </div>
          </TransformComponent>
        </TransformWrapper>
      </div>

      <p className="text-xs text-[#4B5563]">Pinça ou scroll para zoom · Clique fora para fechar</p>
    </div>
  );
}

// ── Art Card ──────────────────────────────────────────────────────────────────

function ArtCard({ art, onZoom }) {
  const typeCfg = TYPE_CONFIG[art.type] ?? TYPE_CONFIG.square;

  return (
    <div className="group relative bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl overflow-hidden hover:border-[#6366F1]/40 transition-all duration-200">
      {/* Thumbnail */}
      <div
        className="w-full relative"
        style={{ aspectRatio: typeCfg.ratio, background: art.gradient }}
      >
        <div className="absolute inset-0 flex flex-col items-center justify-center text-white/60">
          <div className="w-8 h-8 rounded-full bg-white/10 flex items-center justify-center text-lg mb-1">L</div>
          <p className="text-[9px] font-medium">Logia</p>
        </div>

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
          <button
            onClick={() => onZoom(art)}
            className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 flex items-center justify-center transition-colors"
            title="Ampliar"
          >
            <ZoomIn size={13} className="text-white" />
          </button>
          <button
            className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 flex items-center justify-center transition-colors"
            title="Download"
          >
            <Download size={13} className="text-white" />
          </button>
          <button
            className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 flex items-center justify-center transition-colors"
            title="Reusar"
          >
            <Repeat2 size={13} className="text-white" />
          </button>
          <button
            className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 flex items-center justify-center transition-colors"
            title="Regenerar"
          >
            <RefreshCw size={13} className="text-white" />
          </button>
        </div>
      </div>

      {/* Footer */}
      <div className="px-3 py-2 flex items-center justify-between">
        <span className="text-[10px] font-mono text-[#6B7280] truncate">{art.topic.split(" ").slice(0, 3).join(" ")}</span>
        <span className="shrink-0 text-[9px] font-semibold bg-[#2E2E2E] text-[#9CA3AF] px-1.5 py-0.5 rounded ml-2">
          {typeCfg.label}
        </span>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function LibraryArtTab() {
  const [loading] = useState(false);
  const [typeFilter, setTypeFilter] = useState(null);
  const [zoomedArt, setZoomedArt] = useState(null);

  const filtered = typeFilter
    ? MOCK_ARTS.filter((a) => a.type === typeFilter)
    : MOCK_ARTS;

  if (loading) return <ArtSkeleton />;

  return (
    <div className="space-y-4">
      {/* Type filters */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setTypeFilter(null)}
          className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${!typeFilter
              ? "border-[#6366F1] bg-[#6366F1]/10 text-[#818CF8]"
              : "border-[#2E2E2E] text-[#6B7280] hover:border-[#6366F1]/40 hover:text-[#9CA3AF]"
            }`}
        >
          Todos
        </button>
        {Object.entries(ART_TYPE_LABELS).map(([type, label]) => (
          <button
            key={type}
            onClick={() => setTypeFilter((f) => f === type ? null : type)}
            className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${typeFilter === type
                ? "border-[#6366F1] bg-[#6366F1]/10 text-[#818CF8]"
                : "border-[#2E2E2E] text-[#6B7280] hover:border-[#6366F1]/40 hover:text-[#9CA3AF]"
              }`}
          >
            {label}
          </button>
        ))}
        <span className="ml-auto self-center text-xs text-[#6B7280]">{filtered.length} artes</span>
      </div>

      {/* Masonry-style grid */}
      {filtered.length === 0 ? (
        <div className="py-12 text-center text-sm text-[#6B7280]">
          Nenhuma arte encontrada.
        </div>
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {filtered.map((art) => (
            <ArtCard key={art.id} art={art} onZoom={setZoomedArt} />
          ))}
        </div>
      )}

      {/* Lightbox */}
      {zoomedArt && (
        <Lightbox art={zoomedArt} onClose={() => setZoomedArt(null)} />
      )}
    </div>
  );
}
