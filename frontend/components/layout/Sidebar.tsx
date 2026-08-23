"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { NAV_ITEMS } from "@/lib/nav";
import { PRODUCT_NAME } from "@/lib/brand";
import { LOGO_URL } from "@/lib/demo-data";
import { cn } from "@/lib/cn";

type SidebarProps = {
  open: boolean;
  onClose: () => void;
};

export function Sidebar({ open, onClose }: SidebarProps) {
  const pathname = usePathname();

  return (
    <>
      <div
        className={cn(
          "fixed inset-0 bg-primary/40 z-40 lg:hidden transition-opacity",
          open ? "opacity-100" : "opacity-0 pointer-events-none",
        )}
        onClick={onClose}
        aria-hidden
      />
      <aside
        className={cn(
          "fixed left-0 top-0 h-full w-72 bg-surface-container-lowest z-50 flex flex-col border-r border-outline-variant transition-transform lg:translate-x-0",
          open ? "translate-x-0" : "-translate-x-full",
        )}
      >
        <div className="p-lg flex items-center gap-xs border-b border-outline-variant">
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img alt={`${PRODUCT_NAME} emblem`} className="h-8 w-auto object-contain" src={LOGO_URL} />
          <span className="font-headline-sm text-headline-sm text-primary tracking-tight">
            {PRODUCT_NAME}
          </span>
        </div>
        <nav className="flex-1 px-sm py-md space-y-base overflow-y-auto">
          {NAV_ITEMS.map((item) => {
            const active = pathname === item.href;
            return (
              <Link
                key={item.href}
                href={item.href}
                onClick={onClose}
                aria-current={active ? "page" : undefined}
                className={cn(
                  "flex items-center gap-sm px-md py-sm rounded-lg transition-all",
                  active
                    ? "bg-secondary-container text-on-secondary-container font-label-bold"
                    : "text-on-surface-variant hover:bg-surface-container hover:text-on-surface",
                )}
              >
                <span className="material-symbols-outlined">{item.icon}</span>
                <span className="font-body-md">{item.label}</span>
              </Link>
            );
          })}
        </nav>
        <div className="px-md py-sm border-t border-outline-variant">
          <p className="font-label-bold text-label-bold uppercase text-on-surface-variant">
            {PRODUCT_NAME}
          </p>
          <p className="text-label-sm text-on-surface-variant mt-base">Command center</p>
        </div>
      </aside>
    </>
  );
}
