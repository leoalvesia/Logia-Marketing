import { useState } from "react";
import { Send, Clock, CheckCircle2, AlertCircle } from "lucide-react";
import { ChannelBadge } from "@/components/ui/ChannelBadge";

const MOCK_CHANNELS_PREVIEW = [
    { channel: "instagram", copy: "✨ A IA generativa está transformando como as PMEs fazem marketing — e os números são impressionantes..." },
    { channel: "linkedin", copy: "🔍 Novo estudo da FGV revela: PMEs que adotam IA generativa crescem 3x mais rápido..." },
    { channel: "twitter", copy: "A IA generativa está transformando PMEs brasileiras: 180% ROI médio em 6 meses ⚡" },
];

const PUBLISH_STATUS = {
    idle: { bg: "bg-[#2E2E2E]", fill: "bg-[#6366F1]", label: "" },
    publishing: { bg: "bg-[#2E2E2E]", fill: "bg-[#6366F1]", label: "Publicando..." },
    done: { bg: "bg-emerald-950/30", fill: "bg-emerald-500", label: "Publicado" },
    error: { bg: "bg-red-950/30", fill: "bg-red-500", label: "Erro" },
};

function ChannelRow({ channel, copy, progress, status }) {
    const cfg = PUBLISH_STATUS[status] ?? PUBLISH_STATUS.idle;

    return (
        <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-4 space-y-3">
            {/* Header */}
            <div className="flex items-center justify-between">
                <ChannelBadge channel={channel} variant="badge" size="sm" />
                {status === "done" && <CheckCircle2 size={16} className="text-emerald-400" />}
                {status === "error" && <AlertCircle size={16} className="text-red-400" />}
            </div>

            {/* Copy preview */}
            <p className="text-xs text-[#9CA3AF] line-clamp-2 leading-relaxed">{copy}</p>

            {/* Progress bar */}
            {(status === "publishing" || status === "done" || status === "error") && (
                <div className="space-y-1">
                    <div className={`h-1 w-full rounded-full overflow-hidden ${cfg.bg}`}>
                        <div
                            className={`h-full rounded-full transition-all duration-500 ${cfg.fill} ${status === "publishing" ? "animate-[shimmer_2s_linear_infinite] bg-[length:200%_100%]" : ""}`}
                            style={{ width: status === "done" ? "100%" : status === "error" ? "60%" : `${progress}%` }}
                        />
                    </div>
                    {cfg.label && (
                        <p className="text-[10px] font-mono text-[#6B7280]">{cfg.label}</p>
                    )}
                </div>
            )}
        </div>
    );
}

export default function PublishPanel({ channels = MOCK_CHANNELS_PREVIEW, onPublish, onSchedule }) {
    const [scheduledAt, setScheduledAt] = useState("");
    const [publishing, setPublishing] = useState(false);
    const [scheduling, setScheduling] = useState(false);
    const [publishStatuses, setPublishStatuses] = useState({});
    const [progress, setProgress] = useState({});

    // Minimum datetime for the picker: now + 5 min
    const minDatetime = new Date(Date.now() + 5 * 60 * 1000)
        .toISOString()
        .slice(0, 16);

    async function handlePublish() {
        setPublishing(true);
        const initial = {};
        const prog = {};
        channels.forEach(({ channel }) => {
            initial[channel] = "publishing";
            prog[channel] = 0;
        });
        setPublishStatuses(initial);
        setProgress(prog);

        // Simulate sequential publication progress
        for (const { channel } of channels) {
            await simulateProgress(channel);
        }

        setPublishing(false);
        try {
            await onPublish?.();
        } catch { /* handled in parent */ }
    }

    function simulateProgress(channel) {
        return new Promise((resolve) => {
            let pct = 0;
            const iv = setInterval(() => {
                pct += Math.random() * 25;
                if (pct >= 100) {
                    pct = 100;
                    clearInterval(iv);
                    setPublishStatuses((s) => ({ ...s, [channel]: "done" }));
                    resolve();
                }
                setProgress((p) => ({ ...p, [channel]: Math.round(pct) }));
            }, 300);
        });
    }

    async function handleSchedule() {
        if (!scheduledAt) return;
        setScheduling(true);
        await new Promise((r) => setTimeout(r, 800));
        setScheduling(false);
        onSchedule?.(scheduledAt);
    }

    const allDone = channels.every(({ channel }) => publishStatuses[channel] === "done");

    return (
        <div className="space-y-6">
            <div>
                <h2 className="text-lg font-semibold text-[#F9FAFB]">Publicar</h2>
                <p className="text-sm text-[#9CA3AF] mt-0.5">
                    Revise o preview final e publique ou agende pelos canais selecionados.
                </p>
            </div>

            {/* Channel previews */}
            <div className="space-y-3">
                {channels.map(({ channel, copy }) => (
                    <ChannelRow
                        key={channel}
                        channel={channel}
                        copy={copy}
                        progress={progress[channel] ?? 0}
                        status={publishStatuses[channel] ?? "idle"}
                    />
                ))}
            </div>

            {allDone && (
                <div className="flex items-center gap-2 text-sm text-emerald-400 bg-emerald-950/30 border border-emerald-900/50 rounded-lg px-4 py-3">
                    <CheckCircle2 size={16} />
                    <span className="font-medium">Todos os canais publicados com sucesso!</span>
                </div>
            )}

            {/* Schedule + publish actions */}
            {!allDone && (
                <div className="flex flex-col sm:flex-row gap-3 pt-3 border-t border-[#2E2E2E]">
                    {/* Schedule datetime + button */}
                    <div className="flex flex-1 gap-2">
                        <input
                            type="datetime-local"
                            min={minDatetime}
                            value={scheduledAt}
                            onChange={(e) => setScheduledAt(e.target.value)}
                            className="flex-1 bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] focus:outline-none focus:border-[#6366F1] transition-colors [color-scheme:dark]"
                        />
                        <button
                            onClick={handleSchedule}
                            disabled={!scheduledAt || scheduling || publishing}
                            className="flex items-center gap-1.5 px-4 py-2 rounded-lg border border-[#2E2E2E] bg-[#1A1A1A] hover:bg-[#242424] text-sm text-[#9CA3AF] hover:text-[#F9FAFB] disabled:opacity-50 transition-all"
                        >
                            <Clock size={14} />
                            {scheduling ? "Agendando..." : "Agendar"}
                        </button>
                    </div>

                    {/* Publish now */}
                    <button
                        onClick={handlePublish}
                        disabled={publishing || scheduling}
                        className="flex items-center justify-center gap-2 bg-[#6366F1] hover:bg-[#4F46E5] disabled:opacity-60 text-white text-sm font-semibold px-6 py-2.5 rounded-lg transition-all shadow-[0_0_16px_rgba(99,102,241,0.3)]"
                    >
                        <Send size={15} className={publishing ? "animate-pulse" : ""} />
                        {publishing ? "Publicando..." : "Publicar Agora"}
                    </button>
                </div>
            )}
        </div>
    );
}
