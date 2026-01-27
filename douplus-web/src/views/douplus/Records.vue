<template>
  <div class="douplus-records">
    <div class="page-header">
      <div class="header-left">
        <h2>我的订单</h2>
      </div>
      <div class="header-right">
        <el-button 
          type="success" 
          :loading="syncing"
          :disabled="syncTask?.status === 'running'"
          @click="handleSyncOrders"
        >
          <template v-if="syncTask?.status === 'running'">
            <el-icon><Loading /></el-icon> 同步中 {{ syncTask.progress }}
          </template>
          <template v-else>
            <el-icon><Refresh /></el-icon> 同步历史订单
          </template>
        </el-button>
        <el-button type="primary" class="hot-btn" @click="goToCreate">
          去上热门 <el-icon><TopRight /></el-icon>
        </el-button>
      </div>
    </div>
    
    <!-- 同步进度提示条 -->
    <el-alert
      v-if="syncTask?.status === 'running'"
      type="info"
      :closable="false"
      show-icon
      class="sync-alert"
    >
      <template #title>
        <div class="sync-progress-info">
          <span>{{ syncTask.message }}</span>
          <el-link type="primary" @click="showSyncDialog = true">查看详情</el-link>
        </div>
      </template>
      <el-progress 
        :percentage="syncTask.progressPercent" 
        :stroke-width="8"
        style="margin-top: 8px"
      />
    </el-alert>
    
    <!-- 使用共享的订单列表组件 -->
    <OrderListView 
      ref="orderListRef"
      :show-member-filter="true"
      :show-account-column="true"
    />
    
    <!-- 同步任务详情弹窗 -->
    <el-dialog
      v-model="showSyncDialog"
      title="同步任务进度"
      width="700px"
      :close-on-click-modal="false"
    >
      <div v-if="syncTaskDetail" class="sync-detail">
        <!-- 整体进度 -->
        <div class="overall-progress">
          <div class="progress-header">
            <span class="progress-title">整体进度</span>
            <el-tag :type="getStatusTagType(syncTaskDetail.status)">
              {{ getStatusName(syncTaskDetail.status) }}
            </el-tag>
          </div>
          <el-progress 
            :percentage="syncTaskDetail.progressPercent"
            :status="syncTaskDetail.status === 'failed' ? 'exception' : undefined"
            :stroke-width="12"
          />
          <div class="progress-stats">
            <span>{{ syncTaskDetail.progress }} 个账号</span>
            <span>共同步 {{ syncTaskDetail.totalRecords }} 条订单</span>
            <span v-if="syncTaskDetail.duration">耗时 {{ syncTaskDetail.duration }}</span>
          </div>
        </div>
        
        <!-- 账号详情列表 -->
        <div class="account-details">
          <div class="detail-title">账号同步详情</div>
          <el-table :data="syncTaskDetail.details" stripe>
            <el-table-column prop="accountName" label="账号名称" width="150" />
            <el-table-column label="状态" width="100">
              <template #default="{row}">
                <el-tag :type="getStatusTagType(row.status)" size="small">
                  {{ getStatusName(row.status) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="recordCount" label="同步数量" width="100" align="right">
              <template #default="{row}">
                {{ row.recordCount || 0 }}
              </template>
            </el-table-column>
            <el-table-column label="耗时" width="120">
              <template #default="{row}">
                <span v-if="row.startTime && row.endTime">
                  {{ calculateDuration(row.startTime, row.endTime) }}
                </span>
                <span v-else-if="row.startTime" class="running-text">
                  <el-icon class="is-loading"><Loading /></el-icon> 进行中...
                </span>
                <span v-else class="pending-text">等待中</span>
              </template>
            </el-table-column>
            <el-table-column label="错误信息" min-width="200">
              <template #default="{row}">
                <el-text v-if="row.errorMessage" type="danger" size="small">
                  {{ row.errorMessage }}
                </el-text>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
      
      <template #footer>
        <el-button @click="showSyncDialog = false">关闭</el-button>
        <el-button
          v-if="syncTaskDetail?.status === 'completed'"
          type="primary"
          @click="refreshAndClose"
        >
          查看订单
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { Refresh, TopRight, Loading } from '@element-plus/icons-vue'
import { OrderListView } from '@/components/order'

const router = useRouter()
const syncing = ref(false)
const orderListRef = ref<any>(null)
const showSyncDialog = ref(false)
const syncTask = ref<any>(null)
const syncTaskDetail = ref<any>(null)
let pollingTimer: any = null

// 同步历史订单
const handleSyncOrders = async () => {
  syncing.value = true
  try {
    const response = await fetch('/api/douplus/task/sync-all', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    const result = await response.json()
    
    if (result.code === 200) {
      ElMessage.success('同步任务已提交')
      syncTask.value = result.data
      
      // 打开详情弹窗
      showSyncDialog.value = true
      
      // 开始轮询任务状态
      startPolling(result.data.taskId)
    } else {
      ElMessage.error(result.message || '同步失败')
    }
  } catch (error: any) {
    console.error('同步失败', error)
    ElMessage.error(error.message || '同步失败')
  } finally {
    syncing.value = false
  }
}

// 开始轮询任务状态
const startPolling = (taskId: number) => {
  // 清除旧的定时器
  if (pollingTimer) {
    clearInterval(pollingTimer)
  }
  
  // 立即查询一次
  fetchTaskStatus(taskId)
  
  // 每2秒查询一次
  pollingTimer = setInterval(() => {
    fetchTaskStatus(taskId)
  }, 2000)
}

// 查询任务状态
const fetchTaskStatus = async (taskId: number) => {
  try {
    const response = await fetch(`/api/douplus/task/sync-status/${taskId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    const result = await response.json()
    
    if (result.code === 200) {
      syncTaskDetail.value = result.data
      syncTask.value = {
        status: result.data.status,
        progress: result.data.progress,
        progressPercent: result.data.progressPercent,
        message: getProgressMessage(result.data)
      }
      
      // 任务完成或失败，停止轮询
      if (result.data.status === 'completed' || result.data.status === 'failed') {
        stopPolling()
        
        // 显示完成消息
        if (result.data.status === 'completed') {
          ElMessage.success(`同步完成！共同步 ${result.data.totalRecords} 条订单`)
          // 自动刷新订单列表
          setTimeout(() => {
            if (orderListRef.value) {
              orderListRef.value.refresh()
            }
          }, 1000)
        } else {
          ElMessage.error(`同步失败：${result.data.errorMessage}`)
        }
      }
    }
  } catch (error) {
    console.error('查询任务状态失败', error)
  }
}

// 停止轮询
const stopPolling = () => {
  if (pollingTimer) {
    clearInterval(pollingTimer)
    pollingTimer = null
  }
}

// 查询最新状态（页面加载时）
const checkLatestStatus = async () => {
  try {
    const response = await fetch('/api/douplus/task/latest-status', {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    
    const result = await response.json()
    
    if (result.code === 200 && result.data.hasTask) {
      syncTask.value = result.data
      
      // 如果有正在进行的任务，开始轮询
      if (result.data.status === 'running') {
        startPolling(result.data.taskId)
      }
    }
  } catch (error) {
    console.error('查询最新状态失败', error)
  }
}

// 获取进度消息
const getProgressMessage = (data: any) => {
  if (data.status === 'pending') {
    return '同步任务等待中...'
  } else if (data.status === 'running') {
    return `正在同步中，已完成 ${data.completedAccounts}/${data.totalAccounts} 个账号`
  } else if (data.status === 'completed') {
    return `同步完成！共同步 ${data.totalRecords} 条订单`
  } else {
    return `同步失败：${data.errorMessage}`
  }
}

// 获取状态标签类型
const getStatusTagType = (status: string) => {
  const typeMap: Record<string, any> = {
    pending: 'info',
    running: 'warning',
    completed: 'success',
    failed: 'danger'
  }
  return typeMap[status] || 'info'
}

// 获取状态名称
const getStatusName = (status: string) => {
  const nameMap: Record<string, string> = {
    pending: '等待中',
    running: '进行中',
    completed: '已完成',
    failed: '失败'
  }
  return nameMap[status] || status
}

// 计算耗时
const calculateDuration = (startTime: string, endTime: string) => {
  const start = new Date(startTime).getTime()
  const end = new Date(endTime).getTime()
  const seconds = Math.floor((end - start) / 1000)
  
  if (seconds < 60) {
    return `${seconds}秒`
  } else {
    const minutes = Math.floor(seconds / 60)
    const remainSeconds = seconds % 60
    return `${minutes}分${remainSeconds}秒`
  }
}

// 刷新并关闭
const refreshAndClose = () => {
  showSyncDialog.value = false
  if (orderListRef.value) {
    orderListRef.value.refresh()
  }
}

// 去投放
const goToCreate = () => {
  router.push('/douplus/create')
}

// 生命周期
onMounted(() => {
  // 页面加载时检查是否有正在进行的任务
  checkLatestStatus()
})

onUnmounted(() => {
  // 组件销毁时清除定时器
  stopPolling()
})
</script>

<style scoped lang="scss">
.douplus-records {
  .page-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .header-left {
      h2 {
        margin: 0;
        font-size: 20px;
        font-weight: 600;
        color: #303133;
      }
    }
    
    .header-right {
      display: flex;
      gap: 12px;
      
      .hot-btn {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        
        &:hover {
          background: linear-gradient(135deg, #5568d3 0%, #63408a 100%);
        }
      }
    }
  }
  
  .sync-alert {
    margin-bottom: 20px;
    
    .sync-progress-info {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 4px;
    }
  }
  
  .sync-detail {
    .overall-progress {
      padding: 20px;
      background: #f5f7fa;
      border-radius: 8px;
      margin-bottom: 20px;
      
      .progress-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
        
        .progress-title {
          font-size: 16px;
          font-weight: 600;
          color: #303133;
        }
      }
      
      .progress-stats {
        display: flex;
        gap: 24px;
        margin-top: 12px;
        font-size: 14px;
        color: #606266;
      }
    }
    
    .account-details {
      .detail-title {
        font-size: 14px;
        font-weight: 600;
        color: #303133;
        margin-bottom: 12px;
      }
      
      .running-text {
        color: #e6a23c;
        display: flex;
        align-items: center;
        gap: 4px;
      }
      
      .pending-text {
        color: #909399;
      }
    }
  }
}
</style>
