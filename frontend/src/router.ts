import {
  createRouter,
  createWebHistory,
} from "vue-router";

import LibraryView
  from "./views/LibraryView.vue";

import GroupsView
  from "./views/GroupsView.vue";

import ArxivView
  from "./views/ArxivView.vue";

import ChatView
  from "./views/ChatView.vue";


const router =
  createRouter({

    history:
      createWebHistory(),

    routes: [

      {
        path: "/",

        redirect:
          "/library",
      },

      {
        path:
          "/library",

        component:
          LibraryView,
      },

      {
        path:
          "/groups",

        component:
          GroupsView,
      },

      {
        path:
          "/arxiv",

        component:
          ArxivView,
      },

      {
        path:
          "/chat/:scopeType/:scopeId",

        component:
          ChatView,
      },
    ],
  });


export default router;