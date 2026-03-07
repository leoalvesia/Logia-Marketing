import { useState } from "react";
import { Zap } from "lucide-react";
import OnboardingWelcome from "./OnboardingWelcome";
import OnboardingNicho from "./OnboardingNicho";
import OnboardingProfiles from "./OnboardingProfiles";
import OnboardingFirstPost from "./OnboardingFirstPost";
import { useAuthStore } from "@/stores/authStore";

const STEPS = ["Bem-vindo", "Negócio", "Perfis", "Primeiro post"];

export default function OnboardingPage() {
    const user = useAuthStore((s) => s.user);
    const [step, setStep] = useState(0);
    const [data, setData] = useState({
        nicho: "",
        persona: "",
        tom: "",
        profiles: [],
    });

    function handleNichoChange(values) {
        setData((prev) => ({ ...prev, ...values }));
    }

    function handleProfilesNext({ profiles }) {
        setData((prev) => ({ ...prev, profiles }));
        setStep(3);
    }

    const progressPercent = Math.round((step / (STEPS.length - 1)) * 100);

    return (
        <main
            className="min-h-screen bg-[#0F0F0F] flex flex-col items-center justify-start p-4 pt-8"
            aria-label="Onboarding"
        >
            <div className="w-full max-w-md space-y-6">
                {/* Header */}
                <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                        <div className="w-7 h-7 rounded-lg bg-[#6366F1] flex items-center justify-center">
                            <Zap size={14} className="text-white" aria-hidden="true" />
                        </div>
                        <span className="text-sm font-semibold text-[#F9FAFB]">Logia</span>
                    </div>
                    <span className="text-xs text-[#6B7280]">
                        Passo {step + 1} de {STEPS.length}
                    </span>
                </div>

                {/* Barra de progresso */}
                <div
                    role="progressbar"
                    aria-valuenow={progressPercent}
                    aria-valuemin={0}
                    aria-valuemax={100}
                    aria-label={`Progresso do onboarding: ${progressPercent}%`}
                    className="w-full h-1.5 bg-[#2E2E2E] rounded-full overflow-hidden"
                >
                    <div
                        className="h-full bg-gradient-to-r from-[#6366F1] to-[#10B981] transition-all duration-500 ease-out rounded-full"
                        style={{ width: `${progressPercent}%` }}
                    />
                </div>

                {/* Indicadores de passo */}
                <div className="flex justify-between">
                    {STEPS.map((label, idx) => (
                        <div key={label} className="flex flex-col items-center gap-1">
                            <div
                                className={`w-2 h-2 rounded-full transition-colors ${
                                    idx <= step ? "bg-[#6366F1]" : "bg-[#2E2E2E]"
                                }`}
                            />
                            <span
                                className={`text-[10px] hidden sm:block transition-colors ${
                                    idx === step ? "text-[#9CA3AF]" : "text-[#4B5563]"
                                }`}
                            >
                                {label}
                            </span>
                        </div>
                    ))}
                </div>

                {/* Conteúdo do passo */}
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl p-6 shadow-[0_8px_32px_rgba(0,0,0,0.6)]">
                    {step === 0 && (
                        <OnboardingWelcome
                            userName={user?.name?.split(" ")[0] || ""}
                            onNext={() => setStep(1)}
                        />
                    )}
                    {step === 1 && (
                        <OnboardingNicho
                            data={data}
                            onChange={handleNichoChange}
                            onNext={() => setStep(2)}
                            onBack={() => setStep(0)}
                        />
                    )}
                    {step === 2 && (
                        <OnboardingProfiles
                            data={data}
                            onNext={handleProfilesNext}
                            onBack={() => setStep(1)}
                        />
                    )}
                    {step === 3 && (
                        <OnboardingFirstPost
                            onBack={() => setStep(2)}
                        />
                    )}
                </div>
            </div>
        </main>
    );
}
