<script setup lang="ts">
import {
  ref,
} from "vue";

import {
  useRouter,
} from "vue-router";

import {
  ElMessage,
} from "element-plus";

import {
  importArxiv,
  searchArxiv,
} from "../api/arxiv";

import type {
  ArxivPaper,
} from "../api/arxiv";


const router = useRouter();


const query = ref("");

const directImportValue =
  ref("");

const results =
  ref<ArxivPaper[]>([]);


const searching =
  ref(false);

const directImporting =
  ref(false);

const importingIds =
  ref<Set<string>>(
    new Set(),
  );


function formatAuthors(
  authors: string[],
) {
  if (
    !authors
    || authors.length === 0
  ) {
    return "-";
  }

  return authors.join(", ");
}


function formatDate(
  value: string | null,
) {
  if (!value) {
    return "-";
  }

  const date =
    new Date(value);

  if (
    Number.isNaN(
      date.getTime(),
    )
  ) {
    return value;
  }

  return date.toLocaleDateString();
}


async function handleSearch() {
  const keyword =
    query.value.trim();

  if (!keyword) {
    ElMessage.warning(
      "请输入搜索关键词",
    );

    return;
  }

  searching.value = true;

  try {
    results.value =
      await searchArxiv(
        keyword,
      );

    if (
      results.value.length
      === 0
    ) {
      ElMessage.info(
        "没有找到匹配的论文",
      );
    }

  } catch (error) {
    console.error(
      error,
    );

    ElMessage.error(
      "Arxiv 搜索失败",
    );

  } finally {
    searching.value = false;
  }
}


async function handleDirectImport() {
  const value =
    directImportValue.value.trim();

  if (!value) {
    ElMessage.warning(
      "请输入 Arxiv ID 或链接",
    );

    return;
  }

  directImporting.value = true;

  try {
    const paper =
      await importArxiv(
        value,
      );

    directImportValue.value =
      "";

    ElMessage.success(
      `已加入导入队列：${paper.title}`,
    );

  } catch (error) {
    console.error(
      error,
    );

    ElMessage.error(
      "Arxiv 论文导入失败",
    );

  } finally {
    directImporting.value =
      false;
  }
}


async function handleImport(
  paper: ArxivPaper,
) {
  if (
    importingIds.value.has(
      paper.paper_id,
    )
  ) {
    return;
  }

  importingIds.value.add(
    paper.paper_id,
  );

  try {
    const imported =
      await importArxiv(
        paper.paper_id,
      );

    ElMessage.success(
      `已加入导入队列：${imported.title}`,
    );

  } catch (error) {
    console.error(
      error,
    );

    ElMessage.error(
      `导入失败：${paper.title}`,
    );

  } finally {
    importingIds.value.delete(
      paper.paper_id,
    );

    // Set 内部修改不会总是触发模板更新，
    // 所以重新赋值一个新 Set。
    importingIds.value =
      new Set(
        importingIds.value,
      );
  }
}


function goToLibrary() {
  void router.push(
    "/library",
  );
}
</script>


<template>
  <main class="arxiv-page">

    <div class="page-header">

      <div>
        <h1>Arxiv 导入</h1>

        <p class="page-description">
          搜索 Arxiv 论文，或通过 Arxiv ID / 链接直接导入论文库
        </p>
      </div>


      <el-button
        @click="goToLibrary"
      >
        返回论文库
      </el-button>

    </div>


    <!-- 直接导入 -->
    <el-card
      class="section-card"
      shadow="never"
    >

      <template #header>
        <div class="card-title">
          通过 ID 或链接导入
        </div>
      </template>


      <div class="direct-import-row">

        <el-input
          v-model="
            directImportValue
          "
          clearable
          placeholder="例如 1706.03762 或 https://arxiv.org/abs/1706.03762"
          @keyup.enter="
            handleDirectImport
          "
        />


        <el-button
          type="primary"
          :loading="
            directImporting
          "
          @click="
            handleDirectImport
          "
        >
          导入
        </el-button>

      </div>

    </el-card>


    <!-- 搜索 -->
    <el-card
      class="section-card"
      shadow="never"
    >

      <template #header>
        <div class="card-title">
          搜索 Arxiv
        </div>
      </template>


      <div class="search-row">

        <el-input
          v-model="query"
          clearable
          placeholder="输入论文标题、关键词或作者"
          @keyup.enter="
            handleSearch
          "
        />


        <el-button
          type="primary"
          :loading="searching"
          @click="
            handleSearch
          "
        >
          搜索
        </el-button>

      </div>

    </el-card>


    <!-- 搜索结果 -->
    <el-card
      class="section-card"
      shadow="never"
    >

      <template #header>

        <div class="results-header">

          <span class="card-title">
            搜索结果
          </span>

          <span
            v-if="
              results.length > 0
            "
            class="result-count"
          >
            共 {{ results.length }} 篇
          </span>

        </div>

      </template>


      <div
        v-loading="searching"
        class="results-container"
      >

        <el-empty
          v-if="
            !searching
            &&
            results.length === 0
          "
          description="暂无搜索结果"
        />


        <div
          v-for="paper in results"
          :key="paper.paper_id"
          class="paper-card"
        >

          <div class="paper-main">

            <div class="paper-title-row">

              <h3 class="paper-title">
                {{ paper.title }}
              </h3>


              <el-button
                type="primary"
                size="small"
                :loading="
                  importingIds.has(
                    paper.paper_id,
                  )
                "
                @click="
                  handleImport(
                    paper,
                  )
                "
              >
                导入
              </el-button>

            </div>


            <div class="paper-meta">

              <span>
                <strong>
                  Arxiv ID：
                </strong>

                {{ paper.paper_id }}
              </span>


              <span>
                <strong>
                  发布时间：
                </strong>

                {{
                  formatDate(
                    paper.published,
                  )
                }}
              </span>

            </div>


            <div class="paper-authors">

              <strong>
                作者：
              </strong>

              {{
                formatAuthors(
                  paper.authors,
                )
              }}

            </div>


            <div
              v-if="
                paper.categories
                &&
                paper.categories.length > 0
              "
              class="paper-categories"
            >

              <strong>
                分类：
              </strong>


              <el-tag
                v-for="
                  category
                  in paper.categories
                "
                :key="category"
                size="small"
                effect="plain"
              >
                {{ category }}
              </el-tag>

            </div>


            <div
              v-if="paper.abstract"
              class="paper-abstract"
            >

              <strong>
                摘要：
              </strong>

              <p>
                {{ paper.abstract }}
              </p>

            </div>

          </div>

        </div>

      </div>

    </el-card>

  </main>
</template>


<style scoped>
.arxiv-page {
  padding: 24px;
}


.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 24px;
  margin-bottom: 20px;
}


.page-header h1 {
  margin: 0;
}


.page-description {
  margin-top: 8px;
  margin-bottom: 0;
  color: var(
    --el-text-color-secondary
  );
}


.section-card {
  margin-bottom: 20px;
}


.card-title {
  font-weight: 600;
}


.direct-import-row,
.search-row {
  display: flex;
  align-items: center;
  gap: 12px;
}


.direct-import-row
.el-input,
.search-row
.el-input {
  max-width: 760px;
}


.results-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}


.result-count {
  font-size: 14px;
  color: var(
    --el-text-color-secondary
  );
}


.results-container {
  min-height: 120px;
}


.paper-card {
  padding: 20px 0;
  border-bottom:
    1px solid
    var(
      --el-border-color-lighter
    );
}


.paper-card:first-child {
  padding-top: 4px;
}


.paper-card:last-child {
  border-bottom: none;
  padding-bottom: 4px;
}


.paper-main {
  width: 100%;
}


.paper-title-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
}


.paper-title {
  flex: 1;
  margin: 0;
  font-size: 17px;
  line-height: 1.5;
}


.paper-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 20px;
  margin-top: 12px;

  font-size: 14px;

  color: var(
    --el-text-color-secondary
  );
}


.paper-authors {
  margin-top: 10px;
  font-size: 14px;
  line-height: 1.6;
}


.paper-categories {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 10px;
  font-size: 14px;
}


.paper-abstract {
  margin-top: 12px;
  font-size: 14px;
  line-height: 1.7;
}


.paper-abstract p {
  margin: 6px 0 0;
  color: var(
    --el-text-color-regular
  );
}
</style>