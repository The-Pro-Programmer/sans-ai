import React, { useEffect, useState } from "react";
import axios from "axios";
import { Languages, Wand2, Loader2, BookOpen } from "lucide-react";
import "@/App.css";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { Toaster, toast } from "sonner";

import { ThemeProvider } from "@/context/ThemeContext";
import Header from "@/components/Header";
import TranslationCard from "@/components/TranslationCard";
import HistorySheet from "@/components/HistorySheet";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const LANGUAGE_OPTIONS = [
    { value: "all", label: "All three languages", native: "सर्वाणि" },
    { value: "marathi", label: "Marathi", native: "मराठी" },
    { value: "hindi", label: "Hindi", native: "हिन्दी" },
    { value: "english", label: "English", native: "English" },
];

const SAMPLE = "सत्यमेव जयते";

function Translator() {
    const [sanskrit, setSanskrit] = useState("");
    const [target, setTarget] = useState("all");
    const [loading, setLoading] = useState(false);
    const [result, setResult] = useState(null); // { id, sanskrit_text, results, timestamp }
    const [history, setHistory] = useState([]);
    const [historyOpen, setHistoryOpen] = useState(false);

    const fetchHistory = async () => {
        try {
            const { data } = await axios.get(`${API}/history?limit=50`);
            setHistory(data.items || []);
        } catch (e) {
            // silent fail – history is auxiliary
        }
    };

    useEffect(() => {
        fetchHistory();
    }, []);

    const translate = async () => {
        const text = sanskrit.trim();
        if (!text) {
            toast.error("Please enter some Sanskrit text");
            return;
        }
        setLoading(true);
        try {
            const langs =
                target === "all" ? ["marathi", "hindi", "english"] : [target];
            const { data } = await axios.post(`${API}/translate`, {
                text,
                target_langs: langs,
            });
            setResult(data);
            fetchHistory();
        } catch (e) {
            toast.error(
                e?.response?.data?.detail ||
                    "Translation failed. Please try again.",
            );
        } finally {
            setLoading(false);
        }
    };

    const handleFeedback = async (payload) => {
        try {
            await axios.post(`${API}/feedback/v2`, payload);
            fetchHistory();
        } catch (e) {
            toast.error(
                e?.response?.data?.detail || "Failed to save feedback",
            );
        }
    };

    const loadFromHistory = (item) => {
        setSanskrit(item.sanskrit_text);
        setResult({
            id: item.id,
            sanskrit_text: item.sanskrit_text,
            results: item.results,
            timestamp: item.timestamp,
        });
    };

    const fillSample = () => setSanskrit(SAMPLE);

    return (
        <div className="app-shell">
            <Header onOpenHistory={() => setHistoryOpen(true)} />

            <main className="relative mx-auto max-w-7xl px-6 pb-24 pt-10 sm:px-10">
                {/* Hero */}
                <section className="mb-10 max-w-3xl">
                    <div className="label-tiny text-muted-foreground">
                        Saṃskṛta → Mā­rā­ṭhī · Hindī · English
                    </div>
                    <h1 className="mt-3 font-display text-4xl leading-[1.05] tracking-tight sm:text-5xl lg:text-6xl">
                        A quiet bridge between{" "}
                        <span className="text-primary">ancient verse</span> and
                        modern tongue.
                    </h1>
                    <p className="mt-5 max-w-xl text-base leading-relaxed text-muted-foreground">
                        Paste a shloka, a sutra, or a single pada in Devanagari.
                        Receive faithful translations with a confidence reading
                        — and teach the system when you know better.
                    </p>
                </section>

                {/* Bento grid */}
                <section className="grid grid-cols-1 gap-8 lg:grid-cols-12">
                    {/* Input column */}
                    <div
                        data-testid="input-panel"
                        className="sharp border border-border bg-card p-6 sm:p-8 lg:col-span-5"
                    >
                        <div className="mb-4 flex items-center justify-between">
                            <div className="flex items-center gap-2">
                                <BookOpen className="h-4 w-4 text-primary" />
                                <span className="label-tiny text-muted-foreground">
                                    Sanskrit input
                                </span>
                            </div>
                            <button
                                data-testid="sample-btn"
                                type="button"
                                onClick={fillSample}
                                className="label-tiny text-muted-foreground hover:text-primary"
                            >
                                try a sample
                            </button>
                        </div>

                        <Textarea
                            data-testid="sanskrit-input"
                            value={sanskrit}
                            onChange={(e) => setSanskrit(e.target.value)}
                            placeholder="श्लोकं अत्र लिखतु..."
                            className="sharp font-devanagari min-h-[260px] resize-y border-border bg-background p-5 text-xl leading-relaxed focus-visible:border-primary focus-visible:ring-0"
                        />

                        <div className="mt-6 flex flex-col gap-4 sm:flex-row sm:items-center">
                            <div className="flex-1">
                                <div className="label-tiny mb-2 flex items-center gap-2 text-muted-foreground">
                                    <Languages className="h-3 w-3" />
                                    target
                                </div>
                                <Select value={target} onValueChange={setTarget}>
                                    <SelectTrigger
                                        data-testid="language-selector"
                                        className="sharp border-border bg-background"
                                    >
                                        <SelectValue />
                                    </SelectTrigger>
                                    <SelectContent className="sharp">
                                        {LANGUAGE_OPTIONS.map((o) => (
                                            <SelectItem
                                                key={o.value}
                                                value={o.value}
                                                data-testid={`lang-option-${o.value}`}
                                            >
                                                <span className="mr-3">
                                                    {o.label}
                                                </span>
                                                <span className="text-muted-foreground">
                                                    {o.native}
                                                </span>
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>

                            <Button
                                data-testid="translate-btn"
                                onClick={translate}
                                disabled={loading || !sanskrit.trim()}
                                className="sharp h-11 gap-2 self-end bg-primary px-6 text-primary-foreground hover:bg-primary/90 sm:min-w-[180px]"
                            >
                                {loading ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Wand2 className="h-4 w-4" />
                                )}
                                <span className="label-tiny">
                                    {loading ? "translating" : "translate"}
                                </span>
                            </Button>
                        </div>

                        <div className="mt-6 border-t border-border pt-5">
                            <div className="label-tiny mb-2 text-muted-foreground">
                                how it learns
                            </div>
                            <p className="text-sm leading-relaxed text-muted-foreground">
                                Every correction you submit is stored locally
                                and takes priority the next time the same
                                source appears — so the tool grows sharper with
                                use.
                            </p>
                        </div>
                    </div>

                    {/* Output column */}
                    <div className="space-y-5 lg:col-span-7">
                        {!result && !loading && (
                            <div
                                data-testid="empty-state"
                                className="sharp relative overflow-hidden border border-border bg-card p-10 sm:p-14"
                            >
                                <div
                                    className="absolute inset-0 opacity-10"
                                    style={{
                                        backgroundImage:
                                            "url(https://images.unsplash.com/photo-1657562690244-1885a25280b6?crop=entropy&cs=srgb&fm=jpg&ixid=M3w4NjA1NzB8MHwxfHNlYXJjaHwxfHxpbmRpYW4lMjB0ZW1wbGUlMjBhcmNoaXRlY3R1cmUlMjBtaW5pbWFsaXN0fGVufDB8fHx8MTc3NzY1NzE5MHww&ixlib=rb-4.1.0&q=85)",
                                        backgroundSize: "cover",
                                        backgroundPosition: "center",
                                    }}
                                />
                                <div className="relative">
                                    <div className="label-tiny text-muted-foreground">
                                        awaiting invocation
                                    </div>
                                    <h2 className="mt-3 font-display text-3xl leading-tight sm:text-4xl">
                                        Translations will unfold here.
                                    </h2>
                                    <p className="mt-4 max-w-md text-sm leading-relaxed text-muted-foreground">
                                        Each result arrives with a confidence
                                        reading and a feedback channel — your
                                        approval teaches the engine.
                                    </p>
                                </div>
                            </div>
                        )}

                        {loading && (
                            <div
                                data-testid="loading-state"
                                className="sharp flex items-center gap-4 border border-border bg-card p-10"
                            >
                                <Loader2 className="h-5 w-5 animate-spin text-primary" />
                                <div>
                                    <div className="label-tiny text-muted-foreground">
                                        consulting the scrolls
                                    </div>
                                    <p className="mt-1 text-sm text-muted-foreground">
                                        Preparing your translations...
                                    </p>
                                </div>
                            </div>
                        )}

                        {result && !loading && (
                            <div
                                data-testid="results-panel"
                                className="space-y-5"
                            >
                                {result.results.map((r, idx) => (
                                    <TranslationCard
                                        key={`${result.id}-${r.language}`}
                                        result={r}
                                        itemId={result.id}
                                        onFeedback={handleFeedback}
                                        delay={idx * 90}
                                    />
                                ))}
                            </div>
                        )}
                    </div>
                </section>
            </main>

            <HistorySheet
                open={historyOpen}
                onOpenChange={setHistoryOpen}
                items={history}
                onRefresh={fetchHistory}
                onLoad={loadFromHistory}
            />

            <Toaster
                position="bottom-right"
                toastOptions={{ className: "sharp" }}
            />
        </div>
    );
}

function App() {
    return (
        <ThemeProvider>
            <Translator />
        </ThemeProvider>
    );
}

export default App;
