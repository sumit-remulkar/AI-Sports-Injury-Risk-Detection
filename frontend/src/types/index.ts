export type UserRole =
  | "athlete"
  | "coach"
  | "physiotherapist"
  | "sports_scientist"
  | "admin";

export interface User {
  id: string;
  full_name: string;
  email: string;
  role: UserRole;
  created_at: string;
}

export interface AthleteProfile {
  athlete_id: string;
  user_id: string;
  age: number | null;
  gender: string | null;
  sport: string | null;
  position: string | null;
  height: number | null;
  weight: number | null;
  injury_history: string | null;
  training_load: string | null;
}

export type AthleteProfileUpdate = Partial<
  Omit<AthleteProfile, "athlete_id" | "user_id">
>;

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export type RiskLevel = "low" | "moderate" | "high" | "critical";
