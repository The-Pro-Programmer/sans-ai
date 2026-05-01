import React from "react";
import { Moon, Sun, ScrollText, History } from "lucide-react";
import { Button } from "./ui/button";
import { useTheme } from "../context/ThemeContext";

export const Header = ({ onOpenHistory }) => {
    const { theme, toggle } = useTheme();

    return (
        <header
            data-testid="app-header"
            className="glass-header sticky top-0 z-40 border-b border-border"
        >
            <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5 sm:px-10">
                <div className="flex items-center gap-3">
                    <div className="flex h-9 w-9 items-center justify-center border border-border text-primary">
                        <ScrollText className="h-4 w-4" />
                    </div>
                    <div>
                        <div className="label-tiny text-muted-foreground">
                            Saṁskṛtam
                        </div>
                        <div className="font-display text-2xl leading-none">
                            Antarवाणी
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2">
                    <Button
                        data-testid="history-btn"
                        variant="ghost"
                        size="sm"
                        onClick={onOpenHistory}
                        className="gap-2 text-foreground hover:text-primary"
                    >
                        <History className="h-4 w-4" />
                        <span className="hidden sm:inline label-tiny">
                            History
                        </span>
                    </Button>
                    <Button
                        data-testid="theme-toggle"
                        variant="ghost"
                        size="icon"
                        onClick={toggle}
                        aria-label="Toggle theme"
                        className="text-foreground hover:text-primary"
                    >
                        {theme === "dark" ? (
                            <Sun className="h-4 w-4" />
                        ) : (
                            <Moon className="h-4 w-4" />
                        )}
                    </Button>
                </div>
            </div>
        </header>
    );
};

export default Header;
