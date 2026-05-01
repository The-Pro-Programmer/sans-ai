import React, { useEffect, useState } from "react";
import axios from "axios";
import { CloudOff, Cloud, Loader2, Download } from "lucide-react";
import { Switch } from "./ui/switch";
import { toast } from "sonner";

const API = `${process.env.REACT_APP_BACKEND_URL}/api`;

/** Toggle to switch between cloud (LLM) and on-device (IndicTrans2) modes. */
export const OfflineModeToggle = ({ enabled, onChange }) => {
    const [status, setStatus] = useState({
        available: false,
        loaded: false,
        loading: false,
        error: null,
    });
    const [warming, setWarming] = useState(false);

    const refresh = async () => {
        try {
            const { data } = await axios.get(`${API}/offline/status`);
            setStatus(data);
            return data;
        } catch {
            return null;
        }
    };

    useEffect(() => {
        refresh();
        const i = setInterval(() => {
            if (status.loading || warming) refresh();
        }, 3000);
        return () => clearInterval(i);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [status.loading, warming]);

    const handleToggle = async (value) => {
        if (!value) {
            onChange(false);
            return;
        }
        if (!status.available) {
            toast.error(
                "Offline engine not installed on the server.",
            );
            return;
        }
        if (!status.loaded) {
            setWarming(true);
            toast.info(
                "Preparing on-device model (one-time download ~1.5GB). This may take a few minutes...",
            );
            try {
                const { data } = await axios.post(
                    `${API}/offline/warmup`,
                    {},
                    { timeout: 10 * 60 * 1000 },
                );
                setStatus(data);
                if (data.loaded) {
                    toast.success("On-device model ready.");
                    onChange(true);
                } else if (data.error) {
                    toast.error(`Offline load failed: ${data.error}`);
                }
            } catch (e) {
                toast.error(
                    "Model warmup timed out — try again once the download completes.",
                );
            } finally {
                setWarming(false);
            }
        } else {
            onChange(true);
        }
    };

    const Icon = enabled ? CloudOff : Cloud;
    const busy = warming || status.loading;

    let hint;
    if (!status.available) hint = "engine unavailable";
    else if (busy) hint = "downloading model…";
    else if (enabled && status.loaded) hint = "on-device";
    else if (status.loaded) hint = "ready";
    else hint = "tap to enable";

    return (
        <div
            data-testid="offline-toggle-panel"
            className="flex items-center justify-between border-t border-border pt-5"
        >
            <div className="flex items-center gap-3">
                {busy ? (
                    <Loader2 className="h-4 w-4 animate-spin text-primary" />
                ) : (
                    <Icon className="h-4 w-4 text-muted-foreground" />
                )}
                <div>
                    <div className="label-tiny text-muted-foreground">
                        offline engine
                    </div>
                    <div className="text-sm">
                        {enabled ? "IndicTrans2 (on-device)" : "Claude Sonnet 4.5 (cloud)"}
                    </div>
                </div>
            </div>
            <div className="flex items-center gap-2">
                <span className="label-tiny text-muted-foreground">
                    {hint}
                </span>
                <Switch
                    data-testid="offline-mode-toggle"
                    checked={enabled}
                    onCheckedChange={handleToggle}
                    disabled={busy || !status.available}
                />
                {!status.loaded && status.available && !busy && (
                    <Download className="hidden h-3 w-3 text-muted-foreground sm:inline" />
                )}
            </div>
        </div>
    );
};

export default OfflineModeToggle;
