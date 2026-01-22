<template>
  <div class="account-page">
    <!-- 顶部标题和操作区 -->
    <div class="page-header">
      <div class="header-left">
        <h2 class="page-title">DOU+ <el-icon class="help-icon"><QuestionFilled /></el-icon></h2>
      </div>
      <div class="header-right">
        <span class="help-link">如何绑定DOU+？</span>
      </div>
    </div>

    <!-- 操作栏 -->
    <div class="action-bar">
      <div class="action-left">
        <el-button type="primary" @click="handleAddAccount">
          <el-icon><Plus /></el-icon>
          绑定DOU+
        </el-button>
        <el-button @click="showRecordsDialog = true">申请记录</el-button>
      </div>
      <div class="action-right">
        <el-select v-model="searchType" placeholder="抖音号" style="width: 100px; margin-right: 10px;">
          <el-option label="抖音号" value="douyinId" />
          <el-option label="昵称" value="nickname" />
          <el-option label="账户ID" value="accountId" />
        </el-select>
        <el-input 
          v-model="searchKeyword" 
          placeholder="请输入抖音号搜索" 
          style="width: 200px;"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #suffix>
            <el-icon class="search-icon" @click="handleSearch"><Search /></el-icon>
          </template>
        </el-input>
      </div>
    </div>

    <!-- 账号列表 -->
    <div class="account-list">
      <el-table :data="filteredAccounts" v-loading="loading" stripe>
        <el-table-column label="抖音号信息" min-width="280">
          <template #default="{ row }">
            <div class="account-info">
              <el-avatar :size="50" :src="row.avatar">
                <span class="avatar-text">{{ getAvatarText(row.remark || row.nickname) }}</span>
              </el-avatar>
              <div class="account-detail">
                <div class="nickname">
                  {{ row.remark || row.nickname || '未知账号' }}
                  <el-icon v-if="!row.remark" class="edit-icon" @click.stop="handleEditRemark(row)"><Edit /></el-icon>
                </div>
                <div class="douyin-id">抖音号: {{ row.douyinId || row.openId || '-' }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="120" align="center">
          <template #default="{ row }">
            <div class="status-cell">
              <span class="status-dot" :class="{ active: row.status === 1 }"></span>
              <span class="status-text">{{ row.status === 1 ? '生效中' : '已失效' }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="DOU+账户ID" width="200">
          <template #default="{ row }">
            <span class="account-id">{{ row.advertiserId || row.openId }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="220" align="center">
          <template #default="{ row }">
            <el-button type="primary" link @click="handleVisit(row)">访问</el-button>
            <el-button type="primary" link @click="handleViewDetail(row)">查看详情</el-button>
            <el-button type="primary" link @click="handleEditRemark(row)">编辑</el-button>
            <el-button type="danger" link @click="handleUnbind(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <!-- 分页 -->
      <div class="pagination-wrapper">
        <span class="total-text">共{{ accounts.length }}条记录</span>
        <el-pagination
          v-model:current-page="currentPage"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50]"
          :total="accounts.length"
          layout="prev, pager, next, sizes, jumper"
          background
        />
      </div>
    </div>

    <!-- 查看详情弹窗 -->
    <el-dialog v-model="showDetailDialog" :title="currentAccount?.nickname || '账户详情'" width="600px">
      <div class="detail-content" v-if="currentAccount">
        <h3 class="section-title">账户概览</h3>
        
        <div class="info-section">
          <h4 class="sub-title">基础信息</h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">账户类型</span>
              <span class="value">DOU+</span>
            </div>
            <div class="info-item">
              <span class="label">账户ID</span>
              <span class="value">{{ currentAccount.advertiserId || currentAccount.openId }}</span>
            </div>
            <div class="info-item">
              <span class="label">账户绑定来源</span>
              <span class="value">
                自动绑定 
                <el-tooltip content="通过OAuth授权自动绑定">
                  <el-icon><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </div>
            <div class="info-item">
              <span class="label">账户绑定时间</span>
              <span class="value">{{ formatDateTime(currentAccount.createTime) }}</span>
            </div>
          </div>
        </div>

        <div class="info-section">
          <h4 class="sub-title">主体信息</h4>
          <div class="info-grid">
            <div class="info-item full">
              <span class="label">主体名称</span>
              <span class="value">{{ currentAccount.companyName || '个人账户' }}</span>
            </div>
          </div>
        </div>

        <div class="info-section">
          <h4 class="sub-title">资质信息 <a href="#" class="link">前往认证</a></h4>
          <div class="info-grid">
            <div class="info-item">
              <span class="label">主体资质状态</span>
              <span class="value success">已通过</span>
            </div>
            <div class="info-item">
              <span class="label">对公验证状态</span>
              <span class="value success">已通过</span>
            </div>
          </div>
        </div>

        <div class="info-section">
          <h4 class="sub-title">
            API能力
            <el-tooltip content="白名单账号可通过API创建DOU+订单，非白名单账号需通过抖音APP下单">
              <el-icon><QuestionFilled /></el-icon>
            </el-tooltip>
          </h4>
          <div class="info-grid">
            <div class="info-item full">
              <span class="label">创建订单权限</span>
              <span class="value" v-if="whitelistLoading">
                <el-icon class="is-loading"><Loading /></el-icon>
                查询中...
              </span>
              <span class="value" v-else-if="!whitelistStatus.checked">
                -
              </span>
              <span class="value success" v-else-if="whitelistStatus.inWhitelist">
                <el-icon><CircleCheckFilled /></el-icon>
                已开通（白名单）
              </span>
              <span class="value warning" v-else>
                <el-icon><WarningFilled /></el-icon>
                未开通
                <el-tooltip v-if="whitelistStatus.errorMsg" :content="whitelistStatus.errorMsg">
                  <el-icon style="margin-left: 4px;"><QuestionFilled /></el-icon>
                </el-tooltip>
              </span>
            </div>
          </div>
          <div class="whitelist-tip" v-if="whitelistStatus.checked && !whitelistStatus.inWhitelist">
            <el-alert 
              type="info" 
              :closable="false"
              show-icon
            >
              <template #title>
                此账号暂不支持API创建订单，需通过抖音APP手动下单。如需开通API权限，请联系巨量引擎销售申请白名单。
              </template>
            </el-alert>
          </div>
        </div>
      </div>
      <template #footer>
        <el-button @click="showDetailDialog = false">关闭</el-button>
        <el-button type="primary" @click="handleVisit(currentAccount)">访问账户</el-button>
      </template>
    </el-dialog>

    <!-- 申请记录弹窗 -->
    <el-dialog v-model="showRecordsDialog" title="申请记录" width="800px">
      <el-empty description="暂无申请记录" />
    </el-dialog>

    <!-- 编辑备注弹窗 -->
    <el-dialog v-model="showRemarkDialog" title="编辑账号信息" width="500px">
      <el-form :model="remarkForm" label-width="100px">
        <el-form-item label="原显示名称">
          <span style="color: #999;">{{ editingAccount?.nickname }}</span>
        </el-form-item>
        <el-form-item label="备注名称">
          <el-input 
            v-model="remarkForm.remark" 
            placeholder="请输入抖音昵称（如：不知道取什么名）"
            clearable
          />
          <div class="form-tip">备注名称将作为显示名称，方便您识别账号</div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRemarkDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveRemark" :loading="saving">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAccountList, deleteAccount, getOAuthUrl, updateAccountRemark, checkAccountWhitelist } from '@/api/account'
import type { DouyinAccount } from '@/api/types'

const router = useRouter()
const loading = ref(false)
const saving = ref(false)
const accounts = ref<DouyinAccount[]>([])
const currentPage = ref(1)
const pageSize = ref(10)
const searchType = ref('douyinId')
const searchKeyword = ref('')
const showDetailDialog = ref(false)
const showRecordsDialog = ref(false)
const showRemarkDialog = ref(false)
const currentAccount = ref<DouyinAccount | null>(null)
const editingAccount = ref<DouyinAccount | null>(null)
const remarkForm = reactive({
  remark: ''
})

// 白名单状态
const whitelistLoading = ref(false)
const whitelistStatus = ref<{
  checked: boolean
  inWhitelist: boolean
  errorMsg?: string
}>({ checked: false, inWhitelist: false })

// 过滤后的账号列表
const filteredAccounts = computed(() => {
  let result = accounts.value
  if (searchKeyword.value) {
    const keyword = searchKeyword.value.toLowerCase()
    result = result.filter(acc => {
      if (searchType.value === 'douyinId') {
        return (acc.douyinId || acc.openId || '').toLowerCase().includes(keyword)
      } else if (searchType.value === 'nickname') {
        return (acc.nickname || '').toLowerCase().includes(keyword)
      } else if (searchType.value === 'accountId') {
        return (acc.advertiserId || acc.openId || '').toLowerCase().includes(keyword)
      }
      return true
    })
  }
  // 分页
  const start = (currentPage.value - 1) * pageSize.value
  return result.slice(start, start + pageSize.value)
})

// 获取头像文字
const getAvatarText = (nickname: string) => {
  if (!nickname) return '?'
  return nickname.charAt(0)
}

// 格式化日期时间
const formatDateTime = (dateStr: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', { 
    year: 'numeric', 
    month: '2-digit', 
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 检查Token是否即将过期
const isTokenExpiring = (account: DouyinAccount) => {
  if (!account?.tokenExpiresAt) return false
  const expiresAt = new Date(account.tokenExpiresAt).getTime()
  const now = Date.now()
  const sevenDays = 7 * 24 * 60 * 60 * 1000
  return expiresAt - now < sevenDays
}

// 加载数据
const loadData = async () => {
  loading.value = true
  try {
    const res = await getAccountList()
    if (res.code === 200) {
      accounts.value = res.data || []
    }
  } catch (error) {
    console.error('加载账号失败', error)
  } finally {
    loading.value = false
  }
}

// 搜索
const handleSearch = () => {
  currentPage.value = 1
}

// 添加账号
const handleAddAccount = async () => {
  try {
    const res = await getOAuthUrl()
    if (res.code === 200 && res.data) {
      window.open(res.data, '_blank')
    }
  } catch (error) {
    ElMessage.warning('请在后台配置抖音OAuth参数后再添加账号')
  }
}

// 访问账户（跳转到账户概览页面）
const handleVisit = (row: DouyinAccount | null) => {
  if (!row) return
  showDetailDialog.value = false
  router.push({ path: `/account/${row.id}/dashboard` })
}

// 查看详情
const handleViewDetail = async (row: DouyinAccount) => {
  currentAccount.value = row
  showDetailDialog.value = true
  // 重置白名单状态
  whitelistStatus.value = { checked: false, inWhitelist: false }
  // 查询白名单状态
  await checkWhitelistStatus(row.id)
}

// 查询白名单状态
const checkWhitelistStatus = async (accountId: number) => {
  whitelistLoading.value = true
  try {
    const res = await checkAccountWhitelist(accountId)
    if (res.code === 200) {
      whitelistStatus.value = {
        checked: true,
        inWhitelist: res.data.inWhitelist,
        errorMsg: res.data.errorMsg
      }
    }
  } catch (error: any) {
    whitelistStatus.value = {
      checked: true,
      inWhitelist: false,
      errorMsg: error.message || '查询失败'
    }
  } finally {
    whitelistLoading.value = false
  }
}

// 解绑
const handleUnbind = async (row: DouyinAccount) => {
  await ElMessageBox.confirm(
    `确认解绑账号「${row.remark || row.nickname}」吗？解绑后需要重新授权。`,
    '解绑账号',
    { type: 'warning' }
  )
  try {
    await deleteAccount(row.id)
    ElMessage.success('账号已解绑')
    loadData()
  } catch (error) {
    // 错误已在拦截器处理
  }
}

// 编辑备注
const handleEditRemark = (row: DouyinAccount) => {
  editingAccount.value = row
  remarkForm.remark = row.remark || ''
  showRemarkDialog.value = true
}

// 保存备注
const handleSaveRemark = async () => {
  if (!editingAccount.value) return
  saving.value = true
  try {
    await updateAccountRemark(editingAccount.value.id, remarkForm.remark)
    ElMessage.success('保存成功')
    showRemarkDialog.value = false
    loadData()
  } catch (error) {
    // 错误已在拦截器处理
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped lang="scss">
.account-page {
  padding: 20px;
  background: #f5f7fa;
  min-height: calc(100vh - 60px);
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  
  .page-title {
    font-size: 18px;
    font-weight: 600;
    color: #333;
    display: flex;
    align-items: center;
    gap: 6px;
    
    .help-icon {
      font-size: 14px;
      color: #999;
      cursor: pointer;
    }
  }
  
  .help-link {
    color: #1890ff;
    font-size: 13px;
    cursor: pointer;
    &:hover { text-decoration: underline; }
  }
}

.action-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  
  .action-left {
    display: flex;
    gap: 12px;
  }
  
  .action-right {
    display: flex;
    align-items: center;
    
    .search-icon {
      cursor: pointer;
      &:hover { color: #1890ff; }
    }
  }
}

.account-list {
  background: #fff;
  border-radius: 8px;
  padding: 0 0 16px;
  
  :deep(.el-table) {
    border-radius: 8px;
    
    th {
      background: #fafafa;
      color: #666;
      font-weight: 500;
    }
  }
}

.account-info {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
  
  .avatar-text {
    font-size: 18px;
    color: #fff;
  }
  
  :deep(.el-avatar) {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  }
  
  .account-detail {
    .nickname {
      font-size: 14px;
      font-weight: 500;
      color: #333;
      margin-bottom: 4px;
      display: flex;
      align-items: center;
      gap: 6px;
      
      .edit-icon {
        font-size: 14px;
        color: #c0c4cc;
        cursor: pointer;
        &:hover { color: #1890ff; }
      }
    }
    
    .douyin-id {
      font-size: 12px;
      color: #999;
    }
  }
}

.status-cell {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;
  
  .status-dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
    background: #ddd;
    
    &.active {
      background: #52c41a;
    }
  }
  
  .status-text {
    font-size: 13px;
    color: #666;
  }
}

.account-id {
  font-size: 13px;
  color: #666;
  font-family: monospace;
}

.pagination-wrapper {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 16px 20px 0;
  gap: 16px;
  
  .total-text {
    font-size: 13px;
    color: #999;
  }
}

// 详情弹窗样式
.detail-content {
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #333;
    padding-bottom: 12px;
    border-bottom: 1px solid #e8e8e8;
    margin-bottom: 20px;
  }
  
  .info-section {
    margin-bottom: 24px;
    
    .sub-title {
      font-size: 14px;
      font-weight: 500;
      color: #333;
      margin-bottom: 16px;
      display: flex;
      align-items: center;
      gap: 12px;
      
      .link {
        font-size: 12px;
        color: #1890ff;
        font-weight: normal;
        text-decoration: none;
        &:hover { text-decoration: underline; }
      }
    }
    
    .info-grid {
      display: grid;
      grid-template-columns: repeat(2, 1fr);
      gap: 16px;
      
      .info-item {
        display: flex;
        flex-direction: column;
        gap: 4px;
        
        &.full {
          grid-column: span 2;
        }
        
        .label {
          font-size: 12px;
          color: #999;
        }
        
        .value {
          font-size: 14px;
          color: #333;
          display: flex;
          align-items: center;
          gap: 6px;
          
          &.success {
            color: #52c41a;
          }
          
          &.warning {
            color: #faad14;
          }
          
          .el-icon {
            font-size: 12px;
            color: #999;
            cursor: help;
          }
        }
      }
    }
  }
}

.form-tip {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.whitelist-tip {
  margin-top: 12px;
  
  :deep(.el-alert__title) {
    font-size: 13px;
    line-height: 1.5;
  }
}

.is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}
</style>
