"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/PageHeader";

import { fetchAlerts } from "@/lib/api";

import type { AlertItem } from "@/lib/demo-data";

import { cn } from "@/lib/cn";


const SEVERITY = {
  critical: "bg-error/10 text-error",
  high: "bg-secondary-container text-on-secondary-container",
  info: "bg-success/10 text-success",
};


export default function AlertsPage() {
  // IMPORTANT:
  // Start empty.
  // Never fall back to demo alerts.
  const [alerts, setAlerts] =
    useState<AlertItem[]>([]);

  const [loading, setLoading] =
    useState(true);


  // =========================================================
  // LOAD REAL ALERTS
  // =========================================================

  useEffect(() => {
    let active = true;

    const load = async () => {
      try {
        setLoading(true);

        const data =
          await fetchAlerts();

        if (!active) {
          return;
        }

        if (Array.isArray(data)) {
          setAlerts(data);
        } else {
          setAlerts([]);
        }

      } catch (error) {
        console.error(
          "Failed to load alerts:",
          error
        );

        // Never show demo data on API failure.
        if (active) {
          setAlerts([]);
        }

      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    load();

    return () => {
      active = false;
    };
  }, []);


  return (
    <>
      <PageHeader
        title="Alerts"
        description="High-confidence matches and verification events that require operator attention."
      />


      <Card className="overflow-hidden">

        {/* =====================================================
            LOADING
        ===================================================== */}

        {loading ? (

          <div className="p-xl flex flex-col items-center justify-center text-center">

            <span className="material-symbols-outlined text-[40px] text-on-surface-variant">
              sync
            </span>

            <p className="font-headline-sm text-headline-sm mt-md">
              Loading alerts...
            </p>

            <p className="text-label-sm text-on-surface-variant mt-xs">
              Fetching live alert records.
            </p>

          </div>

        ) : alerts.length === 0 ? (

          /* ===================================================
             EMPTY STATE
          =================================================== */

          <div className="p-xl flex flex-col items-center justify-center text-center">

            <span className="material-symbols-outlined text-[40px] text-outline">
              notifications_none
            </span>

            <p className="font-headline-sm text-headline-sm mt-md">
              No alerts
            </p>

            <p className="text-label-sm text-on-surface-variant mt-xs">
              There are currently no alerts requiring operator attention.
            </p>

          </div>

        ) : (

          /* ===================================================
             REAL ALERTS
          =================================================== */

          <div className="divide-y divide-surface-variant/50">

            {alerts.map((alert) => (

              <article
                key={alert.id}
                className="p-md flex flex-col md:flex-row md:items-start gap-sm"
              >

                {/* =================================================
                    SEVERITY
                ================================================= */}

                <span
                  className={cn(
                    "inline-flex items-center px-2 py-1 rounded-md font-label-bold text-[10px] uppercase tracking-wide w-fit",

                    SEVERITY[
                      alert.severity as keyof typeof SEVERITY
                    ] || SEVERITY.info
                  )}
                >
                  {alert.severity}
                </span>


                {/* =================================================
                    ALERT DETAILS
                ================================================= */}

                <div className="flex-1">

                  <h2 className="font-headline-sm text-[16px] leading-tight">
                    {alert.title}
                  </h2>

                  <p className="text-body-md text-on-surface-variant mt-base">
                    {alert.detail}
                  </p>

                  <p className="font-mono-data text-mono-data text-on-surface-variant mt-xs">
                    {alert.id} · {alert.caseId}
                  </p>

                </div>


                {/* =================================================
                    TIME
                ================================================= */}

                <span className="font-mono-data text-mono-data text-on-surface-variant">
                  {alert.time}
                </span>

              </article>

            ))}

          </div>

        )}

      </Card>
    </>
  );
}