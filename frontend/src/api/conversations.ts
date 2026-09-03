import {
    apiFetch,
  } from "./client";
  
  
  export interface Citation {
    id: string;
    source_number: number;
  
    paper_id: string;
    paper_title: string;
  
    page_number: number;
    chunk_id: string;
  }
  
  
  export interface Message {
    id: string;
  
    role:
      | "user"
      | "assistant";
  
    content: string;
  
    sequence: number;
    created_at: string;
  
    citations: Citation[];
  }
  
  
  export interface Conversation {
    id: string;
  
    title: string;
  
    scope_type:
      | "paper"
      | "group";
  
    scope_id: string;
  
    model_provider: string;
    model_name: string;
  
    supports_tool_calling:
      boolean;
  
    created_at: string;
    updated_at: string;
  }
  
  
  export function listConversations(
    scopeType: string,
    scopeId: string,
  ) {
    const query =
      new URLSearchParams({
        scope_type:
          scopeType,
  
        scope_id:
          scopeId,
      });
  
    return apiFetch<
      Conversation[]
    >(
      `/api/conversations?${
        query.toString()
      }`,
    );
  }
  
  
  export function createConversation(
    scopeType:
      "paper" | "group",
  
    scopeId: string,
  ) {
    return apiFetch<
      Conversation
    >(
      "/api/conversations",
  
      {
        method: "POST",
  
        headers: {
          "Content-Type":
            "application/json",
        },
  
        body:
          JSON.stringify({
            scope_type:
              scopeType,
  
            scope_id:
              scopeId,
  
            title:
              "新会话",
          }),
      },
    );
  }
  
  
  export function listMessages(
    conversationId: string,
  ) {
    return apiFetch<
      Message[]
    >(
      `/api/conversations/${
        encodeURIComponent(
          conversationId,
        )
      }/messages`,
    );
  }
  
  
  export function deleteConversation(
    conversationId: string,
  ) {
    return apiFetch<void>(
      `/api/conversations/${
        encodeURIComponent(
          conversationId,
        )
      }`,
  
      {
        method: "DELETE",
      },
    );
  }