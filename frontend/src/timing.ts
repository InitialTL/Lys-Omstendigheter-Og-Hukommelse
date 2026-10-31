/**
 * Server deadlines are Unix seconds. Derive remaining time from the CURRENT
 * deadline on every render; never carry the previous phase's `00:00` into the
 * recall phase, since that would trigger an immediate answer submission.
 */
export function secondsRemaining(
  deadline: number | null | undefined,
  offsetSeconds: number,
  currentUnixSeconds: number,
): number {
  if (deadline == null || !Number.isFinite(deadline)) return 0;
  return Math.max(0, Math.ceil(deadline - (currentUnixSeconds + offsetSeconds)));
}

/** The actual deadline must have passed before an automatic submission. */
export function deadlinePassed(
  deadline: number | null | undefined,
  offsetSeconds: number,
  currentUnixSeconds: number,
): boolean {
  return deadline != null && Number.isFinite(deadline) &&
    currentUnixSeconds + offsetSeconds >= deadline;
}
