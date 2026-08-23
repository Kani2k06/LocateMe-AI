import Link from "next/link";
import { cn } from "@/lib/cn";

type ButtonVariant = "primary" | "secondary" | "ghost" | "destructive";

type ButtonProps = {
  children: React.ReactNode;
  variant?: ButtonVariant;
  className?: string;
  href?: string;
  type?: "button" | "submit";
  onClick?: () => void;
  disabled?: boolean;
};

const variants: Record<ButtonVariant, string> = {
  primary:
    "bg-primary text-on-primary hover:bg-tertiary-container shadow-md",
  secondary:
    "bg-secondary-container text-on-secondary-container hover:bg-tertiary-fixed-dim shadow-sm",
  ghost:
    "bg-surface-container text-on-surface hover:bg-surface-variant shadow-sm",
  destructive: "bg-error text-on-error hover:bg-on-error-container shadow-sm",
};

export function Button({
  children,
  variant = "primary",
  className,
  href,
  type = "button",
  onClick,
  disabled,
}: ButtonProps) {
  const classes = cn(
    "inline-flex items-center justify-center gap-xs px-md py-sm rounded-lg font-label-bold text-label-bold uppercase tracking-wide transition-colors disabled:opacity-50",
    variants[variant],
    className,
  );

  if (href) {
    return (
      <Link href={href} className={classes}>
        {children}
      </Link>
    );
  }

  return (
    <button type={type} onClick={onClick} disabled={disabled} className={classes}>
      {children}
    </button>
  );
}
