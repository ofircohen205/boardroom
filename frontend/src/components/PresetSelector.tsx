import { Zap, Target, Microscope } from "lucide-react";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

export type AnalysisMode = "quick" | "standard" | "deep";

interface PresetOption {
  mode: AnalysisMode;
  label: string;
  description: string;
  icon: React.ElementType;
}

const presets: PresetOption[] = [
  {
    mode: "quick",
    label: "Quick Scan",
    description: "Technical analysis only",
    icon: Zap,
  },
  {
    mode: "standard",
    label: "Standard",
    description: "All agents (recommended)",
    icon: Target,
  },
  {
    mode: "deep",
    label: "Deep Dive",
    description: "Extended analysis",
    icon: Microscope,
  },
];

interface Props {
  value: AnalysisMode;
  onChange: (mode: AnalysisMode) => void;
  disabled?: boolean;
}

export function PresetSelector({ value, onChange, disabled }: Props) {
  return (
    <div className="flex gap-2">
      {presets.map((preset) => {
        const Icon = preset.icon;
        const isSelected = value === preset.mode;

        return (
          <Button
            key={preset.mode}
            variant={isSelected ? "default" : "outline"}
            size="sm"
            onClick={() => onChange(preset.mode)}
            disabled={disabled}
            className={cn(
              "flex flex-col items-start gap-1 h-auto py-2 px-3 transition-all",
              isSelected
                ? "bg-primary text-primary-foreground border-primary shadow-md"
                : "border-white/10 hover:bg-white/5 hover:border-primary/30"
            )}
            title={preset.description}
          >
            <div className="flex items-center gap-1.5 w-full">
              <Icon className="h-3.5 w-3.5" />
              <span className="text-xs font-semibold">{preset.label}</span>
            </div>
            <span className="text-[10px] opacity-70 font-normal">
              {preset.description}
            </span>
          </Button>
        );
      })}
    </div>
  );
}
