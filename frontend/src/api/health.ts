import {
  apiFetch,
} from "./client";


export interface HealthStatus {
  status: string;
  environment: string;
  embedding_model: string;
}


export function getHealth() {
  return apiFetch<HealthStatus>(
    "/health",
  );
}
