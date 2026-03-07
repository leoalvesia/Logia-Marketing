/**
 * Toast notification system using Radix UI Toast.
 * Export: ToastProvider (wrap app), useToast (hook to fire toasts).
 */
import { createContext, useContext, useCallback, useRef, useState } from "react";
import * as RadixToast from "@radix-ui/react-toast";
import { CheckCircle2, XCircle, Info, AlertTriangle, X } from "lucide-react";

// ── Types ─────────────────────────────────────────────────────────────────────
// type: 'success' | 'error' | 'info' | 'warning'
const TOAST_CONFIG = {
    success: {
        icon: CheckCircle2,
        iconColor: "#10B981",
        bg: "bg-emerald-950/90 border-emerald-800/60",
        duration: 3000,
    },
    error: {
        icon: XCircle,
        iconColor: "#EF4444",
        bg: "bg-red-950/90 border-red-800/60",
        duration: 5000,
    },
    info: {
        icon: Info,
        iconColor: "#6366F1",
        bg: "bg-indigo-950/90 border-indigo-800/60",
        duration: 3000,
    },
    warning: {
        icon: AlertTriangle,
        iconColor: "#F59E0B",
        bg: "bg-amber-950/90 border-amber-800/60",
        duration: 4000,
    },
};

// ── Context ───────────────────────────────────────────────────────────────────
const ToastContext = createContext(null);

let idCounter = 0;

export function ToastProvider({ children }) {
    const [toasts, setToasts] = useState([]);

    const toast = useCallback(({ title, description, type = "info", details }) => {
        const id = ++idCounter;
        setToasts((prev) => [...prev, { id, title, description, type, details }]);
        return id;
    }, []);

    const dismiss = useCallback((id) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    }, []);

    return (
        <ToastContext.Provider value={{ toast, dismiss }}>
            <RadixToast.Provider swipeDirection="right">
                {children}

                {/* Toast items */}
                {toasts.map((t) => {
                    const cfg = TOAST_CONFIG[t.type] ?? TOAST_CONFIG.info;
                    const Icon = cfg.icon;
                    return (
                        <RadixToast.Root
                            key={t.id}
                            duration={cfg.duration}
                            onOpenChange={(open) => { if (!open) dismiss(t.id); }}
                            className={[
                                "group relative w-[340px] flex items-start gap-3 p-4 rounded-xl border shadow-2xl",
                                "backdrop-blur-sm will-change-transform",
                                "data-[state=open]:animate-[slide-in-right_0.25s_ease-out]",
                                "data-[state=closed]:animate-[slide-out-right_0.2s_ease-in]",
                                cfg.bg,
                            ].join(" ")}
                            aria-live="polite"
                            role="status"
                        >
                            {/* Icon */}
                            <div className="shrink-0 mt-0.5">
                                <Icon size={18} style={{ color: cfg.iconColor }} aria-hidden="true" />
                            </div>

                            {/* Content */}
                            <div className="flex-1 min-w-0 space-y-0.5">
                                {t.title && (
                                    <RadixToast.Title className="text-sm font-semibold text-[#F9FAFB]">
                                        {t.title}
                                    </RadixToast.Title>
                                )}
                                {t.description && (
                                    <RadixToast.Description className="text-xs text-[#9CA3AF] leading-relaxed">
                                        {t.description}
                                    </RadixToast.Description>
                                )}
                                {t.details && t.type === "error" && (
                                    <details className="mt-1">
                                        <summary className="text-[10px] text-red-400 cursor-pointer hover:text-red-300 transition-colors">
                                            Detalhes do erro
                                        </summary>
                                        <p className="text-[10px] font-mono text-red-400/80 mt-1 break-all">{t.details}</p>
                                    </details>
                                )}
                            </div>

                            {/* Close button */}
                            <RadixToast.Close
                                className="shrink-0 opacity-0 group-hover:opacity-100 w-5 h-5 flex items-center justify-center rounded-full hover:bg-white/10 transition-all"
                                aria-label="Fechar notificação"
                            >
                                <X size={11} className="text-[#9CA3AF]" />
                            </RadixToast.Close>
                        </RadixToast.Root>
                    );
                })}

                {/* Viewport */}
                <RadixToast.Viewport
                    className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 w-[340px] max-w-[calc(100vw-2rem)] outline-none"
                    aria-label="Notificações"
                />
            </RadixToast.Provider>
        </ToastContext.Provider>
    );
}

// ── Hook ──────────────────────────────────────────────────────────────────────
export function useToast() {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error("useToast must be used inside ToastProvider");
    return ctx.toast;
}

export function useDismissToast() {
    const ctx = useContext(ToastContext);
    if (!ctx) throw new Error("useDismissToast must be used inside ToastProvider");
    return ctx.dismiss;
}
