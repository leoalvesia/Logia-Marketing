/**
 * BugReport — botão flutuante "?" + modal de bug report.
 *
 * Captura:
 *   - Descrição (obrigatório, min 10 chars)
 *   - Screenshot via html2canvas (opcional, com aviso de privacidade)
 *   - URL atual e userAgent (automático)
 *
 * POST /feedback/bug → confirmação visual.
 */

import { useState, useRef } from "react";
import { HelpCircle, X, Camera, Loader2, CheckCircle2 } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function BugReport() {
    const token = useAuthStore((s) => s.token);
    const [open, setOpen] = useState(false);
    const [description, setDescription] = useState("");
    const [screenshot, setScreenshot] = useState(null); // base64 string
    const [captureLoading, setCaptureLoading] = useState(false);
    const [loading, setLoading] = useState(false);
    const [submitted, setSubmitted] = useState(false);
    const [error, setError] = useState("");
    const modalRef = useRef(null);

    function resetState() {
        setDescription("");
        setScreenshot(null);
        setSubmitted(false);
        setError("");
    }

    function close() {
        setOpen(false);
        setTimeout(resetState, 300);
    }

    async function captureScreenshot() {
        setCaptureLoading(true);
        try {
            // Dynamic import — não falha se html2canvas não estiver instalado
            const html2canvas = (await import("html2canvas")).default;
            const canvas = await html2canvas(document.body, {
                scale: 0.5,         // reduz tamanho do base64
                useCORS: true,
                logging: false,
                ignoreElements: (el) => el === modalRef.current,
            });
            setScreenshot(canvas.toDataURL("image/jpeg", 0.7));
        } catch {
            setError("html2canvas não disponível — instale com: npm install html2canvas");
        }
        setCaptureLoading(false);
    }

    async function submit() {
        if (description.trim().length < 10) {
            setError("Descreva o problema em pelo menos 10 caracteres.");
            return;
        }
        setError("");
        setLoading(true);
        try {
            const resp = await fetch(`${API_BASE}/feedback/bug`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    description: description.trim(),
                    url: window.location.href,
                    user_agent: navigator.userAgent,
                    screenshot_b64: screenshot
                        ? screenshot.replace(/^data:image\/[^;]+;base64,/, "")
                        : null,
                }),
            });
            if (!resp.ok) throw new Error("Falha ao enviar");
            setSubmitted(true);
            setTimeout(close, 3000);
        } catch {
            setError("Falha ao enviar. Tente novamente.");
        }
        setLoading(false);
    }

    return (
        <>
            {/* Botão flutuante */}
            <button
                type="button"
                onClick={() => { setOpen(true); resetState(); }}
                aria-label="Reportar problema"
                title="Reportar problema"
                className="fixed bottom-5 left-5 z-40 w-10 h-10 rounded-full bg-[#1A1A1A] border border-[#2E2E2E] text-[#9CA3AF] hover:text-[#F9FAFB] hover:border-[#4B5563] flex items-center justify-center shadow-lg transition-all hover:scale-110"
            >
                <HelpCircle size={18} aria-hidden="true" />
            </button>

            {/* Modal */}
            {open && (
                <div
                    className="fixed inset-0 z-50 flex items-end sm:items-center justify-center sm:justify-start p-4 sm:p-5 sm:pb-5"
                    role="dialog"
                    aria-modal="true"
                    aria-label="Reportar problema"
                >
                    {/* Overlay */}
                    <div
                        className="absolute inset-0 bg-black/60 backdrop-blur-sm"
                        onClick={close}
                        aria-hidden="true"
                    />

                    <div
                        ref={modalRef}
                        className="relative w-full sm:w-96 sm:ml-16 bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl shadow-[0_24px_64px_rgba(0,0,0,0.8)] animate-[slide-up_0.25s_ease-out]"
                    >
                        {submitted ? (
                            <div className="p-6 text-center space-y-3">
                                <CheckCircle2
                                    size={40}
                                    className="text-[#10B981] mx-auto"
                                    aria-hidden="true"
                                />
                                <p className="text-sm font-semibold text-[#F9FAFB]">
                                    Recebemos!
                                </p>
                                <p className="text-xs text-[#9CA3AF]">
                                    Investigaremos em breve. Obrigado por ajudar a melhorar a Logia.
                                </p>
                            </div>
                        ) : (
                            <div className="p-5 space-y-4">
                                {/* Header */}
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-2">
                                        <HelpCircle size={16} className="text-[#6366F1]" aria-hidden="true" />
                                        <h2 className="text-sm font-semibold text-[#F9FAFB]">
                                            Reportar problema
                                        </h2>
                                    </div>
                                    <button
                                        onClick={close}
                                        aria-label="Fechar"
                                        className="text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
                                    >
                                        <X size={15} aria-hidden="true" />
                                    </button>
                                </div>

                                {/* Descrição */}
                                <div className="space-y-1.5">
                                    <label
                                        htmlFor="bug-description"
                                        className="block text-xs font-medium text-[#9CA3AF]"
                                    >
                                        O que aconteceu?{" "}
                                        <span className="text-red-400">*</span>
                                    </label>
                                    <textarea
                                        id="bug-description"
                                        value={description}
                                        onChange={(e) => setDescription(e.target.value)}
                                        placeholder="Descreva o problema em detalhes: o que você tentou fazer, o que aconteceu e o que esperava acontecer."
                                        rows={4}
                                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 resize-none transition-colors"
                                    />
                                    <p className="text-[10px] text-[#6B7280]">
                                        URL e navegador são capturados automaticamente.
                                    </p>
                                </div>

                                {/* Screenshot */}
                                <div className="space-y-1.5">
                                    {screenshot ? (
                                        <div className="relative">
                                            <img
                                                src={screenshot}
                                                alt="Screenshot capturada"
                                                className="w-full rounded-lg border border-[#2E2E2E] opacity-90"
                                            />
                                            <button
                                                type="button"
                                                onClick={() => setScreenshot(null)}
                                                aria-label="Remover screenshot"
                                                className="absolute top-1.5 right-1.5 w-6 h-6 bg-[#0F0F0F]/80 rounded-full flex items-center justify-center text-[#9CA3AF] hover:text-white"
                                            >
                                                <X size={12} aria-hidden="true" />
                                            </button>
                                        </div>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={captureScreenshot}
                                            disabled={captureLoading}
                                            className="flex items-center gap-2 text-xs text-[#9CA3AF] hover:text-[#F9FAFB] border border-dashed border-[#2E2E2E] hover:border-[#4B5563] rounded-lg px-3 py-2 w-full transition-colors"
                                        >
                                            {captureLoading ? (
                                                <Loader2 size={13} className="animate-spin" aria-hidden="true" />
                                            ) : (
                                                <Camera size={13} aria-hidden="true" />
                                            )}
                                            {captureLoading ? "Capturando..." : "Adicionar screenshot (opcional)"}
                                        </button>
                                    )}
                                    {!screenshot && (
                                        <p className="text-[9px] text-[#4B5563]">
                                            A screenshot captura sua tela atual. Informações sensíveis
                                            visíveis serão incluídas — você pode revisar antes de enviar.
                                        </p>
                                    )}
                                </div>

                                {/* Erro */}
                                {error && (
                                    <p className="text-xs text-red-400 bg-red-950/30 border border-red-900/40 rounded-lg px-3 py-2">
                                        {error}
                                    </p>
                                )}

                                {/* Submit */}
                                <button
                                    type="button"
                                    onClick={submit}
                                    disabled={loading || description.trim().length < 10}
                                    className="w-full bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 text-white text-sm font-semibold py-2.5 rounded-xl transition-colors"
                                >
                                    {loading ? "Enviando..." : "Enviar relatório"}
                                </button>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </>
    );
}
