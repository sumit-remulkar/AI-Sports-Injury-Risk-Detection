import { useEffect, useRef, useState } from "react";
import { api } from "../lib/api";
import type { VideoDetail, VideoSummary, VideoStatus } from "../types";

const ACCEPTED = ".mp4,.mov,.avi,.mkv";

const STATUS_COLOR: Record<VideoStatus, string> = {
  uploaded: "var(--color-text-muted)",
  processing: "var(--color-risk-moderate)",
  completed: "var(--color-risk-low)",
  failed: "var(--color-risk-high)",
};

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-line bg-court-graphite p-6 ${className}`}>
      {children}
    </div>
  );
}

function Metric({ label, value, unit = "" }: { label: string; value: number | null; unit?: string }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-text-muted">{label}</dt>
      <dd className="font-data text-xl text-text-primary">
        {value === null ? "—" : `${value}${unit}`}
      </dd>
    </div>
  );
}

/**
 * Fetches a video through the authenticated API (as a blob, since a
 * plain <video src="..."> request can't carry an Authorization header)
 * and plays it locally via an object URL. Cleans the object URL up on
 * unmount / when the source video_id changes, so repeated plays don't
 * leak memory.
 */
function AnnotatedVideoPlayer({ videoId }: { videoId: string }) {
  const [objectUrl, setObjectUrl] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(false);

  useEffect(() => {
    let currentUrl: string | null = null;
    let cancelled = false;

    setLoading(true);
    setError(false);

    api
      .get(`/videos/${videoId}/annotated`, { responseType: "blob" })
      .then((res) => {
        if (cancelled) return;
        currentUrl = URL.createObjectURL(res.data);
        setObjectUrl(currentUrl);
      })
      .catch(() => !cancelled && setError(true))
      .finally(() => !cancelled && setLoading(false));

    return () => {
      cancelled = true;
      if (currentUrl) URL.revokeObjectURL(currentUrl);
    };
  }, [videoId]);

  if (loading) return <p className="text-sm text-text-muted">Loading annotated video…</p>;
  if (error || !objectUrl) return <p className="text-sm text-risk-high">Couldn't load annotated video.</p>;

  return (
    <video
      src={objectUrl}
      controls
      loop
      className="w-full rounded-lg border border-line"
      style={{ maxHeight: 480, backgroundColor: "black" }}
    />
  );
}

export function VideoUploadPage() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<VideoDetail | null>(null);
  const [history, setHistory] = useState<VideoSummary[]>([]);
  const [expandedHistoryId, setExpandedHistoryId] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);

  function loadHistory() {
    api.get<VideoSummary[]>("/videos/").then((res) => setHistory(res.data)).catch(() => {});
  }

  useEffect(() => {
    loadHistory();
  }, []);

  async function handleUpload() {
    if (!selectedFile) return;
    setUploading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const { data } = await api.post<VideoDetail>("/videos/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setResult(data);
      loadHistory();
    } catch (err: any) {
      const detail = err?.response?.data?.detail;
      setError(typeof detail === "string" ? detail : "Upload failed. Try a shorter, well-lit clip.");
    } finally {
      setUploading(false);
      if (fileInputRef.current) fileInputRef.current.value = "";
      setSelectedFile(null);
    }
  }

  async function handleDelete(videoId: string, fileName: string) {
    if (!window.confirm(`Delete "${fileName}"? This can't be undone.`)) return;

    setDeletingId(videoId);
    try {
      await api.delete(`/videos/${videoId}`);
      setHistory((h) => h.filter((v) => v.video_id !== videoId));
      if (result?.video_id === videoId) setResult(null);
      if (expandedHistoryId === videoId) setExpandedHistoryId(null);
    } catch {
      window.alert("Couldn't delete this video. Try again.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <div className="max-w-3xl space-y-6">
      <div>
        <p className="font-display text-2xl font-semibold">Upload video</p>
        <p className="text-sm text-text-muted">
          Pose estimation + biomechanical analysis run automatically once you upload.
          Best results: single person, side-on view, well lit, a few seconds long.
        </p>
      </div>

      <Card>
        <div className="flex flex-wrap items-center gap-3">
          <input
            ref={fileInputRef}
            type="file"
            accept={ACCEPTED}
            onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            className="text-sm text-text-muted file:mr-3 file:rounded-lg file:border-0 file:bg-court-graphite-light file:px-3 file:py-2 file:text-sm file:text-text-primary"
          />
          <button
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
            className="rounded-lg bg-pulse-cyan px-4 py-2 text-sm font-semibold text-track-slate transition-opacity hover:opacity-90 disabled:opacity-50"
          >
            {uploading ? "Analyzing…" : "Upload & analyze"}
          </button>
        </div>
        {uploading && (
          <p className="mt-3 text-xs text-text-muted">
            Running pose estimation frame by frame and building the annotated video —
            this can take a little while on CPU, don't navigate away.
          </p>
        )}
        {error && <p className="mt-3 text-sm text-risk-high">{error}</p>}
      </Card>

      {result && (
        <Card>
          <div className="mb-4 flex items-center justify-between">
            <p className="font-display text-sm font-semibold uppercase tracking-wide text-text-muted">
              Latest result — {result.file_name}
            </p>
            <span
              className="rounded-full px-3 py-1 text-xs font-semibold uppercase"
              style={{ color: STATUS_COLOR[result.status], border: `1px solid ${STATUS_COLOR[result.status]}` }}
            >
              {result.status}
            </span>
          </div>

          {result.status === "failed" && (
            <p className="text-sm text-risk-high">{result.error_message}</p>
          )}

          {result.has_annotated_video && (
            <div className="mb-4">
              <AnnotatedVideoPlayer videoId={result.video_id} />
              <p className="mt-2 text-xs text-text-muted">
                Skeleton overlay on the analyzed frames (not the full original clip —
                see notes below). Cyan dots are detected joints; numbers are knee angles.
              </p>
            </div>
          )}

          {result.biomechanics_summary && (
            <div className="grid grid-cols-2 gap-4 sm:grid-cols-3">
              <Metric label="Frames analyzed" value={result.biomechanics_summary.frames_analyzed} />
              <Metric label="Frames w/ detection" value={result.biomechanics_summary.frames_with_detection} />
              <Metric label="Avg left knee angle" value={result.biomechanics_summary.avg_left_knee_angle} unit="°" />
              <Metric label="Avg right knee angle" value={result.biomechanics_summary.avg_right_knee_angle} unit="°" />
              <Metric label="Avg trunk lean" value={result.biomechanics_summary.avg_trunk_lean_deg} unit="°" />
              <Metric label="Knee ROM asymmetry" value={result.biomechanics_summary.knee_rom_asymmetry} unit="°" />
              <Metric label="Left knee ROM" value={result.biomechanics_summary.left_knee_rom} unit="°" />
              <Metric label="Right knee ROM" value={result.biomechanics_summary.right_knee_rom} unit="°" />
            </div>
          )}

          <p className="mt-4 text-xs text-text-muted">
            Knee valgus proxy is a 2D single-camera estimate, not a clinical measurement —
            treat it as directional, not diagnostic. "Knee ROM asymmetry" compares how much
            range of motion each leg moved through over the whole clip — this works for both
            bilateral movements (squats) and cyclical gait (running), unlike a same-instant
            left-right comparison which would flag normal running as falsely asymmetric. The
            annotated video shows the sampled frames pose estimation analyzed (up to 60,
            evenly spaced across the clip) played back at a fixed rate — it's a representative
            motion sequence, not a frame-exact replay of your original footage. Injury risk
            scoring (Milestone 3) will combine this with training load and history to produce
            an actual risk score.
          </p>
        </Card>
      )}

      <Card>
        <p className="mb-3 font-display text-sm font-semibold uppercase tracking-wide text-text-muted">
          Upload history
        </p>
        {history.length === 0 ? (
          <p className="text-sm text-text-muted">No videos uploaded yet.</p>
        ) : (
          <ul className="divide-y divide-line">
            {history.map((v) => (
              <li key={v.video_id} className="py-2">
                <div className="flex items-center justify-between text-sm">
                  <span className="text-text-primary">{v.file_name}</span>
                  <div className="flex items-center gap-3">
                    {v.has_annotated_video && (
                      <button
                        onClick={() =>
                          setExpandedHistoryId(expandedHistoryId === v.video_id ? null : v.video_id)
                        }
                        className="text-xs text-pulse-cyan hover:underline"
                      >
                        {expandedHistoryId === v.video_id ? "Hide" : "View"}
                      </button>
                    )}
                    <button
                      onClick={() => handleDelete(v.video_id, v.file_name)}
                      disabled={deletingId === v.video_id}
                      className="text-xs text-risk-high hover:underline disabled:opacity-50"
                    >
                      {deletingId === v.video_id ? "Deleting…" : "Delete"}
                    </button>
                    <span style={{ color: STATUS_COLOR[v.status] }} className="text-xs uppercase">
                      {v.status}
                    </span>
                  </div>
                </div>
                {expandedHistoryId === v.video_id && (
                  <div className="mt-3">
                    <AnnotatedVideoPlayer videoId={v.video_id} />
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Card>
    </div>
  );
}
