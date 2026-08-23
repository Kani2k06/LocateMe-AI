"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { StatCard, Card } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ConfidenceMeter, Avatar } from "@/components/ui/ConfidenceMeter";
import { Icon } from "@/components/ui/Icon";

import {
  fetchDashboardStats,
  fetchDetections,
  fetchAlerts,
} from "@/lib/api";

import type {
  Detection,
  AlertItem,
} from "@/lib/demo-data";

export default function DashboardPage() {
  const [stats, setStats] = useState<any[]>([]);
  const [recentDetections, setRecentDetections] = useState<Detection[]>([]);
  const [alerts, setAlerts] = useState<AlertItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;

    const loadDashboard = async () => {
      try {
        setLoading(true);

        const [
          statsData,
          detectionsData,
          alertsData,
        ] = await Promise.all([
          fetchDashboardStats(),
          fetchDetections(),
          fetchAlerts(),
        ]);

        if (!mounted) return;

        // --------------------------------------------------
        // LIVE STATISTICS
        // --------------------------------------------------

        if (statsData?.stats) {
          setStats(statsData.stats);
        } else if (Array.isArray(statsData)) {
          setStats(statsData);
        } else {
          setStats([]);
        }

        // --------------------------------------------------
        // LIVE DETECTIONS
        // IMPORTANT:
        // Do NOT fall back to demo data.
        // --------------------------------------------------

        if (Array.isArray(detectionsData)) {
          setRecentDetections(
            detectionsData.slice(0, 3)
          );
        } else {
          setRecentDetections([]);
        }

        // --------------------------------------------------
        // LIVE ALERTS
        // IMPORTANT:
        // Do NOT fall back to demo data.
        // --------------------------------------------------

        if (Array.isArray(alertsData)) {
          setAlerts(alertsData);
        } else {
          setAlerts([]);
        }
      } catch (error) {
        console.error(
          "Failed to load dashboard:",
          error
        );

        if (mounted) {
          setStats([]);
          setRecentDetections([]);
          setAlerts([]);
        }
      } finally {
        if (mounted) {
          setLoading(false);
        }
      }
    };

    loadDashboard();

    return () => {
      mounted = false;
    };
  }, []);

  return (
    <>
      <PageHeader
        title="Operations Dashboard"
        description="Live overview of missing-person cases, CCTV match activity, and verification queue."
        actions={
          <>
            <Button
              variant="secondary"
              href="/cctv-analysis"
              className="flex-1 md:flex-none"
            >
              <Icon
                name="videocam"
                className="text-[20px]"
              />
              Upload CCTV
            </Button>

            <Button
              href="/register-person"
              className="flex-1 md:flex-none"
            >
              <Icon
                name="person_add"
                className="text-[20px]"
              />
              Register Person
            </Button>
          </>
        }
      />

      {/* =====================================================
          STATISTICS
      ===================================================== */}

      <div className="grid grid-cols-1 sm:grid-cols-2 xl:grid-cols-4 gap-sm">
        {loading ? (
          <>
            <StatCard
              label="Active Cases"
              value="..."
              hint="Loading live data"
              icon={
                <Icon
                  name="person_search"
                  className="text-[22px]"
                />
              }
            />

            <StatCard
              label="Matches Today"
              value="..."
              hint="Loading live data"
              icon={
                <Icon
                  name="biotech"
                  className="text-[22px]"
                />
              }
            />

            <StatCard
              label="Open Alerts"
              value="..."
              hint="Loading live data"
              icon={
                <Icon
                  name="notifications"
                  className="text-[22px]"
                />
              }
            />

            <StatCard
              label="CCTV Jobs"
              value="..."
              hint="Loading live data"
              icon={
                <Icon
                  name="videocam"
                  className="text-[22px]"
                />
              }
            />
          </>
        ) : stats.length > 0 ? (
          stats.map((stat) => (
            <StatCard
              key={stat.label}
              label={stat.label}
              value={stat.value}
              hint={stat.hint}
              icon={
                <Icon
                  name={stat.icon}
                  className="text-[22px]"
                />
              }
            />
          ))
        ) : (
          <div className="xl:col-span-4 text-label-sm text-on-surface-variant p-md">
            No live dashboard statistics available.
          </div>
        )}
      </div>

      {/* =====================================================
          RECENT DETECTIONS + ALERTS
      ===================================================== */}

      <div className="grid grid-cols-1 xl:grid-cols-3 gap-md">

        {/* ===================================================
            RECENT DETECTIONS
        =================================================== */}

        <Card className="xl:col-span-2 overflow-hidden">

          <div className="px-md py-sm border-b border-outline-variant flex items-center justify-between">
            <h2 className="font-headline-sm text-headline-sm">
              Recent detections
            </h2>

            <Link
              href="/detections"
              className="text-label-sm text-on-secondary-container font-label-bold"
            >
              View all
            </Link>
          </div>

          <div className="divide-y divide-surface-variant/50">

            {loading ? (
              <div className="p-md text-label-sm text-on-surface-variant">
                Loading live detections...
              </div>
            ) : recentDetections.length === 0 ? (
              <div className="p-xl text-center">

                <Icon
                  name="search_off"
                  className="text-[32px] text-outline"
                />

                <p className="font-headline-sm mt-sm">
                  No recent detections
                </p>

                <p className="text-label-sm text-on-surface-variant mt-xs">
                  CCTV detection results will appear here
                  after processing.
                </p>

              </div>
            ) : (
              recentDetections.map((item) => (
                <div
                  key={item.id}
                  className="p-md flex flex-col sm:flex-row sm:items-center gap-sm"
                >

                  <Avatar
                    src={item.personPhoto}
                    alt={item.personName}
                  />

                  <div className="flex-1 min-w-0">

                    <p className="font-headline-sm text-[16px] leading-tight">
                      {item.personName}
                    </p>

                    <p className="text-label-sm text-on-surface-variant truncate">
                      {item.location} · {item.cameraId}
                    </p>

                  </div>

                  <ConfidenceMeter
                    value={item.confidence}
                  />

                  <StatusBadge
                    status={item.verificationStatus}
                  />

                </div>
              ))
            )}

          </div>
        </Card>

        {/* ===================================================
            ALERTS
        =================================================== */}

        <Card>

          <div className="px-md py-sm border-b border-outline-variant">
            <h2 className="font-headline-sm text-headline-sm">
              Alerts
            </h2>
          </div>

          <div className="divide-y divide-surface-variant/50">

            {loading ? (
              <div className="p-md text-label-sm text-on-surface-variant">
                Loading live alerts...
              </div>
            ) : alerts.length === 0 ? (
              <div className="p-xl text-center">

                <Icon
                  name="notifications_none"
                  className="text-[32px] text-outline"
                />

                <p className="font-headline-sm mt-sm">
                  No open alerts
                </p>

                <p className="text-label-sm text-on-surface-variant mt-xs">
                  New verification alerts will appear here.
                </p>

              </div>
            ) : (
              alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="p-md"
                >

                  <div className="flex items-center justify-between gap-sm">

                    <p className="font-label-bold text-label-bold uppercase">
                      {alert.title}
                    </p>

                    <span className="font-mono-data text-mono-data text-on-surface-variant">
                      {alert.time}
                    </span>

                  </div>

                  <p className="text-body-md text-on-surface-variant mt-xs">
                    {alert.detail}
                  </p>

                </div>
              ))
            )}

          </div>
        </Card>

      </div>
    </>
  );
}