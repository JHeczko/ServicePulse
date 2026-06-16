import type { ServiceStatus } from "../types";

interface Props {
  status: ServiceStatus;
}

const labels: Record<ServiceStatus, string> = {
  up: "UP",
  down: "DOWN",
  unknown: "UNKNOWN",
};

export default function StatusBadge({ status }: Props) {
  return (
    <span className={`status-badge status-badge--${status}`}>
      <span className={`status-dot${status === "up" ? " status-dot--up" : ""}`} />
      {labels[status]}
    </span>
  );
}
