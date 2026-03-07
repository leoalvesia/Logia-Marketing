import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import * as Sentry from "@sentry/react";
import { ToastProvider } from "@/components/ui/Toast";
import App from "./App";
import "./index.css";

// ── Sentry — inicializar antes de renderizar ────────────────────────────────
if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    environment: import.meta.env.VITE_ENVIRONMENT || "development",
    release: import.meta.env.VITE_BUILD_SHA
      ? `logia@${import.meta.env.VITE_BUILD_SHA}`
      : undefined,
    integrations: [
      Sentry.browserTracingIntegration(),
      // Replay: grava sessão apenas em erros (sem gravar em produção normal)
      Sentry.replayIntegration({
        maskAllText: true,    // não gravar texto dos usuários (LGPD)
        blockAllMedia: true,
      }),
    ],
    tracesSampleRate: 0.1,
    replaysSessionSampleRate: 0.0,  // 0% sessões normais
    replaysOnErrorSampleRate: 1.0,  // 100% sessões com erro
    beforeSend(event) {
      // Não enviar erros em ambiente dev local
      if (import.meta.env.DEV) return null;
      return event;
    },
  });
}

createRoot(document.getElementById("root")).render(
  <StrictMode>
    <Sentry.ErrorBoundary
      fallback={
        <div
          role="alert"
          style={{
            display: "flex",
            flexDirection: "column",
            alignItems: "center",
            justifyContent: "center",
            height: "100vh",
            gap: "1rem",
            background: "#0F0F0F",
            color: "#F9FAFB",
            fontFamily: "Inter, sans-serif",
          }}
        >
          <h1 style={{ fontSize: "1.25rem", fontWeight: 600 }}>
            Algo deu errado
          </h1>
          <p style={{ color: "#9CA3AF", fontSize: "0.875rem" }}>
            O erro foi registrado automaticamente.
          </p>
          <button
            onClick={() => window.location.reload()}
            style={{
              padding: "0.5rem 1.25rem",
              background: "#4F46E5",
              color: "#fff",
              border: "none",
              borderRadius: "0.375rem",
              cursor: "pointer",
              fontSize: "0.875rem",
            }}
          >
            Recarregar
          </button>
        </div>
      }
    >
      <BrowserRouter>
        <ToastProvider>
          <App />
        </ToastProvider>
      </BrowserRouter>
    </Sentry.ErrorBoundary>
  </StrictMode>
);
