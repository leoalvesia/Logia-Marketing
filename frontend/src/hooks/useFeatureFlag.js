/**
 * Hook para verificar se uma feature flag está ativa.
 *
 * Os flags são carregados de GET /api/features no startup da aplicação
 * e armazenados em localStorage (cache de 5 minutos).
 *
 * Uso:
 *   const isCarouselEnabled = useFeatureFlag("carousel_agent");
 */

import { useEffect, useState } from "react";

const CACHE_KEY = "logia:feature_flags";
const CACHE_TTL_MS = 5 * 60 * 1000; // 5 minutos

const API_BASE = import.meta.env.VITE_API_URL || "";

function getCached() {
    try {
        const raw = localStorage.getItem(CACHE_KEY);
        if (!raw) return null;
        const { flags, fetchedAt } = JSON.parse(raw);
        if (Date.now() - fetchedAt > CACHE_TTL_MS) return null;
        return flags;
    } catch {
        return null;
    }
}

function setCache(flags) {
    try {
        localStorage.setItem(CACHE_KEY, JSON.stringify({ flags, fetchedAt: Date.now() }));
    } catch {
        // Sem acesso ao localStorage — ignorar
    }
}

let _fetchPromise = null;

async function fetchFlags() {
    // Deduplica chamadas paralelas
    if (!_fetchPromise) {
        _fetchPromise = fetch(`${API_BASE}/api/features`)
            .then((r) => r.json())
            .then((data) => {
                const flags = data.flags || {};
                setCache(flags);
                _fetchPromise = null;
                return flags;
            })
            .catch(() => {
                _fetchPromise = null;
                return {};
            });
    }
    return _fetchPromise;
}

// Store global em memória para evitar múltiplos fetches entre hooks
let _globalFlags = getCached();
const _listeners = new Set();

function notifyListeners() {
    _listeners.forEach((fn) => fn(_globalFlags));
}

// Carrega flags na inicialização se o cache expirou
if (!_globalFlags) {
    fetchFlags().then((flags) => {
        _globalFlags = flags;
        notifyListeners();
    });
}

/**
 * @param {string} name - Nome do feature flag
 * @param {boolean} [fallback=false] - Valor padrão enquanto carrega ou em caso de erro
 */
export function useFeatureFlag(name, fallback = false) {
    const [flags, setFlags] = useState(_globalFlags);

    useEffect(() => {
        const update = (newFlags) => setFlags(newFlags);
        _listeners.add(update);

        // Se ainda não temos flags, buscar
        if (!_globalFlags) {
            fetchFlags().then((f) => {
                _globalFlags = f;
                notifyListeners();
            });
        }

        return () => _listeners.delete(update);
    }, []);

    if (!flags) return fallback;
    return flags[name] ?? fallback;
}
