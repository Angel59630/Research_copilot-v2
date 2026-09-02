<script setup lang="ts">
import {
  ref,
} from "vue";

import {
  ElMessage,
} from "element-plus";

import {
  API_BASE,
} from "../api/client";

import {
  usePapersStore,
} from "../stores/papers";


const papers =
  usePapersStore();

const uploading =
  ref(false);


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

  const form =
    new FormData();

  form.append(
    "file",
    file,
  );

  uploading.value = true;

  try {
    const response =
      await fetch(
        `${API_BASE}/api/imports/local`,
        {
          method: "POST",
          body: form,
        },
      );

    if (!response.ok) {
      const body =
        await response.json();

      throw new Error(
        body.detail ??
          "上传失败",
      );
    }

    ElMessage.success(
      "论文已加入处理队列",
    );

    await papers.load();

  } catch (error) {
    ElMessage.error(
      error instanceof Error
        ? error.message
        : "上传失败",
    );

  } finally {
    uploading.value = false;

    input.value = "";
  }
}
</script>


<template>
  <label>
    <input
      type="file"
      accept="application/pdf"
      hidden
      :disabled="uploading"
      @change="upload"
    />

    <el-button
      type="primary"
      :loading="uploading"
    >
      上传 PDF
    </el-button>
  </label>
</template>