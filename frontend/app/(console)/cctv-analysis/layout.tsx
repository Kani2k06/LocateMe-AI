import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "CCTV Analysis",
};

export default function CctvAnalysisLayout({ children }: { children: React.ReactNode }) {
  return children;
}
