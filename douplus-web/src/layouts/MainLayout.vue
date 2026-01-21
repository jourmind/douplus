<template>
  <div class="main-layout" :class="{ 'sidebar-collapsed': isCollapsed }">
    <!-- 侧边栏 -->
    <aside class="sidebar" :class="{ collapsed: isCollapsed }">
      <div class="logo">
        <template v-if="!isCollapsed">
          <span style="color: #ff6b35">DOU</span>+
        </template>
        <template v-else>
          <span style="color: #ff6b35; font-size: 16px;">D+</span>
        </template>
      </div>
      
      <div class="menu">
        <el-menu
          :default-active="activeMenu"
          :router="true"
          :collapse="isCollapsed"
          background-color="transparent"
          text-color="#9ca3af"
          active-text-color="#ff6b35"
        >
          <!-- 首页概览 -->
          <el-menu-item index="/dashboard">
            <el-icon><HomeFilled /></el-icon>
            <template #title><span>首页概览</span></template>
          </el-menu-item>
          
          <!-- 账号管理 -->
          <el-menu-item index="/account">
            <el-icon><User /></el-icon>
            <template #title><span>账号管理</span></template>
          </el-menu-item>
          
          <!-- DOU+监控 -->
          <el-sub-menu index="douplus-menu">
            <template #title>
              <el-icon><VideoPlay /></el-icon>
              <span>DOU+监控</span>
            </template>
            <el-menu-item index="/douplus/create">DOU+投放</el-menu-item>
            <el-menu-item index="/douplus/records">DOU+投放记录</el-menu-item>
          </el-sub-menu>
          
          <!-- 评论管理 -->
          <el-sub-menu index="comment-menu">
            <template #title>
              <el-icon><ChatDotRound /></el-icon>
              <span>评论管理</span>
            </template>
            <el-menu-item index="/comment/list">实时删除新增评论</el-menu-item>
            <el-menu-item index="/comment/negative">实时删除负面评论</el-menu-item>
            <el-menu-item index="/comment/blacklist">黑名单管理</el-menu-item>
          </el-sub-menu>
        </el-menu>
      </div>
      
      <!-- 收起/展开按钮 -->
      <div class="collapse-btn" @click="toggleSidebar">
        <el-icon :size="18">
          <Fold v-if="!isCollapsed" />
          <Expand v-else />
        </el-icon>
      </div>
    </aside>
    
    <!-- 主内容区 -->
    <div class="main-container">
      <!-- 顶部导航 -->
      <header class="header">
        <div class="header-left">
          <el-icon class="toggle-btn" :size="20" @click="toggleSidebar">
            <Fold v-if="!isCollapsed" />
            <Expand v-else />
          </el-icon>
          <div class="tabs">
          <el-tag 
            v-for="tab in tabs" 
            :key="tab.path"
            :type="tab.path === route.path ? '' : 'info'"
            :closable="tabs.length > 1"
            style="cursor: pointer; margin-right: 8px;"
            @click="router.push(tab.path)"
            @close="closeTab(tab)"
          >
            {{ tab.title }}
          </el-tag>
          </div>
        </div>
        
        <div class="user-info">
          <el-dropdown>
            <span style="cursor: pointer; display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="32" :src="userStore.userInfo?.avatar">
                {{ userStore.userInfo?.nickname?.charAt(0) || 'U' }}
              </el-avatar>
              <span>{{ userStore.userInfo?.nickname || '用户' }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="showPasswordDialog = true">修改密码</el-dropdown-item>
                <el-dropdown-item @click="showInvestPwdDialog = true">投放密码</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>
      
      <!-- 页面内容 -->
      <main class="main-content">
        <router-view />
      </main>
    </div>
    
    <!-- 修改密码对话框 -->
    <el-dialog v-model="showPasswordDialog" title="修改密码" width="400px">
      <el-form :model="passwordForm" label-width="80px">
        <el-form-item label="旧密码">
          <el-input v-model="passwordForm.oldPassword" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.newPassword" type="password" show-password />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showPasswordDialog = false">取消</el-button>
        <el-button type="primary" @click="handleChangePassword">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 投放密码对话框 -->
    <el-dialog v-model="showInvestPwdDialog" title="设置投放密码" width="400px">
      <el-form :model="investPwdForm" label-width="80px">
        <el-form-item label="投放密码">
          <el-input v-model="investPwdForm.investPassword" type="password" show-password placeholder="设置投放密码（投放时需要验证）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showInvestPwdDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSetInvestPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, reactive, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { HomeFilled, ChatDotRound, VideoPlay, User, ArrowDown, Fold, Expand } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import { changePassword, setInvestPassword } from '@/api/auth'

const route = useRoute()
const router = useRouter()
const userStore = useUserStore()

// 侧边栏收起状态
const isCollapsed = ref(false)

const toggleSidebar = () => {
  isCollapsed.value = !isCollapsed.value
}

// 标签页
interface Tab {
  path: string
  title: string
}
const tabs = ref<Tab[]>([])

// 当前激活菜单
const activeMenu = computed(() => route.path)

// 监听路由变化，添加标签
watch(() => route.path, (path) => {
  const title = route.meta.title as string || '页面'
  if (!tabs.value.find(t => t.path === path)) {
    tabs.value.push({ path, title })
  }
}, { immediate: true })

// 关闭标签
const closeTab = (tab: Tab) => {
  const index = tabs.value.findIndex(t => t.path === tab.path)
  if (index > -1) {
    tabs.value.splice(index, 1)
    if (route.path === tab.path && tabs.value.length > 0) {
      router.push(tabs.value[tabs.value.length - 1].path)
    }
  }
}

// 退出登录
const handleLogout = () => {
  userStore.logout()
  router.push('/login')
  ElMessage.success('已退出登录')
}

// 修改密码
const showPasswordDialog = ref(false)
const passwordForm = reactive({
  oldPassword: '',
  newPassword: ''
})

const handleChangePassword = async () => {
  try {
    await changePassword(passwordForm)
    ElMessage.success('密码修改成功')
    showPasswordDialog.value = false
    passwordForm.oldPassword = ''
    passwordForm.newPassword = ''
  } catch (error) {
    // 错误已在拦截器处理
  }
}

// 投放密码
const showInvestPwdDialog = ref(false)
const investPwdForm = reactive({
  investPassword: ''
})

const handleSetInvestPassword = async () => {
  try {
    await setInvestPassword(investPwdForm.investPassword)
    ElMessage.success('投放密码设置成功')
    showInvestPwdDialog.value = false
    investPwdForm.investPassword = ''
    userStore.fetchUserInfo()
  } catch (error) {
    // 错误已在拦截器处理
  }
}

onMounted(() => {
  userStore.fetchUserInfo()
})
</script>
