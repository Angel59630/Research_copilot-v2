import {
    createRouter,
    createWebHistory,
  } from "vue-router";
  
  import LibraryView
    from "./views/LibraryView.vue";
  
  
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
      ],
    });
  
  
  export default router;