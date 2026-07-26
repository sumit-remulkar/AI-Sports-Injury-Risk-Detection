import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { api } from "../lib/api";
import { useAuth } from "../context/AuthContext";
import { RiskGauge } from "../components/RiskGauge";
import type { AthleteProfile } from "../types";

function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return (
    <div className={`rounded-2xl border border-line bg-court-graphite p-6 ${className}`}>
      {children}
    </div>
  );
}

export function DashboardPage() {
  const { user } = useAuth();
  const [profile, setProfile] = useState<AthleteProfile | null>(null);
  const [athleteCount, setAthleteCount] = useState<number | null>(null);

  useEffect(() => {
    if (user?.role === "athlete") {
      api
        .get<AthleteProfile>("/athletes/me")
        .then((res) => setProfile(res.data))
        .catch(() => setProfile(null));
    } else {
      api
        .get<AthleteProfile[]>("/athletes/")
        .then((res) => setAthleteCount(res.data.length))
        .catch(() => setAthleteCount(null));
    }
  }, [user]);

  return (
    <div className="space-y-6">
      <div>
        <p className="font-display text-2xl font-semibold">
          Welcome back, {user?.full_name?.split(" ")[0]}
        </p>
        <p className="text-sm text-text-muted">
          {user?.role === "athlete"
            ? "Here's where your injury risk overview will live once video analysis is enabled."
            : "Team overview across your connected athletes."}
        </p>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
        <Card className="flex flex-col items-center justify-center gap-4 md:col-span-1">
          <RiskGauge score={null} label="Injury risk score" />
          <p className="text-center text-xs text-text-muted">
            Risk scoring goes live once the prediction engine
            (Milestone 3) is connected to real video analysis.
          </p>
        </Card>

        <Card className="md:col-span-2">
          <p className="mb-3 font-display text-sm font-semibold uppercase tracking-wide text-text-muted">
            {user?.role === "athlete" ? "Your profile" : "Roster"}
          </p>

          {user?.role === "athlete" ? (
            profile ? (
              <dl className="grid grid-cols-2 gap-4 text-sm sm:grid-cols-3">
                <Field label="Sport" value={profile.sport} />
                <Field label="Position" value={profile.position} />
                <Field label="Age" value={profile.age} />
                <Field label="Height (cm)" value={profile.height} />
                <Field label="Weight (kg)" value={profile.weight} />
                <Field label="Training load" value={profile.training_load} />
              </dl>
            ) : (
              <p className="text-sm text-text-muted">Loading profile…</p>
            )
          ) : (
            <p className="text-sm text-text-primary">
              {athleteCount === null
                ? "Loading roster…"
                : `${athleteCount} athlete profile${athleteCount === 1 ? "" : "s"} in the system.`}
            </p>
          )}

          <Link
            to="/profile"
            className="mt-4 inline-block text-sm text-pulse-cyan hover:underline"
          >
            {user?.role === "athlete" ? "Edit profile →" : "View all athletes →"}
          </Link>
        </Card>
      </div>

      <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
        <Card>
          <p className="mb-2 font-display text-sm font-semibold uppercase tracking-wide text-text-muted">
            Previous reports
          </p>
          <EmptyState text="No reports generated yet. This unlocks once video uploads and the recommendation engine (Milestone 3) are live." />
        </Card>

        <Card>
          <p className="mb-2 font-display text-sm font-semibold uppercase tracking-wide text-text-muted">
            Notifications
          </p>
          <EmptyState text="High-risk movement alerts and training load warnings will appear here (Milestone 3)." />
        </Card>
      </div>
    </div>
  );
}

function Field({ label, value }: { label: string; value: string | number | null }) {
  return (
    <div>
      <dt className="text-xs uppercase tracking-wide text-text-muted">{label}</dt>
      <dd className="font-data text-text-primary">{value ?? "—"}</dd>
    </div>
  );
}

function EmptyState({ text }: { text: string }) {
  return (
    <p className="rounded-lg border border-dashed border-line px-4 py-6 text-center text-sm text-text-muted">
      {text}
    </p>
  );
}
