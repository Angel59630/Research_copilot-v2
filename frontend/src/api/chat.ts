import {
    API_BASE,
  } from "./client";
  
  
  export interface StreamHandlers {
    onEvent: (
      event: string,
      data: unknown,
    ) => void;
  }
  
  
  export async function streamChat(
    conversationId: string,
    content: string,
    handlers: StreamHandlers,
    signal: AbortSignal,
  ): Promise<void> {
    const response =
      await fetch(
        `${API_BASE}/api/conversations/${conversationId}/messages`,
        {
          method:
            "POST",
  
          headers: {
            "Content-Type":
              "application/json",
          },
  
          body:
            JSON.stringify({
              content,
            }),
  
          signal,
        },
      );
  
    if (!response.ok) {
      throw new Error(
        `HTTP ${response.status}`,
      );
    }
  
    if (!response.body) {
      throw new Error(
        "浏览器不支持流式读取"
      );
    }
  
    const reader =
      response.body.getReader();
  
    const decoder =
      new TextDecoder(
        "utf-8"
      );
  
    let buffer = "";
  
    while (true) {
      const {
        value,
        done,
      } = await reader.read();
  
      if (done) {
        break;
      }
  
      buffer += decoder.decode(
        value,
        {
          stream: true,
        },
      );
  
      const blocks =
        buffer.split(
          "\n\n"
        );
  
      buffer =
        blocks.pop() ?? "";
  
      for (
        const block
        of blocks
      ) {
        let event =
          "message";
  
        const dataLines:
          string[] = [];
  
        for (
          const line
          of block.split("\n")
        ) {
          if (
            line.startsWith(
              "event:"
            )
          ) {
            event =
              line
                .slice(6)
                .trim();
          }
  
          if (
            line.startsWith(
              "data:"
            )
          ) {
            dataLines.push(
              line
                .slice(5)
                .trim(),
            );
          }
        }
  
        const rawData =
          dataLines.join(
            "\n"
          );
  
        if (!rawData) {
          continue;
        }
  
        let parsed:
          unknown;
  
        try {
          parsed =
            JSON.parse(
              rawData
            );
        } catch {
          parsed =
            rawData;
        }
  
        handlers.onEvent(
          event,
          parsed,
        );
      }
    }
  }