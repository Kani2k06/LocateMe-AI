"use client";

import { PRODUCT_NAME } from "@/lib/brand";
import { CURRENT_USER } from "@/lib/demo-data";

type HeaderProps = {
  onMenu: () => void;
};

export function Header({ onMenu }: HeaderProps) {
  return (
    <header className="fixed top-0 left-0 lg:left-72 right-0 h-16 bg-surface-container-lowest/80 backdrop-blur-xl border-b border-outline-variant z-40 flex items-center justify-between px-sm md:px-lg gap-sm">
      <button
        type="button"
        className="lg:hidden p-xs text-on-surface-variant hover:bg-surface-container-high rounded-full"
        onClick={onMenu}
        aria-label="Open navigation"
      >
        <span className="material-symbols-outlined">menu</span>
      </button>
      <span className="lg:hidden font-headline-sm text-[16px] text-primary tracking-tight shrink-0">
        {PRODUCT_NAME}
      </span>
      <div className="flex-1 max-w-xl">
        <div className="relative flex items-center">
          <span className="material-symbols-outlined absolute left-sm text-outline">search</span>
          <input
            className="w-full pl-xl pr-md py-xs bg-surface-container-low border border-outline-variant rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary"
            placeholder="Search database, cases, or alerts..."
            type="search"
          />
        </div>
      </div>
      <div className="flex items-center gap-md">
        <button
          className="relative p-xs text-on-surface-variant hover:bg-surface-container-high rounded-full transition-colors"
          type="button"
          aria-label="Notifications"
        >
          <span className="material-symbols-outlined">notifications</span>
          <span className="absolute top-1 right-1 w-2 h-2 bg-error rounded-full" />
        </button>
        <div className="flex items-center gap-sm pl-md border-l border-outline-variant">
          <div className="text-right hidden lg:block">
            <p className="font-label-bold text-on-surface">{CURRENT_USER.name}</p>
            <p className="text-label-sm text-on-surface-variant">{CURRENT_USER.org}</p>
          </div>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            alt="Profile"
            className="w-9 h-9 rounded-full object-cover border border-outline-variant"
            src={CURRENT_USER.photoUrl}
          />
        </div>
      </div>
    </header>
  );
}
