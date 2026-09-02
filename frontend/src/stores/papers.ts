import {
  defineStore,
} from "pinia";

import {
  deletePaper,
  listPapers,
  updatePaper,
} from "../api/papers";

import type {
  Paper,
  PaperUpdate,
} from "../api/papers";

import {
  formatApiError,
} from "../api/client";


const ACTIVE_STATUSES = [
  "queued",
  "parsing",
  "embedding",
];


export const usePapersStore =
  defineStore(
    "papers",
    {
      state: () => ({
        items: [] as Paper[],
        total: 0,
        page: 1,
        pageSize: 20,
        q: "",
        status: "",
        loading: false,
        loadError: "" as string,
        pollingTimer:
          null as number | null,
      }),

      actions: {
        async load(
          silent = false,
        ) {
          if (!silent) {
            this.loading = true;
          }

          try {
            const result =
              await listPapers({
                q: this.q,
                status: this.status,
                page: this.page,
                pageSize:
                  this.pageSize,
              });

            this.items = result.items;
            this.total = result.total;
            this.loadError = "";
            this.schedulePolling();

          } catch (error) {
            this.loadError =
              formatApiError(
                error,
                "论文列表加载失败",
              );

            this.stopPolling();

            if (!silent) {
              throw error;
            }

          } finally {
            if (!silent) {
              this.loading = false;
            }
          }
        },

        async search() {
          this.page = 1;
          await this.load();
        },

        async changePage(
          page: number,
        ) {
          this.page = page;
          await this.load();
        },

        async save(
          paperId: string,
          payload: PaperUpdate,
        ) {
          const paper =
            await updatePaper(
              paperId,
              payload,
            );

          const index =
            this.items.findIndex(
              (item) =>
                item.id === paperId,
            );

          if (index >= 0) {
            this.items[index] = paper;
          }

          return paper;
        },

        async remove(
          paperId: string,
        ) {
          await deletePaper(paperId);

          if (
            this.items.length === 1
            && this.page > 1
          ) {
            this.page -= 1;
          }

          await this.load();
        },

        schedulePolling() {
          this.stopPolling();

          const active =
            this.items.some(
              (paper) =>
                ACTIVE_STATUSES.includes(
                  paper.status,
                ),
            );

          if (!active) {
            return;
          }

          this.pollingTimer =
            window.setTimeout(
              () => {
                this.pollingTimer = null;
                void this.load(true);
              },
              3000,
            );
        },

        stopPolling() {
          if (
            this.pollingTimer
              === null
          ) {
            return;
          }

          window.clearTimeout(
            this.pollingTimer,
          );

          this.pollingTimer = null;
        },
      },
    },
  );
