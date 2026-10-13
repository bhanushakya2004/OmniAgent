"use client";

import React, { useState, useRef } from "react";
import {
  Mic,
  MicOff,
  Image as ImageIcon,
  Sparkles,
  Send,
  X,
  Loader2,
  Tag,
  AlertCircle,
} from "lucide-react";
import { apiClient } from "@/lib/api-client";
import { useStoreSelectionStore } from "@/stores/store-selection-store";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface MissionComposerProps {
  onMissionCreated: (missionId: string) => void;
  isStreaming: boolean;
}

interface UploadResponse {
  file_url: string;
  filename: string;
  content_type: string;
  size_bytes: number;
}

interface VisionResponse {
  primary_query: string;
  description: string;
  detected_items: Array<{ label: string; brand?: string; category?: string }>;
  suggested_action: string;
}

interface VoiceResponse {
  text: string;
  language: string;
  confidence: number;
}

const GOLDEN_PROMPTS = [
  {
    label: "🍰 Eggless Protein Cake",
    text: "Eggless cake with good protein, suggest all ingredients with quantities",
  },
  {
    label: "🎉 Party for 8 (₹2500)",
    text: "Hosting a party for 8 people, suggest chips, cold drinks, cookies and paper plates within ₹2500",
  },
  {
    label: "✈️ Mumbai Travel Kit",
    text: "Travelling to Mumbai for 3 days, I need travel-size shampoo, toothpaste, and pocket sanitizer under 100ml",
  },
  {
    label: "🇮🇳 Hindi Voice Prompt",
    text: "8 logon ki party ke liye snacks, cold drinks aur disposables chahiye, budget 2000 rupaye",
  },
];

export function MissionComposer({
  onMissionCreated,
  isStreaming,
}: MissionComposerProps): React.JSX.Element {
  const [prompt, setPrompt] = useState("");
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);

  // Multimodal states
  const [isRecording, setIsRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timeout | null>(null);

  // Vision states
  const [attachedImage, setAttachedImage] = useState<UploadResponse | null>(null);
  const [visionAnalysis, setVisionAnalysis] = useState<VisionResponse | null>(null);
  const [isUploadingImage, setIsUploadingImage] = useState(false);
  const fileInputRef = useRef<HTMLInputElement | null>(null);

  const selectedStoreIds = useStoreSelectionStore((state) => state.selectedStoreIds);

  // Voice recording handlers
  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream);
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      recorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());
        const audioBlob = new Blob(audioChunksRef.current, { type: "audio/webm" });
        await handleAudioUpload(audioBlob);
      };

      recorder.start();
      setIsRecording(true);
      setRecordingSeconds(0);
      timerRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      console.warn("Microphone access unavailable or denied", err);
      // Fallback demo speech simulation for offline environments
      simulateVoiceInput();
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      if (timerRef.current) clearInterval(timerRef.current);
    }
  };

  const simulateVoiceInput = () => {
    setPrompt(
      "Hosting a party for 8 people, suggest chips, cold drinks, cookies and paper plates within ₹2500"
    );
  };

  const handleAudioUpload = async (blob: Blob) => {
    try {
      setIsSubmitting(true);
      const formData = new FormData();
      formData.append("file", blob, "voice_input.webm");

      const res = await apiClient.post<VoiceResponse>("/api/v1/voice/transcribe", formData);
      if (res.text) {
        setPrompt((prev) => (prev ? `${prev} ${res.text}` : res.text));
      }
    } catch (err) {
      console.error("Audio transcription error", err);
      simulateVoiceInput();
    } finally {
      setIsSubmitting(false);
    }
  };

  // Image upload and vision parsing handlers
  const handleImageSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    try {
      setIsUploadingImage(true);
      setErrorMessage(null);

      // 1. Upload file
      const formData = new FormData();
      formData.append("file", file);
      const uploadRes = await apiClient.post<UploadResponse>("/api/v1/uploads", formData);
      setAttachedImage(uploadRes);

      // 2. Vision analysis
      const visionRes = await apiClient.post<VisionResponse>("/api/v1/vision/analyze", {
        file_url: uploadRes.file_url,
        prompt: prompt || "identify this product or pantry item",
      });
      setVisionAnalysis(visionRes);

      if (!prompt) {
        setPrompt(`Find ${visionRes.primary_query} or closest store alternatives`);
      }
    } catch (err) {
      console.error("Image upload/vision failed", err);
      setErrorMessage("Image analysis failed. Please verify format (JPEG/PNG/WebP).");
    } finally {
      setIsUploadingImage(false);
    }
  };

  const removeAttachedImage = () => {
    setAttachedImage(null);
    setVisionAnalysis(null);
    if (fileInputRef.current) fileInputRef.current.value = "";
  };

  // Submit mission handler
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!prompt.trim()) return;

    if (selectedStoreIds.length === 0) {
      setErrorMessage("Please select at least one physical store from the list above.");
      return;
    }

    try {
      setIsSubmitting(true);
      setErrorMessage(null);

      const modalities = ["text"];
      if (attachedImage) modalities.push("image");
      if (isRecording) modalities.push("voice");

      const res = await apiClient.post<{ id: string; status: string; stream_url: string }>(
        "/api/v1/missions",
        {
          prompt: prompt.trim(),
          store_ids: selectedStoreIds,
          language: "en",
          input_modalities: modalities,
        }
      );

      onMissionCreated(res.id);
    } catch (err) {
      console.error("Failed to launch mission", err);
      setErrorMessage("Failed to initiate mission. Please check connection.");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <Card className="p-6 bg-card/80 backdrop-blur-md border-border/80 shadow-lg">
      <form onSubmit={handleSubmit} className="space-y-4">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-primary" />
            <h3 className="font-bold text-lg">Goal-Driven Shopping Mission</h3>
          </div>
          <span className="text-xs text-muted-foreground">
            Multimodal: Text • Voice • Image
          </span>
        </div>

        {/* Golden Prompt Chips */}
        <div className="flex items-center gap-1.5 flex-wrap">
          {GOLDEN_PROMPTS.map((gp) => (
            <button
              key={gp.label}
              type="button"
              disabled={isStreaming || isSubmitting}
              onClick={() => setPrompt(gp.text)}
              className="text-xs px-3 py-1.5 rounded-full bg-muted/60 hover:bg-muted text-foreground/80 hover:text-foreground border border-border/60 transition-colors font-medium flex items-center gap-1"
            >
              {gp.label}
            </button>
          ))}
        </div>

        {/* Input Textarea & Attachments Container */}
        <div className="relative rounded-2xl border border-border/80 bg-background/90 focus-within:border-primary focus-within:ring-2 focus-within:ring-primary/20 transition-all p-3 shadow-inner">
          {/* Attached Image Preview */}
          {attachedImage && (
            <div className="mb-3 p-2 rounded-xl bg-muted/40 border border-border flex items-center justify-between gap-3">
              <div className="flex items-center gap-2.5 overflow-hidden">
                <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center shrink-0">
                  <ImageIcon className="w-5 h-5 text-primary" />
                </div>
                <div className="truncate">
                  <p className="text-xs font-semibold truncate">{attachedImage.filename}</p>
                  {visionAnalysis && (
                    <p className="text-[11px] text-muted-foreground truncate">
                      Detected: {visionAnalysis.primary_query}
                    </p>
                  )}
                </div>
              </div>

              <button
                type="button"
                onClick={removeAttachedImage}
                className="p-1 rounded-md text-muted-foreground hover:text-foreground hover:bg-muted transition-colors"
              >
                <X className="w-4 h-4" />
              </button>
            </div>
          )}

          {isUploadingImage && (
            <div className="mb-3 p-3 rounded-xl bg-muted/40 border border-border flex items-center gap-2 text-xs text-muted-foreground animate-pulse">
              <Loader2 className="w-4 h-4 animate-spin text-primary" />
              <span>Analyzing image with Gemini Vision...</span>
            </div>
          )}

          <Textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            disabled={isStreaming || isSubmitting}
            placeholder="Tell OmniMission what you want to achieve (e.g. 'Eggless chocolate cake with high protein', 'Travel toiletries for Mumbai trip', or upload a photo)..."
            className="border-0 shadow-none focus-visible:ring-0 p-0 text-base resize-none min-h-[90px] bg-transparent"
          />

          {/* Action Bar */}
          <div className="flex items-center justify-between pt-2 border-t border-border/40 mt-2">
            <div className="flex items-center gap-1.5">
              {/* Mic Button */}
              <button
                type="button"
                disabled={isStreaming || isSubmitting}
                onClick={isRecording ? stopRecording : startRecording}
                className={`p-2 rounded-lg text-sm font-medium flex items-center gap-1.5 transition-colors ${
                  isRecording
                    ? "bg-destructive text-destructive-foreground animate-pulse"
                    : "text-muted-foreground hover:text-foreground hover:bg-muted"
                }`}
                title={isRecording ? "Stop recording" : "Speak your mission"}
              >
                {isRecording ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                {isRecording && <span className="text-xs font-mono">{recordingSeconds}s</span>}
              </button>

              {/* Photo Button */}
              <button
                type="button"
                disabled={isStreaming || isSubmitting || isUploadingImage}
                onClick={() => fileInputRef.current?.click()}
                className="p-2 rounded-lg text-muted-foreground hover:text-foreground hover:bg-muted transition-colors flex items-center gap-1.5"
                title="Attach product or pantry photo"
              >
                <ImageIcon className="w-4 h-4" />
                <span className="text-xs hidden sm:inline">Attach Photo</span>
              </button>
              <input
                ref={fileInputRef}
                type="file"
                accept="image/jpeg,image/png,image/webp"
                onChange={handleImageSelect}
                className="hidden"
              />
            </div>

            {/* Launch Button */}
            <Button
              type="submit"
              disabled={!prompt.trim() || isStreaming || isSubmitting || selectedStoreIds.length === 0}
              isLoading={isSubmitting || isStreaming}
              className="rounded-xl px-5"
            >
              <Send className="w-4 h-4 mr-1.5" />
              Launch Mission
            </Button>
          </div>
        </div>

        {/* Error Alert */}
        {errorMessage && (
          <div className="p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{errorMessage}</span>
          </div>
        )}
      </form>
    </Card>
  );
}
