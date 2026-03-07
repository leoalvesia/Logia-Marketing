import { NavLink, useNavigate } from "react-router-dom";
import {
    LayoutDashboard,
    Zap,
    BookOpen,
    Calendar,
    Settings,
    Circle,
    LogOut,
} from "lucide-react";
import { useAuthStore } from "@/stores/authStore";
import { usePipelineStore } from "@/stores/pipelineStore";

const ACTIVE_PIPELINE_STATES = new Set([
    "RESEARCHING",
    "ORCHESTRATING",
    "AWAITING_SELECTION",
    "GENERATING_COPY",
    "COPY_REVIEW",
    "GENERATING_ART",
    "ART_REVIEW",
    "PUBLISHING",
]);

const NAV_ITEMS = [
    { to: "/", icon: LayoutDashboard, label: "Dashboard" },
    { to: "/pipeline", icon: Zap, label: "Pipeline", cta: true },
    { to: "/library", icon: BookOpen, label: "Biblioteca" },
    { to: "/calendar", icon: Calendar, label: "Calendário" },
    { to: "/settings", icon: Settings, label: "Configurações" },
];

// Status dot color mapping
const DOT = {
    ok: "bg-emerald-500",
    error: "bg-red-500",
    unknown: "bg-zinc-600",
};

export default function Sidebar() {
    const { user, logout } = useAuthStore();
    const navigate = useNavigate();
    const pipelineState = usePipelineStore((s) => s.pipelineState);
    const pipelineActive = ACTIVE_PIPELINE_STATES.has(pipelineState);

    // Mock service status — replace with real health check later
    const services = [
        { label: "API", status: "ok" },
        { label: "Redis", status: "ok" },
        { label: "Celery", status: "unknown" },
    ];

    function handleLogout() {
        logout();
        navigate("/login");
    }

    return (
        <aside className="hidden md:flex flex-col w-56 shrink-0 h-screen bg-[#1A1A1A] border-r border-[#2E2E2E]">
            {/* ── Logo ────────────────────────────────────────────── */}
            <div className="flex items-center gap-2.5 px-5 py-5 border-b border-[#2E2E2E]">
                <div className="w-7 h-7 rounded-lg bg-[#6366F1] flex items-center justify-center shadow-[0_0_12px_rgba(99,102,241,0.4)]">
                    <span className="text-white font-bold text-sm">L</span>
                </div>
                <div>
                    <span className="text-[#F9FAFB] font-bold text-sm tracking-tight">Logia</span>
                    <span className="block text-[10px] text-[#6B7280] font-mono -mt-0.5">Marketing Platform</span>
                </div>
            </div>

            {/* ── Navigation ──────────────────────────────────────── */}
            <nav className="flex-1 overflow-y-auto py-3 px-3 space-y-0.5">
                {NAV_ITEMS.map(({ to, icon: Icon, label, cta }) => (
                    <NavLink
                        key={to}
                        to={to}
                        end={to === "/"}
                        className={({ isActive }) =>
                            [
                                "group flex items-center gap-2.5 px-3 py-2 rounded-md text-sm font-medium transition-all duration-150",
                                isActive
                                    ? "bg-[#6366F1] text-white shadow-[0_0_12px_rgba(99,102,241,0.25)]"
                                    : cta
                                        ? "text-[#818CF8] hover:bg-[#242424] hover:text-[#A5B4FC]"
                                        : "text-[#9CA3AF] hover:bg-[#242424] hover:text-[#F9FAFB]",
                            ].join(" ")
                        }
                    >
                        {({ isActive }) => (
                            <>
                                <Icon
                                    size={16}
                                    className={[
                                        "shrink-0 transition-colors",
                                        isActive ? "text-white" : cta ? "text-[#818CF8]" : "text-[#6B7280] group-hover:text-[#9CA3AF]",
                                    ].join(" ")}
                                />
                                <span className="flex-1">{label}</span>

                                {/* Pipeline active badge */}
                                {to === "/pipeline" && pipelineActive && !isActive && (
                                    <span className="relative flex h-2 w-2">
                                        <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-[#6366F1] opacity-75" />
                                        <span className="relative inline-flex rounded-full h-2 w-2 bg-[#818CF8]" />
                                    </span>
                                )}
                            </>
                        )}
                    </NavLink>
                ))}
            </nav>

            {/* ── Footer ──────────────────────────────────────────── */}
            <div className="px-4 py-4 border-t border-[#2E2E2E] space-y-3">
                {/* Service status */}
                <div className="space-y-1.5">
                    {services.map(({ label, status }) => (
                        <div key={label} className="flex items-center justify-between">
                            <span className="text-[11px] text-[#6B7280] font-mono">{label}</span>
                            <span className={`w-1.5 h-1.5 rounded-full ${DOT[status]}`} />
                        </div>
                    ))}
                </div>

                {/* Divider */}
                <div className="border-t border-[#2E2E2E]" />

                {/* User + logout */}
                <div className="flex items-center justify-between gap-2">
                    <div className="min-w-0">
                        <p className="text-xs font-medium text-[#F9FAFB] truncate">{user?.name ?? "Usuário"}</p>
                        <p className="text-[10px] text-[#6B7280] truncate">{user?.email ?? ""}</p>
                    </div>
                    <button
                        onClick={handleLogout}
                        title="Sair"
                        className="shrink-0 p-1.5 rounded-md text-[#6B7280] hover:text-[#EF4444] hover:bg-red-950/30 transition-colors"
                    >
                        <LogOut size={14} />
                    </button>
                </div>

                {/* Version */}
                <p className="text-[10px] font-mono text-[#4B5563]">v2.0 beta</p>
            </div>
        </aside>
    );
}
