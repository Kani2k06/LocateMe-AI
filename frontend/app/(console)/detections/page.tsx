"use client";

import { useEffect, useState } from "react";

import { PageHeader } from "@/components/ui/PageHeader";
import { Card } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { ConfidenceMeter } from "@/components/ui/ConfidenceMeter";
import { Avatar } from "@/components/ui/ConfidenceMeter";
import { Icon } from "@/components/ui/Icon";

import {
  fetchDetections,
  verifyDetection,
} from "@/lib/api";

import type { Detection } from "@/lib/demo-data";


export default function DetectionsPage() {
  // =========================================================
  // STATE
  // =========================================================

  // IMPORTANT:
  // Start with an EMPTY array.
  // Do NOT use demo/fake detection data.
  const [detections, setDetections] =
    useState<Detection[]>([]);

  const [filter, setFilter] =
    useState<string>("all");

  const [loading, setLoading] =
    useState(true);

  const [downloadingId, setDownloadingId] =
    useState<string | null>(null);


  // =========================================================
  // LOAD DETECTIONS FROM DATABASE
  // =========================================================

  const loadDetections = async () => {
    try {
      setLoading(true);

      const live = await fetchDetections(filter);

      // Only accept real API data.
      if (Array.isArray(live)) {
        setDetections(live);
      } else {
        setDetections([]);
      }

    } catch (error) {
      console.error(
        "Failed to load detections:",
        error
      );

      // Never fall back to demo data.
      setDetections([]);

    } finally {
      setLoading(false);
    }
  };


  // =========================================================
  // FILTER CHANGE
  // =========================================================

  useEffect(() => {
    loadDetections();
  }, [filter]);


  // =========================================================
  // VERIFY / REJECT DETECTION
  // =========================================================

  const handleStatusChange = async (
    id: string,
    newStatus: "verified" | "rejected"
  ) => {
    // -------------------------------------------------------
    // Optimistic update
    // -------------------------------------------------------

    setDetections((prev) =>
      prev.map((d) =>
        d.id === id
          ? {
              ...d,
              verificationStatus:
                newStatus,
            }
          : d
      )
    );

    // -------------------------------------------------------
    // Update database
    // -------------------------------------------------------

    const success =
      await verifyDetection(
        id,
        newStatus
      );

    // -------------------------------------------------------
    // If backend failed, reload actual DB state
    // -------------------------------------------------------

    if (!success) {
      await loadDetections();
    }
  };


  // =========================================================
  // DOWNLOAD VERIFIED MATCH REPORT
  // =========================================================

  const downloadMatchReport = async (
    item: Detection
  ) => {
    // Only verified detections can generate reports.
    if (
      item.verificationStatus !==
      "verified"
    ) {
      return;
    }

    setDownloadingId(item.id);

    try {
      const apiBase =
  process.env.NEXT_PUBLIC_API_URL ||
  "https://locateme-api.onrender.com";

      const response =
        await fetch(
          `${apiBase}/api/detections/${encodeURIComponent(
            item.id
          )}/report`,
          {
            method: "GET",
          }
        );

      // -----------------------------------------------------
      // Handle backend errors
      // -----------------------------------------------------

      if (!response.ok) {
        let message =
          "Unable to generate the match report.";

        try {
          const errorData =
            await response.json();

          if (errorData?.detail) {
            message =
              errorData.detail;
          }
        } catch {
          // Ignore JSON parsing errors.
        }

        throw new Error(message);
      }

      // -----------------------------------------------------
      // Get PDF binary
      // -----------------------------------------------------

      const blob =
        await response.blob();

      // -----------------------------------------------------
      // Create temporary browser URL
      // -----------------------------------------------------

      const url =
        window.URL.createObjectURL(
          blob
        );

      // -----------------------------------------------------
      // Create download link
      // -----------------------------------------------------

      const link =
        document.createElement("a");

      link.href = url;

      const safeName =
        item.personName
          .replace(
            /[^a-z0-9]/gi,
            "_"
          )
          .toLowerCase();

      link.download =
        `LocateMe_${safeName}_match_report.pdf`;

      document.body.appendChild(
        link
      );

      link.click();

      document.body.removeChild(
        link
      );

      // -----------------------------------------------------
      // Clean temporary URL
      // -----------------------------------------------------

      window.URL.revokeObjectURL(
        url
      );

    } catch (error) {
      console.error(
        "Failed to download match report:",
        error
      );

      window.alert(
        error instanceof Error
          ? error.message
          : "Unable to generate the match report."
      );

    } finally {
      setDownloadingId(null);
    }
  };


  // =========================================================
  // PAGE
  // =========================================================

  return (
    <>
      <PageHeader
        title="Detection Results"
        description="Possible matches above the configured similarity threshold. Each record pairs a registered subject with a CCTV frame and verification status."
        actions={
          <div className="flex gap-xs bg-surface-container-low p-1 rounded-lg border border-outline-variant">

            {[
              "all",
              "pending",
              "verified",
              "rejected",
            ].map((st) => (
              <button
                key={st}
                type="button"
                onClick={() =>
                  setFilter(st)
                }
                className={`px-sm py-xs rounded-md text-label-sm uppercase font-label-bold transition-colors ${
                  filter === st
                    ? "bg-primary text-on-primary shadow-sm"
                    : "text-on-surface-variant hover:text-on-surface"
                }`}
              >
                {st}
              </button>
            ))}

          </div>
        }
      />


      {/* =====================================================
          LOADING STATE
      ===================================================== */}

      {loading ? (

        <Card className="p-xl flex flex-col items-center justify-center text-center">

          <Icon
            name="sync"
            className="text-[40px] text-on-surface-variant"
          />

          <h2 className="font-headline-sm text-headline-sm mt-md">
            Loading detection results...
          </h2>

          <p className="text-body-md text-on-surface-variant mt-xs">
            Fetching live detection records.
          </p>

        </Card>

      ) : detections.length === 0 ? (

        /* ===================================================
           EMPTY STATE
        =================================================== */

        <Card className="p-xl flex flex-col items-center justify-center text-center">

          <Icon
            name="search_off"
            className="text-[40px] text-on-surface-variant"
          />

          <h2 className="font-headline-sm text-headline-sm mt-md">
            No detection results found
          </h2>

          <p className="text-body-md text-on-surface-variant mt-xs">
            There are no detection records for this
            verification status.
          </p>

        </Card>

      ) : (

        /* ===================================================
           DETECTION CARDS
        =================================================== */

        <div className="grid grid-cols-1 xl:grid-cols-2 gap-md">

          {detections.map((item) => (

            <Card
              key={item.id}
              className="p-md flex flex-col gap-md"
            >

              {/* =================================================
                  HEADER
              ================================================= */}

              <div className="flex items-start justify-between gap-sm">

                <div>

                  <p className="font-label-bold text-label-bold uppercase text-on-surface-variant">
                    {item.id}
                  </p>

                  <h2 className="font-headline-sm text-headline-sm mt-base">
                    {item.personName}
                  </h2>

                  <p className="font-mono-data text-mono-data text-on-surface-variant">
                    #{item.personId}
                  </p>

                </div>

                <StatusBadge
                  status={
                    item.verificationStatus
                  }
                />

              </div>


              {/* =================================================
                  PERSON + CCTV IMAGES
              ================================================= */}

              <div className="grid grid-cols-2 gap-sm">

                {/* PERSON PHOTO */}

                <figure className="bg-surface-container-low rounded-xl overflow-hidden border border-outline-variant">

                  <div className="aspect-[4/3] bg-surface-container flex items-center justify-center">

                    {item.personPhoto ? (

                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={
                          item.personPhoto
                        }
                        alt={
                          item.personName
                        }
                        className="w-full h-full object-cover"
                      />

                    ) : (

                      <Avatar
                        src={null}
                        alt={
                          item.personName
                        }
                        size="lg"
                      />

                    )}

                  </div>

                  <figcaption className="p-xs text-label-sm text-on-surface-variant">
                    Missing person
                  </figcaption>

                </figure>


                {/* CCTV FRAME */}

                <figure className="bg-surface-container-low rounded-xl overflow-hidden border border-outline-variant">

                  <div className="aspect-[4/3] bg-surface-container flex items-center justify-center">

                    {item.frameUrl ? (

                      // eslint-disable-next-line @next/next/no-img-element
                      <img
                        src={
                          item.frameUrl
                        }
                        alt="CCTV frame"
                        className="w-full h-full object-cover"
                      />

                    ) : (

                      <span className="material-symbols-outlined text-outline">
                        image
                      </span>

                    )}

                  </div>

                  <figcaption className="p-xs text-label-sm text-on-surface-variant">
                    CCTV frame
                  </figcaption>

                </figure>

              </div>


              {/* =================================================
                  CONFIDENCE
              ================================================= */}

              <ConfidenceMeter
                value={
                  item.confidence
                }
              />


              {/* =================================================
                  MATCH INFORMATION
              ================================================= */}

              <dl className="grid grid-cols-2 gap-sm text-body-md">

                <Meta
                  term="CCTV location"
                  value={
                    item.location
                  }
                />

                <Meta
                  term="Camera ID"
                  value={
                    item.cameraId
                  }
                  mono
                />

                <Meta
                  term="Date"
                  value={
                    item.date
                  }
                />

                <Meta
                  term="Detected timestamp"
                  value={
                    item.detectedAt
                  }
                  mono
                />

              </dl>


              {/* =================================================
                  OPERATOR ACTIONS
              ================================================= */}

              <div className="flex flex-wrap items-center justify-end gap-sm pt-sm border-t border-surface-variant">

                {/* REJECT */}

                <button
                  type="button"
                  onClick={() =>
                    handleStatusChange(
                      item.id,
                      "rejected"
                    )
                  }
                  className={`px-md py-xs rounded-lg text-label-sm font-label-bold uppercase flex items-center gap-xs transition-colors ${
                    item.verificationStatus ===
                    "rejected"
                      ? "bg-error text-on-error shadow-sm"
                      : "bg-surface-container text-on-surface hover:bg-error/10 hover:text-error"
                  }`}
                >

                  <Icon
                    name="close"
                    className="text-[18px]"
                  />

                  Reject

                </button>


                {/* VERIFY */}

                <button
                  type="button"
                  onClick={() =>
                    handleStatusChange(
                      item.id,
                      "verified"
                    )
                  }
                  className={`px-md py-xs rounded-lg text-label-sm font-label-bold uppercase flex items-center gap-xs transition-colors ${
                    item.verificationStatus ===
                    "verified"
                      ? "bg-success text-on-success shadow-sm"
                      : "bg-primary text-on-primary hover:bg-tertiary-container"
                  }`}
                >

                  <Icon
                    name="check"
                    className="text-[18px]"
                  />

                  Verify Match

                </button>


                {/* DOWNLOAD PDF */}

                {item.verificationStatus ===
                  "verified" && (

                  <button
                    type="button"
                    disabled={
                      downloadingId ===
                      item.id
                    }
                    onClick={() =>
                      downloadMatchReport(
                        item
                      )
                    }
                    className="px-md py-xs rounded-lg text-label-sm font-label-bold uppercase flex items-center gap-xs bg-secondary-container text-on-secondary-container hover:bg-secondary-container/80 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
                  >

                    <Icon
                      name="download"
                      className="text-[18px]"
                    />

                    {downloadingId ===
                    item.id
                      ? "Generating..."
                      : "Download Report"}

                  </button>

                )}

              </div>

            </Card>

          ))}

        </div>

      )}

    </>
  );
}


/* ============================================================
   META FIELD
============================================================ */

function Meta({
  term,
  value,
  mono,
}: {
  term: string;
  value: string;
  mono?: boolean;
}) {
  return (
    <div>

      <dt className="font-label-bold text-label-bold uppercase text-on-surface-variant">
        {term}
      </dt>

      <dd
        className={
          mono
            ? "font-mono-data text-mono-data mt-base"
            : "mt-base"
        }
      >
        {value}
      </dd>

    </div>
  );
}