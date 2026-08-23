"use client";

import { useState, useEffect, useRef } from "react";
import { PageHeader } from "@/components/ui/PageHeader";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/PageHeader";
import { StatusBadge } from "@/components/ui/StatusBadge";
import { Icon } from "@/components/ui/Icon";
import { uploadCctvFootage, fetchCctvJobs } from "@/lib/api";
import { CCTV_JOBS, type CctvJob } from "@/lib/demo-data";

export default function CctvAnalysisPage() {
  const [jobs, setJobs] = useState<CctvJob[]>(CCTV_JOBS);
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [location, setLocation] = useState("Downtown Transit Center, Sector 4");
  const [cameraId, setCameraId] = useState("CAM-04-DT-12");
  const [captureDate, setCaptureDate] = useState(new Date().toISOString().split("T")[0]);
  const [uploading, setUploading] = useState(false);
  const [statusMessage, setStatusMessage] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  // Poll processing queue every 3 seconds if active jobs exist
  useEffect(() => {
    let interval: any;
    const loadJobs = async () => {
      const liveJobs = await fetchCctvJobs();
      setJobs(liveJobs);
    };

    loadJobs();
    interval = setInterval(loadJobs, 3000);
    return () => clearInterval(interval);
  }, []);

  const handleVideoSelect = (file: File) => {
    setVideoFile(file);
    setStatusMessage(null);
  };

  const handleUpload = async () => {
    if (!videoFile) {
      fileInputRef.current?.click();
      return;
    }

    setUploading(true);
    setStatusMessage(null);

    const formData = new FormData();
    formData.append("video", videoFile);
    formData.append("location", location);
    formData.append("camera_id", cameraId);
    formData.append("capture_time", new Date(captureDate).toISOString());

    const result = await uploadCctvFootage(formData);
    setUploading(false);

    if (result.success) {
      setVideoFile(null);
      setStatusMessage("Footage uploaded successfully. Frame extraction & face matching dispatched.");
      const updated = await fetchCctvJobs();
      setJobs(updated);
    } else {
      setStatusMessage(result.error || "Upload failed. Please check file format.");
    }
  };

  return (
    <>
      <PageHeader
        title="CCTV Analysis"
        description="Upload footage, assign camera metadata, and queue frame extraction. The vision engine extracts frames (1 fps) and runs face matching against active cases."
        actions={
          <Button
            onClick={() => fileInputRef.current?.click()}
            className="flex-1 md:flex-none"
          >
            <Icon name="upload" className="text-[20px]" />
            Select footage
          </Button>
        }
      />

      <Card className="p-md relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary-fixed-dim/20 rounded-full blur-[80px] -mr-32 -mt-32 pointer-events-none" />

        {statusMessage ? (
          <div className="relative z-10 mb-sm p-sm bg-secondary-container text-on-secondary-container rounded-lg text-body-md">
            {statusMessage}
          </div>
        ) : null}

        <label
          onClick={() => fileInputRef.current?.click()}
          onDragOver={(e) => e.preventDefault()}
          onDrop={(e) => {
            e.preventDefault();
            if (e.dataTransfer.files?.[0]) {
              handleVideoSelect(e.dataTransfer.files[0]);
            }
          }}
          className="relative z-10 flex flex-col items-center justify-center gap-sm py-xl border border-dashed border-outline-variant rounded-xl bg-surface-container-low cursor-pointer hover:bg-surface-container transition-colors"
        >
          <Icon name="videocam" className="text-[36px] text-outline" />
          <p className="font-headline-sm text-headline-sm">
            {videoFile ? `Selected: ${videoFile.name}` : "Drop CCTV video here"}
          </p>
          <p className="text-body-md text-on-surface-variant">
            {videoFile
              ? `${(videoFile.size / (1024 * 1024)).toFixed(1)} MB · Ready to process`
              : "MP4, MKV, or AVI · metadata captured with the file"}
          </p>
          <input
            ref={fileInputRef}
            type="file"
            accept="video/*"
            className="hidden"
            onChange={(e) => {
              if (e.target.files?.[0]) {
                handleVideoSelect(e.target.files[0]);
              }
            }}
          />
        </label>

        <div className="relative z-10 grid grid-cols-1 md:grid-cols-3 gap-sm mt-md">
          <MetaField
            label="CCTV location"
            value={location}
            onChange={(e) => setLocation(e.target.value)}
            placeholder="Downtown Transit Center, Sector 4"
          />
          <MetaField
            label="Camera ID"
            value={cameraId}
            onChange={(e) => setCameraId(e.target.value)}
            placeholder="CAM-04-DT-12"
          />
          <MetaField
            label="Capture date"
            type="date"
            value={captureDate}
            onChange={(e) => setCaptureDate(e.target.value)}
          />
        </div>

        {videoFile ? (
          <div className="relative z-10 mt-md flex justify-end">
            <Button onClick={handleUpload} disabled={uploading}>
              <Icon name="biotech" className="text-[20px]" />
              {uploading ? "Uploading & Ingesting..." : "Start Frame Extraction & Matching"}
            </Button>
          </div>
        ) : null}
      </Card>

      <Card className="overflow-hidden">
        <div className="px-md py-sm border-b border-outline-variant flex items-center justify-between">
          <h2 className="font-headline-sm text-headline-sm">Processing queue</h2>
          <span className="text-label-sm text-on-surface-variant">
            {jobs.length} jobs in queue
          </span>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-surface-container-low text-on-surface-variant font-label-bold text-label-bold uppercase tracking-wider border-b border-surface-variant">
                <th className="p-sm pl-md font-medium">Job</th>
                <th className="p-sm font-medium">Location / Camera</th>
                <th className="p-sm font-medium">Uploaded</th>
                <th className="p-sm font-medium">Frames</th>
                <th className="p-sm font-medium">Faces</th>
                <th className="p-sm font-medium">Matches</th>
                <th className="p-sm pr-md font-medium">Status</th>
              </tr>
            </thead>
            <tbody className="text-body-md divide-y divide-surface-variant/50">
              {jobs.map((job, index) => (
                <tr key={job.id} className={index % 2 === 1 ? "bg-surface-bright" : undefined}>
                  <td className="p-sm pl-md">
                    <div className="flex flex-col">
                      <span className="font-headline-sm text-[16px] leading-tight">{job.filename}</span>
                      <span className="font-mono-data text-mono-data text-on-surface-variant">{job.id}</span>
                    </div>
                  </td>
                  <td className="p-sm text-on-surface-variant">
                    <div>{job.location}</div>
                    <div className="font-mono-data text-mono-data">{job.cameraId}</div>
                  </td>
                  <td className="p-sm font-mono-data text-mono-data">{job.uploadedAt}</td>
                  <td className="p-sm font-mono-data text-mono-data">{job.frames}</td>
                  <td className="p-sm font-mono-data text-mono-data">{job.faces}</td>
                  <td className="p-sm font-mono-data text-mono-data">{job.matches}</td>
                  <td className="p-sm pr-md">
                    <StatusBadge status={job.status} />
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </Card>
    </>
  );
}

function MetaField({
  label,
  value,
  onChange,
  placeholder,
  type = "text",
}: {
  label: string;
  value: string;
  onChange: (e: React.ChangeEvent<HTMLInputElement>) => void;
  placeholder?: string;
  type?: string;
}) {
  return (
    <label className="flex flex-col gap-base">
      <span className="font-label-bold text-label-bold uppercase text-on-surface-variant">{label}</span>
      <input
        type={type}
        value={value}
        onChange={onChange}
        placeholder={placeholder}
        className="px-sm py-sm bg-surface-container-lowest border border-outline-variant rounded-lg text-body-md focus:outline-none focus:ring-1 focus:ring-primary"
      />
    </label>
  );
}
