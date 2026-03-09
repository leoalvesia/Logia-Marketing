import { useEffect, useState } from "react";
import { Download, RefreshCw, Repeat2, Wand2, X, ZoomIn } from "lucide-react";
import { TransformWrapper, TransformComponent } from "react-zoom-pan-pinch";
import { useLibraryStore } from "@/stores/libraryStore";

// Tipos conforme o backend (ArtType enum)
const TYPE_CONFIG = {
  static: { label: "Estático", ratio: "1/1" },
  carousel: { label: "Carrossel", ratio: "4/5" },
  thumbnail: { label: "Thumbnail", ratio: "16/9" },
};

const ART_TYPE_LABELS = {
  static: "Estático",
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
  const typeCfg = TYPE_CONFIG[art.type] ?? TYPE_CONFIG.static;
  const imageUrl = art.image_urls?.[0];

  return (
    <div
      className="fixed inset-0 z-50 bg-black/85 backdrop-blur-sm flex flex-col items-center justify-center p-6 gap-4"
      onClick={onClose}
    >
      <div className="flex items-center justify-between w-full max-w-xl" onClick={(e) => e.stopPropagation()}>
        <div className="space-y-0.5">
          <p className="text-sm font-semibold text-[#F9FAFB]">{ART_TYPE_LABELS[art.type] ?? art.type}</p>
          <p className="text-xs text-[#9CA3AF]">Pipeline · {new Date(art.created_at).toLocaleDateString("pt-BR")}</p>
        </div>
        <button
          onClick={onClose}
          className="w-8 h-8 rounded-full bg-[#2E2E2E] flex items-center justify-center hover:bg-[#3E3E3E] transition-colors"
        >
          <X size={14} className="text-[#9CA3AF]" />
        </button>
      </div>

      <div
        className="rounded-2xl overflow-hidden shadow-2xl bg-[#1A1A1A]"
        style={{ width: "min(500px, 90vw)", aspectRatio: typeCfg.ratio }}
        onClick={(e) => e.stopPropagation()}
      >
        <TransformWrapper>
          <TransformComponent>
            {imageUrl ? (
              <img
                src={imageUrl}
                alt="Arte gerada"
                className="w-full h-full object-cover"
                style={{ aspectRatio: typeCfg.ratio }}
              />
            ) : (
              <div
                className="w-full h-full flex items-center justify-center bg-gradient-to-br from-[#242424] to-[#1A1A1A]"
                style={{ aspectRatio: typeCfg.ratio, width: "min(500px, 90vw)" }}
              >
                <div className="text-center text-white/40 space-y-1">
                  <div className="w-12 h-12 rounded-full bg-white/5 mx-auto flex items-center justify-center text-xl">L</div>
                  <p className="text-xs">Sem imagem</p>
                </div>
              </div>
            )}
          </TransformComponent>
        </TransformWrapper>
      </div>

      <p className="text-xs text-[#4B5563]">Pinça ou scroll para zoom · Clique fora para fechar</p>
    </div>
  );
}

// ── Art Card ──────────────────────────────────────────────────────────────────

function ArtCard({ art, onZoom }) {
  const typeCfg = TYPE_CONFIG[art.type] ?? TYPE_CONFIG.static;
  const imageUrl = art.image_urls?.[0];

  return (
    <div className="group relative bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl overflow-hidden hover:border-[#6366F1]/40 transition-all duration-200">
      {/* Thumbnail */}
      <div className="w-full relative" style={{ aspectRatio: typeCfg.ratio }}>
        {imageUrl ? (
          <img
            src={imageUrl}
            alt="Arte"
            className="w-full h-full object-cover"
          />
        ) : (
          <div className="absolute inset-0 flex flex-col items-center justify-center bg-gradient-to-br from-[#242424] to-[#1A1A1A] text-white/40">
            <div className="w-8 h-8 rounded-full bg-white/5 flex items-center justify-center text-lg mb-1">L</div>
            <p className="text-[9px] font-medium">Logia</p>
          </div>
        )}

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/60 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center gap-2">
          <button
            onClick={() => onZoom(art)}
            className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 flex items-center justify-center transition-colors"
            title="Ampliar"
          >
            <ZoomIn size={13} className="text-white" />
          </button>
          {imageUrl && (
            <a
              href={imageUrl}
              download
              className="w-8 h-8 rounded-full bg-white/10 backdrop-blur-sm hover:bg-white/20 flex items-center justify-center transition-colors"
              title="Download"
              onClick={(e) => e.stopPropagation()}
            >
              <Download size={13} className="text-white" />
            </a>
          )}
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
        <span className="text-[10px] font-mono text-[#6B7280] truncate">
          {art.pipeline_id?.slice(-8) ?? "—"}
        </span>
        <span className="shrink-0 text-[9px] font-semibold bg-[#2E2E2E] text-[#9CA3AF] px-1.5 py-0.5 rounded ml-2">
          {typeCfg.label}
        </span>
      </div>
    </div>
  );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function ArtEmptyState() {
  return (
    <div className="py-20 flex flex-col items-center gap-4 text-center">
      <div className="w-14 h-14 rounded-full bg-[#1A1A1A] border border-[#2E2E2E] flex items-center justify-center">
        <Wand2 size={22} className="text-[#4B5563]" />
      </div>
      <div className="space-y-1">
        <p className="text-sm font-semibold text-[#9CA3AF]">Nenhuma arte gerada ainda</p>
        <p className="text-xs text-[#4B5563] max-w-xs">
          A geração de arte está em desenvolvimento. Em breve você poderá criar
          imagens a partir das suas copys aprovadas.
        </p>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function LibraryArtTab() {
  const { arts, artsTotal, loading, error, fetchArts } = useLibraryStore();
  const [typeFilter, setTypeFilter] = useState(null);
  const [zoomedArt, setZoomedArt] = useState(null);

  useEffect(() => {
    fetchArts({ type: typeFilter });
  }, [typeFilter]);

  const filtered = typeFilter
    ? arts.filter((a) => a.type === typeFilter)
    : arts;

  if (loading) return <ArtSkeleton />;

  return (
    <div className="space-y-4">
      {/* Error */}
      {error && (
        <div className="text-xs text-red-400 bg-red-950/30 border border-red-800/40 rounded-lg px-4 py-3">
          Erro ao carregar artes: {error}
        </div>
      )}

      {/* Type filters */}
      <div className="flex gap-2 flex-wrap">
        <button
          onClick={() => setTypeFilter(null)}
          className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${!typeFilter ? "border-[#6366F1] bg-[#6366F1]/10 text-[#818CF8]" : "border-[#2E2E2E] text-[#6B7280] hover:border-[#6366F1]/40 hover:text-[#9CA3AF]"}`}
        >
          Todos
        </button>
        {Object.entries(ART_TYPE_LABELS).map(([type, label]) => (
          <button
            key={type}
            onClick={() => setTypeFilter((f) => (f === type ? null : type))}
            className={`text-xs px-3 py-1.5 rounded-lg border font-medium transition-all ${typeFilter === type ? "border-[#6366F1] bg-[#6366F1]/10 text-[#818CF8]" : "border-[#2E2E2E] text-[#6B7280] hover:border-[#6366F1]/40 hover:text-[#9CA3AF]"}`}
          >
            {label}
          </button>
        ))}
        <span className="ml-auto self-center text-xs text-[#6B7280]">{artsTotal} artes</span>
      </div>

      {/* Grid or empty state */}
      {filtered.length === 0 ? (
        <ArtEmptyState />
      ) : (
        <div className="grid grid-cols-2 md:grid-cols-3 gap-3">
          {filtered.map((art) => (
            <ArtCard key={art.id} art={art} onZoom={setZoomedArt} />
          ))}
        </div>
      )}

      {/* Lightbox */}
      {zoomedArt && <Lightbox art={zoomedArt} onClose={() => setZoomedArt(null)} />}
    </div>
  );
}
