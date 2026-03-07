import { NavLink } from "react-router-dom";
import { LayoutDashboard, Zap, BookOpen, Calendar, Settings } from "lucide-react";
import { usePipelineStore } from "@/stores/pipelineStore";

const ACTIVE_PIPELINE_STATES = new Set([
    "RESEARCHING", "ORCHESTRATING", "AWAITING_SELECTION",
    "GENERATING_COPY", "COPY_REVIEW", "GENERATING_ART",
    "ART_REVIEW", "PUBLISHING",
]);

const NAV_ITEMS = [
    { to: "/", icon: LayoutDashboard, label: "Home" },
    { to: "/pipeline", icon: Zap, label: "Pipeline" },
    { to: "/library", icon: BookOpen, label: "Biblioteca" },
    { to: "/calendar", icon: Calendar, label: "Calendário" },
    { to: "/settings", icon: Settings, label: "Config" },
];

export default function BottomNav() {
    const pipelineState = usePipelineStore((s) => s.pipelineState);
    const pipelineActive = ACTIVE_PIPELINE_STATES.has(pipelineState);

    return (
        <nav className="md:hidden fixed bottom-0 inset-x-0 z-50 bg-[#1A1A1A] border-t border-[#2E2E2E] flex items-stretch">
            {NAV_ITEMS.map(({ to, icon: Icon, label }) => (
                <NavLink
                    key={to}
                    to={to}
                    end={to === "/"}
                    className={({ isActive }) =>
                        [
                            "flex-1 flex flex-col items-center justify-center gap-0.5 py-2 text-[10px] font-medium transition-colors relative",
                            isActive ? "text-[#6366F1]" : "text-[#6B7280]",
                        ].join(" ")
                    }
                >
                    {({ isActive }) => (
                        <>
                            {/* Active indicator bar */}
                            {isActive && (
                                <span className="absolute top-0 inset-x-3 h-0.5 rounded-full bg-[#6366F1]" />
                            )}

                            <div className="relative">
                                <Icon size={20} />
                                {/* Pipeline activity dot */}
                                {to === "/pipeline" && pipelineActive && !isActive && (
                                    <span className="absolute -top-0.5 -right-0.5 w-2 h-2 rounded-full bg-[#6366F1] border border-[#1A1A1A]">
                                        <span className="absolute inset-0 rounded-full bg-[#6366F1] animate-ping opacity-75" />
                                    </span>
                                )}
                            </div>

                            <span>{label}</span>
                        </>
                    )}
                </NavLink>
            ))}
        </nav>
    );
}
