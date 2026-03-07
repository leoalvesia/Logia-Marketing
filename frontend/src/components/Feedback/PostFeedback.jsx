/**
 * PostFeedback — avaliação pós-publicação com estrelas (1–5).
 *
 * Uso:
 *   <PostFeedback
 *     pipelineId="abc-123"
 *     onClose={() => setShowFeedback(false)}
 *   />
 *
 * Se rating ≤ 3 abre campo de texto para melhoria.
 * X fecha sem punir — experiência não intrusiva.
 */

import { useState } from "react";
import { X, Star } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function PostFeedback({ pipelineId, onClose }) {
    const token = useAuthStore((s) => s.token);
    const [hovered, setHovered] = useState(0);
    const [rating, setRating] = useState(0);
    const [comment, setComment] = useState("");
    const [submitted, setSubmitted] = useState(false);
    const [loading, setLoading] = useState(false);

    const needsComment = rating > 0 && rating <= 3;

    async function submit() {
        if (!rating) return;
        setLoading(true);
        try {
            await fetch(`${API_BASE}/feedback/post`, {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    Authorization: `Bearer ${token}`,
                },
                body: JSON.stringify({
                    pipeline_id: pipelineId,
                    rating,
                    comment: comment.trim() || null,
                }),
            });
        } catch {
            // Falha silenciosa
        }
        setSubmitted(true);
        setTimeout(onClose, 2000);
        setLoading(false);
    }

    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-label="Avaliação da publicação"
            className="fixed bottom-5 right-5 z-50 w-72 bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl shadow-[0_16px_48px_rgba(0,0,0,0.7)] animate-[slide-up_0.3s_ease-out]"
        >
            {submitted ? (
                <div className="p-5 text-center space-y-2">
                    <p className="text-2xl">✨</p>
                    <p className="text-sm font-semibold text-[#F9FAFB]">Valeu o feedback!</p>
                </div>
            ) : (
                <div className="p-5 space-y-4">
                    {/* Header */}
                    <div className="flex items-center justify-between">
                        <p className="text-sm font-semibold text-[#F9FAFB]">
                            Como foi essa publicação?
                        </p>
                        <button
                            onClick={onClose}
                            aria-label="Fechar avaliação"
                            className="text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
                        >
                            <X size={15} aria-hidden="true" />
                        </button>
                    </div>

                    {/* Estrelas */}
                    <div className="flex justify-center gap-2" role="group" aria-label="Selecionar nota">
                        {[1, 2, 3, 4, 5].map((star) => (
                            <button
                                key={star}
                                type="button"
                                onClick={() => setRating(star)}
                                onMouseEnter={() => setHovered(star)}
                                onMouseLeave={() => setHovered(0)}
                                aria-label={`${star} estrela${star > 1 ? "s" : ""}`}
                                aria-pressed={rating === star}
                                className="transition-transform hover:scale-110"
                            >
                                <Star
                                    size={28}
                                    className="transition-colors"
                                    fill={(hovered || rating) >= star ? "#F59E0B" : "none"}
                                    stroke={(hovered || rating) >= star ? "#F59E0B" : "#4B5563"}
                                    aria-hidden="true"
                                />
                            </button>
                        ))}
                    </div>

                    {/* Label de sentimento */}
                    {rating > 0 && (
                        <p className="text-center text-xs text-[#9CA3AF] animate-[fade-in_0.15s_ease-out]">
                            {rating <= 2 && "Que pena! Vamos melhorar 🙁"}
                            {rating === 3 && "Razoável. Podemos fazer melhor 😐"}
                            {rating === 4 && "Boa publicação! 😊"}
                            {rating === 5 && "Perfeito! Obrigado! 🎉"}
                        </p>
                    )}

                    {/* Campo de melhoria (≤ 3 estrelas) */}
                    {needsComment && (
                        <div className="animate-[fade-in_0.2s_ease-out]">
                            <label
                                htmlFor="post-comment"
                                className="block text-xs text-[#9CA3AF] mb-1.5"
                            >
                                O que podemos melhorar?
                            </label>
                            <textarea
                                id="post-comment"
                                value={comment}
                                onChange={(e) => setComment(e.target.value)}
                                placeholder="Conte o que aconteceu..."
                                rows={2}
                                className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] resize-none"
                            />
                        </div>
                    )}

                    {/* Enviar */}
                    {rating > 0 && (
                        <button
                            type="button"
                            onClick={submit}
                            disabled={loading}
                            className="w-full bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 text-white text-sm font-semibold py-2 rounded-lg transition-colors"
                        >
                            {loading ? "Enviando..." : "Enviar avaliação"}
                        </button>
                    )}
                </div>
            )}
        </div>
    );
}
