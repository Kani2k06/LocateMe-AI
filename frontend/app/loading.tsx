import { PRODUCT_NAME } from "@/lib/brand";

export default function Loading() {
  return (
    <div className="min-h-screen bg-background flex items-center justify-center">
      <p className="font-headline-sm text-headline-sm text-on-surface tracking-tight">{PRODUCT_NAME}</p>
    </div>
  );
}
