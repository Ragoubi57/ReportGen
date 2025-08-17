// frontend/src/app/models/report-request.model.ts
export interface ReportRequest {
  title: string;
  query: string;
  authors: string[];
  date?: string;
  mentors?: string[];
  university?: string;
  logo?: File | null;
  color?: string;     // This is the RGB string e.g., "127, 0, 255"
  no_rag: boolean;   // Kept as non-optional
  // --- NEW FIELDS for the figure feature ---
  user_figure?: File | null;
  user_figure_caption?: string;
  // --- END NEW FIELDS ---
}