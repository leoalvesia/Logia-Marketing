import {
  Search,
  GitBranch,
  MousePointerClick,
  PenLine,
  ClipboardCheck,
  Palette,
  Eye,
  Clock,
  Send,
  CheckCircle2,
  XCircle,
} from "lucide-react";

/**
 * Badge que representa o estado atual de um Pipeline.
 * Props:
 *   state  — PipelineState string (ex: "RESEARCHING")
 *   size   — "sm" | "md" (default "md")
 *   pulse  — boolean, força animação mesmo nos estados estáticos
 */

const STATE_CONFIG = {
  RESEARCHING: {
    label: "Pesquisando...",
    Icon: Search,
    bg: "bg-blue-950/60",
    text: "text-blue-300",
    border: "border-blue-800/50",
    dot: "bg-blue-400",
    animated: true,
    glow: "shadow-[0_0_12px_rgba(59,130,246,0.4)]",
  },
  ORCHESTRATING: {
    label: "Orquestrando...",
    Icon: GitBranch,
    bg: "bg-indigo-950/60",
    text: "text-indigo-300",
    border: "border-indigo-800/50",
    dot: "bg-indigo-400",
    animated: true,
    glow: "shadow-[0_0_12px_rgba(99,102,241,0.4)]",
  },
  AWAITING_SELECTION: {
    label: "Aguardando seleção",
    Icon: MousePointerClick,
    bg: "bg-amber-950/60",
    text: "text-amber-300",
    border: "border-amber-800/50",
    dot: "bg-amber-400",
    animated: false,
    glow: "",
  },
  GENERATING_COPY: {
    label: "Gerando copy...",
    Icon: PenLine,
    bg: "bg-purple-950/60",
    text: "text-purple-300",
    border: "border-purple-800/50",
    dot: "bg-purple-400",
    animated: true,
    glow: "shadow-[0_0_12px_rgba(168,85,247,0.4)]",
  },
  COPY_REVIEW: {
    label: "Revisão de copy",
    Icon: ClipboardCheck,
    bg: "bg-yellow-950/60",
    text: "text-yellow-300",
    border: "border-yellow-800/50",
    dot: "bg-yellow-400",
    animated: false,
    glow: "",
  },
  GENERATING_ART: {
    label: "Gerando arte...",
    Icon: Palette,
    bg: "bg-pink-950/60",
    text: "text-pink-300",
    border: "border-pink-800/50",
    dot: "bg-pink-400",
    animated: true,
    glow: "shadow-[0_0_12px_rgba(236,72,153,0.4)]",
  },
  ART_REVIEW: {
    label: "Revisão de arte",
    Icon: Eye,
    bg: "bg-orange-950/60",
    text: "text-orange-300",
    border: "border-orange-800/50",
    dot: "bg-orange-400",
    animated: false,
    glow: "",
  },
  SCHEDULED: {
    label: "Agendado",
    Icon: Clock,
    bg: "bg-cyan-950/60",
    text: "text-cyan-300",
    border: "border-cyan-800/50",
    dot: "bg-cyan-400",
    animated: false,
    glow: "",
  },
  PUBLISHING: {
    label: "Publicando...",
    Icon: Send,
    bg: "bg-blue-950/60",
    text: "text-blue-300",
    border: "border-blue-800/50",
    dot: "bg-blue-400",
    animated: true,
    glow: "shadow-[0_0_12px_rgba(59,130,246,0.4)]",
  },
  PUBLISHED: {
    label: "Publicado",
    Icon: CheckCircle2,
    bg: "bg-emerald-950/60",
    text: "text-emerald-300",
    border: "border-emerald-800/50",
    dot: "bg-emerald-400",
    animated: false,
    glow: "shadow-[0_0_8px_rgba(16,185,129,0.25)]",
  },
  FAILED: {
    label: "Falhou",
    Icon: XCircle,
    bg: "bg-red-950/60",
    text: "text-red-300",
    border: "border-red-800/50",
    dot: "bg-red-400",
    animated: false,
    glow: "",
  },
};

const UNKNOWN = {
  label: "Desconhecido",
  Icon: null,
  bg: "bg-zinc-900/60",
  text: "text-zinc-400",
  border: "border-zinc-700/50",
  dot: "bg-zinc-500",
  animated: false,
  glow: "",
};

const SIZE = {
  sm: { badge: "px-2 py-0.5 gap-1 text-xs", dot: "w-1.5 h-1.5", icon: 12 },
  md: { badge: "px-2.5 py-1 gap-1.5 text-xs", dot: "w-2 h-2", icon: 14 },
};

export function StatusBadge({ state, size = "md", pulse }) {
  const cfg = STATE_CONFIG[state] ?? UNKNOWN;
  const { Icon } = cfg;
  const sz = SIZE[size] ?? SIZE.md;
  const isAnimated = pulse ?? cfg.animated;

  return (
    <span
      className={[
        "inline-flex items-center rounded-full border font-medium",
        "transition-all duration-300",
        cfg.bg,
        cfg.text,
        cfg.border,
        sz.badge,
        isAnimated && cfg.glow ? cfg.glow : "",
      ]
        .filter(Boolean)
        .join(" ")}
    >
      {/* Dot indicator */}
      <span className="relative flex shrink-0">
        <span
          className={[
            "rounded-full",
            cfg.dot,
            sz.dot,
            isAnimated ? "animate-ping absolute opacity-75" : "hidden",
          ].join(" ")}
        />
        <span className={["rounded-full", cfg.dot, sz.dot].join(" ")} />
      </span>

      {/* Icon */}
      {Icon && <Icon size={sz.icon} className="shrink-0" />}

      {/* Label */}
      <span>{cfg.label}</span>
    </span>
  );
}
