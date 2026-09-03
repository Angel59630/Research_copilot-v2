import {
    apiFetch,
  } from "./client";
  
  import type {
    Paper,
  } from "./papers";
  
  
  export interface Group {
    id: string;
  
    name: string;
  
    description:
      string | null;
  
    created_at: string;
    updated_at: string;
  }
  
  
  export function listGroups() {
    return apiFetch<
      Group[]
    >(
      "/api/groups",
    );
  }
  
  
  export function createGroup(
    name: string,
  ) {
    return apiFetch<
      Group
    >(
      "/api/groups",
  
      {
        method: "POST",
  
        headers: {
          "Content-Type":
            "application/json",
        },
  
        body:
          JSON.stringify({
            name,
          }),
      },
    );
  }
  
  
  export function deleteGroup(
    groupId: string,
  ) {
    return apiFetch<void>(
      `/api/groups/${
        encodeURIComponent(
          groupId,
        )
      }`,
  
      {
        method: "DELETE",
      },
    );
  }
  
  
  export function listGroupPapers(
    groupId: string,
  ) {
    return apiFetch<
      Paper[]
    >(
      `/api/groups/${
        encodeURIComponent(
          groupId,
        )
      }/papers`,
    );
  }
  
  
  export function addPaperToGroup(
    groupId: string,
    paperId: string,
  ) {
    return apiFetch<void>(
      `/api/groups/${
        encodeURIComponent(
          groupId,
        )
      }/papers/${
        encodeURIComponent(
          paperId,
        )
      }`,
  
      {
        method: "PUT",
      },
    );
  }
  
  
  export function removePaperFromGroup(
    groupId: string,
    paperId: string,
  ) {
    return apiFetch<void>(
      `/api/groups/${
        encodeURIComponent(
          groupId,
        )
      }/papers/${
        encodeURIComponent(
          paperId,
        )
      }`,
  
      {
        method: "DELETE",
      },
    );
  }