<script setup lang="ts">
import {
  ref,
} from "vue";

import {
  ElMessage,
} from "element-plus";

import {
  formatApiError,
} from "../api/client";

import {
  uploadPaper,
} from "../api/papers";

import {
  usePapersStore,
} from "../stores/papers";


const papers =
  usePapersStore();

const uploading =
  ref(false);

const fileInput =
  ref<HTMLInputElement | null>(
    null,
  );


function chooseFile() {
  if (uploading.value) {
    return;
  }

  fileInput.value?.click();
}


async function upload(
  event: Event,
) {
  const input =
    event.target as HTMLInputElement;

  const file =
    input.files?.[0];

  if (!file) {
    return;
  }

  if (
    file.type
    !== "application/pdf"
  ) {
    ElMessage.error(
      "请选择 PDF 文件",
    );

    return;
  }

  uploading.value = true;

  try {
    await uploadPaper(file);

    ElMessage.success(
      "论文已加入处理队列",
    );

    papers.q = "";
    papers.status = "";
    papers.page = 1;

    await papers.load();

  } catch (error) {
    ElMessage.error(
      formatApiError(
        error,
        "上传失败",
      ),
    );

  } finally {
    uploading.value = false;

    input.value = "";
  }
}
</script>


<template>
  <span>
    <input
      ref="fileInput"
      type="file"
      accept="application/pdf"
      hidden
      :disabled="uploading"
      @change="upload"
    />

    <el-button
      type="primary"
      native-type="button"
      :loading="uploading"
      @click="chooseFile"
    >
      上传 PDF
    </el-button>
  </span>
</template>
