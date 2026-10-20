export type ImportedCsvEvent = { id: string; timestamp: string; source: string; kind: string; summary: string; };
export function parseCsv(text: string): ImportedCsvEvent[];
export function parseIsoTimestamp(value: unknown): string | null;
export const SIMULATED_TAMPER_MARKER: string;
export function toggleSimulatedTamper(summary: string, currentlyTampered: boolean): string;
