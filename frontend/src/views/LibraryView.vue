<script setup lang="ts">
import {
  onMounted,
} from "vue";

import PaperUpload
  from "../components/PaperUpload.vue";

import {
  usePapersStore,
} from "../stores/papers";


const papers =
  usePapersStore();


onMounted(
  () => {
    void papers.load();
  },
);
</script>


<template>
  <main class="page">
    <header class="toolbar">
      <h1>
        论文库
      </h1>

      <PaperUpload />
    </header>

    <el-table
      :data="papers.items"
      v-loading="papers.loading"
    >
      <el-table-column
        prop="title"
        label="论文"
        min-width="320"
      />

      <el-table-column
        prop="authors"
        label="作者"
        min-width="220"
      />

      <el-table-column
        prop="status"
        label="状态"
        width="130"
      />

      <el-table-column
        prop="page_count"
        label="页数"
        width="100"
      />
    </el-table>
  </main>
</template>


<style scoped>
.page {
  padding: 24px;
}

.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 24px;
}
</style>