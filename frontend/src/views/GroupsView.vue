<script setup lang="ts">
import {
  onMounted,
  ref,
} from "vue";

import {
  useRouter,
} from "vue-router";

import {
  ElMessage,
  ElMessageBox,
} from "element-plus";

import {
  createGroup,
  deleteGroup,
  listGroups,
} from "../api/groups";

import type {
  Group,
} from "../api/groups";


const router = useRouter();

const groups = ref<Group[]>([]);

const loading = ref(false);

const creating = ref(false);

const deletingId = ref<string | null>(
  null,
);

const newGroupName = ref("");


async function loadGroups() {
  loading.value = true;

  try {
    groups.value =
      await listGroups();

  } catch (error) {
    console.error(error);

    ElMessage.error(
      "分组加载失败",
    );

  } finally {
    loading.value = false;
  }
}


async function addGroup() {
  const name =
    newGroupName.value.trim();

  if (!name) {
    ElMessage.warning(
      "请输入分组名称",
    );

    return;
  }

  creating.value = true;

  try {
    await createGroup(name);

    newGroupName.value = "";

    await loadGroups();

    ElMessage.success(
      "分组创建成功",
    );

  } catch (error) {
    console.error(error);

    ElMessage.error(
      "分组创建失败",
    );

  } finally {
    creating.value = false;
  }
}


async function removeGroup(
  group: Group,
) {
  try {
    await ElMessageBox.confirm(
      `确定删除分组“${group.name}”吗？论文不会被删除。`,
      "删除分组",
      {
        confirmButtonText:
          "删除",

        cancelButtonText:
          "取消",

        type:
          "warning",
      },
    );

  } catch {
    return;
  }

  deletingId.value =
    group.id;

  try {
    await deleteGroup(
      group.id,
    );

    await loadGroups();

    ElMessage.success(
      "分组已删除",
    );

  } catch (error) {
    console.error(error);

    ElMessage.error(
      "删除分组失败",
    );

  } finally {
    deletingId.value =
      null;
  }
}


function openGroupChat(
  group: Group,
) {
  void router.push(
    `/chat/group/${
      encodeURIComponent(
        group.id,
      )
    }`,
  );
}


onMounted(() => {
  void loadGroups();
});
</script>


<template>
  <main class="groups-page">

    <div class="page-header">
      <div>
        <h1>论文分组</h1>

        <p class="description">
          创建论文分组，并基于整个分组进行 RAG 问答
        </p>
      </div>
    </div>


    <el-card
      class="create-card"
      shadow="never"
    >
      <div class="create-row">

        <el-input
          v-model="newGroupName"
          placeholder="输入分组名称"
          clearable
          @keyup.enter="addGroup"
        />

        <el-button
          type="primary"
          :loading="creating"
          @click="addGroup"
        >
          新建分组
        </el-button>

      </div>
    </el-card>


    <el-table
      v-loading="loading"
      :data="groups"
      style="width: 100%"
    >

      <el-table-column
        prop="name"
        label="分组名称"
        min-width="220"
      />

      <el-table-column
        prop="description"
        label="描述"
        min-width="300"
      >
        <template #default="scope">
          {{
            scope.row.description
              || "-"
          }}
        </template>
      </el-table-column>


      <el-table-column
        prop="created_at"
        label="创建时间"
        width="200"
      >
        <template #default="scope">
          {{
            new Date(
              scope.row.created_at,
            ).toLocaleString()
          }}
        </template>
      </el-table-column>


      <el-table-column
        label="操作"
        width="180"
        fixed="right"
      >
        <template #default="scope">

          <el-button
            link
            type="primary"
            @click="
              openGroupChat(
                scope.row,
              )
            "
          >
            问答
          </el-button>

          <el-button
            link
            type="danger"
            :loading="
              deletingId
                === scope.row.id
            "
            @click="
              removeGroup(
                scope.row,
              )
            "
          >
            删除
          </el-button>

        </template>
      </el-table-column>

    </el-table>


    <el-empty
      v-if="
        !loading
        && groups.length === 0
      "
      description="暂无论文分组"
    />

  </main>
</template>


<style scoped>
.groups-page {
  padding: 24px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}

.page-header h1 {
  margin: 0;
}

.description {
  margin-top: 8px;
  color: var(--el-text-color-secondary);
}

.create-card {
  margin-bottom: 20px;
}

.create-row {
  display: flex;
  gap: 12px;
  max-width: 600px;
}
</style>