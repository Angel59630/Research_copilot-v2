<template>
  <el-container class="app">
    <el-aside width="220px">
      <div class="brand">
        Research Copilot
      </div>

      <el-menu
        router
        default-active="/library"
      >
        <el-menu-item
          index="/library"
        >
          论文库
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-main>
      <router-view />
    </el-main>
  </el-container>
</template>

<style>
html,
body,
#app,
.app {
  height: 100%;
  margin: 0;
}

body {
  font-family:
    Inter,
    "Microsoft YaHei",
    sans-serif;
}

.brand {
  padding: 24px;
  font-weight: 700;
  font-size: 18px;
}
</style>