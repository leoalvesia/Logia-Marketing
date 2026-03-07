import { useEffect, useRef, useState } from "react";
import { Search, PenLine, Palette, Globe, CheckCircle2, XCircle, Loader2 } from "lucide-react";

/**
 * Card de execução de agente de IA com streaming de texto em tempo real.
 * Props:
 *   agent     — "research" | "copy_instagram" | "copy_linkedin" | "copy_twitter"
 *               | "copy_youtube" | "copy_email" | "art"
 *   status    — "idle" | "running" | "done" | "error"
 *   channel   — string opcional (para agentes de copy)
 *   startedAt — Date ou ISO string (calcula tempo decorrido)
 *   chunks    — string[] — chunks de streaming recebidos em tempo real
 *   error     — string opcional (mensagem de erro)
 *   onRetry   — callback opcional
 */

const AGENT_META = {
  research:       { label: "Research Agent",   Icon: Search,  color: "#3B82F6" },
  copy_instagram: { label: "Copy · Instagram", Icon: PenLine, color: "#E1306C" },
  copy_linkedin:  { label: "Copy · LinkedIn",  Icon: PenLine, color: "#0A66C2" },
  copy_twitter:   { label: "Copy · Twitter/X", Icon: PenLine, color: "#F9FAFB" },
  copy_youtube:   { label: "Copy · YouTube",   Icon: PenLine, color: "#FF0000" },
  copy_email:     { label: "Copy · E-mail",    Icon: PenLine, color: "#6366F1" },
  art:            { label: "Art Agent",        Icon: Palette, color: "#EC4899" },
  default:        { label: "Agent",            Icon: Globe,   color: "#9CA3AF" },
};

function useElapsed(startedAt, running) {
  const [elapsed, setElapsed] = useState(0);
  const ref = useRef(null);

  useEffect(() => {
    if (!running || !startedAt) { setElapsed(0); return; }
    const start = new Date(startedAt).getTime();
    ref.current = setInterval(() => {
      setElapsed(Math.floor((Date.now() - start) / 1000));
    }, 1000);
    return () => clearInterval(ref.current);
  }, [startedAt, running]);

  return elapsed;
}

function formatElapsed(s) {
  if (s < 60)  return `${s}s`;
  if (s < 3600) return `${Math.floor(s / 60)}m ${s % 60}s`;
  return `${Math.floor(s / 3600)}h ${Math.floor((s % 3600) / 60)}m`;
}

export function AgentCard({
  agent = "default",
  status = "idle",
  channel,
  startedAt,
  chunks = [],
  error,
  onRetry,
}) {
  const key = channel ? `copy_${channel}` : agent;
  const meta = AGENT_META[key] ?? AGENT_META.default;
  const { Icon } = meta;

  const isRunning = status === "running";
  const isDone    = status === "done";
  const isError   = status === "error";

  const elapsed = useElapsed(startedAt, isRunning);
  const streamingText = chunks.join("");

  // Auto-scroll do container de streaming
  const streamRef = useRef(null);
  useEffect(() => {
    if (streamRef.current) {
      streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }
  }, [streamingText]);

  // ── Status indicator ────────────────────────────────────────────────────────
  function StatusIcon() {
    if (isRunning) return <Loader2 size={14} className="animate-spin text-[#6366F1]" />;
    if (isDone)    return <CheckCircle2 size={14} className="text-emerald-400" />;
    if (isError)   return <XCircle size={14} className="text-red-400" />;
    return <span className="w-3.5 h-3.5 rounded-full bg-[#2E2E2E] inline-block" />;
  }

  const borderColor = isRunning
    ? "border-[#6366F1]/40"
    : isDone
    ? "border-emerald-800/40"
    : isError
    ? "border-red-900/40"
    : "border-[#2E2E2E]";

  const glowClass = isRunning
    ? "shadow-[0_0_20px_rgba(99,102,241,0.15)]"
    : isDone
    ? "shadow-[0_0_12px_rgba(16,185,129,0.1)]"
    : "";

  return (
    <div
      className={[
        "rounded-lg border bg-[#1A1A1A] p-4 space-y-3 transition-all duration-300",
        borderColor,
        glowClass,
      ].join(" ")}
    >
      {/* ── Header ─────────────────────────────────────────────────────────── */}
      <div className="flex items-center justify-between gap-3">
        <div className="flex items-center gap-2.5 min-w-0">
          {/* Agent avatar */}
          <div
            className="flex-shrink-0 flex items-center justify-center rounded-md w-8 h-8"
            style={{ backgroundColor: `${meta.color}18`, border: `1px solid ${meta.color}30` }}
          >
            <Icon size={16} style={{ color: meta.color }} />
          </div>

          <div className="min-w-0">
            <p className="text-sm font-semibold text-[#F9FAFB] truncate">{meta.label}</p>
            <div className="flex items-center gap-1.5 mt-0.5">
              <StatusIcon />
              <span className="text-xs text-[#6B7280]">
                {isRunning && `Em execução · ${formatElapsed(elapsed)}`}
                {isDone    && "Concluído"}
                {isError   && "Erro"}
                {status === "idle" && "Aguardando"}
              </span>
            </div>
          </div>
        </div>

        {/* Elapsed badge */}
        {(isRunning || isDone) && (
          <span className="flex-shrink-0 font-mono text-[10px] text-[#6B7280] bg-[#242424] px-2 py-0.5 rounded-md border border-[#2E2E2E]">
            {formatElapsed(elapsed)}
          </span>
        )}

        {/* Retry */}
        {isError && onRetry && (
          <button
            onClick={onRetry}
            className="flex-shrink-0 text-xs text-[#6366F1] hover:text-[#818CF8] transition-colors font-medium"
          >
            Tentar novamente
          </button>
        )}
      </div>

      {/* ── Streaming text ──────────────────────────────────────────────────── */}
      {(isRunning || isDone) && streamingText && (
        <div
          ref={streamRef}
          className="relative rounded-md bg-[#0F0F0F] border border-[#2E2E2E] p-3 max-h-40 overflow-y-auto"
        >
          <pre
            className={[
              "font-mono text-[11px] text-[#9CA3AF] whitespace-pre-wrap break-words leading-relaxed",
              isRunning ? "streaming-cursor" : "",
            ].join(" ")}
          >
            {streamingText || " "}
          </pre>

          {/* Fade overlay no topo */}
          <div className="absolute top-0 left-0 right-0 h-4 rounded-t-md bg-gradient-to-b from-[#0F0F0F] to-transparent pointer-events-none" />
        </div>
      )}

      {/* ── Error message ───────────────────────────────────────────────────── */}
      {isError && error && (
        <div className="rounded-md bg-red-950/40 border border-red-900/50 px-3 py-2">
          <p className="text-xs text-red-300 font-mono">{error}</p>
        </div>
      )}

      {/* ── Progress bar (running) ─────────────────────────────────────────── */}
      {isRunning && (
        <div className="h-0.5 w-full rounded-full bg-[#2E2E2E] overflow-hidden">
          <div className="h-full rounded-full bg-gradient-to-r from-[#4F46E5] to-[#6366F1] animate-[shimmer_2s_linear_infinite] bg-[length:200%_100%]" />
        </div>
      )}
    </div>
  );
}

/**
 * Grade de AgentCards para múltiplos agentes simultâneos.
 */
export function AgentGrid({ agents = [] }) {
  if (agents.length === 0) return null;
  return (
    <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-3">
      {agents.map((a) => (
        <AgentCard key={a.agent + (a.channel ?? "")} {...a} />
      ))}
    </div>
  );
}
