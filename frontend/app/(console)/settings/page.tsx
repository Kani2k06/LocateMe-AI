"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { fetchSettings, updateSettings } from "@/lib/api";

export default function SettingsPage() {
  const [threshold, setThreshold] = useState(80);
  const [alertThreshold, setAlertThreshold] = useState(90);
  const [supabaseConnected, setSupabaseConnected] = useState(false);
  const [savedMessage, setSavedMessage] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      const data = await fetchSettings();
      if (data) {
        setThreshold(Math.round((data.similarity_threshold || 0.8) * 100));
        setAlertThreshold(Math.round((data.alert_threshold || 0.9) * 100));
        setSupabaseConnected(Boolean(data.supabase_connected));
      }
    };
    load();
  }, []);

  const handleSave = async () => {
    const updated = await updateSettings({
      similarity_threshold: threshold / 100,
      alert_threshold: alertThreshold / 100,
    });
    if (updated) {
      setSavedMessage("Settings saved successfully.");
      setTimeout(() => setSavedMessage(null), 3000);
    }
  };

  return (
    <>
      <PageHeader
        title="Settings"
        description="Match thresholds and command-center preferences. Synchronized with the FastAPI recognition service."
      />

      {savedMessage ? (
        <div className="p-sm bg-success/10 text-success border border-success/20 rounded-lg text-body-md">
          {savedMessage}
        </div>
      ) : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
        <Card className="p-md flex flex-col gap-md">
          <h2 className="font-headline-sm text-headline-sm">Recognition</h2>
          <label className="flex flex-col gap-xs">
            <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">
              Similarity threshold
            </span>
            <div className="flex items-center gap-sm">
              <input
                type="range"
                min={50}
                max={99}
                value={threshold}
                onChange={(event) => setThreshold(Number(event.target.value))}
                className="flex-1 accent-primary"
              />
              <span className="font-mono-data text-mono-data w-12">{threshold}%</span>
            </div>
            <span className="text-label-sm text-on-surface-variant">
              CCTV embeddings below this score will not create detection records.
            </span>
          </label>

          <label className="flex items-center gap-sm text-body-md">
            <input
              type="checkbox"
              checked={alertThreshold <= threshold + 10}
              onChange={(e) => setAlertThreshold(e.target.checked ? 90 : 95)}
              className="accent-primary"
            />
            Alert operators on matches at or above 90%
          </label>

          <Button onClick={handleSave} className="w-fit">
            Save preferences
          </Button>
        </Card>

        <Card className="p-md flex flex-col gap-sm">
          <h2 className="font-headline-sm text-headline-sm">Integrations</h2>
          <Row label="FastAPI vision service" value="Connected (localhost:8000)" isGood />
          <Row label="Face embedding engine" value="Active (512-d ArcFace/SFace)" isGood />
          <Row
            label="Supabase PostgreSQL"
            value={supabaseConnected ? "Connected" : "Local Repository Active"}
          />
          <Row
            label="Supabase Storage"
            value={supabaseConnected ? "Connected" : "Local Storage (/static)"}
          />
        </Card>
      </div>
    </>
  );
}

function Row({ label, value, isGood }: { label: string; value: string; isGood?: boolean }) {
  return (
    <div className="flex items-center justify-between gap-sm py-xs border-b border-surface-variant/60 last:border-0">
      <span className="text-body-md">{label}</span>
      <span className={`font-mono-data text-mono-data ${isGood ? "text-success" : "text-on-surface-variant"}`}>
        {value}
      </span>
    </div>
  );
}
