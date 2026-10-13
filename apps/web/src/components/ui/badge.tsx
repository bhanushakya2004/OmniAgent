import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "secondary" | "outline" | "accent" | "destructive" | "warning";
}

export function Badge({
  className,
  variant = "default",
  ...props
}: BadgeProps): React.JSX.Element {
  const variants = {
    default: "bg-primary/10 text-primary border-primary/20",
    secondary: "bg-secondary text-secondary-foreground border-transparent",
    outline: "border-border text-foreground bg-transparent",
    accent: "bg-accent/15 text-emerald-700 dark:text-emerald-300 border-accent/30",
    destructive: "bg-destructive/15 text-destructive border-destructive/20",
    warning: "bg-amber-500/15 text-amber-700 dark:text-amber-300 border-amber-500/30",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 rounded-full border px-2.5 py-0.5 text-xs font-semibold tracking-wide transition-colors",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
