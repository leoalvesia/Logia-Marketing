import { useEffect, useState } from "react";
import { LayoutGrid, X, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { useLibraryStore } from "@/stores/libraryStore";

const STATUS_CFG = {
    published: { icon: CheckCircle2, color: "#10B981", label: "Publicado" },
    approved:  { icon: CheckCircle2, color: "#6366F1", label: "Aprovado" },
    pending:   { icon: Clock,        color: "#F59E0B", label: "Pendente" },
    draft:     { icon: Clock,        color: "#6B7280", label: "Rascunho" },
    scheduled: { icon: Clock,        color: "#6366F1", label: "Agendado" },
    failed:    { icon: AlertCircle,  color: "#EF4444", label: "Erro" },
};

/** Extrai a primeira string de texto de um objeto de conteúdo de qualquer canal. */
function firstText(content) {
    if (!content || typeof content !== "object") return "";
    const v =
        content.caption ||
        content.post ||
        (Array.isArray(content.tweets) ? content.tweets[0] : null) ||
        content.subject ||
        content.roteiro ||
        "";
    return typeof v === "string" ? v.slice(0, 140) + (v.length > 140 ? "…" : "") : "";
}

// ── Skeleton ──────────────────────────────────────────────────────────────────

function PostSkeleton() {
    return (
        <div className="space-y-2">
            {Array.from({ length: 4 }).map((_, i) => (
                <div key={i} className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl h-24 animate-pulse" />
            ))}
        </div>
    );
}

// ── Post Detail Modal ─────────────────────────────────────────────────────────

function PostModal({ post, onClose }) {
    const firstCopy = post.copies?.[0];
    const firstArt = post.arts?.[0];
    const imageUrl = firstArt?.image_urls?.[0];

    return (
        <div
            className="fixed inset-0 z-50 bg-black/75 backdrop-blur-sm flex items-center justify-center p-4"
            onClick={onClose}
        >
            <div
                className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl shadow-2xl max-w-lg w-full max-h-[85vh] overflow-y-auto"
                onClick={(e) => e.stopPropagation()}
            >
                {/* Header */}
                <div className="flex items-start justify-between p-5 border-b border-[#2E2E2E]">
                    <div>
                        <h3 className="text-sm font-semibold text-[#F9FAFB]">
                            Pipeline <span className="font-mono text-[#6366F1]">#{post.pipeline_id.slice(-8)}</span>
                        </h3>
                        <p className="text-[10px] text-[#6B7280] mt-0.5">
                            {post.copies.length} cop{post.copies.length !== 1 ? "ys" : "y"} · {post.arts.length} arte{post.arts.length !== 1 ? "s" : ""}
                        </p>
                    </div>
                    <button
                        onClick={onClose}
                        className="w-7 h-7 rounded-full bg-[#2E2E2E] flex items-center justify-center hover:bg-[#3E3E3E] transition-colors"
                    >
                        <X size={13} className="text-[#9CA3AF]" />
                    </button>
                </div>

                <div className="p-5 space-y-5">
                    {/* Art preview */}
                    <div className="w-full aspect-square rounded-xl overflow-hidden bg-[#242424]">
                        {imageUrl ? (
                            <img src={imageUrl} alt="Arte" className="w-full h-full object-cover" />
                        ) : (
                            <div className="w-full h-full flex flex-col items-center justify-center text-white/30 gap-2">
                                <div className="w-14 h-14 rounded-full bg-white/5 flex items-center justify-center text-2xl">L</div>
                                <p className="text-xs">Arte não gerada</p>
                            </div>
                        )}
                    </div>

                    {/* Copies per channel */}
                    <div className="space-y-2">
                        <p className="text-[10px] font-medium text-[#6B7280] uppercase tracking-wider">Copys por canal</p>
                        {post.copies.length === 0 ? (
                            <p className="text-xs text-[#4B5563]">Nenhuma copy gerada.</p>
                        ) : (
                            post.copies.map((c) => {
                                const cfg = STATUS_CFG[c.status] ?? STATUS_CFG.draft;
                                const Icon = cfg.icon;
                                const preview = firstText(c.content);
                                return (
                                    <div key={c.id} className="bg-[#0F0F0F] rounded-lg px-3 py-3 space-y-1.5">
                                        <div className="flex items-center gap-2">
                                            <ChannelBadge channel={c.channel} size="xs" variant="icon" />
                                            <div className="ml-auto flex items-center gap-1" style={{ color: cfg.color }}>
                                                <Icon size={11} />
                                                <span className="text-[10px] font-medium">{cfg.label}</span>
                                            </div>
                                        </div>
                                        {preview && (
                                            <p className="text-[11px] text-[#9CA3AF] leading-relaxed line-clamp-3">{preview}</p>
                                        )}
                                    </div>
                                );
                            })
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── Post Card ─────────────────────────────────────────────────────────────────

function PostCard({ post, onView }) {
    const firstCopy = post.copies?.[0];
    const firstArt = post.arts?.[0];
    const imageUrl = firstArt?.image_urls?.[0];
    const preview = firstCopy ? firstText(firstCopy.content) : null;

    return (
        <div className="bg-[#1A1A1A] border border-[#2E2E2E] hover:border-[#6366F1]/30 rounded-xl overflow-hidden transition-all duration-200 group">
            <div className="flex gap-0">
                {/* Art thumbnail */}
                <div className="shrink-0 w-20 sm:w-28 bg-[#242424]">
                    {imageUrl ? (
                        <img
                            src={imageUrl}
                            alt="Arte"
                            className="w-full h-full min-h-[80px] object-cover"
                        />
                    ) : (
                        <div className="w-full h-full min-h-[80px] flex items-center justify-center text-white/20">
                            <span className="text-xl">L</span>
                        </div>
                    )}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 p-3 sm:p-4 flex flex-col gap-2">
                    {/* Pipeline ID */}
                    <p className="text-[10px] font-mono text-[#6366F1]">
                        #{post.pipeline_id.slice(-8)}
                    </p>

                    {/* Copy preview */}
                    {preview ? (
                        <p className="text-xs text-[#9CA3AF] line-clamp-2 leading-relaxed">{preview}</p>
                    ) : (
                        <p className="text-xs text-[#4B5563] italic">Sem copy gerada</p>
                    )}

                    {/* Channel statuses */}
                    <div className="flex items-center gap-2 flex-wrap mt-auto">
                        {post.copies.map((c) => {
                            const cfg = STATUS_CFG[c.status] ?? STATUS_CFG.draft;
                            const Icon = cfg.icon;
                            return (
                                <div key={c.id} className="flex items-center gap-1">
                                    <ChannelBadge channel={c.channel} size="xs" variant="icon" />
                                    <Icon size={10} style={{ color: cfg.color }} />
                                </div>
                            );
                        })}

                        <button
                            onClick={() => onView(post)}
                            className="ml-auto text-[10px] font-medium text-[#6366F1] hover:text-[#818CF8] transition-colors opacity-0 group-hover:opacity-100"
                        >
                            Ver Detalhes →
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── Empty state ───────────────────────────────────────────────────────────────

function PostsEmptyState() {
    return (
        <div className="py-20 flex flex-col items-center gap-4 text-center">
            <div className="w-14 h-14 rounded-full bg-[#1A1A1A] border border-[#2E2E2E] flex items-center justify-center">
                <LayoutGrid size={22} className="text-[#4B5563]" />
            </div>
            <div className="space-y-1">
                <p className="text-sm font-semibold text-[#9CA3AF]">Nenhum post ainda</p>
                <p className="text-xs text-[#4B5563] max-w-xs">
                    Inicie um pipeline, selecione um tema e aprove uma copy para ver seus posts aqui.
                </p>
            </div>
        </div>
    );
}

// ── Main component ────────────────────────────────────────────────────────────

export default function LibraryPostsTab() {
    const { posts, postsTotal, loading, error, fetchPosts } = useLibraryStore();
    const [selectedPost, setSelectedPost] = useState(null);

    useEffect(() => {
        fetchPosts();
    }, []);

    if (loading) return <PostSkeleton />;

    return (
        <div className="space-y-3">
            {error && (
                <div className="text-xs text-red-400 bg-red-950/30 border border-red-800/40 rounded-lg px-4 py-3">
                    Erro ao carregar posts: {error}
                </div>
            )}

            <div className="flex items-center justify-between">
                <p className="text-xs text-[#6B7280]">{postsTotal} post{postsTotal !== 1 ? "s" : ""}</p>
            </div>

            {posts.length === 0 ? (
                <PostsEmptyState />
            ) : (
                <div className="space-y-2">
                    {posts.map((post) => (
                        <PostCard key={post.pipeline_id} post={post} onView={setSelectedPost} />
                    ))}
                </div>
            )}

            {selectedPost && (
                <PostModal post={selectedPost} onClose={() => setSelectedPost(null)} />
            )}
        </div>
    );
}
