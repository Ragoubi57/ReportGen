// frontend/src/app/services/report-generator.service.ts
import { Injectable } from '@angular/core';
import { HttpClient, HttpErrorResponse } from '@angular/common/http';
import { Observable, throwError } from 'rxjs';
import { catchError } from 'rxjs/operators';
import { ReportRequest } from '../models/report-request.model';

@Injectable({
  providedIn: 'root'
})
export class ReportGeneratorService {
  private apiUrl = 'http://localhost:8000/generate-report'; // Ensure this is your correct backend URL

  constructor(private http: HttpClient) { }

  generateReport(requestData: ReportRequest): Observable<Blob> {
    console.log("Service: generateReport called with requestData:", JSON.stringify(requestData, (key, value) => {
        if (value instanceof File) { return { name: value.name, size: value.size, type: value.type }; }
        return value;
    }, 2)); // <-- SERVICE DEBUG 1 (Keep this for debugging)

    const formData = new FormData();

    // Required fields
    formData.append('title', requestData.title);
    formData.append('query', requestData.query);

    // Authors (array to comma-separated string)
    if (requestData.authors && requestData.authors.length > 0) {
      formData.append('authors', requestData.authors.join(','));
    } else {
      formData.append('authors', ''); // Backend expects the field
    }

    // Mentors (optional array to comma-separated string)
    if (requestData.mentors && requestData.mentors.length > 0) {
      formData.append('mentors', requestData.mentors.join(','));
    } else {
      formData.append('mentors', ''); // Backend expects the field, send empty if not provided
    }

    // Optional string fields
    if (requestData.date) { // If undefined or empty string, this block is skipped or sends empty
      formData.append('date', requestData.date);
    }
    if (requestData.university) {
      formData.append('university', requestData.university);
    }
    if (requestData.color) { // This should be the "R, G, B" string
      formData.append('color', requestData.color);
    }

    // Boolean field
    formData.append('no_rag', requestData.no_rag.toString()); // "true" or "false"

    // File fields (check if file exists before accessing .name)
    if (requestData.logo && requestData.logo instanceof File) {
      formData.append('logo', requestData.logo, requestData.logo.name);
    }

    if (requestData.user_figure && requestData.user_figure instanceof File) {
      formData.append('user_figure', requestData.user_figure, requestData.user_figure.name);
      // Handle caption only if user_figure exists
      if (requestData.user_figure_caption) {
        formData.append('user_figure_caption', requestData.user_figure_caption);
      } else {
        formData.append('user_figure_caption', ''); // Send empty caption if figure exists but no caption text
      }
    }
    // If requestData.user_figure is null/undefined, user_figure_caption won't be appended by the above logic,
    // which is fine as FastAPI will treat it as an optional missing field.

    // For debugging FormData entries:
    console.log("Service: FormData entries before HTTP post:");
    for (const [key, value] of (formData as any).entries()) { // Cast to any for entries()
        if (value instanceof File) {
            console.log(`  ${key}: File(name: ${value.name}, size: ${value.size}, type: ${value.type})`);
        } else {
            console.log(`  ${key}: ${value}`);
        }
    } // <-- SERVICE DEBUG 2 (Keep this)

    console.log("Service: About to make HTTP POST request to:", this.apiUrl); // <-- SERVICE DEBUG 3 (Keep this)
    return this.http.post(this.apiUrl, formData, {
      responseType: 'blob'
    }).pipe(
      catchError(err => { // Explicitly type err here
        console.error("Service: HTTP POST request error caught in catchError:", err); // <-- SERVICE DEBUG 4 (Keep this)
        return this.handleError(err as HttpErrorResponse); // Cast to HttpErrorResponse
      })
    );
  }

  private handleError(error: HttpErrorResponse): Observable<never> {
    console.error("Service: handleError method called with:", JSON.stringify(error, null, 2)); // <-- SERVICE DEBUG 5 (Keep this)
    let errorMessage = 'An unknown error occurred during report generation!';
    if (error.error instanceof ErrorEvent) {
      errorMessage = `Client-side error: ${error.error.message}`;
    } else {
      if (error.error instanceof Blob && error.error.type && error.error.type.includes('application/json')) {
        return new Observable((observer) => {
          const reader = new FileReader();
          reader.onload = (e: any) => {
            try {
              const errObj = JSON.parse(e.target.result);
              errorMessage = `Server error (${error.status}): ${errObj.detail || errObj.error || errObj.message || 'Failed to parse server error details.'}`;
            } catch (jsonError) {
              errorMessage = `Server error (${error.status}): ${error.statusText}. Failed to parse JSON error.`;
            }
            console.error("Service handleError (Blob JSON):", errorMessage, error);
            observer.error(new Error(errorMessage));
          };
          reader.onerror = () => {
            errorMessage = `Server error (${error.status}): ${error.statusText}. Failed to read error blob.`;
            console.error("Service handleError (Blob Read Error):", errorMessage, error);
            observer.error(new Error(errorMessage));
          };
          reader.readAsText(error.error);
        });
      } else if (error.error instanceof Blob) {
        errorMessage = `Server error (${error.status}): ${error.statusText}. Received non-JSON error blob.`;
      } else if (typeof error.error === 'string') {
        try {
          const errObj = JSON.parse(error.error);
          errorMessage = `Server error (${error.status}): ${errObj.detail || errObj.error || errObj.message || error.statusText}`;
        } catch (e) {
          errorMessage = `Server error (${error.status}): ${error.error}`;
        }
      } else if (error.statusText) {
         errorMessage = `Server error (${error.status}): ${error.statusText || 'Unknown server error with status.'}`;
      } else {
         errorMessage = `Server error (${error.status}): Unknown server error.`;
      }
    }
    console.error(`ReportGeneratorService Error (final processed): ${errorMessage}`, error);
    return throwError(() => new Error(errorMessage));
  }
}