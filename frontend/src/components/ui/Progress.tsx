import * as React from "react";
import { cn } from "@/lib/utils";

export function Progress({
  value = 0,
  max = 100,
  className,
  indicatorClassName,
}: {
  value?: number;
  max?: number;
  className?: string;
  indicatorClassName?: string;
}) {
  const percentage = Math.min(100, Math.max(0, (value / max) * 100));

  return (
    <div className={cn("relative h-2 w-full overflow-hidden rounded-full bg-slate-800", className)}>
      <div
        className={cn("h-full bg-gradient-to-r from-blue-500 to-indigo-500 transition-all duration-500 ease-out", indicatorClassName)}
        style={{ width: `${percentage}%` }}
      />
    </div>
  );
}
