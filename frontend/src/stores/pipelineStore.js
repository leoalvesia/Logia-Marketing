import { create } from "zustand";
import { immer } from "zustand/middleware/immer";

export const usePipelineStore = create(
  immer((set) => ({
    currentPipeline: null,
    pipelineState: null,
    topics: [],
    selectedTopicId: null,
    selectedChannels: [],
    copies: {},       // { [channel]: { id, content, status } }
    streamingChunks: {}, // { [channel]: string }

    setPipeline: (pipeline) =>
      set((s) => {
        s.currentPipeline = pipeline;
        s.pipelineState = pipeline?.state ?? null;
      }),

    setPipelineState: (state) =>
      set((s) => {
        s.pipelineState = state;
      }),

    setTopics: (topics) =>
      set((s) => {
        s.topics = topics;
      }),

    selectTopic: (topicId) =>
      set((s) => {
        s.selectedTopicId = topicId;
      }),

    toggleChannel: (channel) =>
      set((s) => {
        const idx = s.selectedChannels.indexOf(channel);
        if (idx === -1) s.selectedChannels.push(channel);
        else s.selectedChannels.splice(idx, 1);
      }),

    // Handles incoming WebSocket messages from the pipeline
    handleWsMessage: (msg) =>
      set((s) => {
        const { type, state, data } = msg;
        if (state) s.pipelineState = state;

        if (type === "copy_chunk" && data?.channel) {
          const prev = s.streamingChunks[data.channel] ?? "";
          s.streamingChunks[data.channel] = prev + (data.chunk ?? "");
        }

        if (state === "GENERATING_COPY" && data?.channel && data?.copy_id) {
          s.copies[data.channel] = { id: data.copy_id, status: "draft" };
          // Clear streaming buffer once copy is saved
          delete s.streamingChunks[data.channel];
        }
      }),

    reset: () =>
      set((s) => {
        s.currentPipeline = null;
        s.pipelineState = null;
        s.topics = [];
        s.selectedTopicId = null;
        s.selectedChannels = [];
        s.copies = {};
        s.streamingChunks = {};
      }),
  }))
);
