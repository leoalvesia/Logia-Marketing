import { useState, useMemo } from "react";
import { Search, Eye, Palette, Pencil, Trash2, ChevronLeft, ChevronRight } from "lucide-react";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { MOCK_COPIES } from "@/data/mockLibrary";

const PER_PAGE = 20;

const CHANNELS = ["instagram", "linkedin", "twitter", "youtube", "email"];

const STATUS_CONFIG = {
  draft: { label: "Rascunho", bg: "bg-amber-950/40 border-amber-800/50", text: "text-amber-400" },
  approved: { label: "Aprovado", bg: "bg-emerald-950/40 border-emerald-800/50", text: "text-emerald-400" },
  published: { label: "Publicado", bg: "bg-blue-950/40 border-blue-800/50", text: "text-blue-400" },
};

// ── Skeleton ──────────────────────────────────────────────────────────────────

function CopySkeleton() {
  return (
    <div className="space-y-3">
      {Array.from({ length: 6 }).map((_, i) => (
        <div key={i} className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 animate-pulse">
          <div className="flex items-center gap-2 mb-3">
            <div className="w-16 h-5 bg-[#2E2E2E] rounded-full" />
            <div className="w-20 h-5 bg-[#2E2E2E] rounded-full" />
            <div className="ml-auto w-16 h-4 bg-[#2E2E2E] rounded" />
          </div>
          <div className="space-y-1.5">
            <div className="h-3 bg-[#2E2E2E] rounded w-full" />
            <div className="h-3 bg-[#2E2E2E] rounded w-3/4" />
          </div>
        </div>
      ))}
    </div>
  );
}

// ── Pagination ────────────────────────────────────────────────────────────────

function Pagination({ page, totalPages, onPage }) {
  if (totalPages <= 1) return null;

  const pages = Array.from({ length: totalPages }, (_, i) => i + 1);
  // Show at most 5 page numbers
  const visible = pages.slice(
    Math.max(0, page - 3),
    Math.min(totalPages, page + 2)
  );

  return (
    <div className="flex items-center justify-center gap-1.5 pt-4">
      <button
        onClick={() => onPage(page - 1)}
        disabled={page <= 1}
        className="w-8 h-8 flex items-center justify-center rounded-lg border border-[#2E2E2E] bg-[#1A1A1A] text-[#9CA3AF] hover:bg-[#242424] disabled:opacity-40 transition-colors"
      >
        <ChevronLeft size={14} />
      </button>

      {visible[0] > 1 && (
        <>
          <button onClick={() => onPage(1)} className="w-8 h-8 flex items-center justify-center rounded-lg text-xs text-[#9CA3AF] hover:bg-[#242424] transition-colors">1</button>
          {visible[0] > 2 && <span className="text-[#4B5563] text-xs px-1">…</span>}
        </>
      )}

      {visible.map((p) => (
        <button
          key={p}
          onClick={() => onPage(p)}
          className={`w-8 h-8 flex items-center justify-center rounded-lg text-xs font-medium transition-colors ${p === page
              ? "bg-[#6366F1] text-white"
              : "text-[#9CA3AF] hover:bg-[#242424]"
            }`}
        >
          {p}
        </button>
      ))}

      {visible[visible.length - 1] < totalPages && (
        <>
          {visible[visible.length - 1] < totalPages - 1 && <span className="text-[#4B5563] text-xs px-1">…</span>}
          <button onClick={() => onPage(totalPages)} className="w-8 h-8 flex items-center justify-center rounded-lg text-xs text-[#9CA3AF] hover:bg-[#242424] transition-colors">{totalPages}</button>
        </>
      )}

      <button
        onClick={() => onPage(page + 1)}
        disabled={page >= totalPages}
        className="w-8 h-8 flex items-center justify-center rounded-lg border border-[#2E2E2E] bg-[#1A1A1A] text-[#9CA3AF] hover:bg-[#242424] disabled:opacity-40 transition-colors"
      >
        <ChevronRight size={14} />
      </button>
    </div>
  );
}

// ── Copy Card ─────────────────────────────────────────────────────────────────

function CopyCard({ copy }) {
  const cfg = STATUS_CONFIG[copy.status] ?? STATUS_CONFIG.draft;
  const preview = copy.content.slice(0, 100) + (copy.content.length > 100 ? "…" : "");

  return (
    <div className="group bg-[#1A1A1A] border border-[#2E2E2E] hover:border-[#6366F1]/30 rounded-xl p-4 transition-all duration-200 space-y-2.5">
      {/* Header */}
      <div className="flex items-center gap-2 flex-wrap">
        <ChannelBadge channel={copy.channel} size="xs" variant="badge" />

        <span className={`inline-flex items-center text-[10px] font-semibold px-2 py-0.5 rounded-full border ${cfg.bg} ${cfg.text}`}>
          {cfg.label}
        </span>

        <time className="ml-auto text-[10px] font-mono text-[#4B5563]">
          {new Date(copy.created_at).toLocaleDateString("pt-BR")}
        </time>
      </div>

      {/* Topic */}
      <p className="text-[10px] font-medium text-[#6366F1]">{copy.topic}</p>

      {/* Preview */}
      <p className="text-xs text-[#9CA3AF] leading-relaxed">{preview}</p>

      {/* Actions row — visible on hover */}
      <div className="flex items-center gap-2 opacity-0 group-hover:opacity-100 transition-opacity pt-0.5">
        <button className="flex items-center gap-1 text-[10px] text-[#9CA3AF] hover:text-[#F9FAFB] transition-colors">
          <Eye size={11} /> Ver
        </button>
        <span className="text-[#2E2E2E]">·</span>
        <button className="flex items-center gap-1 text-[10px] text-[#9CA3AF] hover:text-[#F9FAFB] transition-colors">
          <Palette size={11} /> Gerar Arte
        </button>
        <span className="text-[#2E2E2E]">·</span>
        <button className="flex items-center gap-1 text-[10px] text-[#9CA3AF] hover:text-[#F9FAFB] transition-colors">
          <Pencil size={11} /> Editar
        </button>
        <span className="text-[#2E2E2E]">·</span>
        <button className="flex items-center gap-1 text-[10px] text-red-500/70 hover:text-red-400 transition-colors ml-auto">
          <Trash2 size={11} /> Deletar
        </button>
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function LibraryCopysTab() {
  const [loading] = useState(false);
  const [search, setSearch] = useState("");
  const [channelFilter, setChannelFilter] = useState(null);
  const [statusFilter, setStatusFilter] = useState(null);
  const [page, setPage] = useState(1);

  const filtered = useMemo(() => {
    return MOCK_COPIES.filter((c) => {
      if (channelFilter && c.channel !== channelFilter) return false;
      if (statusFilter && c.status !== statusFilter) return false;
      if (search && !c.content.toLowerCase().includes(search.toLowerCase()) &&
        !c.topic.toLowerCase().includes(search.toLowerCase())) return false;
      return true;
    });
  }, [channelFilter, statusFilter, search]);

  const totalPages = Math.max(1, Math.ceil(filtered.length / PER_PAGE));
  const safePage = Math.min(page, totalPages);
  const paginated = filtered.slice((safePage - 1) * PER_PAGE, safePage * PER_PAGE);

  function handleChannelClick(ch) {
    setChannelFilter((prev) => (prev === ch ? null : ch));
    setPage(1);
  }

  if (loading) return <CopySkeleton />;

  return (
    <div className="space-y-4">
      {/* ── Filters ──────────────────────────────────────────── */}
      <div className="flex flex-col sm:flex-row gap-3">
        {/* Search */}
        <div className="relative flex-1">
          <Search size={13} className="absolute left-3 top-1/2 -translate-y-1/2 text-[#4B5563]" />
          <input
            type="text"
            placeholder="Buscar por texto ou tema..."
            value={search}
            onChange={(e) => { setSearch(e.target.value); setPage(1); }}
            className="w-full pl-8 pr-3 py-2 bg-[#1A1A1A] border border-[#2E2E2E] rounded-lg text-xs text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] transition-colors"
          />
        </div>

        {/* Status select */}
        <select
          value={statusFilter ?? ""}
          onChange={(e) => { setStatusFilter(e.target.value || null); setPage(1); }}
          className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-lg px-3 py-2 text-xs text-[#9CA3AF] focus:outline-none focus:border-[#6366F1] transition-colors [color-scheme:dark]"
        >
          <option value="">Todos os status</option>
          <option value="draft">Rascunho</option>
          <option value="approved">Aprovado</option>
          <option value="published">Publicado</option>
        </select>

        {/* Total */}
        <span className="self-center text-xs text-[#6B7280] whitespace-nowrap">
          {filtered.length} cop{filtered.length !== 1 ? "ys" : "y"}
        </span>
      </div>

      {/* ── Channel filter badges ─────────────────────────────── */}
      <div className="flex gap-2 flex-wrap">
        {CHANNELS.map((ch) => (
          <button
            key={ch}
            onClick={() => handleChannelClick(ch)}
            className={`transition-all ${channelFilter === ch ? "ring-2 ring-[#6366F1] ring-offset-2 ring-offset-[#0F0F0F] rounded-full" : "opacity-60 hover:opacity-100"}`}
          >
            <ChannelBadge channel={ch} size="sm" variant="icon" />
          </button>
        ))}
        {channelFilter && (
          <button
            onClick={() => { setChannelFilter(null); setPage(1); }}
            className="text-[10px] text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
          >
            × limpar
          </button>
        )}
      </div>

      {/* ── Cards list ───────────────────────────────────────── */}
      {paginated.length === 0 ? (
        <div className="py-12 text-center text-sm text-[#6B7280]">
          Nenhuma copy encontrada para os filtros aplicados.
        </div>
      ) : (
        <div className="space-y-2">
          {paginated.map((copy) => (
            <CopyCard key={copy.id} copy={copy} />
          ))}
        </div>
      )}

      {/* ── Pagination ────────────────────────────────────────── */}
      <Pagination page={safePage} totalPages={totalPages} onPage={(p) => setPage(p)} />
    </div>
  );
}
