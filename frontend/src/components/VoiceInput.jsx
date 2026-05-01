import React, { useEffect, useRef, useState } from "react";
import axios from "axios";
import { Mic, Square, Loader2 } from "lucide-react";
import { Button } from "./ui/button";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

// Web Speech API support check
const SpeechRecognition =
    typeof window !== "undefined"
        ? window.SpeechRecognition || window.webkitSpeechRecognition
        : null;

/** Mic button that dictates Sanskrit/Hindi Devanagari into an input.
 *  Uses Web Speech API when available (instant, free), otherwise records
 *  via MediaRecorder and posts to `/api/transcribe` (Whisper fallback).
 */
export const VoiceInput = ({ onTranscript }) => {
    const [recording, setRecording] = useState(false);
    const [processing, setProcessing] = useState(false);
    const recognitionRef = useRef(null);
    const mediaRecorderRef = useRef(null);
    const chunksRef = useRef([]);
    const streamRef = useRef(null);

    useEffect(
        () => () => {
            // cleanup on unmount
            try {
                recognitionRef.current?.stop?.();
                mediaRecorderRef.current?.stop?.();
                streamRef.current?.getTracks?.().forEach((t) => t.stop());
            } catch {
                /* noop */
            }
        },
        [],
    );

    const startWebSpeech = () => {
        const rec = new SpeechRecognition();
        rec.lang = "hi-IN"; // Hindi Devanagari — closest Web Speech support for Sanskrit
        rec.interimResults = false;
        rec.continuous = false;
        rec.maxAlternatives = 1;

        rec.onresult = (event) => {
            const transcript = event.results?.[0]?.[0]?.transcript || "";
            if (transcript) {
                onTranscript(transcript);
                toast.success("Transcribed via browser");
            }
        };
        rec.onerror = (event) => {
            if (event.error === "not-allowed") {
                toast.error("Microphone permission denied");
            } else if (event.error === "no-speech") {
                toast.error("No speech detected. Try again.");
            } else {
                // fall through to Whisper fallback on other errors
                startWhisperRecording();
                return;
            }
            setRecording(false);
        };
        rec.onend = () => setRecording(false);

        recognitionRef.current = rec;
        try {
            rec.start();
            setRecording(true);
        } catch {
            startWhisperRecording();
        }
    };

    const startWhisperRecording = async () => {
        try {
            const stream = await navigator.mediaDevices.getUserMedia({
                audio: true,
            });
            streamRef.current = stream;
            const mr = new MediaRecorder(stream, { mimeType: "audio/webm" });
            mediaRecorderRef.current = mr;
            chunksRef.current = [];

            mr.ondataavailable = (e) => {
                if (e.data && e.data.size > 0) chunksRef.current.push(e.data);
            };
            mr.onstop = async () => {
                stream.getTracks().forEach((t) => t.stop());
                const blob = new Blob(chunksRef.current, {
                    type: "audio/webm",
                });
                chunksRef.current = [];
                if (blob.size < 1000) {
                    toast.error("Recording too short");
                    setProcessing(false);
                    return;
                }
                setProcessing(true);
                try {
                    const form = new FormData();
                    form.append("audio", blob, "recording.webm");
                    const { data } = await axios.post(
                        `${API}/transcribe`,
                        form,
                        {
                            headers: {
                                "Content-Type": "multipart/form-data",
                            },
                        },
                    );
                    const text = data?.text?.trim();
                    if (text) {
                        onTranscript(text);
                        toast.success("Transcribed via Whisper");
                    } else {
                        toast.error("Couldn't hear anything clearly");
                    }
                } catch (e) {
                    toast.error(
                        e?.response?.data?.detail ||
                            "Transcription failed. Please try again.",
                    );
                } finally {
                    setProcessing(false);
                }
            };

            mr.start();
            setRecording(true);
        } catch (e) {
            toast.error("Microphone permission denied");
            setRecording(false);
        }
    };

    const start = () => {
        if (recording || processing) return;
        if (SpeechRecognition) startWebSpeech();
        else startWhisperRecording();
    };

    const stop = () => {
        try {
            if (recognitionRef.current) {
                recognitionRef.current.stop();
                recognitionRef.current = null;
            }
            if (mediaRecorderRef.current?.state === "recording") {
                mediaRecorderRef.current.stop();
            }
        } catch {
            /* noop */
        }
        setRecording(false);
    };

    const onClick = () => (recording ? stop() : start());

    const Icon = processing
        ? Loader2
        : recording
          ? Square
          : Mic;

    return (
        <Button
            data-testid="voice-input-btn"
            type="button"
            variant="ghost"
            size="sm"
            onClick={onClick}
            disabled={processing}
            className={`icon-btn gap-2 ${
                recording
                    ? "bg-destructive/10 text-destructive opacity-100"
                    : ""
            }`}
            aria-label={recording ? "Stop recording" : "Start voice input"}
        >
            <Icon
                className={`h-4 w-4 ${processing ? "animate-spin" : ""} ${
                    recording ? "animate-pulse" : ""
                }`}
            />
            <span className="label-tiny">
                {processing
                    ? "transcribing"
                    : recording
                      ? "stop"
                      : "dictate"}
            </span>
        </Button>
    );
};

export default VoiceInput;
