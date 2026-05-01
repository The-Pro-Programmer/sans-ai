import React, { useState } from "react";
import { Copy, ThumbsUp, ThumbsDown, Check, Sparkles, Pen } from "lucide-react";
import { Button } from "./ui/button";
import { Progress } from "./ui/progress";
import { Textarea } from "./ui/textarea";
import { toast } from "sonner";

const LABELS = {
    marathi: { name: "Marathi", native: "मराठी" },
    hindi: { name: "Hindi", native: "हिन्दी" },
    english: { name: "English", native: "English" },
};

export const TranslationCard = ({ result, itemId, onFeedback, delay = 0 }) => {
    const [copied, setCopied] = useState(false);
    const [feedback, setFeedback] = useState(null); // "up" | "down" | null
    const [showCorrection, setShowCorrection] = useState(false);
    const [correction, setCorrection] = useState("");
    const [submitting, setSubmitting] = useState(false);

    const label = LABELS[result.language] || { name: result.language, native: "" };

    const copyToClipboard = async () => {
        try {
            await navigator.clipboard.writeText(result.translation);
            setCopied(true);
            toast.success(`Copied ${label.name} translation`);
            setTimeout(() => setCopied(false), 1500);
        } catch {
            toast.error("Failed to copy");
        }
    };

    const handleUp = async () => {
        if (feedback) return;
        setSubmitting(true);
        await onFeedback({
            item_id: itemId,
            language: result.language,
            is_correct: true,
        });
        setFeedback("up");
        setSubmitting(false);
        toast.success("Thanks — marked as correct.");
    };

    const handleDown = () => {
        if (feedback) return;
        setShowCorrection(true);
    };

    const submitCorrection = async () => {
        if (!correction.trim()) {
            toast.error("Enter a correction first");
            return;
        }
        setSubmitting(true);
        await onFeedback({
            item_id: itemId,
            language: result.language,
            is_correct: false,
            correction: correction.trim(),
        });
        setFeedback("down");
        setShowCorrection(false);
        setSubmitting(false);
        toast.success("Correction saved — future translations will use it.");
    };

    const confColor =
        result.confidence >= 80
            ? "text-primary"
            : result.confidence >= 50
              ? "text-foreground"
              : "text-muted-foreground";

    return (
        <article
            data-testid={`translation-card-${result.language}`}
            className="hover-lift stagger-in sharp border border-border bg-card p-6 sm:p-7"
            style={{ animationDelay: `${delay}ms` }}
        >
            <div className="flex items-start justify-between gap-4">
                <div>
                    <div className="label-tiny text-muted-foreground">
                        {label.name}
                    </div>
                    <div className="font-display text-xl text-foreground/80">
                        {label.native}
                    </div>
                </div>
                {result.source === "correction" && (
                    <span
                        data-testid={`source-badge-${result.language}`}
                        className="label-tiny inline-flex items-center gap-1 border border-primary/40 px-2 py-1 text-primary"
                    >
                        <Sparkles className="h-3 w-3" />
                        learned
                    </span>
                )}
            </div>

            <p
                data-testid={`translated-text-${result.language}`}
                className={`mt-5 text-lg leading-relaxed text-foreground ${
                    result.language !== "english" ? "font-devanagari" : ""
                }`}
            >
                {result.translation}
            </p>

            <div className="mt-6 space-y-2">
                <div className="flex items-center justify-between">
                    <span className="label-tiny text-muted-foreground">
                        confidence
                    </span>
                    <span
                        data-testid={`confidence-${result.language}`}
                        className={`text-sm font-medium ${confColor}`}
                    >
                        {result.confidence.toFixed(1)}%
                    </span>
                </div>
                <Progress
                    value={result.confidence}
                    className="confidence-bar sharp bg-muted"
                />
            </div>

            <div className="mt-6 flex items-center gap-1 border-t border-border pt-4">
                <Button
                    data-testid={`copy-btn-${result.language}`}
                    variant="ghost"
                    size="sm"
                    onClick={copyToClipboard}
                    className="icon-btn gap-2 text-foreground"
                >
                    {copied ? (
                        <Check className="h-4 w-4" />
                    ) : (
                        <Copy className="h-4 w-4" />
                    )}
                    <span className="label-tiny">
                        {copied ? "copied" : "copy"}
                    </span>
                </Button>
                <div className="ml-auto flex items-center gap-1">
                    <Button
                        data-testid={`thumbs-up-btn-${result.language}`}
                        variant="ghost"
                        size="sm"
                        onClick={handleUp}
                        disabled={submitting || feedback !== null}
                        className={`icon-btn gap-2 ${
                            feedback === "up" ? "text-primary opacity-100" : ""
                        }`}
                    >
                        <ThumbsUp className="h-4 w-4" />
                    </Button>
                    <Button
                        data-testid={`thumbs-down-btn-${result.language}`}
                        variant="ghost"
                        size="sm"
                        onClick={handleDown}
                        disabled={submitting || feedback !== null}
                        className={`icon-btn gap-2 ${
                            feedback === "down" ? "text-destructive opacity-100" : ""
                        }`}
                    >
                        <ThumbsDown className="h-4 w-4" />
                    </Button>
                </div>
            </div>

            {showCorrection && (
                <div
                    data-testid={`correction-panel-${result.language}`}
                    className="stagger-in mt-4 border border-primary/30 bg-secondary/50 p-4"
                >
                    <div className="label-tiny mb-2 flex items-center gap-2 text-muted-foreground">
                        <Pen className="h-3 w-3" />
                        provide correct translation
                    </div>
                    <Textarea
                        data-testid={`correction-input-${result.language}`}
                        value={correction}
                        onChange={(e) => setCorrection(e.target.value)}
                        placeholder={`Correct ${label.name} translation...`}
                        className="sharp mb-3 min-h-[90px] border-border bg-background"
                    />
                    <div className="flex gap-2">
                        <Button
                            data-testid={`submit-correction-${result.language}`}
                            onClick={submitCorrection}
                            disabled={submitting}
                            className="sharp bg-primary text-primary-foreground hover:bg-primary/90"
                            size="sm"
                        >
                            Save correction
                        </Button>
                        <Button
                            variant="ghost"
                            size="sm"
                            className="sharp"
                            onClick={() => {
                                setShowCorrection(false);
                                setCorrection("");
                            }}
                            disabled={submitting}
                        >
                            Cancel
                        </Button>
                    </div>
                </div>
            )}
        </article>
    );
};

export default TranslationCard;
