import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";
import { Zap, AlertCircle } from "lucide-react";

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function LoginPage() {
    const navigate = useNavigate();
    const loginStore = useAuthStore((s) => s.login);

    const [tab, setTab] = useState("login"); // "login" | "register"

    // Login state
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");

    // Register state
    const [regName, setRegName] = useState("");
    const [regEmail, setRegEmail] = useState("");
    const [regPassword, setRegPassword] = useState("");
    const [inviteCode, setInviteCode] = useState("");

    const [error, setError] = useState("");
    const [loading, setLoading] = useState(false);

    async function handleLogin(e) {
        e.preventDefault();
        setError("");
        if (!email || !password) { setError("Preencha e-mail e senha."); return; }

        setLoading(true);
        try {
            const resp = await fetch(`${API_BASE}/auth/login`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ email, password }),
            });
            const data = await resp.json();
            if (!resp.ok) {
                setError(data.detail || "E-mail ou senha incorretos.");
                return;
            }
            loginStore(data.user, data.access_token);
            navigate(data.user.onboarding_completed ? "/" : "/onboarding", { replace: true });
        } catch {
            setError("Erro de conexão. Tente novamente.");
        } finally {
            setLoading(false);
        }
    }

    async function handleRegister(e) {
        e.preventDefault();
        setError("");
        if (!regName || !regEmail || !regPassword || !inviteCode) {
            setError("Preencha todos os campos.");
            return;
        }
        if (regPassword.length < 6) {
            setError("Senha deve ter pelo menos 6 caracteres.");
            return;
        }

        setLoading(true);
        try {
            const resp = await fetch(`${API_BASE}/auth/register`, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    name: regName,
                    email: regEmail,
                    password: regPassword,
                    invite_code: inviteCode.trim(),
                }),
            });
            const data = await resp.json();
            if (!resp.ok) {
                const msgs = {
                    404: "Código de convite inválido.",
                    410: "Código de convite expirado.",
                    409: "Código de convite já utilizado.",
                    400: data.detail || "E-mail já cadastrado.",
                };
                setError(msgs[resp.status] || data.detail || "Erro ao criar conta.");
                return;
            }
            loginStore(data.user, data.access_token);
            navigate("/onboarding", { replace: true });
        } catch {
            setError("Erro de conexão. Tente novamente.");
        } finally {
            setLoading(false);
        }
    }

    return (
        <main className="min-h-screen bg-[#0F0F0F] flex items-center justify-center p-4" aria-label="Autenticação">
            <div className="w-full max-w-sm space-y-8 animate-[fade-in_0.3s_ease-out]">

                {/* Logo */}
                <div className="text-center space-y-2">
                    <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl bg-[#6366F1] shadow-[0_0_24px_rgba(99,102,241,0.4)] mb-2">
                        <Zap size={24} className="text-white" aria-hidden="true" />
                    </div>
                    <h1 className="text-2xl font-bold text-[#F9FAFB]">Logia</h1>
                    <p className="text-sm text-[#9CA3AF]">Marketing Platform</p>
                </div>

                {/* Card */}
                <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl shadow-[0_8px_32px_rgba(0,0,0,0.6)] overflow-hidden">
                    {/* Tabs */}
                    <div className="flex border-b border-[#2E2E2E]" role="tablist">
                        {[
                            { id: "login", label: "Entrar" },
                            { id: "register", label: "Criar conta" },
                        ].map(({ id, label }) => (
                            <button
                                key={id}
                                role="tab"
                                aria-selected={tab === id}
                                onClick={() => { setTab(id); setError(""); }}
                                className={`flex-1 py-3 text-sm font-medium transition-colors ${
                                    tab === id
                                        ? "text-[#F9FAFB] border-b-2 border-[#6366F1] -mb-px"
                                        : "text-[#6B7280] hover:text-[#9CA3AF]"
                                }`}
                            >
                                {label}
                            </button>
                        ))}
                    </div>

                    <div className="p-6">
                        {tab === "login" ? (
                            <form onSubmit={handleLogin} className="space-y-4" noValidate>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-medium text-[#9CA3AF]" htmlFor="email">
                                        E-mail
                                    </label>
                                    <input
                                        id="email"
                                        type="email"
                                        autoComplete="email"
                                        value={email}
                                        onChange={(e) => setEmail(e.target.value)}
                                        placeholder="voce@empresa.com"
                                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-md px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-medium text-[#9CA3AF]" htmlFor="password">
                                        Senha
                                    </label>
                                    <input
                                        id="password"
                                        type="password"
                                        autoComplete="current-password"
                                        value={password}
                                        onChange={(e) => setPassword(e.target.value)}
                                        placeholder="••••••••"
                                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-md px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                                    />
                                </div>
                                {error && (
                                    <div className="flex items-center gap-2 text-xs text-red-400 bg-red-950/40 border border-red-900/50 rounded-md px-3 py-2">
                                        <AlertCircle size={13} aria-hidden="true" />
                                        {error}
                                    </div>
                                )}
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-60 text-white text-sm font-semibold py-2.5 rounded-md transition-colors shadow-[0_0_16px_rgba(99,102,241,0.3)] hover:shadow-[0_0_24px_rgba(99,102,241,0.4)] mt-2"
                                >
                                    {loading ? "Entrando..." : "Entrar"}
                                </button>
                            </form>
                        ) : (
                            <form onSubmit={handleRegister} className="space-y-4" noValidate>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-medium text-[#9CA3AF]" htmlFor="reg-name">
                                        Nome completo
                                    </label>
                                    <input
                                        id="reg-name"
                                        type="text"
                                        autoComplete="name"
                                        value={regName}
                                        onChange={(e) => setRegName(e.target.value)}
                                        placeholder="Seu nome"
                                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-md px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-medium text-[#9CA3AF]" htmlFor="reg-email">
                                        E-mail
                                    </label>
                                    <input
                                        id="reg-email"
                                        type="email"
                                        autoComplete="email"
                                        value={regEmail}
                                        onChange={(e) => setRegEmail(e.target.value)}
                                        placeholder="voce@empresa.com"
                                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-md px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-medium text-[#9CA3AF]" htmlFor="reg-password">
                                        Senha
                                    </label>
                                    <input
                                        id="reg-password"
                                        type="password"
                                        autoComplete="new-password"
                                        value={regPassword}
                                        onChange={(e) => setRegPassword(e.target.value)}
                                        placeholder="Mínimo 6 caracteres"
                                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-md px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                                    />
                                </div>
                                <div className="space-y-1.5">
                                    <label className="block text-xs font-medium text-[#9CA3AF]" htmlFor="invite-code">
                                        Código de convite
                                    </label>
                                    <input
                                        id="invite-code"
                                        type="text"
                                        value={inviteCode}
                                        onChange={(e) => setInviteCode(e.target.value)}
                                        placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                                        className="w-full bg-[#0F0F0F] border border-[#2E2E2E] rounded-md px-3 py-2 text-sm text-[#F9FAFB] placeholder:text-[#4B5563] font-mono focus:outline-none focus:border-[#6366F1] focus:ring-1 focus:ring-[#6366F1]/40 transition-colors"
                                    />
                                    <p className="text-[10px] text-[#6B7280]">
                                        Recebeu um convite por email? Cole o código aqui.
                                    </p>
                                </div>
                                {error && (
                                    <div className="flex items-center gap-2 text-xs text-red-400 bg-red-950/40 border border-red-900/50 rounded-md px-3 py-2">
                                        <AlertCircle size={13} aria-hidden="true" />
                                        {error}
                                    </div>
                                )}
                                <button
                                    type="submit"
                                    disabled={loading}
                                    className="w-full bg-[#4F46E5] hover:bg-[#4338CA] disabled:opacity-60 text-white text-sm font-semibold py-2.5 rounded-md transition-colors shadow-[0_0_16px_rgba(99,102,241,0.3)] hover:shadow-[0_0_24px_rgba(99,102,241,0.4)] mt-2"
                                >
                                    {loading ? "Criando conta..." : "Criar conta"}
                                </button>
                            </form>
                        )}
                    </div>
                </div>

                <p className="text-center text-[10px] text-[#9CA3AF] font-mono">
                    v2.0 beta · Logia Marketing Platform
                </p>
            </div>
        </main>
    );
}
