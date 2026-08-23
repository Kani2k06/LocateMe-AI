import { cn } from "@/lib/cn";
import type { CaseStatus } from "@/lib/demo-data";

type StatusBadgeProps = {
  status: CaseStatus | "pending" | "verified" | "rejected" | "queued" | "extracting" | "matching" | "complete";
};

const STYLES: Record<string, { className: string; label: string; pulse?: boolean }> = {
  active_alert: {
    className: "bg-error/10 text-error",
    label: "Active Alert",
    pulse: true,
  },
  found_safe: {
    className: "bg-surface-variant text-on-surface-variant",
    label: "Found Safe",
  },
  pending_verification: {
    className: "bg-secondary-container text-on-secondary-container",
    label: "Pending Verification",
  },
  pending: {
    className: "bg-surface-container text-on-surface-variant",
    label: "Pending",
  },
  verified: {
    className: "bg-success/10 text-success",
    label: "Verified",
  },
  rejected: {
    className: "bg-error/10 text-error",
    label: "Rejected",
  },
  queued: {
    className: "bg-surface-container text-on-surface-variant",
    label: "Queued",
  },
  extracting: {
    className: "bg-secondary-container text-on-secondary-container",
    label: "Extracting Frames",
  },
  matching: {
    className: "bg-secondary-container text-on-secondary-container",
    label: "Matching",
  },
  complete: {
    className: "bg-success/10 text-success",
    label: "Complete",
  },
};

export function StatusBadge({ status }: StatusBadgeProps) {
  const style = STYLES[status] ?? STYLES.pending;

  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-1 rounded-md font-label-bold text-[10px] uppercase tracking-wide",
        style.className,
      )}
    >
      {style.pulse ? (
        <span className="w-1.5 h-1.5 rounded-full bg-error mr-1.5 animate-pulse" />
      ) : null}
      {style.label}
    </span>
  );
}
