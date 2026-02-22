import { Dialog, DialogContent, DialogHeader, DialogTitle } from "@/components/ui/dialog";
import { Badge } from "@/components/ui/badge";

interface Shortcut {
  keys: string[];
  description: string;
}

const SHORTCUTS: Shortcut[] = [
  { keys: ["Ctrl", "K"], description: "Focus ticker search" },
  { keys: ["Ctrl", "H"], description: "Toggle analysis history" },
  { keys: ["Ctrl", "B"], description: "Toggle watchlist sidebar" },
  { keys: ["Enter"], description: "Run analysis" },
  { keys: ["Escape"], description: "Close history / dismiss" },
  { keys: ["?"], description: "Show this help" },
];

interface Props {
  open: boolean;
  onClose: () => void;
}

export function ShortcutsModal({ open, onClose }: Props) {
  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-sm">
        <DialogHeader>
          <DialogTitle className="text-sm font-bold uppercase tracking-widest text-muted-foreground">
            Keyboard Shortcuts
          </DialogTitle>
        </DialogHeader>
        <div className="space-y-2 py-2">
          {SHORTCUTS.map((shortcut) => (
            <div key={shortcut.description} className="flex items-center justify-between gap-4">
              <span className="text-sm text-muted-foreground">{shortcut.description}</span>
              <div className="flex items-center gap-1 shrink-0">
                {shortcut.keys.map((key) => (
                  <Badge
                    key={key}
                    variant="outline"
                    className="font-mono text-xs px-1.5 py-0.5 border-border"
                  >
                    {key}
                  </Badge>
                ))}
              </div>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  );
}
