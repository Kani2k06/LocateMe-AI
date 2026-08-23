import type { Metadata } from "next";
import { MissingPersonsView } from "@/components/views/MissingPersonsView";

export const metadata: Metadata = {
  title: "Missing Persons",
};

export default function MissingPersonsPage() {
  return <MissingPersonsView />;
}
