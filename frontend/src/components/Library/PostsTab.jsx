import { useState } from "react";
import { X, CheckCircle2, AlertCircle, Clock } from "lucide-react";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { MOCK_POSTS } from "@/data/mockLibrary";

const CHANNEL_STATUS_CONFIG = {
    published: { icon: CheckCircle2, color: "#10B981", label: "Publicado" },
    pending: { icon: Clock, color: "#F59E0B", label: "Pendente" },
    draft: { icon: Clock, color: "#6B7280", label: "Rascunho" },
    scheduled: { icon: Clock, color: "#6366F1", label: "Agendado" },
    failed: { icon: AlertCircle, color: "#EF4444", label: "Erro" },
};

// ── Post Detail Modal ─────────────────────────────────────────────────────────

function PostModal({ post, onClose }) {
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
                        <h3 className="text-sm font-semibold text-[#F9FAFB]">{post.topic}</h3>
                        <p className="text-[10px] text-[#6B7280] mt-0.5">
                            {new Date(post.created_at).toLocaleDateString("pt-BR", { weekday: "long", day: "numeric", month: "long" })}
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
                    <div
                        className="w-full aspect-square rounded-xl overflow-hidden"
                        style={{ background: post.artGradient }}
                    >
                        <div className="w-full h-full flex flex-col items-center justify-center text-white/70">
                            <div className="w-14 h-14 rounded-full bg-white/10 flex items-center justify-center text-2xl mb-2">L</div>
                            <p className="text-sm font-semibold">Logia Marketing</p>
                            <p className="text-xs opacity-70 mt-0.5">{post.topic}</p>
                        </div>
                    </div>

                    {/* Copy */}
                    <div className="space-y-1.5">
                        <p className="text-[10px] font-medium text-[#6B7280] uppercase tracking-wider">Copy</p>
                        <p className="text-sm text-[#9CA3AF] leading-relaxed">{post.copy}</p>
                    </div>

                    {/* Channel statuses */}
                    <div className="space-y-2">
                        <p className="text-[10px] font-medium text-[#6B7280] uppercase tracking-wider">Status por canal</p>
                        <div className="space-y-2">
                            {post.channelStatuses.channels.map((ch, i) => {
                                const status = post.channelStatuses.statuses[i];
                                const cfg = CHANNEL_STATUS_CONFIG[status] ?? CHANNEL_STATUS_CONFIG.draft;
                                const Icon = cfg.icon;
                                return (
                                    <div key={ch} className="flex items-center gap-3 bg-[#0F0F0F] rounded-lg px-3 py-2">
                                        <ChannelBadge channel={ch} size="xs" variant="icon" />
                                        <span className="text-xs capitalize text-[#9CA3AF]">{ch === "twitter" ? "X / Twitter" : ch.charAt(0).toUpperCase() + ch.slice(1)}</span>
                                        <div className="ml-auto flex items-center gap-1.5" style={{ color: cfg.color }}>
                                            <Icon size={13} />
                                            <span className="text-[10px] font-medium">{cfg.label}</span>
                                        </div>
                                    </div>
                                );
                            })}
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
}

// ── Post Card ─────────────────────────────────────────────────────────────────

function PostCard({ post, onView }) {
    return (
        <div className="bg-[#1A1A1A] border border-[#2E2E2E] hover:border-[#6366F1]/30 rounded-xl overflow-hidden transition-all duration-200 group">
            <div className="flex gap-0">
                {/* Art thumbnail */}
                <div
                    className="shrink-0 w-20 sm:w-28"
                    style={{ background: post.artGradient }}
                >
                    <div className="w-full h-full min-h-[80px] flex items-center justify-center text-white/50">
                        <span className="text-xl">L</span>
                    </div>
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0 p-3 sm:p-4 flex flex-col gap-2">
                    {/* Topic */}
                    <p className="text-xs font-semibold text-[#F9FAFB]">{post.topic}</p>

                    {/* Copy preview */}
                    <p className="text-xs text-[#9CA3AF] line-clamp-2 leading-relaxed">{post.copy}</p>

                    {/* Channel statuses */}
                    <div className="flex items-center gap-2 flex-wrap mt-auto">
                        {post.channelStatuses.channels.map((ch, i) => {
                            const status = post.channelStatuses.statuses[i];
                            const cfg = CHANNEL_STATUS_CONFIG[status] ?? CHANNEL_STATUS_CONFIG.draft;
                            const Icon = cfg.icon;
                            return (
                                <div key={ch} className="flex items-center gap-1">
                                    <ChannelBadge channel={ch} size="xs" variant="icon" />
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

// ── Main component ────────────────────────────────────────────────────────────

export default function LibraryPostsTab() {
    const [selectedPost, setSelectedPost] = useState(null);

    return (
        <div className="space-y-3">
            <div className="flex items-center justify-between">
                <p className="text-xs text-[#6B7280]">{MOCK_POSTS.length} posts</p>
            </div>

            <div className="space-y-2">
                {MOCK_POSTS.map((post) => (
                    <PostCard key={post.id} post={post} onView={setSelectedPost} />
                ))}
            </div>

            {selectedPost && (
                <PostModal post={selectedPost} onClose={() => setSelectedPost(null)} />
            )}
        </div>
    );
}
