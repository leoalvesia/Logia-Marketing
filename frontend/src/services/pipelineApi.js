/**
 * Pipeline API — thin wrapper sobre fetch.
 * Base URL lida da variável de ambiente VITE_API_URL.
 */

const BASE = import.meta.env.VITE_API_URL || "http://localhost:8000";

function getToken() {
    try {
        const raw = localStorage.getItem("logia-auth");
        return raw ? JSON.parse(raw)?.state?.token : null;
    } catch {
        return null;
    }
}

async function request(method, path, body) {
    const token = getToken();
    const res = await fetch(`${BASE}${path}`, {
        method,
        headers: {
            "Content-Type": "application/json",
            ...(token ? { Authorization: `Bearer ${token}` } : {}),
        },
        body: body !== undefined ? JSON.stringify(body) : undefined,
    });

    if (!res.ok) {
        const err = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(err.detail ?? `HTTP ${res.status}`);
    }
    return res.json();
}

// ── Pipeline endpoints ─────────────────────────────────────────────────────────

export const pipelineApi = {
    /** POST /api/pipeline/start */
    start: (channels) =>
        request("POST", "/api/pipeline/start", { channels }),

    /** GET /api/pipeline/:id */
    get: (id) => request("GET", `/api/pipeline/${id}`),

    /** POST /api/pipeline/:id/select-topic */
    selectTopic: (id, topicId) =>
        request("POST", `/api/pipeline/${id}/select-topic`, { topic_id: topicId }),

    /** POST /api/pipeline/:id/approve-copy */
    approveCopy: (id, edits) =>
        request("POST", `/api/pipeline/${id}/approve-copy`, { edits }),

    /** POST /api/pipeline/:id/approve-art */
    approveArt: (id, artId) =>
        request("POST", `/api/pipeline/${id}/approve-art`, { art_id: artId }),

    /** POST /api/pipeline/:id/publish */
    publish: (id, payload) =>
        request("POST", `/api/pipeline/${id}/publish`, payload),

    /** POST /api/pipeline/:id/schedule */
    schedule: (id, scheduledAt) =>
        request("POST", `/api/pipeline/${id}/schedule`, { scheduled_at: scheduledAt }),
};

export default pipelineApi;
