import { useState, useEffect } from "react";
import { Zap, ChevronRight } from "lucide-react";
import { usePipelineStore } from "@/stores/pipelineStore";
import { usePipelineWebSocket } from "@/hooks/usePipelineWebSocket";
import { StatusBadge } from "@/components/ui/StatusBadge";
import ChannelSelector from "@/components/Pipeline/ChannelSelector";
import TopicList from "@/components/Pipeline/TopicList";
import CopyEditor from "@/components/Pipeline/CopyEditor";
import ArtViewer from "@/components/Pipeline/ArtViewer";
import PublishPanel from "@/components/Pipeline/PublishPanel";
import { pipelineApi } from "@/services/pipelineApi";

// ── Pipeline stage steps for progress indicator ───────────────────────────────
const STEPS = [
  { label: "Pesquisa", states: ["RESEARCHING", "ORCHESTRATING"] },
  { label: "Tema", states: ["AWAITING_SELECTION"] },
  { label: "Copy", states: ["GENERATING_COPY", "COPY_REVIEW"] },
  { label: "Arte", states: ["GENERATING_ART", "ART_REVIEW"] },
  { label: "Publicação", states: ["SCHEDULED", "PUBLISHING", "PUBLISHED"] },
];

function getStepIndex(state) {
  if (!state) return -1;
  return STEPS.findIndex((s) => s.states.includes(state));
}

function StepProgress({ pipelineState }) {
  const currentStep = getStepIndex(pipelineState);

  return (
    <div className="flex items-center gap-1.5 flex-wrap">
      {STEPS.map((step, i) => {
        const isDone = i < currentStep;
        const isCurrent = i === currentStep;
        return (
          <div key={step.label} className="flex items-center gap-1.5">
            <div className="flex items-center gap-1.5">
              <div
                className={[
                  "w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold transition-all",
                  isDone ? "bg-[#10B981] text-white"
                    : isCurrent ? "bg-[#6366F1] text-white shadow-[0_0_10px_rgba(99,102,241,0.4)] animate-pulse"
                      : "bg-[#2E2E2E] text-[#6B7280]",
                ].join(" ")}
              >
                {isDone ? "✓" : i + 1}
              </div>
              <span
                className={`text-xs font-medium hidden sm:block ${isCurrent ? "text-[#F9FAFB]" : isDone ? "text-[#9CA3AF]" : "text-[#4B5563]"
                  }`}
              >
                {step.label}
              </span>
            </div>
            {i < STEPS.length - 1 && (
              <ChevronRight size={12} className={isDone ? "text-[#10B981]" : "text-[#2E2E2E]"} />
            )}
          </div>
        );
      })}
    </div>
  );
}

// ── Idle screen: no active pipeline ───────────────────────────────────────────
function EmptyPipelineScreen({ onStartFlow }) {
  return (
    <div className="min-h-[60vh] flex flex-col items-center justify-center gap-6 text-center px-4 animate-[fade-in_0.3s_ease-out]">
      {/* Icon */}
      <div className="relative">
        <div className="w-20 h-20 rounded-2xl bg-[#6366F1]/10 border border-[#6366F1]/20 flex items-center justify-center shadow-[0_0_40px_rgba(99,102,241,0.15)]">
          <Zap size={40} className="text-[#6366F1]" />
        </div>
        <div className="absolute -top-1 -right-1 w-5 h-5 rounded-full bg-[#10B981] border-2 border-[#0F0F0F] flex items-center justify-center">
          <span className="text-[8px] font-bold text-white">+</span>
        </div>
      </div>

      {/* Text */}
      <div className="space-y-2 max-w-sm">
        <h2 className="text-2xl font-bold text-[#F9FAFB]">Criar novo conteúdo</h2>
        <p className="text-sm text-[#9CA3AF] leading-relaxed">
          O pipeline pesquisa temas, gera copy com IA e distribui para todos os seus canais. Comece em segundos.
        </p>
      </div>

      {/* Steps preview */}
      <div className="flex items-center gap-3 text-xs text-[#6B7280]">
        {["Pesquisa", "Tema", "Copy", "Arte", "Publicação"].map((s, i) => (
          <div key={s} className="flex items-center gap-3">
            <span>{s}</span>
            {i < 4 && <ChevronRight size={12} />}
          </div>
        ))}
      </div>

      {/* CTA */}
      <button
        onClick={onStartFlow}
        className="flex items-center gap-2.5 bg-[#6366F1] hover:bg-[#4F46E5] text-white font-semibold px-8 py-3.5 rounded-xl text-sm transition-all shadow-[0_0_24px_rgba(99,102,241,0.35)] hover:shadow-[0_0_36px_rgba(99,102,241,0.45)] hover:scale-[1.02] active:scale-[0.98]"
      >
        <Zap size={18} />
        Iniciar Novo Post
      </button>
    </div>
  );
}

// ── Researching / Orchestrating loading screen ────────────────────────────────
function ResearchingScreen({ pipelineState }) {
  return (
    <div className="min-h-[50vh] flex flex-col items-center justify-center gap-5 text-center px-4">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-2 border-[#6366F1]/20 animate-[pulse-glow_2s_ease-in-out_infinite]" />
        <div className="absolute inset-2 rounded-full border-2 border-t-[#6366F1] border-r-transparent border-b-transparent border-l-transparent animate-spin" />
        <Zap size={24} className="absolute inset-0 m-auto text-[#6366F1]" />
      </div>
      <div className="space-y-1.5">
        <StatusBadge state={pipelineState} size="md" />
        <p className="text-xs text-[#6B7280]">
          {pipelineState === "RESEARCHING"
            ? "Coletando e analisando fontes relevantes para o seu nicho..."
            : "Orquestrando agentes e priorizando temas por relevância..."}
        </p>
      </div>
    </div>
  );
}

// ── GENERATING_COPY loading ───────────────────────────────────────────────────
function GeneratingCopyScreen({ pipelineState, selectedChannels }) {
  return (
    <div className="min-h-[40vh] flex flex-col items-center justify-center gap-5 text-center px-4">
      <div className="relative w-16 h-16">
        <div className="absolute inset-0 rounded-full border-2 border-purple-500/20 animate-[pulse-glow_2s_ease-in-out_infinite]" />
        <div className="absolute inset-2 rounded-full border-2 border-t-purple-400 border-r-transparent border-b-transparent border-l-transparent animate-spin" />
        <span className="absolute inset-0 m-auto w-5 h-5 flex items-center justify-center text-purple-400">✍</span>
      </div>
      <div className="space-y-1.5">
        <StatusBadge state={pipelineState} size="md" />
        <p className="text-xs text-[#6B7280]">
          Gerando copies para {selectedChannels.length} canal{selectedChannels.length > 1 ? "is" : ""} em paralelo...
        </p>
      </div>
    </div>
  );
}

// ── Main PipelinePage ────────────────────────────────────────────────────────
export default function PipelinePage() {
  const {
    currentPipeline,
    pipelineState,
    selectedChannels,
    topics,
    setPipeline,
    setPipelineState,
    setTopics,
    selectTopic,
    reset,
  } = usePipelineStore();

  const [phase, setPhase] = useState("idle"); // idle | channel-select | pipeline
  const [startLoading, setStartLoading] = useState(false);
  const [topicLoadingId, setTopicLoadingId] = useState(null);
  const [error, setError] = useState(null);

  // Connect websocket if there's an active pipeline
  usePipelineWebSocket(currentPipeline?.id);

  // When WS pushes AWAITING_SELECTION, fetch topics from API
  useEffect(() => {
    if (pipelineState === "AWAITING_SELECTION" && currentPipeline?.id) {
      pipelineApi.getTopics(currentPipeline.id)
        .then((data) => setTopics(data.topics ?? []))
        .catch((e) => console.error("Falha ao buscar tópicos:", e));
    }
  }, [pipelineState, currentPipeline?.id]);

  // Derive sub-phase from pipeline state for rendering
  function renderPipelineBody() {
    switch (pipelineState) {
      case "RESEARCHING":
      case "ORCHESTRATING":
        return <ResearchingScreen pipelineState={pipelineState} />;

      case "AWAITING_SELECTION":
        return (
          <TopicList
            topics={topics}
            onSelect={handleSelectTopic}
            loadingId={topicLoadingId}
          />
        );

      case "GENERATING_COPY":
        return <GeneratingCopyScreen pipelineState={pipelineState} selectedChannels={selectedChannels} />;

      case "COPY_REVIEW":
        return (
          <CopyEditor
            channels={selectedChannels.length ? selectedChannels : ["instagram", "linkedin", "twitter"]}
            pipelineId={currentPipeline?.id}
            onApprove={handleApproveCopy}
          />
        );

      case "GENERATING_ART":
        return (
          <div className="min-h-[40vh] flex flex-col items-center justify-center gap-4 text-center">
            <StatusBadge state="GENERATING_ART" size="md" />
            <p className="text-xs text-[#6B7280]">Agente de arte criando variações visuais...</p>
          </div>
        );

      case "ART_REVIEW":
        return <ArtViewer onApprove={handleApproveArt} />;

      case "SCHEDULED":
      case "PUBLISHING":
      case "PUBLISHED":
        return <PublishPanel onPublish={handlePublish} />;

      default:
        return (
          <div className="min-h-[40vh] flex items-center justify-center">
            <StatusBadge state={pipelineState} size="md" />
          </div>
        );
    }
  }

  // ── Handlers ───────────────────────────────────────────────────────────────

  async function handleStartPipeline() {
    setStartLoading(true);
    setError(null);
    try {
      const pipeline = await pipelineApi.start(selectedChannels);
      setPipeline({ id: pipeline.session_id, state: pipeline.state });
      setPhase("pipeline");
      // State updates (RESEARCHING → AWAITING_SELECTION) chegam via WebSocket
    } catch (e) {
      setError(e.message || "Falha ao iniciar pipeline");
      console.error(e);
    } finally {
      setStartLoading(false);
    }
  }

  async function handleSelectTopic(topicId) {
    setTopicLoadingId(topicId);
    setError(null);
    try {
      selectTopic(topicId);
      await pipelineApi.selectTopic(currentPipeline?.id, topicId);
      // Estado GENERATING_COPY → COPY_REVIEW chega via WebSocket
    } catch (e) {
      setError(e.message || "Falha ao selecionar tema");
      console.error(e);
    } finally {
      setTopicLoadingId(null);
    }
  }

  async function handleApproveCopy() {
    setError(null);
    try {
      await pipelineApi.approveCopy(currentPipeline?.id);
      // Estado GENERATING_ART → ART_REVIEW chega via WebSocket
    } catch (e) {
      setError(e.message || "Falha ao aprovar copy");
      console.error(e);
    }
  }

  async function handleApproveArt(artId) {
    setError(null);
    try {
      await pipelineApi.approveArt(currentPipeline?.id, artId);
      // Estado SCHEDULED ou PUBLISHING chega via WebSocket
    } catch (e) {
      setError(e.message || "Falha ao aprovar arte");
      console.error(e);
    }
  }

  async function handlePublish() {
    setError(null);
    try {
      await pipelineApi.publish(currentPipeline?.id, { schedule: false });
      // Estado PUBLISHED chega via WebSocket (ou pela resposta HTTP)
    } catch (e) {
      setError(e.message || "Falha ao publicar");
      console.error(e);
    }
  }

  function handleRestart() {
    reset();
    setPhase("idle");
  }

  // ── Render ─────────────────────────────────────────────────────────────────

  return (
    <div className="p-5 md:p-6 max-w-3xl mx-auto space-y-6 animate-[fade-in_0.25s_ease-out]">

      {/* Header */}
      <div className="flex items-start justify-between gap-4">
        <div>
          <h1 className="text-xl font-bold text-[#F9FAFB]">Pipeline</h1>
          <p className="text-xs text-[#6B7280] mt-0.5">
            {phase === "idle"
              ? "Pesquisa → Copy → Arte → Publicação"
              : currentPipeline?.id
                ? `Pipeline #${currentPipeline.id.toString().slice(-6)}`
                : "Iniciando..."}
          </p>
        </div>

        {/* Status + restart */}
        {phase === "pipeline" && pipelineState && (
          <div className="flex items-center gap-2">
            <StatusBadge state={pipelineState} size="sm" />
            {pipelineState === "PUBLISHED" && (
              <button
                onClick={handleRestart}
                className="text-xs text-[#6366F1] hover:text-[#818CF8] font-medium transition-colors"
              >
                Novo post
              </button>
            )}
          </div>
        )}
      </div>

      {/* Error banner */}
      {error && (
        <div className="text-xs text-red-400 bg-red-950/30 border border-red-800/40 rounded-lg px-4 py-3">
          {error}
        </div>
      )}

      {/* Step progress */}
      {phase === "pipeline" && pipelineState && (
        <div className="bg-[#1A1A1A] border border-[#2E2E2E] rounded-xl px-4 py-3">
          <StepProgress pipelineState={pipelineState} />
        </div>
      )}

      {/* Main content */}
      <div>
        {phase === "idle" && (
          <EmptyPipelineScreen onStartFlow={() => setPhase("channel-select")} />
        )}

        {phase === "channel-select" && (
          <ChannelSelector
            onStart={handleStartPipeline}
            loading={startLoading}
          />
        )}

        {phase === "pipeline" && renderPipelineBody()}
      </div>
    </div>
  );
}
