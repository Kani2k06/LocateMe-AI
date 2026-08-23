import { cn } from "@/lib/cn";

type PageHeaderProps = {
  title: string;
  description: string;
  actions?: React.ReactNode;
};

export function PageHeader({ title, description, actions }: PageHeaderProps) {
  return (
    <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-md">
      <div className="flex flex-col gap-base">
        <h1 className="font-display-lg text-display-lg text-on-surface">{title}</h1>
        <p className="font-body-lg text-body-lg text-on-surface-variant max-w-2xl">
          {description}
        </p>
      </div>
      {actions ? (
        <div className="flex gap-sm w-full md:w-auto">{actions}</div>
      ) : null}
    </div>
  );
}

export function Card({
  children,
  className,
}: {
  children: React.ReactNode;
  className?: string;
}) {
  return (
    <div
      className={cn(
        "bg-surface-container-lowest border border-outline-variant/60 shadow-sm rounded-xl",
        className,
      )}
    >
      {children}
    </div>
  );
}

export function StatCard({
  label,
  value,
  hint,
  icon,
}: {
  label: string;
  value: string;
  hint: string;
  icon: React.ReactNode;
}) {
  return (
    <Card className="p-md flex items-start justify-between gap-sm">
      <div>
        <p className="font-label-bold text-label-bold uppercase text-on-surface-variant">
          {label}
        </p>
        <p className="font-display-lg text-[28px] leading-9 text-on-surface mt-xs">
          {value}
        </p>
        <p className="text-label-sm text-on-surface-variant mt-base">{hint}</p>
      </div>
      <div className="w-10 h-10 rounded-lg bg-secondary-container text-on-secondary-container flex items-center justify-center">
        {icon}
      </div>
    </Card>
  );
}
