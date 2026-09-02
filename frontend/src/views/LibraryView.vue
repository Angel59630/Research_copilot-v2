<script setup lang="ts">
import {
  onMounted,
  onUnmounted,
  reactive,
  ref,
} from "vue";

import {
  ElMessage,
  ElMessageBox,
} from "element-plus";

import PaperUpload
  from "../components/PaperUpload.vue";

import {
  formatApiError,
} from "../api/client";

import {
  getHealth,
} from "../api/health";

import {
  downloadPaperPdf,
  getPaper,
} from "../api/papers";

import type {
  Paper,
} from "../api/papers";

import {
  usePapersStore,
} from "../stores/papers";


const papers = usePapersStore();

const backendAvailable =
  ref<boolean | null>(null);

const editing = ref(false);
const saving = ref(false);
const loadingDetail = ref(false);
const downloadingId = ref("");
const deletingId = ref("");

const editForm = reactive({
  id: "",
  title: "",
  authors: "",
  abstract: "",
});


const statusLabels:
  Record<string, string> = {
    queued: "等待处理",
    parsing: "解析中",
    embedding: "向量化中",
    ready: "处理完成",
    failed: "处理失败",
    interrupted: "已中断",
    deleting: "正在删除",
    delete_failed: "删除失败",
  };


function statusLabel(
  status: string,
): string {
  return statusLabels[status]
    ?? status;
}


function statusType(
  status: string,
) {
  if (status === "ready") {
    return "success";
  }

  if (
    status === "failed"
    || status === "delete_failed"
  ) {
    return "danger";
  }

  if (status === "interrupted") {
    return "warning";
  }

  return "primary";
}


function sourceLabel(
  source: string,
): string {
  return source === "local"
    ? "本地上传"
    : source;
}


async function loadHealth() {
  try {
    await getHealth();
    backendAvailable.value = true;

  } catch (error) {
    backendAvailable.value = false;

    ElMessage.error(
      formatApiError(
        error,
        "后端服务不可用",
      ),
    );
  }
}


async function loadPapers() {
  try {
    await papers.load();

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "论文列表加载失败",
      ),
    );
  }
}


async function search() {
  try {
    await papers.search();

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "论文搜索失败",
      ),
    );
  }
}


async function changePage(
  page: number,
) {
  try {
    await papers.changePage(page);

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "论文列表加载失败",
      ),
    );
  }
}


async function openEdit(
  paper: Paper,
) {
  loadingDetail.value = true;

  try {
    const detail =
      await getPaper(paper.id);

    editForm.id = detail.id;
    editForm.title = detail.title;
    editForm.authors =
      detail.authors ?? "";
    editForm.abstract =
      detail.abstract ?? "";

    editing.value = true;

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "论文详情加载失败",
      ),
    );

  } finally {
    loadingDetail.value = false;
  }
}


async function saveEdit() {
  const title =
    editForm.title.trim();

  if (!title) {
    ElMessage.warning(
      "论文标题不能为空",
    );
    return;
  }

  saving.value = true;

  try {
    await papers.save(
      editForm.id,
      {
        title,
        authors:
          editForm.authors.trim()
          || null,
        abstract:
          editForm.abstract.trim()
          || null,
      },
    );

    editing.value = false;

    ElMessage.success(
      "论文信息已保存",
    );

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "论文信息保存失败",
      ),
    );

  } finally {
    saving.value = false;
  }
}


async function downloadPaper(
  paper: Paper,
) {
  downloadingId.value = paper.id;

  try {
    const blob =
      await downloadPaperPdf(
        paper.id,
      );

    const url =
      URL.createObjectURL(blob);

    const link =
      document.createElement("a");

    link.href = url;
    link.download = paper.filename;
    document.body.appendChild(link);
    link.click();
    link.remove();
    URL.revokeObjectURL(url);

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "PDF 下载失败",
      ),
    );

  } finally {
    downloadingId.value = "";
  }
}


async function removePaper(
  paper: Paper,
) {
  try {
    await ElMessageBox.confirm(
      `确定永久删除“${paper.title}”吗？`,
      "删除论文",
      {
        type: "warning",
        confirmButtonText:
          "永久删除",
        cancelButtonText: "取消",
      },
    );

  } catch {
    return;
  }

  deletingId.value = paper.id;

  try {
    await papers.remove(paper.id);

    ElMessage.success(
      "论文已删除",
    );

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "论文删除失败",
      ),
    );

  } finally {
    deletingId.value = "";
  }
}


onMounted(
  () => {
    void loadHealth();
    void loadPapers();
  },
);


onUnmounted(
  () => {
    papers.stopPolling();
  },
);
</script>


<template>
  <main class="page">
    <el-alert
      v-if="backendAvailable === false"
      title="无法连接后端服务，请确认 FastAPI 已启动。"
      type="error"
      show-icon
      :closable="false"
      class="connection-alert"
    />

    <header class="toolbar">
      <div>
        <h1>论文库</h1>
        <p class="subtitle">
          管理论文文件与处理状态
        </p>
      </div>

      <PaperUpload />
    </header>

    <form
      class="filters"
      @submit.prevent="search"
    >
      <el-input
        v-model="papers.q"
        clearable
        placeholder="按标题或作者搜索"
        class="search-input"
        @clear="search"
      />

      <el-select
        v-model="papers.status"
        placeholder="全部状态"
        clearable
        class="status-select"
      >
        <el-option
          v-for="(
            label,
            value
          ) in statusLabels"
          :key="value"
          :label="label"
          :value="value"
        />
      </el-select>

      <el-button
        native-type="submit"
        :loading="papers.loading"
      >
        查询
      </el-button>
    </form>

    <el-alert
      v-if="papers.loadError"
      :title="papers.loadError"
      type="error"
      show-icon
      :closable="false"
      class="list-alert"
    />

    <el-table
      :data="papers.items"
      v-loading="papers.loading"
      row-key="id"
    >
      <el-table-column
        prop="title"
        label="论文"
        min-width="280"
        show-overflow-tooltip
      />

      <el-table-column
        prop="authors"
        label="作者"
        min-width="190"
        show-overflow-tooltip
      />

      <el-table-column
        label="来源"
        width="110"
      >
        <template #default="scope">
          {{ sourceLabel(
            scope.row.source
          ) }}
        </template>
      </el-table-column>

      <el-table-column
        label="状态"
        width="130"
      >
        <template #default="scope">
          <el-tooltip
            :disabled="!
              scope.row.error_message
            "
            :content="
              scope.row.error_message
            "
          >
            <el-tag
              :type="statusType(
                scope.row.status
              )"
            >
              {{ statusLabel(
                scope.row.status
              ) }}
            </el-tag>
          </el-tooltip>
        </template>
      </el-table-column>

      <el-table-column
        prop="page_count"
        label="页数"
        width="80"
      />

      <el-table-column
        label="操作"
        width="250"
        fixed="right"
      >
        <template #default="scope">
          <el-button
            link
            type="primary"
            :loading="loadingDetail"
            @click="openEdit(scope.row)"
          >
            编辑
          </el-button>

          <el-button
            link
            type="primary"
            :loading="
              downloadingId
                === scope.row.id
            "
            @click="
              downloadPaper(scope.row)
            "
          >
            下载
          </el-button>

          <el-button
            link
            type="danger"
            :loading="
              deletingId
                === scope.row.id
            "
            @click="
              removePaper(scope.row)
            "
          >
            删除
          </el-button>
        </template>
      </el-table-column>

      <template #empty>
        暂无论文
      </template>
    </el-table>

    <el-pagination
      v-if="papers.total > 0"
      class="pagination"
      background
      layout="total, prev, pager, next"
      :total="papers.total"
      :page-size="papers.pageSize"
      :current-page="papers.page"
      @current-change="changePage"
    />

    <el-dialog
      v-model="editing"
      title="编辑论文信息"
      width="620px"
      destroy-on-close
    >
      <el-form
        label-position="top"
      >
        <el-form-item
          label="标题"
          required
        >
          <el-input
            v-model="editForm.title"
            maxlength="500"
            show-word-limit
          />
        </el-form-item>

        <el-form-item label="作者">
          <el-input
            v-model="editForm.authors"
            type="textarea"
            :rows="2"
          />
        </el-form-item>

        <el-form-item label="摘要">
          <el-input
            v-model="editForm.abstract"
            type="textarea"
            :rows="7"
          />
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button
          @click="editing = false"
        >
          取消
        </el-button>

        <el-button
          type="primary"
          :loading="saving"
          @click="saveEdit"
        >
          保存
        </el-button>
      </template>
    </el-dialog>
  </main>
</template>


<style scoped>
.page {
  padding: 24px;
}

.connection-alert,
.list-alert {
  margin-bottom: 16px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 24px;
}

.toolbar h1 {
  margin: 0;
  font-size: 28px;
}

.subtitle {
  margin: 8px 0 0;
  color: var(--el-text-color-secondary);
}

.filters {
  display: flex;
  gap: 12px;
  margin-bottom: 20px;
}

.search-input {
  max-width: 360px;
}

.status-select {
  width: 180px;
}

.pagination {
  justify-content: flex-end;
  margin-top: 20px;
}
</style>
