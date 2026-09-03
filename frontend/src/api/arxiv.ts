import {
  apiFetch,
} from "./client";

import type {
  Paper,
} from "./papers";


export interface ArxivPaper {
  paper_id: string;
  title: string;
  authors: string[];
  abstract: string;
  published: string | null;
  categories: string[];
}


export function searchArxiv(
  query: string,
) {
  const params =
    new URLSearchParams({
      q: query,
      start: "0",
      max_results: "20",
    });

  return apiFetch<
    ArxivPaper[]
  >(
    `/api/arxiv/search?${
      params.toString()
    }`,
  );
}


export function importArxiv(
  value: string,
) {
  return apiFetch<
    Paper
  >(
    "/api/arxiv/import",
    {
      method: "POST",

      headers: {
        "Content-Type":
          "application/json",
      },

      body:
        JSON.stringify({
          value,
        }),
    },
  );
}