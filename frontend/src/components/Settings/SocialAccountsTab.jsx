import { useState } from "react";
import { useSettingsStore } from "@/stores/settingsStore";
import { useToast } from "@/components/ui/Toast";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import { ExternalLink, Unlink, AlertTriangle, CheckCircle2, Clock } from "lucide-react";

const PLATFORM_DOCS = {
    instagram: "https://developers.facebook.com/docs/instagram-api",
    linkedin: "https://learn.microsoft.com/linkedin/marketing/integrations/self-serve/oauth",
    twitter: "https://developer.twitter.com/en/portal/dashboard",
    youtube: "https://console.cloud.google.com/apis",
    email: null, // configured via SMTP form
};

function daysUntil(isoStr) {
    if (!isoStr) return null;
    const diff = new Date(isoStr) - new Date();
    return Math.floor(diff / (1000 * 60 * 60 * 24));
}

function TokenStatus({ account }) {
    const days = daysUntil(account.expiresAt);

    if (account.status === "disconnected") {
        return (
            <div className="flex items-center gap-1.5 text-xs text-[#6B7280]">
                <span className="w-2 h-2 rounded-full bg-[#6B7280]" aria-hidden="true" />
                Desconectado
            </div>
        );
    }

    if (days !== null && days < 7) {
        return (
            <div className="flex items-center gap-1.5 text-xs text-amber-400" role="alert">
                <Clock size={13} aria-hidden="true" />
                Expira em {days} dia{days !== 1 ? "s" : ""}
            </div>
        );
    }

    return (
        <div className="flex items-center gap-1.5 text-xs text-emerald-400">
            <CheckCircle2 size={13} aria-hidden="true" />
            Conectado {days !== null ? `· expira em ${days}d` : ""}
        </div>
    );
}

// ── Disconnect confirmation dialog ────────────────────────────────────────────
function DisconnectModal({ account, onConfirm, onCancel }) {
    return (
        <div
            role="dialog"
            aria-modal="true"
            aria-labelledby="disconnect-title"
            className="fixed inset-0 z-50 bg-black/60 backdrop-blur-sm flex items-center justify-center p-4"
            onKeyDown={(e) => { if (e.key === "Escape") onCancel(); }}
        >
            <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-2xl p-6 max-w-sm w-full shadow-2xl space-y-4">
                <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-red-950/60 border border-red-800/50 flex items-center justify-center">
                        <Unlink size={18} className="text-red-400" aria-hidden="true" />
                    </div>
                    <div>
                        <h3 id="disconnect-title" className="text-sm font-semibold text-[#F9FAFB]">
                            Desconectar {account.name}?
                        </h3>
                        <p className="text-xs text-[#9CA3AF]">O token de acesso será revogado.</p>
                    </div>
                </div>

                <div className="flex gap-3 justify-end">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 text-sm text-[#9CA3AF] hover:text-[#F9FAFB] border border-[#2E2E2E] rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                    >
                        Cancelar
                    </button>
                    <button
                        onClick={onConfirm}
                        className="px-4 py-2 text-sm font-semibold text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                    >
                        Desconectar
                    </button>
                </div>
            </div>
        </div>
    );
}

export default function SocialAccountsTab() {
    const socialAccounts = useSettingsStore((s) => s.socialAccounts);
    const connectAccount = useSettingsStore((s) => s.connectAccount);
    const disconnectAccount = useSettingsStore((s) => s.disconnectAccount);
    const toast = useToast();

    const [connecting, setConnecting] = useState(null);
    const [confirmDisconnect, setConfirmDisconnect] = useState(null);

    async function handleConnect(id) {
        setConnecting(id);
        // Simulate OAuth popup
        await new Promise((r) => setTimeout(r, 1800));
        connectAccount(id);
        setConnecting(null);
        toast({
            type: "success",
            title: "Conta conectada",
            description: `${socialAccounts.find((a) => a.id === id)?.name} autenticado com sucesso.`,
        });
    }

    function handleDisconnect(account) {
        setConfirmDisconnect(null);
        disconnectAccount(account.id);
        toast({
            type: "info",
            title: "Conta desconectada",
            description: `${account.name} foi desvinculado da plataforma.`,
        });
    }

    return (
        <section aria-label="Contas sociais conectadas">
            {/* Expiring soon alert */}
            {socialAccounts.some((a) => {
                const d = daysUntil(a.expiresAt);
                return d !== null && d < 7;
            }) && (
                    <div
                        role="alert"
                        aria-live="polite"
                        className="mb-4 flex items-center gap-2 bg-amber-950/40 border border-amber-800/50 rounded-xl px-4 py-3 text-xs text-amber-300"
                    >
                        <AlertTriangle size={14} aria-hidden="true" />
                        Alguns tokens expiram em breve — reconecte para não interromper a publicação.
                    </div>
                )}

            <div className="space-y-3">
                {socialAccounts.map((account) => {
                    const days = daysUntil(account.expiresAt);
                    const expiringSoon = days !== null && days < 7;

                    return (
                        <div
                            key={account.id}
                            className={[
                                "flex items-center justify-between gap-4 p-4 rounded-xl border transition-all",
                                expiringSoon ? "border-amber-800/50 bg-amber-950/20" : "border-[#2E2E2E] bg-[#1A1A1A]",
                            ].join(" ")}
                        >
                            {/* Left: channel + name + status */}
                            <div className="flex items-center gap-3">
                                <ChannelBadge channel={account.id} size="md" variant="icon" />
                                <div>
                                    <p className="text-sm font-medium text-[#F9FAFB]">{account.name}</p>
                                    <TokenStatus account={account} />
                                </div>
                            </div>

                            {/* Right: actions */}
                            <div className="flex items-center gap-2">
                                {PLATFORM_DOCS[account.id] && (
                                    <a
                                        href={PLATFORM_DOCS[account.id]}
                                        target="_blank"
                                        rel="noopener noreferrer"
                                        aria-label={`Documentação da API do ${account.name}`}
                                        className="w-7 h-7 flex items-center justify-center rounded-md text-[#6B7280] hover:text-[#9CA3AF] hover:bg-[#2E2E2E] transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                                    >
                                        <ExternalLink size={13} aria-hidden="true" />
                                    </a>
                                )}

                                {account.status === "connected" ? (
                                    <button
                                        onClick={() => setConfirmDisconnect(account)}
                                        aria-label={`Desconectar ${account.name}`}
                                        className="flex items-center gap-1.5 text-xs font-medium text-red-400 hover:text-red-300 border border-red-900/50 hover:border-red-700/50 px-3 py-1.5 rounded-lg transition-all focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                                    >
                                        <Unlink size={12} aria-hidden="true" /> Desconectar
                                    </button>
                                ) : (
                                    <button
                                        onClick={() => handleConnect(account.id)}
                                        disabled={connecting === account.id}
                                        aria-label={`Conectar ${account.name}`}
                                        aria-busy={connecting === account.id}
                                        className="flex items-center gap-1.5 text-xs font-semibold text-white bg-[#6366F1] hover:bg-[#4F46E5] disabled:opacity-60 px-3 py-1.5 rounded-lg transition-all shadow-[0_0_12px_rgba(99,102,241,0.25)] focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                                    >
                                        {connecting === account.id ? (
                                            <>
                                                <span className="w-3 h-3 rounded-full border-2 border-white/40 border-t-white animate-spin" aria-hidden="true" />
                                                Conectando...
                                            </>
                                        ) : "Conectar"}
                                    </button>
                                )}
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* Confirm disconnect dialog */}
            {confirmDisconnect && (
                <DisconnectModal
                    account={confirmDisconnect}
                    onConfirm={() => handleDisconnect(confirmDisconnect)}
                    onCancel={() => setConfirmDisconnect(null)}
                />
            )}
        </section>
    );
}
