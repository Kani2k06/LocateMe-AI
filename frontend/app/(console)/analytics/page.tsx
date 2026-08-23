"use client";

import { useEffect, useState } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Card, StatCard } from "@/components/ui/PageHeader";
import { Icon } from "@/components/ui/Icon";
import { fetchAnalytics } from "@/lib/api";

type AnalyticsRow = {
  label: string;
  value: number;
};

type AnalyticsData = {
  matchRate: string;
  avgConfidence: string;
  medianTimeToMatch: string;
  camerasOnline: string;
  byStatus: AnalyticsRow[];
  byLocation: AnalyticsRow[];
};

const EMPTY_ANALYTICS: AnalyticsData = {
  matchRate: "0%",
  avgConfidence: "0%",
  medianTimeToMatch: "—",
  camerasOnline: "0",
  byStatus: [],
  byLocation: [],
};

export default function AnalyticsPage() {
  const [analytics, setAnalytics] =
    useState<AnalyticsData>(EMPTY_ANALYTICS);

  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const loadAnalytics = async () => {
      try {
        setLoading(true);

        const data = await fetchAnalytics();

        if (data) {
          setAnalytics({
            matchRate: String(data.matchRate ?? "0%"),
            avgConfidence: String(
              data.avgConfidence ?? "0%"
            ),
            medianTimeToMatch: String(
              data.medianTimeToMatch ?? "—"
            ),
            camerasOnline: String(
              data.camerasOnline ?? "0"
            ),

            byStatus: Array.isArray(data.byStatus)
              ? data.byStatus
              : [],

            byLocation: Array.isArray(data.byLocation)
              ? data.byLocation
              : [],
          });
        }
      } catch (error) {
        console.error(
          "Failed to load analytics:",
          error
        );
      } finally {
        setLoading(false);
      }
    };

    loadAnalytics();
  }, []);

  return (
    <>
      <PageHeader
        title="Analytics"
        description="Operational metrics for match quality, case mix, and camera coverage. Figures update in real-time as CCTV footage is processed."
      />

      {/* =====================================================
          SUMMARY STATISTICS
      ===================================================== */}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-sm">
        <StatCard
          label="Match rate"
          value={
            loading
              ? "..."
              : analytics.matchRate
          }
          hint="Faces compared vs matches"
          icon={
            <Icon
              name="percent"
              className="text-[22px]"
            />
          }
        />

        <StatCard
          label="Avg confidence"
          value={
            loading
              ? "..."
              : analytics.avgConfidence
          }
          hint="Accepted detections"
          icon={
            <Icon
              name="speed"
              className="text-[22px]"
            />
          }
        />

        <StatCard
          label="Time to match"
          value={
            loading
              ? "..."
              : analytics.medianTimeToMatch
          }
          hint="Median from upload"
          icon={
            <Icon
              name="schedule"
              className="text-[22px]"
            />
          }
        />

        <StatCard
          label="Cameras online"
          value={
            loading
              ? "..."
              : analytics.camerasOnline
          }
          hint="Network health"
          icon={
            <Icon
              name="videocam"
              className="text-[22px]"
            />
          }
        />
      </div>

      {/* =====================================================
          ANALYTICS BREAKDOWN
      ===================================================== */}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-md">
        <BarPanel
          title="Cases by status"
          rows={analytics.byStatus}
        />

        <BarPanel
          title="Last-seen locations"
          rows={analytics.byLocation}
        />
      </div>
    </>
  );
}

/* ============================================================
   BAR PANEL
============================================================ */

function BarPanel({
  title,
  rows = [],
}: {
  title: string;
  rows?: AnalyticsRow[];
}) {
  const safeRows = Array.isArray(rows)
    ? rows
    : [];

  const max = Math.max(
    ...safeRows.map(
      (row) => Number(row.value) || 0
    ),
    1
  );

  const total = safeRows.reduce(
    (sum, row) =>
      sum + (Number(row.value) || 0),
    0
  );

  return (
    <Card className="p-md">
      <div className="flex items-center justify-between mb-md">
        <h2 className="font-headline-sm text-headline-sm">
          {title}
        </h2>

        <span className="text-label-sm text-on-surface-variant">
          {total} total
        </span>
      </div>

      <div className="flex flex-col gap-md">
        {safeRows.length === 0 ? (
          <div className="text-label-sm text-on-surface-variant py-md">
            No analytics data available yet.
          </div>
        ) : (
          safeRows.map((row) => {
            const value =
              Number(row.value) || 0;

            const percentage =
              (value / max) * 100;

            return (
              <div key={row.label}>
                <div className="flex justify-between text-label-sm mb-base">
                  <span>{row.label}</span>

                  <span className="font-mono-data">
                    {value}
                  </span>
                </div>

                <div className="h-2 rounded-full bg-surface-container overflow-hidden">
                  <div
                    className="h-full rounded-full bg-primary-container transition-all duration-500"
                    style={{
                      width: `${percentage}%`,
                    }}
                  />
                </div>
              </div>
            );
          })
        )}
      </div>
    </Card>
  );
}