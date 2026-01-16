<template>
  <div class="account-page">
    <div class="card">
      <div class="card-header">
        <div class="card-title">抖音账号管理</div>
        <el-button type="primary" @click="handleAddAccount">
          <el-icon><Plus /></el-icon>
          添加账号
        </el-button>
      </div>
      
      <el-table :data="accounts" v-loading="loading" stripe>
        <el-table-column label="账号信息" min-width="200">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 12px;">
              <el-avatar :size="48" :src="row.avatar">{{ row.nickname?.charAt(0) }}</el-avatar>
              <div>
                <div style="font-weight: 600;">{{ row.nickname }}</div>
                <div style="font-size: 12px; color: #9ca3af;">ID: {{ row.openId?.slice(0, 16) }}...</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="粉丝数" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.fansCount) }}
          </template>
        </el-table-column>
        <el-table-column label="获赞数" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.totalFavorited) }}
          </template>
        </el-table-column>
        <el-table-column label="余额" width="120">
          <template #default="{ row }">
            <span style="color: #ff6b35; font-weight: 600;">¥{{ row.balance || 0 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="日限额" width="120">
          <template #default="{ row }">
            ¥{{ row.dailyLimit || 10000 }}
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.status === 1 ? 'success' : 'danger'">
              {{ row.status === 1 ? '正常' : '失效' }}
            </el-tag>
            <el-tag v-if="row.tokenExpiringSoon" type="warning" size="small" style="margin-left: 5px;">
              即将过期
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button type="primary" size="small" text @click="handleEdit(row)">编辑</el-button>
            <el-button 
              v-if="row.status !== 1" 
              type="warning" 
              size="small" 
              text
            >
              重新授权
            </el-button>
            <el-button type="danger" size="small" text @click="handleDelete(row)">解绑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
    
    <!-- 编辑对话框 -->
    <el-dialog v-model="showEditDialog" title="编辑账号" width="500px">
      <el-form :model="editForm" label-width="80px" v-if="currentAccount">
        <el-form-item label="账号">
          <span>{{ currentAccount.nickname }}</span>
        </el-form-item>
        <el-form-item label="日限额">
          <el-input-number v-model="editForm.dailyLimit" :min="100" :max="100000" />
          <span style="margin-left: 10px; color: #9ca3af;">元</span>
        </el-form-item>
        <el-form-item label="备注">
          <el-input v-model="editForm.remark" type="textarea" :rows="3" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSaveEdit">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAccountList, updateDailyLimit, updateAccountRemark, deleteAccount, getOAuthUrl } from '@/api/account'
import type { DouyinAccount } from '@/api/types'

const loading = ref(false)
const accounts = ref<DouyinAccount[]>([])

const showEditDialog = ref(false)
const currentAccount = ref<DouyinAccount | null>(null)
const editForm = reactive({
  dailyLimit: 10000,
  remark: ''
})

const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

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

const handleEdit = (row: DouyinAccount) => {
  currentAccount.value = row
  editForm.dailyLimit = row.dailyLimit || 10000
  editForm.remark = row.remark || ''
  showEditDialog.value = true
}

const handleSaveEdit = async () => {
  if (!currentAccount.value) return
  try {
    await updateDailyLimit(currentAccount.value.id, editForm.dailyLimit)
    if (editForm.remark !== currentAccount.value.remark) {
      await updateAccountRemark(currentAccount.value.id, editForm.remark)
    }
    ElMessage.success('保存成功')
    showEditDialog.value = false
    loadData()
  } catch (error) {
    // 错误已在拦截器处理
  }
}

const handleDelete = async (row: DouyinAccount) => {
  await ElMessageBox.confirm(
    `确认解绑账号 "${row.nickname}" 吗？解绑后需要重新授权。`,
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

onMounted(() => {
  loadData()
})
</script>
