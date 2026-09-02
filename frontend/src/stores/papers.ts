import {
    defineStore,
  } from "pinia";
  
  import {
    apiFetch,
  } from "../api/client";
  
  
  export interface Paper {
    id: string;
    title: string;
    authors: string | null;
    filename: string;
    status: string;
    page_count: number | null;
    created_at: string;
  }
  
  
  interface PaperListResponse {
    items: Paper[];
    total: number;
    page: number;
    page_size: number;
  }
  
  
  export const usePapersStore =
    defineStore(
      "papers",
      {
        state: () => ({
          items: [] as Paper[],
          loading: false,
  
          pollingTimer:
            null as number | null,
        }),
  
        actions: {
          async load() {
            this.loading = true;
  
            try {
              const result =
                await apiFetch<
                  PaperListResponse
                >(
                  "/api/papers"
                  + "?page=1"
                  + "&page_size=100",
                );
  
              this.items =
                result.items;
  
              this.syncPolling();
  
            } finally {
              this.loading = false;
            }
          },
  
          syncPolling() {
            const active =
              this.items.some(
                (paper) =>
                  [
                    "queued",
                    "parsing",
                    "embedding",
                  ].includes(
                    paper.status,
                  ),
              );
  
            if (
              active
              && this.pollingTimer
                === null
            ) {
              this.pollingTimer =
                window.setInterval(
                  () => {
                    void this.load();
                  },
                  3000,
                );
            }
  
            if (
              !active
              && this.pollingTimer
                !== null
            ) {
              window.clearInterval(
                this.pollingTimer,
              );
  
              this.pollingTimer =
                null;
            }
          },
        },
      },
    );