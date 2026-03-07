import { useState } from "react";
import { Link } from "react-router-dom";
import { Zap } from "lucide-react";

export default function OnboardingWelcome({ onNext, userName }) {
    const [accepted, setAccepted] = useState(false);

    return (
        <div className="flex flex-col items-center text-center space-y-8 animate-[fade-in_0.4s_ease-out]">
            {/* Logo animado */}
            <div className="relative">
                <div className="w-20 h-20 rounded-2xl bg-[#6366F1] flex items-center justify-center shadow-[0_0_48px_rgba(99,102,241,0.5)]">
                    <Zap size={36} className="text-white" aria-hidden="true" />
                </div>
                {/* Pulso */}
                <div className="absolute inset-0 rounded-2xl bg-[#6366F1] animate-ping opacity-20" />
            </div>

            <div className="space-y-3">
                <h1 className="text-3xl font-bold text-[#F9FAFB]">
                    Bem-vindo, {userName}!
                </h1>
                <p className="text-[#9CA3AF] text-lg max-w-sm">
                    Vamos configurar sua plataforma em{" "}
                    <span className="text-[#10B981] font-semibold">3 minutos</span>
                </p>
            </div>

            {/* O que vem por aí */}
            <div className="w-full max-w-sm bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl p-5 text-left space-y-3">
                {[
                    { step: "1", label: "Seu nicho e tom de voz" },
                    { step: "2", label: "Perfis para monitorar" },
                    { step: "3", label: "Seu primeiro post" },
                ].map(({ step, label }) => (
                    <div key={step} className="flex items-center gap-3">
                        <div className="w-7 h-7 rounded-full bg-[#6366F1]/20 border border-[#6366F1]/40 flex items-center justify-center flex-shrink-0">
                            <span className="text-[#6366F1] text-xs font-bold">{step}</span>
                        </div>
                        <span className="text-[#D1D5DB] text-sm">{label}</span>
                    </div>
                ))}
            </div>

            {/* Aceite de termos (obrigatório — LGPD) */}
            <label className="flex items-start gap-3 w-full max-w-sm text-left cursor-pointer">
                <input
                    type="checkbox"
                    checked={accepted}
                    onChange={(e) => setAccepted(e.target.checked)}
                    className="mt-0.5 w-4 h-4 rounded border-[#4B5563] bg-[#0F0F0F] accent-[#6366F1] cursor-pointer flex-shrink-0"
                    aria-required="true"
                />
                <span className="text-xs text-[#9CA3AF] leading-relaxed">
                    Li e concordo com os{" "}
                    <Link
                        to="/terms"
                        target="_blank"
                        className="text-[#6366F1] hover:underline"
                        onClick={(e) => e.stopPropagation()}
                    >
                        Termos de Uso
                    </Link>{" "}
                    e a{" "}
                    <Link
                        to="/privacy"
                        target="_blank"
                        className="text-[#6366F1] hover:underline"
                        onClick={(e) => e.stopPropagation()}
                    >
                        Política de Privacidade
                    </Link>{" "}
                    da Logia, incluindo o tratamento dos meus dados conforme a LGPD.
                </span>
            </label>

            <button
                onClick={onNext}
                disabled={!accepted}
                className="w-full max-w-sm bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-40 disabled:cursor-not-allowed text-white font-semibold py-3 rounded-xl transition-colors shadow-[0_0_24px_rgba(99,102,241,0.35)] hover:shadow-[0_0_32px_rgba(99,102,241,0.5)]"
            >
                Começar configuração
            </button>
        </div>
    );
}
