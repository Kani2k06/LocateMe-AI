import { cn } from "@/lib/cn";

export function ConfidenceMeter({ value }: { value: number }) {
  const pct = Math.round(value * 100);
  const high = pct >= 90;
  const barColor = high ? "bg-error" : pct >= 80 ? "bg-primary-container" : "bg-outline";

  return (
    <div className="min-w-[120px]">
      <div className="flex items-center justify-between mb-1">
        <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">
          Confidence
        </span>
        <span className={cn("font-mono-data text-mono-data", high ? "text-error" : "text-on-surface")}>
          {pct}%
        </span>
      </div>
      <div className="h-1.5 rounded-full bg-surface-container overflow-hidden">
        <div className={cn("h-full rounded-full", barColor)} style={{ width: `${pct}%` }} />
      </div>
    </div>
  );
}

export function Pagination({
  from,
  to,
  total,
}: {
  from: number;
  to: number;
  total: number;
}) {
  return (
    <div className="bg-surface-container-low p-sm px-md flex items-center justify-between border-t border-surface-variant text-label-sm text-on-surface-variant">
      <span>
        Showing {from}-{to} of {total} records
      </span>
      <div className="flex gap-xs">
        <button
          className="p-xs rounded hover:bg-surface-container transition-colors disabled:opacity-50"
          disabled
          type="button"
          aria-label="Previous page"
        >
          <span className="material-symbols-outlined text-[20px]">chevron_left</span>
        </button>
        <button className="w-8 h-8 rounded bg-primary text-on-primary font-label-bold shadow-sm" type="button">
          1
        </button>
        <button className="w-8 h-8 rounded hover:bg-surface-container transition-colors hidden sm:inline-flex items-center justify-center" type="button">
          2
        </button>
        <button className="w-8 h-8 rounded hover:bg-surface-container transition-colors hidden sm:inline-flex items-center justify-center" type="button">
          3
        </button>
        <span className="px-2 self-center hidden sm:inline">...</span>
        <button className="w-8 h-8 rounded hover:bg-surface-container transition-colors hidden sm:inline-flex items-center justify-center" type="button">
          12
        </button>
        <button className="p-xs rounded hover:bg-surface-container transition-colors" type="button" aria-label="Next page">
          <span className="material-symbols-outlined text-[20px]">chevron_right</span>
        </button>
      </div>
    </div>
  );
}

export function Avatar({
  src,
  alt,
  size = "md",
}: {
  src: string | null;
  alt: string;
  size?: "sm" | "md" | "lg";
}) {
  const dim = size === "sm" ? "w-9 h-9" : size === "lg" ? "w-16 h-16" : "w-10 h-10";

  if (!src) {
    return (
      <div className={cn(dim, "rounded-full bg-surface-container flex items-center justify-center shadow-sm shrink-0")}>
        <span className="material-symbols-outlined text-outline">person</span>
      </div>
    );
  }

  return (
    // eslint-disable-next-line @next/next/no-img-element
    <img
      src={src}
      alt={alt}
      className={cn(dim, "rounded-full object-cover shadow-sm shrink-0")}
    />
  );
}
