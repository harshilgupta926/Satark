export type FirstlightEvidence = {
  id: string;
  summary: string;
  kind: string;
  tampered?: boolean;
};
export type FirstlightFinding = {
  title: string;
  detail: string;
  severity: string;
  refs: string[];
};
export function getTrustedFirstlightEvidence<T extends { tampered?: boolean }>(evidence: T[]): T[];
export function buildFirstlightFindings(evidence: FirstlightEvidence[]): FirstlightFinding[];
