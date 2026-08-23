import type { Metadata } from "next";
import { PRODUCT_DESCRIPTION, PRODUCT_NAME } from "@/lib/brand";
import { LOGO_URL } from "@/lib/demo-data";
import { Button } from "@/components/ui/Button";

export const metadata: Metadata = {
  title: "Sign in",
};

export default function LoginPage() {
  return (
    <div className="min-h-screen bg-background flex flex-col">
      <main className="flex-1 flex items-center justify-center p-sm md:p-lg">
        <div className="w-full max-w-md bg-surface-container-lowest border border-outline-variant rounded-xl shadow-sm p-lg flex flex-col gap-md">
          <div className="flex items-center gap-xs">
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img alt={`${PRODUCT_NAME} emblem`} className="h-8 w-auto object-contain" src={LOGO_URL} />
            <span className="font-headline-sm text-headline-sm text-primary tracking-tight">
              {PRODUCT_NAME}
            </span>
          </div>
          <div>
            <h1 className="font-headline-md text-headline-md text-on-surface">Sign in</h1>
            <p className="text-body-md text-on-surface-variant mt-xs">{PRODUCT_DESCRIPTION}</p>
          </div>
          <label className="flex flex-col gap-base">
            <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">Email</span>
            <input
              type="email"
              defaultValue="admin@locateme.local"
              className="px-sm py-sm bg-surface-container-low border border-outline-variant rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </label>
          <label className="flex flex-col gap-base">
            <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">Password</span>
            <input
              type="password"
              defaultValue="demo"
              className="px-sm py-sm bg-surface-container-low border border-outline-variant rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary"
            />
          </label>
          <Button href="/dashboard">Continue to {PRODUCT_NAME}</Button>
        </div>
      </main>
      <footer className="p-sm text-center text-label-sm text-on-surface-variant">
        {PRODUCT_NAME}
      </footer>
    </div>
  );
}
