import { Link, Outlet, useLocation, useNavigate } from "react-router-dom";
import { Plus, Zap } from "lucide-react";
import Sidebar from "./Sidebar";
import BottomNav from "./BottomNav";
import NpsWidget from "@/components/Feedback/NpsWidget";
import BugReport from "@/components/Feedback/BugReport";
import { useAuthStore } from "@/stores/authStore";

const ROUTE_LABELS = {
    "/": "Dashboard",
    "/pipeline": "Pipeline",
    "/library": "Biblioteca",
    "/calendar": "Calendário",
    "/settings": "Configurações",
    "/design-system": "Design System",
};

export default function AppShell() {
    const { pathname } = useLocation();
    const navigate = useNavigate();
    const user = useAuthStore((s) => s.user);

    const pageLabel = ROUTE_LABELS[pathname] ?? "Logia";

    return (
        <>
        <div className="flex h-screen overflow-hidden bg-[#0F0F0F]">
            {/* ── Desktop Sidebar ────────────────────────────────── */}
            <Sidebar />

            {/* ── Main area ─────────────────────────────────────── */}
            <div className="flex-1 flex flex-col min-w-0 overflow-hidden">

                {/* ── Header ──────────────────────────────────────── */}
                <header className="shrink-0 h-14 flex items-center justify-between gap-4 px-5 border-b border-[#2E2E2E] bg-[#0F0F0F]/80 backdrop-blur-sm">
                    {/* Left: logo (mobile only) + breadcrumb */}
                    <div className="flex items-center gap-3">
                        {/* Logo — visible only on mobile where sidebar is hidden */}
                        <div className="flex md:hidden items-center gap-2">
                            <div className="w-6 h-6 rounded-md bg-[#6366F1] flex items-center justify-center">
                                <span className="text-white font-bold text-xs">L</span>
                            </div>
                            <span className="font-bold text-[#F9FAFB] text-sm">Logia</span>
                        </div>

                        {/* Breadcrumb */}
                        <span className="text-sm font-semibold text-[#F9FAFB]">{pageLabel}</span>
                    </div>

                    {/* Right: user greeting + CTA */}
                    <div className="flex items-center gap-3">
                        {/* User name — hidden on very small screens */}
                        <span className="hidden sm:block text-xs text-[#6B7280]">
                            Olá, <span className="text-[#9CA3AF] font-medium">{user?.name?.split(" ")[0] ?? "usuário"}</span>
                        </span>

                        {/* "Novo Post" CTA */}
                        <button
                            onClick={() => navigate("/pipeline")}
                            className="flex items-center gap-1.5 bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs font-semibold px-3 py-1.5 rounded-md transition-colors shadow-[0_0_12px_rgba(99,102,241,0.3)] hover:shadow-[0_0_20px_rgba(99,102,241,0.4)]"
                        >
                            <Plus size={14} />
                            <span className="hidden sm:inline">Novo Post</span>
                            <span className="sm:hidden">
                                <Zap size={14} />
                            </span>
                        </button>
                    </div>
                </header>

                {/* ── Page content ────────────────────────────────── */}
                <main className="flex-1 overflow-y-auto pb-16 md:pb-0">
                    <Outlet />
                </main>

                {/* ── Footer legal (desktop only) ──────────────────── */}
                <footer className="hidden md:flex shrink-0 items-center justify-end gap-4 px-5 py-2 border-t border-[#2E2E2E] bg-[#0F0F0F]/80">
                    <Link to="/privacy" className="text-[10px] text-[#4B5563] hover:text-[#6B7280] transition-colors">
                        Política de Privacidade
                    </Link>
                    <Link to="/terms" className="text-[10px] text-[#4B5563] hover:text-[#6B7280] transition-colors">
                        Termos de Uso
                    </Link>
                    <Link to="/settings" className="text-[10px] text-[#4B5563] hover:text-[#6B7280] transition-colors">
                        Excluir conta
                    </Link>
                </footer>
            </div>

            {/* ── Mobile Bottom Nav ──────────────────────────────── */}
            <BottomNav />
        </div>

        {/* ── Feedback global ────────────────────────────────── */}
        <NpsWidget />
        <BugReport />
        </>
    );
}
