"use client";

import { useEffect, useState } from "react";
import Link from "next/link";

import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { StatusBadge } from "@/components/ui/StatusBadge";
import {
  Avatar,
  Pagination,
} from "@/components/ui/ConfidenceMeter";
import { Icon } from "@/components/ui/Icon";

import {
  fetchMissingPersons,
  updatePersonStatus,
} from "@/lib/api";

import type {
  MissingPerson,
  CaseStatus,
} from "@/lib/demo-data";

import { cn } from "@/lib/cn";

export function MissingPersonsView() {
  const [query, setQuery] = useState("");
  const [statusFilter, setStatusFilter] =
    useState<CaseStatus | "all">("active_alert");

  const [persons, setPersons] = useState<MissingPerson[]>([]);
  const [loading, setLoading] = useState(true);
  const [updatingId, setUpdatingId] = useState<string | null>(null);

  // =========================================================
  // LOAD PERSONS
  // =========================================================

  useEffect(() => {
    let active = true;

    const loadPersons = async () => {
      try {
        setLoading(true);

        const data = await fetchMissingPersons(
          statusFilter,
          query
        );

        if (active) {
          setPersons(Array.isArray(data) ? data : []);
        }
      } catch (error) {
        console.error(
          "Failed to load missing persons:",
          error
        );

        if (active) {
          setPersons([]);
        }
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    };

    loadPersons();

    return () => {
      active = false;
    };
  }, [query, statusFilter]);

  // =========================================================
  // MARK AS FOUND SAFE
  // =========================================================

  const handleMarkFoundSafe = async (
    person: MissingPerson
  ) => {
    const confirmed = window.confirm(
      `Mark ${person.name} as Found Safe?\n\n` +
        `This will resolve the active missing-person case.`
    );

    if (!confirmed) {
      return;
    }

    setUpdatingId(person.id);

    const success = await updatePersonStatus(
      person.id,
      "found_safe"
    );

    if (success) {
      /*
       * If the current filter is Active,
       * the resolved person disappears immediately.
       *
       * If the current filter is All,
       * update the person's status locally so the
       * Found Safe badge appears immediately.
       */
      if (statusFilter === "active_alert") {
        setPersons((current) =>
          current.filter(
            (item) => item.id !== person.id
          )
        );
      } else {
        setPersons((current) =>
          current.map((item) =>
            item.id === person.id
              ? {
                  ...item,
                  status: "found_safe",
                  relativeTime: "Resolved",
                }
              : item
          )
        );
      }
    } else {
      window.alert(
        "Unable to update the case status. Please try again."
      );
    }

    setUpdatingId(null);
  };

  // =========================================================
  // STATUS FILTER LABEL
  // =========================================================

  const statusLabel =
    statusFilter === "active_alert"
      ? "Active"
      : statusFilter === "pending_verification"
      ? "Pending"
      : statusFilter === "found_safe"
      ? "Found Safe"
      : "All";

  return (
    <>
      {/* =====================================================
          PAGE HEADER
      ===================================================== */}

      <PageHeader
        title="Missing Persons Registry"
        description="Centralized database for active and resolved missing person cases. Updated in real-time with cross-agency intel."
        actions={
          <>
            <Button
              variant="secondary"
              className="flex-1 md:flex-none"
              onClick={() => window.print()}
            >
              <Icon
                name="download"
                className="text-[20px]"
              />
              Export Data
            </Button>

            <Button
              href="/register-person"
              className="flex-1 md:flex-none"
            >
              <Icon
                name="person_add"
                className="text-[20px]"
              />
              Add New Entry
            </Button>
          </>
        }
      />

      {/* =====================================================
          SEARCH + STATUS FILTER
      ===================================================== */}

      <div className="flex flex-col bg-surface-container-lowest shadow-sm rounded-xl p-md gap-md relative overflow-hidden">

        <div className="absolute top-0 right-0 w-64 h-64 bg-primary-fixed-dim/20 rounded-full blur-[80px] -mr-32 -mt-32 pointer-events-none" />

        <div className="flex flex-col lg:flex-row gap-sm z-10 relative">

          {/* Search */}

          <div className="relative flex-1 flex items-center">

            <span className="material-symbols-outlined absolute left-sm text-outline">
              search
            </span>

            <input
              className="w-full pl-xl pr-md py-sm bg-surface-container-low rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary shadow-inner"
              placeholder="Search by name, case ID, or physical description..."
              type="search"
              value={query}
              onChange={(event) =>
                setQuery(event.target.value)
              }
            />

          </div>

          {/* Status Buttons */}

          <div className="flex gap-xs overflow-x-auto pb-2 lg:pb-0 shrink-0">

            {(
              [
                {
                  value: "all",
                  label: "All",
                },
                {
                  value: "active_alert",
                  label: "Active",
                },
                {
                  value: "pending_verification",
                  label: "Pending",
                },
                {
                  value: "found_safe",
                  label: "Found Safe",
                },
              ] as {
                value: CaseStatus | "all";
                label: string;
              }[]
            ).map((option) => (
              <button
                key={option.value}
                type="button"
                onClick={() =>
                  setStatusFilter(option.value)
                }
                className={cn(
                  "px-sm py-xs rounded-full font-label-sm text-label-sm whitespace-nowrap transition-colors shadow-sm",
                  statusFilter === option.value
                    ? "bg-primary text-on-primary"
                    : "bg-surface-container text-on-surface hover:bg-surface-variant"
                )}
              >
                {option.label}
              </button>
            ))}

          </div>
        </div>

        {/* Current filter indicator */}

        <div className="relative z-10 flex items-center gap-xs text-label-sm text-on-surface-variant">
          <Icon
            name="filter_alt"
            className="text-[18px]"
          />

          <span>
            Showing:{" "}
            <strong className="text-on-surface">
              {statusLabel}
            </strong>
          </span>
        </div>
      </div>

      {/* =====================================================
          TABLE
      ===================================================== */}

      <div className="bg-surface-container-lowest shadow-md rounded-xl overflow-hidden flex flex-col z-10">

        <div className="overflow-x-auto">

          <table className="w-full text-left border-collapse">

            <thead>
              <tr className="bg-surface-container-low text-on-surface-variant font-label-bold text-label-bold uppercase tracking-wider border-b border-surface-variant">

                <th className="p-sm pl-md font-medium w-16">
                  Photo
                </th>

                <th className="p-sm font-medium min-w-[200px]">
                  Subject Details
                </th>

                <th className="p-sm font-medium">
                  Demographics
                </th>

                <th className="p-sm font-medium">
                  Missing Since
                </th>

                <th className="p-sm font-medium min-w-[250px]">
                  Last Known Location
                </th>

                <th className="p-sm font-medium w-32">
                  Status
                </th>

                <th className="p-sm pr-md font-medium text-right min-w-[180px]">
                  Actions
                </th>

              </tr>
            </thead>

            <tbody className="text-body-md font-body-md text-on-surface divide-y divide-surface-variant/50">

              {/* Loading */}

              {loading ? (
                <tr>
                  <td
                    colSpan={7}
                    className="p-xl text-center text-on-surface-variant"
                  >
                    Loading missing-person records...
                  </td>
                </tr>
              ) : persons.length === 0 ? (

                /* Empty state */

                <tr>
                  <td
                    colSpan={7}
                    className="p-xl text-center"
                  >
                    <div className="flex flex-col items-center gap-sm">

                      <Icon
                        name="person_search"
                        className="text-[40px] text-outline"
                      />

                      <p className="font-headline-sm text-headline-sm">
                        No missing-person records found
                      </p>

                      <p className="text-label-sm text-on-surface-variant">
                        Try another search or status filter.
                      </p>

                    </div>
                  </td>
                </tr>

              ) : (

                /* Records */

                persons.map((person, index) => (
                  <tr
                    key={person.id}
                    className={cn(
                      "hover:bg-surface-container-low/50 transition-colors group",
                      person.status === "found_safe" &&
                        "opacity-75",
                      index % 2 === 1 &&
                        "bg-surface-bright"
                    )}
                  >

                    {/* Photo */}

                    <td className="p-sm pl-md">
                      <Avatar
                        src={person.photoUrl}
                        alt={person.name}
                      />
                    </td>

                    {/* Subject */}

                    <td className="p-sm">
                      <div className="flex flex-col">

                        <Link
                          href="/detections"
                          className="font-headline-sm text-on-surface text-[16px] leading-tight group-hover:text-primary transition-colors"
                        >
                          {person.name}
                        </Link>

                        <span className="font-mono-data text-mono-data text-on-surface-variant mt-1">
                          ID: #{person.id}
                        </span>

                      </div>
                    </td>

                    {/* Demographics */}

                    <td className="p-sm text-on-surface-variant whitespace-nowrap">
                      {person.age} yrs •{" "}
                      {person.sex} •{" "}
                      {person.height}
                    </td>

                    {/* Missing Since */}

                    <td className="p-sm">
                      <div className="flex flex-col">

                        <span className="text-on-surface">
                          {person.missingSince}
                        </span>

                        <span className="text-on-surface-variant text-label-sm">
                          {person.relativeTime}
                        </span>

                      </div>
                    </td>

                    {/* Location */}

                    <td className="p-sm text-on-surface-variant">
                      <span className="flex items-center gap-xs">

                        <span className="material-symbols-outlined text-[16px] text-outline">
                          location_on
                        </span>

                        <span className="truncate max-w-[200px]">
                          {person.lastKnownLocation}
                        </span>

                      </span>
                    </td>

                    {/* Status */}

                    <td className="p-sm">
                      <StatusBadge
                        status={person.status}
                      />
                    </td>

                    {/* Actions */}

                    <td className="p-sm pr-md">

                      <div className="flex items-center justify-end gap-xs">

                        {person.status ===
                          "active_alert" && (

                          <button
                            type="button"
                            disabled={
                              updatingId === person.id
                            }
                            onClick={() =>
                              handleMarkFoundSafe(
                                person
                              )
                            }
                            className="inline-flex items-center gap-xs px-sm py-xs rounded-lg bg-primary text-on-primary text-label-sm font-label-bold uppercase hover:opacity-90 disabled:opacity-50 disabled:cursor-not-allowed transition-opacity"
                          >

                            <Icon
                              name="check_circle"
                              className="text-[18px]"
                            />

                            {updatingId ===
                            person.id
                              ? "Updating..."
                              : "Found Safe"}

                          </button>

                        )}

                        {person.status ===
                          "found_safe" && (

                          <span className="text-label-sm text-on-surface-variant">
                            Resolved
                          </span>

                        )}

                      </div>

                    </td>

                  </tr>
                ))

              )}

            </tbody>
          </table>
        </div>

        {/* ===================================================
            PAGINATION
        =================================================== */}

        {!loading &&
          persons.length > 0 && (
            <Pagination
              from={1}
              to={persons.length}
              total={persons.length}
            />
          )}

      </div>
    </>
  );
}