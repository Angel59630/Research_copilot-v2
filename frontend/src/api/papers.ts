import {
  apiBlob,
  apiFetch,
} from "./client";


export interface Paper {
  id: string;
  title: string;
  authors: string | null;
  abstract: string | null;
  filename: string;
  source: string;
  status: string;
  error_message: string | null;
  page_count: number | null;
  file_size: number | null;
  created_at: string;
  updated_at: string;
}


export interface PaperListResponse {
  items: Paper[];
  total: number;
  page: number;
  page_size: number;
}


export interface PaperListParams {
  q?: string;
  status?: string;
  page: number;
  pageSize: number;
}


export interface PaperUpdate {
  title?: string | null;
  authors?: string | null;
  abstract?: string | null;
}


export function listPapers(
  params: PaperListParams,
) {
  const query =
    new URLSearchParams({
      page: String(params.page),
      page_size:
        String(params.pageSize),
    });

  if (params.q?.trim()) {
    query.set(
      "q",
      params.q.trim(),
    );
  }

  if (params.status) {
    query.set(
      "status",
      params.status,
    );
  }

  return apiFetch<PaperListResponse>(
    `/api/papers?${query.toString()}`,
  );
}


export function getPaper(
  paperId: string,
) {
  return apiFetch<Paper>(
    `/api/papers/${
      encodeURIComponent(paperId)
    }`,
  );
}


export function updatePaper(
  paperId: string,
  payload: PaperUpdate,
) {
  return apiFetch<Paper>(
    `/api/papers/${
      encodeURIComponent(paperId)
    }`,
    {
      method: "PATCH",
      headers: {
        "Content-Type":
          "application/json",
      },
      body: JSON.stringify(payload),
    },
  );
}


export function deletePaper(
  paperId: string,
) {
  return apiFetch<void>(
    `/api/papers/${
      encodeURIComponent(paperId)
    }`,
    {
      method: "DELETE",
    },
  );
}


export function downloadPaperPdf(
  paperId: string,
) {
  return apiBlob(
    `/api/papers/${
      encodeURIComponent(paperId)
    }/pdf`,
  );
}


export function uploadPaper(
  file: File,
) {
  const form = new FormData();

  form.append(
    "file",
    file,
  );

  return apiFetch<Paper>(
    "/api/imports/local",
    {
      method: "POST",
      body: form,
    },
  );
}
