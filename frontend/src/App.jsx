import { lazy, Suspense } from "react";
import { Routes, Route, Navigate } from "react-router-dom";
import { PageSkeleton } from "@/components/ui/Skeleton";
import AppShell from "@/components/Layout/AppShell";
import ProtectedRoute from "@/components/Layout/ProtectedRoute";

// ── Lazy pages ─────────────────────────────────────────────────────────────────
const LoginPage = lazy(() => import("@/pages/LoginPage"));
const OnboardingPage = lazy(() => import("@/pages/Onboarding/index"));
const FeedbackDashboard = lazy(() => import("@/pages/Admin/FeedbackDashboard"));
const Dashboard = lazy(() => import("@/pages/Dashboard"));
const PipelinePage = lazy(() => import("@/pages/PipelinePage"));
const LibraryPage = lazy(() => import("@/pages/LibraryPage"));
const CalendarPage = lazy(() => import("@/pages/CalendarPage"));
const SettingsPage = lazy(() => import("@/pages/SettingsPage"));
const DesignSystemDemo = lazy(() => import("@/pages/DesignSystemDemo"));
const TermsPage = lazy(() => import("@/pages/Legal/TermsPage"));
const PrivacyPage = lazy(() => import("@/pages/Legal/PrivacyPage"));
const StatusPage = lazy(() => import("@/pages/StatusPage"));
const ProductionDashboard = lazy(() => import("@/pages/Admin/ProductionDashboard"));

function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
      <Routes>
        {/* ── Public ───────────────────────────────────────── */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/terms" element={<TermsPage />} />
        <Route path="/privacy" element={<PrivacyPage />} />
        <Route path="/status" element={<StatusPage />} />

        {/* ── Onboarding (protegido, sem AppShell) ─────────── */}
        <Route element={<ProtectedRoute />}>
          <Route path="onboarding" element={<OnboardingPage />} />
        </Route>

        {/* ── Protected (wrapped in AppShell) ──────────────── */}
        <Route element={<ProtectedRoute />}>
          <Route element={<AppShell />}>
            <Route index element={<Dashboard />} />
            <Route path="pipeline" element={<PipelinePage />} />
            <Route path="library" element={<LibraryPage />} />
            <Route path="calendar" element={<CalendarPage />} />
            <Route path="settings" element={<SettingsPage />} />
            <Route path="design-system" element={<DesignSystemDemo />} />
          </Route>
        </Route>

        {/* ── Admin (key-based auth, no ProtectedRoute) ─────── */}
        <Route path="admin" element={<ProductionDashboard />} />
        <Route path="admin/feedback" element={<FeedbackDashboard />} />

        {/* ── Fallback ──────────────────────────────────────── */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Suspense>
  );
}

export default App;
