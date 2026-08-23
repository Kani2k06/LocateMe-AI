"use client";

import { useState, useRef } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/PageHeader";
import { Icon } from "@/components/ui/Icon";
import { createMissingPerson } from "@/lib/api";

export default function RegisterPersonPage() {
  const [loading, setLoading] = useState(false);
  const [submittedPerson, setSubmittedPerson] = useState<any | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);

  const fileInputRef = useRef<HTMLInputElement>(null);

  const handlePhotoSelect = (file: File) => {
    if (!file.type.startsWith("image/")) {
      setErrorMessage("Please select a valid image file.");
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      setErrorMessage("Photo must be smaller than 10 MB.");
      return;
    }

    setErrorMessage(null);
    setPhotoFile(file);

    const reader = new FileReader();

    reader.onload = (e) => {
      setPhotoPreview(
        (e.target?.result as string) || null
      );
    };

    reader.readAsDataURL(file);
  };

  const handleSubmit = async (
    event: React.FormEvent<HTMLFormElement>
  ) => {
    event.preventDefault();

    setErrorMessage(null);

    // Reference photo is required for face embedding.
    if (!photoFile) {
      setErrorMessage(
        "Please upload a reference photograph before saving the record."
      );
      return;
    }

    setLoading(true);

    try {
      const form = event.currentTarget;
      const formData = new FormData(form);

      // Explicitly attach the selected photo.
      formData.set("photo", photoFile);

      const result = await createMissingPerson(formData);

      if (result.success) {
        setSubmittedPerson(result.data);
      } else {
        setErrorMessage(
          result.error ||
            "Failed to register person. Please try again."
        );
      }
    } catch (error) {
      console.error(
        "Register person error:",
        error
      );

      setErrorMessage(
        "Something went wrong while registering the person."
      );
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setSubmittedPerson(null);
    setPhotoFile(null);
    setPhotoPreview(null);
    setErrorMessage(null);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  return (
    <>
      <PageHeader
        title="Register Person"
        description="Create a missing-person record and attach a reference photograph. Facial embeddings (512-d) are automatically generated for live CCTV matching."
      />

      {submittedPerson ? (
        <Card className="p-lg max-w-2xl flex flex-col gap-md">
          <div className="flex items-center gap-sm">
            <div className="w-12 h-12 rounded-full bg-success/10 text-success flex items-center justify-center">
              <Icon
                name="check_circle"
                className="text-[28px]"
              />
            </div>

            <div>
              <p className="font-headline-sm text-headline-sm">
                Record Registered Successfully
              </p>

              <p className="text-body-md text-on-surface-variant">
                #{submittedPerson?.case_id || "Generated Case"}{" "}
                — {submittedPerson?.name || "Person"}
              </p>
            </div>
          </div>

          <div className="p-md bg-surface-container-low rounded-lg text-body-md text-on-surface-variant space-y-xs">
            <p>
              <strong>Status:</strong>{" "}
              Active Alert · Face Embedding:{" "}
              <span className="font-mono-data text-success">
                {submittedPerson?.has_embedding
                  ? "Generated (512-d vector)"
                  : "Generated"}
              </span>
            </p>

            <p>
              <strong>Last Known Location:</strong>{" "}
              {submittedPerson?.last_known_location ||
                "Not provided"}
            </p>

            {submittedPerson?.id ? (
              <p>
                <strong>Record ID:</strong>{" "}
                <span className="font-mono-data">
                  {submittedPerson.id}
                </span>
              </p>
            ) : null}
          </div>

          <div className="flex gap-sm">
            <Button
              onClick={handleReset}
              variant="secondary"
            >
              Register another
            </Button>

            <Button href="/missing-persons">
              View in Registry
            </Button>
          </div>
        </Card>
      ) : (
        <form
          className="grid grid-cols-1 lg:grid-cols-3 gap-md"
          onSubmit={handleSubmit}
        >
          <Card className="lg:col-span-2 p-md grid grid-cols-1 md:grid-cols-2 gap-sm">
            {errorMessage ? (
              <div className="md:col-span-2 p-sm bg-error/10 text-error border border-error/20 rounded-lg text-body-md">
                {errorMessage}
              </div>
            ) : null}

            <Field
              label="Full name"
              name="name"
              placeholder="Mateo Reyes"
              required
            />

            <Field
              label="Case ID"
              name="case_id"
              placeholder="MP-24-0910"
            />

            <Field
              label="Age"
              name="age"
              type="number"
              placeholder="17"
              required
            />

            <label className="flex flex-col gap-base">
              <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">
                Sex
              </span>

              <select
                name="gender"
                className="px-sm py-sm bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary"
              >
                <option value="M">M</option>
                <option value="F">F</option>
                <option value="Unknown">
                  Unknown
                </option>
              </select>
            </label>

            <Field
              label="Height"
              name="height"
              placeholder={'5\'9"'}
            />

            <Field
              label="Last known location"
              name="last_known_location"
              placeholder="Downtown Transit Center"
              required
            />

            <Field
              label="Missing Since"
              name="missing_since"
              type="date"
              defaultValue={
                new Date()
                  .toISOString()
                  .split("T")[0]
              }
            />

            <label className="md:col-span-2 flex flex-col gap-base">
              <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">
                Distinguishing notes
              </span>

              <textarea
                name="notes"
                rows={4}
                className="px-sm py-sm bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary"
                placeholder="Clothing, last-seen context, identifying details..."
              />
            </label>
          </Card>

          <div className="flex flex-col gap-md">
            <Card className="p-md">
              <p className="font-label-bold text-label-bold uppercase text-on-surface-variant">
                Reference photograph *
              </p>

              <div
                onClick={() =>
                  fileInputRef.current?.click()
                }
                onDragOver={(e) =>
                  e.preventDefault()
                }
                onDrop={(e) => {
                  e.preventDefault();

                  const file =
                    e.dataTransfer.files?.[0];

                  if (file) {
                    handlePhotoSelect(file);
                  }
                }}
                className="mt-sm flex flex-col items-center justify-center gap-xs border border-dashed border-outline-variant rounded-xl p-lg bg-surface-container-low cursor-pointer hover:bg-surface-container transition-colors min-h-[160px]"
              >
                {photoPreview ? (
                  <div className="flex flex-col items-center gap-xs">
                    {/* eslint-disable-next-line @next/next/no-img-element */}
                    <img
                      src={photoPreview}
                      alt="Reference photo preview"
                      className="w-24 h-24 rounded-lg object-cover shadow-sm border border-outline-variant"
                    />

                    <span className="text-label-sm text-primary font-label-bold">
                      Click to change photo
                    </span>

                    {photoFile ? (
                      <span className="text-label-sm text-on-surface-variant">
                        {photoFile.name}
                      </span>
                    ) : null}
                  </div>
                ) : (
                  <>
                    <Icon
                      name="add_a_photo"
                      className="text-[28px] text-outline"
                    />

                    <span className="text-body-md text-on-surface-variant text-center">
                      Drop a frontal photo or click to browse
                    </span>

                    <span className="text-label-sm text-on-surface-variant">
                      JPG, PNG · Max 10 MB
                    </span>
                  </>
                )}

                <input
                  ref={fileInputRef}
                  type="file"
                  name="photo"
                  accept="image/jpeg,image/png,image/webp"
                  className="hidden"
                  onChange={(e) => {
                    const file =
                      e.target.files?.[0];

                    if (file) {
                      handlePhotoSelect(file);
                    }
                  }}
                />
              </div>
            </Card>

            <Button
              type="submit"
              disabled={loading}
            >
              <Icon
                name="person_add"
                className="text-[20px]"
              />

              {loading
                ? "Generating Embedding..."
                : "Save record"}
            </Button>
          </div>
        </form>
      )}
    </>
  );
}

function Field({
  label,
  name,
  placeholder,
  type = "text",
  required,
  defaultValue,
}: {
  label: string;
  name: string;
  placeholder?: string;
  type?: string;
  required?: boolean;
  defaultValue?: string;
}) {
  return (
    <label className="flex flex-col gap-base">
      <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">
        {label}
      </span>

      <input
        name={name}
        type={type}
        required={required}
        defaultValue={defaultValue}
        placeholder={placeholder}
        className="px-sm py-sm bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary"
      />
    </label>
  );
}