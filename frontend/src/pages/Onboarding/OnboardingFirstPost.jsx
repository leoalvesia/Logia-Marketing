import { useNavigate } from "react-router-dom";
import { Zap, LayoutDashboard, CheckCircle2 } from "lucide-react";
import { useAuthStore } from "@/stores/authStore";

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function OnboardingFirstPost({ onBack, isLoading }) {
    const navigate = useNavigate();
    const token = useAuthStore((s) => s.token);
    const completeOnboarding = useAuthStore((s) => s.completeOnboarding);

    async function finish(redirectTo) {
        try {
            await fetch(`${API_BASE}/auth/me/onboarding`, {
                method: "PATCH",
                headers: { Authorization: `Bearer ${token}` },
            });
        } catch {
            // Falha silenciosa — onboarding marca local de qualquer forma
        }
        completeOnboarding();
        navigate(redirectTo, { replace: true });
    }

    return (
        <div className="flex flex-col items-center text-center space-y-8 animate-[fade-in_0.3s_ease-out]">
            {/* Ícone de conclusão */}
            <div className="w-20 h-20 rounded-full bg-[#10B981]/20 border border-[#10B981]/40 flex items-center justify-center">
                <CheckCircle2 size={40} className="text-[#10B981]" aria-hidden="true" />
            </div>

            <div className="space-y-3">
                <h2 className="text-2xl font-bold text-[#F9FAFB]">Tudo pronto!</h2>
                <p className="text-[#9CA3AF] max-w-sm">
                    Sua plataforma está configurada. O que você quer fazer agora?
                </p>
            </div>

            {/* Opções */}
            <div className="w-full space-y-3">
                <button
                    type="button"
                    onClick={() => finish("/pipeline")}
                    disabled={isLoading}
                    className="w-full flex items-center gap-4 bg-[#4F46E5] hover:bg-[#4338CA] text-white px-5 py-4 rounded-xl transition-colors shadow-[0_0_24px_rgba(99,102,241,0.3)] text-left"
                >
                    <div className="w-10 h-10 bg-white/10 rounded-lg flex items-center justify-center flex-shrink-0">
                        <Zap size={20} aria-hidden="true" />
                    </div>
                    <div>
                        <p className="font-semibold text-sm">Criar meu primeiro post</p>
                        <p className="text-white/70 text-xs mt-0.5">
                            Pesquisa → copy → arte em poucos minutos
                        </p>
                    </div>
                </button>

                <button
                    type="button"
                    onClick={() => finish("/")}
                    disabled={isLoading}
                    className="w-full flex items-center gap-4 bg-[#1A1A1A] hover:bg-[#242424] border border-[#2E2E2E] text-[#F9FAFB] px-5 py-4 rounded-xl transition-colors text-left"
                >
                    <div className="w-10 h-10 bg-[#2E2E2E] rounded-lg flex items-center justify-center flex-shrink-0">
                        <LayoutDashboard size={20} className="text-[#9CA3AF]" aria-hidden="true" />
                    </div>
                    <div>
                        <p className="font-semibold text-sm">Explorar o dashboard</p>
                        <p className="text-[#9CA3AF] text-xs mt-0.5">
                            Conheça a plataforma antes de começar
                        </p>
                    </div>
                </button>
            </div>

            <button
                type="button"
                onClick={onBack}
                className="text-xs text-[#6B7280] hover:text-[#9CA3AF] transition-colors"
            >
                Voltar
            </button>
        </div>
    );
}
