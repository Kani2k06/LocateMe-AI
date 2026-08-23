import { PRODUCT_NAME } from "@/lib/brand";

export default function ConsoleLoading() {
  return (
    <div className="py-xl flex items-center justify-center text-on-surface-variant">
      <p className="font-headline-sm text-headline-sm text-on-surface tracking-tight">{PRODUCT_NAME}</p>
    </div>
  );
}
