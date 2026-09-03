<script setup lang="ts">
import {
  onMounted,
  ref,
} from "vue";

import {
  useRoute,
} from "vue-router";

import {
  ElMessage,
} from "element-plus";

import {
  createConversation,
  listConversations,
  listMessages,
} from "../api/conversations";

import type {
  Conversation,
  Message,
} from "../api/conversations";

import {
  streamChat,
} from "../api/chat";


const route = useRoute();


const scopeType =
  route.params.scopeType as "paper" | "group";

const scopeId =
  String(
    route.params.scopeId,
  );


const conversation =
  ref<
    Conversation | null
  >(null);

const messages =
  ref<Message[]>([]);

const input = ref("");

const sending =
  ref(false);

const streamingText =
  ref("");

const currentQuestion =
  ref("");

let controller:
  AbortController | null =
    null;


async function load() {

  let conversations =
    await listConversations(
      scopeType,
      scopeId,
    );

  if (
    conversations.length
    === 0
  ) {
    const created =
      await createConversation(
        scopeType,
        scopeId,
      );

    conversations = [
      created,
    ];
  }

  conversation.value =
    conversations[0];

  messages.value =
    await listMessages(
      conversation.value.id,
    );
}


async function send() {

  if (
    !conversation.value
  ) {
    return;
  }

  const content =
    input.value.trim();

  if (!content) {
    return;
  }

  input.value = "";

  currentQuestion.value =
    content;

  streamingText.value = "";

  sending.value = true;

  controller =
    new AbortController();

  let streamFailure:
    string | null = null;

  try {

    await streamChat(
      conversation.value.id,

      content,

      {
        onEvent(
          event,
          data,
        ) {

          if (
            event
            === "delta"
          ) {
            const payload =
              data as {
                text?: string;
              };

            streamingText.value +=
              payload.text ?? "";
          }

          if (
            event
            === "failure"
          ) {
            const payload =
              data as {
                message?: string;
              };

            streamFailure =
              payload.message
              ?? "生成失败";
          }
        },
      },

      controller.signal,
    );

    messages.value =
      await listMessages(
        conversation.value.id,
      );

    if (streamFailure) {
      ElMessage.error(
        streamFailure,
      );
    }

  } catch (error) {

    if (
      error instanceof DOMException
      &&
      error.name
      === "AbortError"
    ) {
      ElMessage.info(
        "已停止生成"
      );

    } else {
      ElMessage.error(
        "发送消息失败"
      );
    }

    messages.value =
      await listMessages(
        conversation.value.id,
      );

  } finally {

    sending.value = false;

    streamingText.value = "";

    currentQuestion.value = "";

    controller = null;
  }
}


function stop() {
  controller?.abort();
}


onMounted(
  () => {
    void load();
  },
);
</script>


<template>
  <main class="chat-page">

    <h1>
      {{
        scopeType === "paper"
          ? "论文问答"
          : "分组问答"
      }}
    </h1>

    <div class="messages">

      <div
        v-for="message in messages"
        :key="message.id"
        :class="[
          'message',
          message.role
        ]"
      >
        <strong>
          {{
            message.role
              === "user"
              ? "你"
              : "Research Copilot"
          }}
        </strong>

        <div class="content">
          {{ message.content }}
        </div>
      </div>


      <div
        v-if="currentQuestion"
        class="message user"
      >
        <strong>你</strong>

        <div class="content">
          {{ currentQuestion }}
        </div>
      </div>


      <div
        v-if="sending"
        class="message assistant"
      >
        <strong>
          Research Copilot
        </strong>

        <div class="content">
          {{
            streamingText
              || "思考中..."
          }}
        </div>
      </div>

    </div>


    <div class="composer">

      <el-input
        v-model="input"
        type="textarea"
        :rows="4"
        placeholder="输入问题"
        @keydown.ctrl.enter="
          send
        "
      />


      <el-button
        v-if="!sending"
        type="primary"
        @click="send"
      >
        发送
      </el-button>


      <el-button
        v-else
        type="danger"
        @click="stop"
      >
        停止生成
      </el-button>

    </div>

  </main>
</template>


<style scoped>
.chat-page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

.messages {
  min-height: 500px;
  margin: 24px 0;
}

.message {
  margin-bottom: 20px;
  padding: 16px;
  border-radius: 8px;
}

.message.user {
  background:
    var(--el-fill-color-light);
}

.message.assistant {
  background:
    var(--el-bg-color);
  border:
    1px solid
    var(--el-border-color);
}

.content {
  margin-top: 8px;
  white-space: pre-wrap;
  line-height: 1.7;
}

.composer {
  display: flex;
  gap: 12px;
  align-items: flex-end;
}
</style>