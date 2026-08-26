import * as React from "react";
import { cn } from "@/lib/utils";

export interface BadgeProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: "default" | "success" | "warning" | "danger" | "info" | "purple" | "outline";
  size?: "sm" | "md";
}

export function Badge({ className, variant = "default", size = "sm", ...props }: BadgeProps) {
  const baseStyles = "inline-flex items-center font-semibold transition-colors rounded-full";

  const variantStyles = {
    default: "bg-slate-800 text-slate-200 border border-slate-700",
    success: "bg-emerald-500/15 text-emerald-300 border border-emerald-500/30",
    warning: "bg-amber-500/15 text-amber-300 border border-amber-500/30",
    danger: "bg-rose-500/15 text-rose-300 border border-rose-500/30",
    info: "bg-blue-500/15 text-blue-300 border border-blue-500/30",
    purple: "bg-purple-500/15 text-purple-300 border border-purple-500/30",
    outline: "border border-slate-700 text-slate-400",
  };

  const sizeStyles = {
    sm: "px-2.5 py-0.5 text-[11px]",
    md: "px-3 py-1 text-xs",
  };

  return <div className={cn(baseStyles, variantStyles[variant], sizeStyles[size], className)} {...props} />;
}
