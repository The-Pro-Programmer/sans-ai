import React from "react";
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
    SheetDescription,
} from "./ui/sheet";
import { Button } from "./ui/button";
import { Trash2, Clock, Sparkles } from "lucide-react";
import { toast } from "sonner";
import axios from "axios";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

const formatTime = (iso) => {
    try {
        return new Date(iso).toLocaleString(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
        });
    } catch {
        return iso;
    }
};

export const HistorySheet = ({ open, onOpenChange, items, onRefresh, onLoad }) => {
    const handleClear = async () => {
        try {
            await axios.delete(`${API}/history`);
            toast.success("History cleared");
            onRefresh?.();
        } catch {
            toast.error("Failed to clear history");
        }
    };

    return (
        <Sheet open={open} onOpenChange={onOpenChange}>
            <SheetContent
                side="right"
                data-testid="history-sheet"
                className="w-full overflow-y-auto border-l border-border bg-background sm:max-w-lg"
            >
                <SheetHeader className="text-left">
                    <SheetTitle className="font-display text-3xl">
                        Translation history
                    </SheetTitle>
                    <SheetDescription className="label-tiny text-muted-foreground">
                        Your recent Sanskrit renderings
                    </SheetDescription>
                </SheetHeader>

                <div className="mt-4 flex items-center justify-between">
                    <span className="label-tiny text-muted-foreground">
                        {items.length} entries
                    </span>
                    {items.length > 0 && (
                        <Button
                            data-testid="clear-history-btn"
                            variant="ghost"
                            size="sm"
                            onClick={handleClear}
                            className="gap-2 text-destructive hover:text-destructive"
                        >
                            <Trash2 className="h-4 w-4" />
                            <span className="label-tiny">clear</span>
                        </Button>
                    )}
                </div>

                <div className="mt-6 space-y-4 pb-8">
                    {items.length === 0 && (
                        <div
                            data-testid="history-empty"
                            className="flex flex-col items-center justify-center border border-dashed border-border p-10 text-center"
                        >
                            <Clock className="mb-3 h-6 w-6 text-muted-foreground" />
                            <p className="text-sm text-muted-foreground">
                                No translations yet. Your journey begins with
                                the first verse.
                            </p>
                        </div>
                    )}

                    {items.map((item) => (
                        <button
                            key={item.id}
                            data-testid={`history-item-${item.id}`}
                            onClick={() => {
                                onLoad?.(item);
                                onOpenChange(false);
                            }}
                            className="hover-lift sharp w-full border border-border bg-card p-5 text-left"
                        >
                            <div className="mb-2 flex items-center justify-between">
                                <span className="label-tiny text-muted-foreground">
                                    {formatTime(item.timestamp)}
                                </span>
                                {(item.results || []).some(
                                    (r) => r.source === "correction",
                                ) && (
                                    <span className="label-tiny inline-flex items-center gap-1 text-primary">
                                        <Sparkles className="h-3 w-3" />
                                        learned
                                    </span>
                                )}
                            </div>
                            <p className="font-devanagari text-lg leading-snug text-foreground">
                                {item.sanskrit_text}
                            </p>
                            <div className="mt-3 flex flex-wrap gap-2">
                                {(item.results || []).map((r) => (
                                    <span
                                        key={r.language}
                                        className="label-tiny border border-border bg-secondary px-2 py-1 text-secondary-foreground"
                                    >
                                        {r.language} · {r.confidence.toFixed(0)}%
                                    </span>
                                ))}
                            </div>
                        </button>
                    ))}
                </div>
            </SheetContent>
        </Sheet>
    );
};

export default HistorySheet;
