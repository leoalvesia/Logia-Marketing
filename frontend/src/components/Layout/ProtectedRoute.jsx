import { Navigate, Outlet, useLocation } from "react-router-dom";
import { useAuthStore } from "@/stores/authStore";

export default function ProtectedRoute() {
    const token = useAuthStore((s) => s.token);
    const user = useAuthStore((s) => s.user);
    const location = useLocation();

    if (!token) return <Navigate to="/login" replace />;

    // Redirecionar para onboarding se ainda não completou (exceto se já está lá)
    if (user && !user.onboarding_completed && location.pathname !== "/onboarding") {
        return <Navigate to="/onboarding" replace />;
    }

    return <Outlet />;
}
