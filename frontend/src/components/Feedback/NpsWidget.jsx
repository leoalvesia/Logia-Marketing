/**
 * NpsWidget — modal não intrusivo no canto inferior direito.
 *
 * Exibido 7 dias após o cadastro, uma única vez.
 * "Agora não" adia 7 dias adicionais.
 *
 * Controle via localStorage:
 *   logia:nps_shown_at  — timestamp da última exibição (null = nunca)
 *   logia:nps_next_show — timestamp mínimo para próxima exibição
 *   logia:nps_done      — "1" se o usuário já respondeu (não exibe mais)
 */

import { useState, useEffect } from "react";
import { X, Send } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

const API_BASE = import.meta.env.VITE_API_URL || "";
const SEVEN_DAYS_MS = 7 * 24 * 60 * 60 * 1000;

function shouldShow(userCreatedAt) {
    if (localStorage.getItem("logia:nps_done") === "1") return false;

    const nextShow = localStorage.getItem("logia:nps_next_show");
    if (nextShow && Date.now() < parseInt(nextShow, 10)) return false;

    // Só exibe após 7 dias do cadastro
    if (userCreatedAt) {
        const registered = new Date(userCreatedAt).getTime();
        if (Date.now() - registered < SEVEN_DAYS_MS) return false;
    }

    return true;
}

function scoreColor(score) {
    if (score <= 6) return "bg-red-500 hover:bg-red-400 border-red-500";
    if (score <= 8) return "bg-yellow-500 hover:bg-yellow-400 border-yellow-500";
    return "bg-green-500 hover:bg-green-400 border-green-500";
}

function scoreColorSelected(score) {
    if (score <= 6) return "bg-red-500 border-red-500 text-white";
    if (score <= 8) return "bg-yellow-500 border-yellow-500 text-white";
    return "bg-green-500 border-green-500 text-white";
}

export default function NpsWidget() {
    const user = useAuthStore((s) => s.user);
    const token = useAuthStore((s) => s.token);

    const [visible, setVisible] = useState(false);
    const [selected, setSelected] = useState(null);
    const [comment, setComment] = useState("");
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);

    useEffect(() => {
        // Checar após breve delay para não bloquear a renderização inicial
        const timer = setTimeout(() => {
            if (user && token && shouldShow(user.created_at)) {
                setVisible(true);
            }
        }, 3000);
        return () => clearTimeout(timer);
    }, [user, token]);

    if (!visible) return null;

    function dismiss() {
        // Adia 7 dias
        localStorage.setItem("logia:nps_next_show", String(Date.now() + SEVEN_DAYS_MS));
        setVisible(false);
    }

    async function submit() {
        if (selected === null) return;
        setLoading(true);
        try {
            await fetch(`${API_BASE}/feedback/nps`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({ score: selected, comment: comment || null }),
            });
        } catch {
            // Falha silenciosa — não penalizar o usuário
        }
        localStorage.setItem("logia:nps_done", "1");
        setSubmitted(true);
        setTimeout(() => setVisible(false), 2500);
        setLoading(false);
    }

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-label="Pesquisa de satisfação"
            className="fixed bottom-5 right-5 z-50 w-80 bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl shadow-[0_16px_48px_rgba(0,0,0,0.7)] animate-[slide-up_0.3s_ease-out]"
        >
            {submitted ? (
                <div className="p-5 text-center space-y-2">
                    <p className="text-2xl">🙏</p>
                    <p className="text-sm font-semibold text-[#F9FAFB]">Obrigado pelo feedback!</p>
                    <p className="text-xs text-[#9CA3AF]">Sua opinião nos ajuda a melhorar.</p>
                </div>
            ) : (
                <div className="p-5 space-y-4">
                    {/* Header */}
                    <div className="flex items-start justify-between gap-2">
                        <p className="text-sm font-semibold text-[#F9FAFB] leading-snug">
                            De 0 a 10, quanto você recomendaria a Logia para um colega?
                        </p>
                        <button
                            onClick={dismiss}
                            aria-label="Fechar e adiar"
                            className="shrink-0 text-[#6B7280] hover:text-[#9CA3AF] transition-colors mt-0.5"
                        >
                            <X size={15} aria-hidden="true" />
                        </button>
                    </div>

                    {/* Grid de notas 0–10 */}
                    <div>
                        <div className="flex justify-between mb-1">
                            <span className="text-[9px] text-[#6B7280]">Jamais</span>
                            <span className="text-[9px] text-[#6B7280]">Com certeza</span>
                        </div>
                        <div className="grid grid-cols-11 gap-1">
                            {Array.from({ length: 11 }, (_, i) => (
                                <button
                                    key={i}
                                    type="button"
                                    onClick={() => setSelected(i)}
                                    aria-label={`Nota ${i}`}
                                    aria-pressed={selected === i}
                                    className={`h-7 rounded text-xs font-semibold border transition-all ${
                                        selected === i
                                            ? scoreColorSelected(i)
                                            : "bg-[#0F0F0F] border-[#2E2E2E] text-[#9CA3AF] hover:border-[#4B5563]"
                                    }`}
                                >
                                    {i}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Comentário */}
                    {selected !== null && (
                        <div className="animate-[fade-in_0.2s_ease-out]">
                            <label
                                htmlFor="nps-comment"
                                className="block text-xs text-[#9CA3AF] mb-1.5"
                            >
                                O que motivou sua nota?{" "}
                                <span className="text-[#6B7280]">(opcional)</span>
                            </label>
                            <textarea
                                id="nps-comment"
                                value={comment}
                                onChange={(e) => setComment(e.target.value)}
                                placeholder="Conte mais sobre sua experiência..."
                                rows={2}
                                className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 resize-none transition-colors"
                            />
                        </div>
                    )}

                    {/* Ações */}
                    <div className="flex items-center justify-between gap-3">
                        <button
                            type="button"
                            onClick={dismiss}
                            className="text-xs text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
                        >
                            Agora não
                        </button>
                        <button
                            type="button"
                            onClick={submit}
                            disabled={selected === null || loading}
                            className="flex items-center gap-1.5 bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors"
                        >
                            <Send size={12} aria-hidden="true" />
                            Enviar
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
