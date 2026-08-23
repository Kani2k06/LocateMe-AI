"use client";

import { useState } from "react";
import { PRODUCT_NAME } from "@/lib/brand";
import { Sidebar } from "./Sidebar";
import { Header } from "./Header";

export function AppShell({ children }: { children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <div className="bg-background min-h-screen font-body-md text-on-background">
      <Sidebar open={open} onClose={() => setOpen(false)} />
      <div className="lg:pl-72">
        <Header onMenu={() => setOpen(true)} />
        <main className="relative pt-16 min-h-screen flex flex-col">
          <div className="flex flex-col w-full p-sm md:p-lg gap-lg flex-1">{children}</div>
          <footer className="px-sm md:px-lg pb-sm text-label-sm text-on-surface-variant">
            {PRODUCT_NAME}
          </footer>
        </main>
      </div>
    </div>
  );
}
