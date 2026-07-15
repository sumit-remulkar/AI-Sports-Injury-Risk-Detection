export function VideoUploadPage() {
  return (
    <ComingSoon
      title="Upload video"
      description="Video upload, frame extraction, and pose detection status will live here. This is wired up in Milestone 2 once the Video Processing Engine and Pose Estimation Engine are built on the backend."
    />
  );
}

function ComingSoon({ title, description }: { title: string; description: string }) {
  return (
    <div className="max-w-xl">
      <p className="font-display text-2xl font-semibold">{title}</p>
      <div className="mt-6 rounded-2xl border border-dashed border-line bg-court-graphite p-8 text-center">
        <p className="text-sm text-text-muted">{description}</p>
      </div>
    </div>
  );
}
