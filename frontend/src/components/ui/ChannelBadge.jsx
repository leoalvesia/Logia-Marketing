/**
 * Badge de canal social com ícone SVG oficial e cor da plataforma.
 * Props:
 *   channel — "instagram" | "linkedin" | "twitter" | "youtube" | "email"
 *   size    — "xs" | "sm" | "md" | "lg" (default "md")
 *   variant — "badge" | "icon" | "pill" (default "badge")
 *             badge: ícone + nome
 *             icon: só ícone com fundo
 *             pill: ícone + nome arredondado
 */

// ── SVG icons (inline, zero dependência externa) ──────────────────────────────

function IconInstagram({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <defs>
        <linearGradient id="ig-grad" x1="0%" y1="100%" x2="100%" y2="0%">
          <stop offset="0%" stopColor="#F58529" />
          <stop offset="50%" stopColor="#E1306C" />
          <stop offset="100%" stopColor="#833AB4" />
        </linearGradient>
      </defs>
      <rect x="2" y="2" width="20" height="20" rx="5.5" stroke="url(#ig-grad)" strokeWidth="2" />
      <circle cx="12" cy="12" r="4.5" stroke="url(#ig-grad)" strokeWidth="2" />
      <circle cx="17.5" cy="6.5" r="1.2" fill="url(#ig-grad)" />
    </svg>
  );
}

function IconLinkedin({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="#0A66C2">
      <rect x="2" y="2" width="20" height="20" rx="4" />
      <text x="5" y="17" fontFamily="Arial" fontWeight="bold" fontSize="12" fill="white">in</text>
    </svg>
  );
}

function IconTwitter({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="currentColor">
      <rect width="24" height="24" rx="4" fill="#000000" />
      <path
        d="M13.988 10.178 19.595 3.5h-1.328l-4.876 5.671L9.5 3.5H4.5l5.884 8.568L4.5 20.5h1.328l5.143-5.981L14.5 20.5h5L13.988 10.178Zm-1.822 2.12-.596-.853-4.735-6.77H8.9l3.826 5.47.596.853 4.973 7.112h-2.065l-4.064-5.812Z"
        fill="white"
      />
    </svg>
  );
}

function IconYoutube({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24">
      <rect width="24" height="24" rx="4" fill="#FF0000" />
      <path d="M19.8 7.8a2.4 2.4 0 0 0-1.7-1.7C16.8 5.7 12 5.7 12 5.7s-4.8 0-6.1.4A2.4 2.4 0 0 0 4.2 7.8C3.8 9.1 3.8 12 3.8 12s0 2.9.4 4.2a2.4 2.4 0 0 0 1.7 1.7c1.3.4 6.1.4 6.1.4s4.8 0 6.1-.4a2.4 2.4 0 0 0 1.7-1.7c.4-1.3.4-4.2.4-4.2s0-2.9-.4-4.2Z" fill="white" />
      <polygon points="10,9 10,15 15,12" fill="#FF0000" />
    </svg>
  );
}

function IconEmail({ size }) {
  return (
    <svg width={size} height={size} viewBox="0 0 24 24" fill="none">
      <rect x="2" y="4" width="20" height="16" rx="3" fill="#6366F1" />
      <path d="M2 7l10 7 10-7" stroke="white" strokeWidth="1.5" strokeLinecap="round" />
    </svg>
  );
}

// ── Configuração por canal ─────────────────────────────────────────────────────

const CHANNEL_CONFIG = {
  instagram: {
    label: "Instagram",
    Icon: IconInstagram,
    textColor: "text-[#E1306C]",
    bg: "bg-[#E1306C]/10",
    border: "border-[#E1306C]/30",
    hover: "hover:bg-[#E1306C]/20",
  },
  linkedin: {
    label: "LinkedIn",
    Icon: IconLinkedin,
    textColor: "text-[#0A66C2]",
    bg: "bg-[#0A66C2]/10",
    border: "border-[#0A66C2]/30",
    hover: "hover:bg-[#0A66C2]/20",
  },
  twitter: {
    label: "Twitter / X",
    Icon: IconTwitter,
    textColor: "text-zinc-200",
    bg: "bg-zinc-800/60",
    border: "border-zinc-600/40",
    hover: "hover:bg-zinc-700/60",
  },
  youtube: {
    label: "YouTube",
    Icon: IconYoutube,
    textColor: "text-[#FF0000]",
    bg: "bg-[#FF0000]/10",
    border: "border-[#FF0000]/30",
    hover: "hover:bg-[#FF0000]/20",
  },
  email: {
    label: "E-mail",
    Icon: IconEmail,
    textColor: "text-[#6366F1]",
    bg: "bg-[#6366F1]/10",
    border: "border-[#6366F1]/30",
    hover: "hover:bg-[#6366F1]/20",
  },
};

const UNKNOWN_CHANNEL = {
  label: "Canal",
  Icon: null,
  textColor: "text-zinc-400",
  bg: "bg-zinc-800/60",
  border: "border-zinc-700/40",
  hover: "",
};

const ICON_SIZE = { xs: 12, sm: 14, md: 16, lg: 20 };
const TEXT_SIZE = { xs: "text-[10px]", sm: "text-xs", md: "text-xs", lg: "text-sm" };
const PADDING   = { xs: "px-1.5 py-0.5 gap-1", sm: "px-2 py-0.5 gap-1.5", md: "px-2.5 py-1 gap-1.5", lg: "px-3 py-1.5 gap-2" };

export function ChannelBadge({ channel, size = "md", variant = "badge" }) {
  const cfg = CHANNEL_CONFIG[channel?.toLowerCase()] ?? UNKNOWN_CHANNEL;
  const iconSz = ICON_SIZE[size] ?? ICON_SIZE.md;
  const { Icon } = cfg;

  if (variant === "icon") {
    return (
      <span
        className={[
          "inline-flex items-center justify-center rounded-md",
          cfg.bg,
          cfg.border,
          "border",
          size === "xs" ? "w-5 h-5" :
          size === "sm" ? "w-6 h-6" :
          size === "lg" ? "w-9 h-9" : "w-7 h-7",
        ].join(" ")}
        title={cfg.label}
      >
        {Icon && <Icon size={iconSz} />}
      </span>
    );
  }

  return (
    <span
      className={[
        "inline-flex items-center rounded-md border font-medium transition-colors",
        cfg.bg,
        cfg.border,
        cfg.textColor,
        cfg.hover,
        PADDING[size] ?? PADDING.md,
        variant === "pill" ? "rounded-full" : "rounded-md",
      ].join(" ")}
    >
      {Icon && <Icon size={iconSz} />}
      <span className={TEXT_SIZE[size] ?? TEXT_SIZE.md}>{cfg.label}</span>
    </span>
  );
}

/** Lista de badges para múltiplos canais */
export function ChannelBadgeList({ channels = [], size = "sm", variant = "badge" }) {
  return (
    <div className="flex flex-wrap gap-1.5">
      {channels.map((ch) => (
        <ChannelBadge key={ch} channel={ch} size={size} variant={variant} />
      ))}
    </div>
  );
}
