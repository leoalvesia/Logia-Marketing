import { useState, useRef, useEffect } from "react";
import * as Tooltip from "@radix-ui/react-tooltip";

/**
 * Barra de score com gradiente vermelho → amarelo → verde e tooltip de breakdown.
 * Props:
 *   score     — 0.0 a 1.0
 *   label     — string (ex: "Relevância")
 *   breakdown — array de { label: string, value: number } para o tooltip
 *   size      — "sm" | "md" | "lg" (default "md")
 *   animated  — boolean (default true) — anima o preenchimento no mount
 */

function scoreToColor(score) {
  // Interpola: vermelho(0) → amarelo(0.5) → verde(1)
  if (score <= 0.5) {
    const t = score * 2; // 0 → 1
    const r = Math.round(239 - (239 - 234) * t); // ~EF → EA
    const g = Math.round(68  + (159 - 68)  * t); // 44 → 9F
    const b = Math.round(68  + (11  - 68)  * t); // 44 → 0B
    return `rgb(${r},${g},${b})`;
  } else {
    const t = (score - 0.5) * 2; // 0 → 1
    const r = Math.round(234 - (234 - 34)  * t); // EA → 22
    const g = Math.round(159 + (197 - 159) * t); // 9F → C5
    const b = Math.round(11  + (94  - 11)  * t); // 0B → 5E
    return `rgb(${r},${g},${b})`;
  }
}

const HEIGHT = { sm: "h-1", md: "h-1.5", lg: "h-2" };
const TEXT_SIZE = { sm: "text-[10px]", md: "text-xs", lg: "text-sm" };

export function ScoreBar({
  score = 0,
  label,
  breakdown,
  size = "md",
  animated = true,
}) {
  const clamped = Math.max(0, Math.min(1, score));
  const pct = Math.round(clamped * 100);
  const color = scoreToColor(clamped);

  const [displayPct, setDisplayPct] = useState(animated ? 0 : pct);
  const rafRef = useRef(null);

  useEffect(() => {
    if (!animated) {
      setDisplayPct(pct);
      return;
    }
    const start = performance.now();
    const duration = 800;
    const from = 0;

    function step(now) {
      const elapsed = now - start;
      const progress = Math.min(elapsed / duration, 1);
      // ease-out cubic
      const eased = 1 - Math.pow(1 - progress, 3);
      setDisplayPct(Math.round(from + (pct - from) * eased));
      if (progress < 1) rafRef.current = requestAnimationFrame(step);
    }
    rafRef.current = requestAnimationFrame(step);
    return () => cancelAnimationFrame(rafRef.current);
  }, [pct, animated]);

  const hasBreakdown = Array.isArray(breakdown) && breakdown.length > 0;

  const bar = (
    <div className="space-y-1 w-full">
      {/* Header row */}
      {(label || score !== undefined) && (
        <div className="flex items-center justify-between">
          {label && (
            <span className={["font-medium text-[#9CA3AF]", TEXT_SIZE[size]].join(" ")}>
              {label}
            </span>
          )}
          <span
            className={["font-mono font-medium tabular-nums", TEXT_SIZE[size]].join(" ")}
            style={{ color }}
          >
            {pct}%
          </span>
        </div>
      )}

      {/* Track */}
      <div
        className={[
          "w-full rounded-full bg-[#2E2E2E] overflow-hidden",
          HEIGHT[size] ?? HEIGHT.md,
        ].join(" ")}
      >
        <div
          className="h-full rounded-full transition-none"
          style={{
            width: `${displayPct}%`,
            background: `linear-gradient(90deg, ${scoreToColor(0)}, ${color})`,
            boxShadow: `0 0 6px ${color}40`,
          }}
        />
      </div>
    </div>
  );

  if (!hasBreakdown) return bar;

  return (
    <Tooltip.Provider delayDuration={200}>
      <Tooltip.Root>
        <Tooltip.Trigger asChild>
          <div className="cursor-default w-full">{bar}</div>
        </Tooltip.Trigger>
        <Tooltip.Portal>
          <Tooltip.Content
            className={[
              "z-50 rounded-lg border border-[#2E2E2E] bg-[#1A1A1A] p-3",
              "shadow-[0_8px_32px_rgba(0,0,0,0.6)]",
              "text-xs text-[#F9FAFB] min-w-[180px]",
              "animate-fade-in",
            ].join(" ")}
            sideOffset={6}
          >
            <p className="mb-2 font-semibold text-[#9CA3AF] uppercase tracking-wider text-[10px]">
              Breakdown do score
            </p>
            <div className="space-y-2">
              {breakdown.map((item) => (
                <div key={item.label} className="flex items-center justify-between gap-4">
                  <span className="text-[#9CA3AF]">{item.label}</span>
                  <div className="flex items-center gap-1.5">
                    <div className="w-16 h-1 rounded-full bg-[#2E2E2E] overflow-hidden">
                      <div
                        className="h-full rounded-full"
                        style={{
                          width: `${Math.round(item.value * 100)}%`,
                          background: scoreToColor(item.value),
                        }}
                      />
                    </div>
                    <span
                      className="font-mono tabular-nums w-7 text-right"
                      style={{ color: scoreToColor(item.value) }}
                    >
                      {Math.round(item.value * 100)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
            <Tooltip.Arrow className="fill-[#2E2E2E]" />
          </Tooltip.Content>
        </Tooltip.Portal>
      </Tooltip.Root>
    </Tooltip.Provider>
  );
}
