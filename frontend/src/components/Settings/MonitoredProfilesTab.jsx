import { useState, useRef, useEffect } from "react";
import { useSettingsStore } from "@/stores/settingsStore";
import { useToast } from "@/components/ui/Toast";
import { ChannelBadge } from "@/components/ui/ChannelBadge";
import {
    DndContext, PointerSensor, useSensor, useSensors, DragOverlay,
    useDraggable, useDroppable,
} from "@dnd-kit/core";
import {
    GripVertical, Plus, Trash2, RefreshCw, ToggleLeft, ToggleRight
} from "lucide-react";

const PLATFORMS = ["instagram", "linkedin", "twitter", "youtube", "email"];

function validateHandle(handle, platform) {
    if (!handle.trim()) return "Campo obrigatório";
    if (platform === "youtube" && !handle.startsWith("http") && !handle.startsWith("@"))
        return "Use @handle ou URL completa";
    if (["instagram", "twitter"].includes(platform) && !handle.startsWith("@") && !handle.startsWith("http"))
        return "Use @handle ou URL";
    return null;
}

// ── Draggable Profile Row ──────────────────────────────────────────────────────
function ProfileRow({ profile, onToggle, onRemove, onFetch, fetchingId }) {
    const { attributes, listeners, setNodeRef: setDragRef, isDragging } = useDraggable({ id: profile.id });
    const { setNodeRef: setDropRef, isOver } = useDroppable({ id: profile.id });

    function setRef(el) { setDragRef(el); setDropRef(el); }

    return (
        <div
            ref={setRef}
            className={[
                "flex items-center gap-3 p-3 rounded-xl border transition-all",
                isDragging ? "opacity-30 border-[#6366F1]/60" : "border-[#2E2E2E] bg-[#1A1A1A]",
                isOver ? "border-[#6366F1]/50 bg-[#6366F1]/5" : "",
                !profile.active ? "opacity-50" : "",
            ].join(" ")}
            role="listitem"
            aria-label={`Perfil monitorado: ${profile.handle}`}
        >
            {/* Drag handle */}
            <button
                {...attributes}
                {...listeners}
                aria-label="Arrastar para reordenar"
                className="shrink-0 text-[#4B5563] hover:text-[#9CA3AF] cursor-grab active:cursor-grabbing touch-none focus-visible:outline-2 focus-visible:outline-[#6366F1] rounded"
            >
                <GripVertical size={16} aria-hidden="true" />
            </button>

            {/* Priority badge */}
            <span className="shrink-0 w-5 h-5 flex items-center justify-center text-[10px] font-bold text-[#6B7280] bg-[#2E2E2E] rounded-full">
                {profile.priority}
            </span>

            {/* Channel badge */}
            <ChannelBadge channel={profile.platform} size="xs" variant="icon" />

            {/* Handle */}
            <p className="flex-1 text-xs font-mono text-[#F9FAFB] truncate">{profile.handle}</p>

            {/* Actions */}
            <div className="flex items-center gap-1.5">
                <button
                    onClick={() => onFetch(profile.id)}
                    disabled={fetchingId === profile.id}
                    aria-label={`Buscar conteúdo de ${profile.handle}`}
                    aria-busy={fetchingId === profile.id}
                    title="Buscar agora"
                    className="w-7 h-7 flex items-center justify-center rounded-lg text-[#6B7280] hover:text-[#6366F1] hover:bg-[#6366F1]/10 transition-all focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                >
                    <RefreshCw size={12} className={fetchingId === profile.id ? "animate-spin" : ""} aria-hidden="true" />
                </button>

                <button
                    onClick={() => onToggle(profile.id)}
                    aria-label={profile.active ? `Desativar ${profile.handle}` : `Ativar ${profile.handle}`}
                    aria-pressed={profile.active}
                    className="w-7 h-7 flex items-center justify-center rounded-lg text-[#6B7280] hover:text-[#9CA3AF] hover:bg-[#2E2E2E] transition-all focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                >
                    {profile.active
                        ? <ToggleRight size={16} className="text-emerald-400" aria-hidden="true" />
                        : <ToggleLeft size={16} aria-hidden="true" />
                    }
                </button>

                <button
                    onClick={() => onRemove(profile.id)}
                    aria-label={`Remover ${profile.handle}`}
                    className="w-7 h-7 flex items-center justify-center rounded-lg text-[#6B7280] hover:text-red-400 hover:bg-red-950/30 transition-all focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                >
                    <Trash2 size={12} aria-hidden="true" />
                </button>
            </div>
        </div>
    );
}

export default function MonitoredProfilesTab() {
    const profiles = useSettingsStore((s) => s.monitoredProfiles);
    const profilesLoaded = useSettingsStore((s) => s.profilesLoaded);
    const fetchProfiles = useSettingsStore((s) => s.fetchProfiles);
    const addProfile = useSettingsStore((s) => s.addProfile);
    const removeProfile = useSettingsStore((s) => s.removeProfile);
    const toggleProfile = useSettingsStore((s) => s.toggleProfile);
    const reorderProfiles = useSettingsStore((s) => s.reorderProfiles);

    useEffect(() => {
        if (!profilesLoaded) fetchProfiles();
    }, []);
    const toast = useToast();

    const [newHandle, setNewHandle] = useState("");
    const [newPlatform, setNewPlatform] = useState("instagram");
    const [error, setError] = useState(null);
    const [fetchingId, setFetchingId] = useState(null);
    const [draggingId, setDraggingId] = useState(null);

    const sensors = useSensors(useSensor(PointerSensor, { activationConstraint: { distance: 6 } }));

    function handleAdd() {
        const err = validateHandle(newHandle, newPlatform);
        if (err) { setError(err); return; }
        addProfile(newHandle.trim(), newPlatform);
        setNewHandle("");
        setError(null);
        toast({ type: "success", title: "Perfil adicionado", description: `${newHandle} agora é monitorado.` });
    }

    async function handleFetch(id) {
        setFetchingId(id);
        await new Promise((r) => setTimeout(r, 1500));
        setFetchingId(null);
        toast({ type: "info", title: "Coleta concluída", description: "Novos conteúdos foram indexados." });
    }

    function handleDragEnd({ active, over }) {
        setDraggingId(null);
        if (!over || active.id === over.id) return;
        const fromIdx = profiles.findIndex((p) => p.id === active.id);
        const toIdx = profiles.findIndex((p) => p.id === over.id);
        if (fromIdx !== -1 && toIdx !== -1) reorderProfiles(fromIdx, toIdx);
    }

    const draggingProfile = profiles.find((p) => p.id === draggingId);

    return (
        <section aria-label="Perfis monitorados">
            {/* Add row */}
            <div className="flex gap-2 mb-4 flex-wrap">
                <div className="flex-1 min-w-[180px] space-y-1">
                    <input
                        type="text"
                        value={newHandle}
                        onChange={(e) => { setNewHandle(e.target.value); setError(null); }}
                        onKeyDown={(e) => e.key === "Enter" && handleAdd()}
                        placeholder="@handle ou URL"
                        aria-label="Handle ou URL do perfil"
                        aria-invalid={!!error}
                        aria-describedby={error ? "handle-error" : undefined}
                        className={[
                            "w-full bg-[#0F0F0F] border rounded-lg px-3 py-2 text-xs text-[#F9FAFB] placeholder:text-[#4B5563]",
                            "focus:outline-none focus:ring-2 focus:ring-[#6366F1]/50 transition-colors",
                            error ? "border-red-700" : "border-[#2E2E2E] focus:border-[#6366F1]",
                        ].join(" ")}
                    />
                    {error && <p id="handle-error" role="alert" className="text-[10px] text-red-400">{error}</p>}
                </div>

                <select
                    value={newPlatform}
                    onChange={(e) => setNewPlatform(e.target.value)}
                    aria-label="Plataforma do perfil"
                    className="bg-[#0F0F0F] border border-[#2E2E2E] rounded-lg px-3 py-2 text-xs text-[#9CA3AF] focus:outline-none focus:border-[#6366F1] focus:ring-2 focus:ring-[#6366F1]/50 [color-scheme:dark]"
                >
                    {PLATFORMS.map((p) => <option key={p} value={p}>{p.charAt(0).toUpperCase() + p.slice(1)}</option>)}
                </select>

                <button
                    onClick={handleAdd}
                    aria-label="Adicionar perfil monitorado"
                    className="flex items-center gap-1.5 bg-[#6366F1] hover:bg-[#4F46E5] text-white text-xs font-semibold px-4 py-2 rounded-lg transition-colors focus-visible:outline-2 focus-visible:outline-[#6366F1]"
                >
                    <Plus size={14} aria-hidden="true" /> Adicionar
                </button>
            </div>

            <p className="text-xs text-[#6B7280] mb-3">
                {profiles.length} perf{profiles.length !== 1 ? "is" : "il"} monitorado{profiles.length !== 1 ? "s" : ""} · arraste para reordenar
            </p>

            {/* Profile list */}
            <DndContext
                sensors={sensors}
                onDragStart={({ active }) => setDraggingId(active.id)}
                onDragEnd={handleDragEnd}
            >
                <div role="list" className="space-y-2" aria-label="Lista de perfis monitorados" aria-live="polite">
                    {profiles.map((profile) => (
                        <ProfileRow
                            key={profile.id}
                            profile={profile}
                            onToggle={toggleProfile}
                            onRemove={removeProfile}
                            onFetch={handleFetch}
                            fetchingId={fetchingId}
                        />
                    ))}
                </div>

                <DragOverlay>
                    {draggingProfile && (
                        <div className="flex items-center gap-2 px-3 py-2 rounded-xl border border-[#6366F1]/60 bg-[#1A1A1A] shadow-2xl opacity-90 text-xs font-mono text-[#F9FAFB]">
                            <GripVertical size={14} className="text-[#6366F1]" />
                            {draggingProfile.handle}
                        </div>
                    )}
                </DragOverlay>
            </DndContext>
        </section>
    );
}
