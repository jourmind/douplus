<template>
  <div class="douplus-history">
    <div class="page-header">
      <div class="header-left">
        <h2>我的订单</h2>
      </div>
      <div class="header-right">
        <el-button type="success" :loading="syncing" @click="handleSyncOrders">
          <el-icon><Refresh /></el-icon> 同步历史订单
        </el-button>
        <el-button type="primary" class="hot-btn">
          去上热门 <el-icon><TopRight /></el-icon>
        </el-button>
      </div>
    </div>
    
    <el-card class="filter-card" shadow="never">
      <OrderFilters 
        v-model="filters" 
        :members="members"
        :show-member-filter="true"
        @change="handleFilterChange"
        @export="exportData" 
      />
    </el-card>
    
    <el-card class="table-card" shadow="never">
      <div class="table-header">
        <div class="header-left">
          <span class="order-count">共 {{ pagination.total }} 个订单</span>
          <!-- 批量操作栏 -->
          <div v-if="selectedTasks.length > 0" class="batch-actions">
            <el-tag type="info" size="large">
              已选择 {{ selectedTasks.length }} 个订单
            </el-tag>
            <el-button type="primary" size="small" @click="handleBatchRenew">
              批量续费
            </el-button>
            <el-button size="small" @click="clearSelection">
              取消选择
            </el-button>
          </div>
        </div>
        <SortCascader v-model="sortOption" @change="handleSortChange" />
      </div>
      
      <!-- 使用共享订单表格组件 -->
      <OrderTable 
        ref="orderTableRef"
        :tasks="tasks"
        :loading="loading"
        :show-account-column="true"
        :show-cancel-button="true"
        :show-renew-button="true"
        :selectable="true"
        @view-details="viewDetails"
        @cancel="cancelTask"
        @delete="deleteTask"
        @renew="handleRenew"
        @reorder="handleReorder"
        @selection-change="handleSelectionChange"
      />
      
      <el-pagination
        v-model:current-page="pagination.currentPage"
        v-model:page-size="pagination.pageSize"
        :total="pagination.total"
        :page-sizes="[10, 20, 50, 100]"
        layout="total, sizes, prev, pager, next, jumper"
        @size-change="handleSizeChange"
        @current-change="handleCurrentChange"
        style="margin-top: 20px; text-align: right"
      />
    </el-card>
    
    <!-- 任务详情弹窗 -->
    <el-dialog v-model="detailVisible" title="任务详情" width="60%">
      <div v-if="currentTask" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="getStatusType(currentTask.status)">
              {{ getStatusText(currentTask.status) }}
            </el-tag>
          </el-descriptions-item>
          
          <el-descriptions-item label="投放账号">{{ currentTask.accountNickname }}</el-descriptions-item>
          <el-descriptions-item label="视频ID">{{ currentTask.itemId }}</el-descriptions-item>
          
          <el-descriptions-item label="投放金额">¥{{ currentTask.budget }}</el-descriptions-item>
          <el-descriptions-item label="实际消耗">¥{{ currentTask.actualCost || 0 }}</el-descriptions-item>
          
          <el-descriptions-item label="预计曝光">{{ currentTask.expectedExposure }}</el-descriptions-item>
          <el-descriptions-item label="实际曝光">{{ currentTask.actualExposure || 0 }}</el-descriptions-item>
          
          <el-descriptions-item label="投放时长">{{ currentTask.duration }}小时</el-descriptions-item>
          <el-descriptions-item label="任务类型">{{ currentTask.taskType === 1 ? '视频投放' : '直播投放' }}</el-descriptions-item>
          
          <el-descriptions-item label="创建时间">{{ formatDate(currentTask.createTime) }}</el-descriptions-item>
          <el-descriptions-item label="计划执行时间">{{ formatDate(currentTask.scheduledTime) }}</el-descriptions-item>
          
          <el-descriptions-item label="实际执行时间" :span="2">
            {{ currentTask.executedTime ? formatDate(currentTask.executedTime) : '未执行' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="完成时间" :span="2">
            {{ currentTask.completedTime ? formatDate(currentTask.completedTime) : '未完成' }}
          </el-descriptions-item>
          
          <el-descriptions-item label="错误信息" :span="2" v-if="currentTask.errorMsg">
            <span style="color: #f56c6c;">{{ currentTask.errorMsg }}</span>
          </el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
    
    <!-- 续费/再次下单弹窗 -->
    <RenewDialog 
      v-model="renewVisible" 
      :task="renewTask" 
      :mode="renewMode"
      ref="renewDialogRef"
      @confirm="confirmRenewOrReorder" 
    />
    
    <!-- 同步进度弹窗 -->
    <el-dialog 
      v-model="syncDialogVisible" 
      title="同步历史订单" 
      width="450px"
      :close-on-click-modal="false"
      :close-on-press-escape="false"
      :show-close="syncStatus !== 'syncing'"
    >
      <div class="sync-dialog-content">
        <div class="sync-status-icon">
          <el-icon v-if="syncStatus === 'syncing' || syncStatus === 'idle'" class="is-loading" :size="48" color="#409eff">
            <Loading />
          </el-icon>
          <el-icon v-else-if="syncStatus === 'completed'" :size="48" color="#67c23a">
            <CircleCheck />
          </el-icon>
          <el-icon v-else :size="48" color="#f56c6c">
            <CircleClose />
          </el-icon>
        </div>
        
        <div class="sync-message">{{ syncMessage }}</div>
        
        <div v-if="syncStatus === 'syncing' || syncStatus === 'idle'" class="sync-progress">
          <el-progress 
            :percentage="syncProgress" 
            :stroke-width="10"
            :show-text="false"
            status="success"
          />
          <div class="sync-count">已同步 <span class="count-num">{{ syncCount }}</span> 条订单</div>
        </div>
        
        <div v-else-if="syncStatus === 'completed'" class="sync-result">
          <div class="result-count">共同步 <span class="count-num">{{ syncCount }}</span> 条订单</div>
        </div>
      </div>
      
      <template #footer v-if="syncStatus !== 'syncing' && syncStatus !== 'idle'">
        <el-button type="primary" @click="closeSyncDialog">确定</el-button>
      </template>
    </el-dialog>
    
    <!-- 批量续费对话框 -->
    <BatchRenewDialog 
      v-model="batchRenewVisible"
      :tasks="selectedTasks"
      @submit="handleBatchRenewSubmit"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { TopRight, Refresh, Loading, CircleCheck, CircleClose } from '@element-plus/icons-vue'
import type { DouplusTaskVO } from '@/api/types'
import { getTaskPage, cancelTask as cancelTaskApi, deleteTask as deleteTaskApi, getTaskDetail, renewTask, syncAllOrders, getSyncStatus } from '@/api/douplus'
import { getAccountList } from '@/api/account'
import { OrderTable, OrderFilters, SortCascader, RenewDialog, BatchRenewDialog } from '@/components/order'
import type { OrderFiltersType, MemberOption, SortOption } from '@/components/order'

interface Pagination {
  currentPage: number
  pageSize: number
  total: number
}

const loading = ref(false)
const tasks = ref<any[]>([])
const allTasks = ref<any[]>([])  // 存储所有数据，用于前端排序
const detailVisible = ref(false)
const currentTask = ref<DouplusTaskVO | null>(null)
const members = ref<MemberOption[]>([])
const renewVisible = ref(false)
const renewTask = ref<any>(null)
const renewMode = ref<'renew' | 'reorder'>('renew')
const renewDialogRef = ref<any>(null)
const syncing = ref(false)
const syncMessage = ref('')
const syncDialogVisible = ref(false)
const syncStatus = ref<'idle' | 'syncing' | 'completed' | 'error'>('idle')
const syncCount = ref(0)
const syncProgress = ref(0)
let syncTimer: ReturnType<typeof setInterval> | null = null

// 批量续费相关
const selectedTasks = ref<any[]>([])
const batchRenewVisible = ref(false)
const orderTableRef = ref<any>(null)

// 初始化默认时间范围为近30天
const getDefaultDateRange = (): [string, string] => {
  const end = new Date()
  const start = new Date()
  start.setDate(start.getDate() - 29)
  return [
    start.toISOString().split('T')[0],
    end.toISOString().split('T')[0]
  ]
}

const filters = ref<OrderFiltersType>({
  status: '',
  objective: '',
  keyword: '',
  memberId: undefined,
  dateRange: getDefaultDateRange()  // 设置默认时间范围
})

const sortOption = ref<SortOption>({
  field: 'createTime',
  order: 'desc'
})

const pagination = reactive<Pagination>({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 加载成员列表（已授权账号）
const loadMembers = async () => {
  try {
    const res = await getAccountList()
    if (res.code === 200) {
      members.value = (res.data || []).map((account: any) => ({
        id: account.id,
        nickname: account.remark || account.nickname || `账号${account.id}`
      }))
    }
  } catch (error) {
    console.error('加载成员列表失败', error)
  }
}

// 筛选条件变化
const handleFilterChange = () => {
  pagination.currentPage = 1
  loadTasks()
}

// 前端排序函数
const sortTasks = (data: any[], field: string, order: 'asc' | 'desc') => {
  return [...data].sort((a, b) => {
    let valA: number, valB: number
    
    switch (field) {
      case 'actualCost':
        valA = a.actualCost || 0
        valB = b.actualCost || 0
        break
      case 'playCount':
        valA = a.playCount || 0
        valB = b.playCount || 0
        break
      case 'costPerPlay':
        // 转化成本 = 消耗 / 播放量
        valA = (a.playCount > 0) ? (a.actualCost || 0) / a.playCount : 0
        valB = (b.playCount > 0) ? (b.actualCost || 0) / b.playCount : 0
        break
      case 'shareRate':
        // 百转发率 = 转发数 / 播放量
        valA = (a.playCount > 0) ? (a.shareCount || 0) / a.playCount : 0
        valB = (b.playCount > 0) ? (b.shareCount || 0) / b.playCount : 0
        break
      case 'createTime':
      default:
        valA = new Date(a.createTimeRaw || a.createTime || 0).getTime()
        valB = new Date(b.createTimeRaw || b.createTime || 0).getTime()
        break
    }
    
    return order === 'asc' ? valA - valB : valB - valA
  })
}

// 应用排序和分页（前端处理）
const applySort = () => {
  const sorted = sortTasks(allTasks.value, sortOption.value.field, sortOption.value.order)
  pagination.total = sorted.length
  const start = (pagination.currentPage - 1) * pagination.pageSize
  const end = start + pagination.pageSize
  tasks.value = sorted.slice(start, end)
}

// 排序变化 - 前端排序，无需请求后端
const handleSortChange = () => {
  pagination.currentPage = 1
  applySort()
}

// 导出数据
const exportData = () => {
  ElMessage.info('导出功能开发中')
}

// 加载任务列表 - 一次性获取全部数据
const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      pageNum: 1,
      pageSize: -1,  // 获取全部数据
    }
    
    // 添加筛选条件
    if (filters.value.status) {
      params.status = filters.value.status
    }
    
    if (filters.value.keyword) {
      params.keyword = filters.value.keyword
    }
    
    if (filters.value.memberId) {
      params.accountId = filters.value.memberId
    }
    
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.startDate = filters.value.dateRange[0]
      params.endDate = filters.value.dateRange[1]
    }
    
    const res = await getTaskPage(params)
    
    if (res.code === 200) {
      // 转换数据格式以匹配共享组件，保留所有原始数据用于指标计算
      allTasks.value = (res.data?.records || []).map((task: DouplusTaskVO) => ({
        ...task,
        videoCover: task.videoCoverUrl,
        // 使用API返回的实际数据
        playCount: task.playCount || task.actualExposure || 0,
        shareCount: task.shareCount || 0,
        clickCount: task.clickCount || 0,
        likeCount: task.likeCount || 0,
        followCount: task.followCount || 0,
        componentClickCount: task.clickCount || 0,  // 组件点击量使用clickCount
        playDuration5sRank: task.avg5sRate || 0,  // 映射5S完播率
        customConvertCost: task.avgConvertCost || 0,  // 映射转化成本
        dpTargetConvertCnt: task.dpTargetConvertCnt || 0,  // 转化数
        createTimeRaw: task.createTime,  // 保留原始时间用于排序
      }))
      // 应用前端排序和分页
      applySort()
    }
  } catch (error) {
    console.error('加载任务失败', error)
  } finally {
    loading.value = false
  }
}

// 分页大小变化 - 前端分页
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  applySort()
}

// 当前页变化 - 前端分页
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  applySort()
}

// 获取状态类型
const getStatusType = (status: string) => {
  switch (status) {
    case 'WAIT': return 'info'
    case 'RUNNING': return 'warning'
    case 'SUCCESS': return 'success'
    case 'FAIL': return 'danger'
    case 'CANCELLED': return 'info'
    default: return 'info'
  }
}

// 获取状态文本
const getStatusText = (status: string) => {
  switch (status) {
    case 'WAIT': return '待执行'
    case 'RUNNING': return '执行中'
    case 'SUCCESS': return '成功'
    case 'FAIL': return '失败'
    case 'CANCELLED': return '已取消'
    default: return status
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN')
}

// 查看任务详情
const viewDetails = async (task: any) => {
  try {
    const res = await getTaskDetail(task.id)
    if (res.code === 200) {
      currentTask.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('获取任务详情失败', error)
  }
}

// 取消任务
const cancelTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确认取消任务 ${task.id}？`,
      '取消任务',
      { type: 'warning' }
    )
    
    await cancelTaskApi(task.id)
    ElMessage.success('任务已取消')
    loadTasks() // 刷新列表
  } catch (error) {
    console.error('取消任务失败', error)
  }
}

// 删除失败的任务
const deleteTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除任务 ${task.id}？删除后无法恢复。`,
      '删除任务',
      { type: 'warning' }
    )
    
    await deleteTaskApi(task.id)
    ElMessage.success('任务已删除')
    loadTasks() // 刷新列表
  } catch (error) {
    console.error('删除任务失败', error)
  }
}

// 续费 - 打开弹窗
const handleRenew = (task: any) => {
  renewTask.value = task
  renewMode.value = 'renew'
  renewVisible.value = true
}

// 再次下单 - 打开弹窗
const handleReorder = (task: any) => {
  renewTask.value = task
  renewMode.value = 'reorder'
  renewVisible.value = true
}

// 批量续费 - 处理选择变化
const handleSelectionChange = (selection: any[]) => {
  selectedTasks.value = selection
}

// 批量续费 - 打开对话框
const handleBatchRenew = () => {
  if (selectedTasks.value.length === 0) {
    ElMessage.warning('请先选择要续费的订单')
    return
  }
  batchRenewVisible.value = true
}

// 批量续费 - 取消选择
const clearSelection = () => {
  if (orderTableRef.value) {
    orderTableRef.value.$refs.table?.clearSelection()
  }
  selectedTasks.value = []
}

// 批量续费 - 提交
const handleBatchRenewSubmit = async (data: { tasks: any[], budget: number, duration: number }) => {
  try {
    const { tasks, budget, duration } = data
    
    // 调用批量续费API
    const orderIds = tasks.map(t => t.orderId).filter(Boolean)
    
    if (orderIds.length === 0) {
      ElMessage.error('选中的订单缺少订单ID')
      return
    }
    
    // TODO: 这里需要添加批量续费API
    const response = await fetch('/api/douplus/batch-renew', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      },
      body: JSON.stringify({
        orderIds,
        budget,
        duration
      })
    })
    
    const result = await response.json()
    
    if (result.code === 200) {
      ElMessage.success(`成功续费 ${result.data.successCount} 个订单`)
      batchRenewVisible.value = false
      clearSelection()
      loadTasks() // 刷新列表
    } else {
      ElMessage.error(result.message || '批量续费失败')
    }
  } catch (error: any) {
    console.error('批量续费失败', error)
    ElMessage.error(error.message || '批量续费失败')
  }
}

// 续费/再次下单 - 确认提交
const confirmRenewOrReorder = async (data: { 
  task: any, 
  budget: number,
  duration: number,
  count: number, 
  investPassword: string,
  customTimeEnabled?: boolean,
  fixedTimeStart?: number,
  fixedTimeEnd?: number
}) => {
  try {
    renewDialogRef.value?.setLoading(true)
    
    if (renewMode.value === 'renew') {
      // 续费模式：调用续费API
      const res = await renewTask({
        orderId: data.task.id,
        budget: data.budget,
        duration: data.duration,
        investPassword: data.investPassword
      })
      
      if (res.code === 200) {
        ElMessage.success(res.message || '续费成功')
        renewVisible.value = false
        loadTasks() // 刷新列表
      } else {
        ElMessage.error(res.message || '续费失败')
      }
    } else {
      // 再次下单模式：暂不支持（需要创建订单API）
      ElMessage.warning('再次下单功能开发中，请通过抖音APP下单')
      renewVisible.value = false
    }
  } catch (error: any) {
    ElMessage.error(error.message || '操作失败')
  } finally {
    renewDialogRef.value?.setLoading(false)
  }
}

// 同步历史订单
const handleSyncOrders = async () => {
  if (syncing.value) {
    ElMessage.warning('正在同步中，请稍候...')
    return
  }
  
  try {
    syncing.value = true
    syncStatus.value = 'syncing'
    syncMessage.value = '正在初始化同步...'
    syncCount.value = 0
    syncProgress.value = 0
    syncDialogVisible.value = true
    
    const res = await syncAllOrders()
    if (res.code === 200) {
      // 不管返回什么状态，都开始轮询
      syncMessage.value = '同步已开始...'
      startPolling()
    } else {
      syncStatus.value = 'error'
      syncMessage.value = res.message || '同步失败'
      syncing.value = false
    }
  } catch (error: any) {
    syncStatus.value = 'error'
    syncMessage.value = error.message || '同步失败'
    syncing.value = false
  }
}

// 开始轮询同步状态
const startPolling = () => {
  if (syncTimer) {
    clearInterval(syncTimer)
  }
  
  // 轮询函数
  const pollStatus = async () => {
    try {
      const res = await getSyncStatus()
      if (res.code === 200) {
        const status = res.data
        syncMessage.value = status?.message || '正在同步...'
        syncCount.value = status?.count || 0
        
        if (status?.status === 'completed') {
          stopPolling()
          syncStatus.value = 'completed'
          syncMessage.value = '同步完成!'
          syncProgress.value = 100
          loadTasks()
        } else if (status?.status === 'error') {
          stopPolling()
          syncStatus.value = 'error'
          syncMessage.value = status.message || '同步失败'
        } else {
          // 模拟进度（因为不知道总数，每次加一点）
          if (syncProgress.value < 95) {
            syncProgress.value = Math.min(95, syncProgress.value + 10)
          }
        }
      }
    } catch (error) {
      console.error('查询同步状态失败', error)
    }
  }
  
  // 立即执行第一次查询
  pollStatus()
  
  // 然后每秒轮询一次
  syncTimer = setInterval(pollStatus, 1000)
}

// 停止轮询
const stopPolling = () => {
  if (syncTimer) {
    clearInterval(syncTimer)
    syncTimer = null
  }
  syncing.value = false
}

// 关闭同步弹窗
const closeSyncDialog = () => {
  syncDialogVisible.value = false
  syncStatus.value = 'idle'
  syncMessage.value = ''
  syncCount.value = 0
  syncProgress.value = 0
}

onMounted(() => {
  loadMembers()
  loadTasks()
})
</script>

<style scoped>
.douplus-history {
  max-width: 1600px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
  padding-bottom: 12px;
  border-bottom: 3px solid #ff6b35;
}

.page-header h2 {
  font-size: 20px;
  font-weight: 600;
  color: #ff6b35;
  margin: 0;
}

.hot-btn {
  background: linear-gradient(135deg, #ff6b35 0%, #ff8c5a 100%);
  border: none;
  border-radius: 4px;
}

.filter-card {
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
}

.filter-card :deep(.el-card__body) {
  padding: 16px;
}

.table-card {
  border: 1px solid #e5e7eb;
}

.table-card :deep(.el-card__body) {
  padding: 0;
}

.table-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  border-bottom: 1px solid #e5e7eb;
}

.order-count {
  color: #1890ff;
  font-size: 14px;
}

/* 分页 */
:deep(.el-pagination) {
  padding: 16px;
  justify-content: flex-end;
}

/* 详情弹窗 */
.task-detail {
  max-height: 60vh;
  overflow-y: auto;
}

/* 同步进度弹窗 */
.sync-dialog-content {
  text-align: center;
  padding: 20px 0;
}

.sync-status-icon {
  margin-bottom: 20px;
}

.sync-status-icon .is-loading {
  animation: rotating 2s linear infinite;
}

@keyframes rotating {
  from { transform: rotate(0deg); }
  to { transform: rotate(360deg); }
}

.sync-message {
  font-size: 16px;
  color: #303133;
  margin-bottom: 20px;
}

.sync-progress {
  max-width: 300px;
  margin: 0 auto;
}

.sync-count, .result-count {
  margin-top: 12px;
  font-size: 14px;
  color: #606266;
}

.count-num {
  font-size: 24px;
  font-weight: bold;
  color: #409eff;
  margin: 0 4px;
}

.sync-result .count-num {
  color: #67c23a;
}

/* 批量操作栏 */
.table-header {
  .header-left {
    display: flex;
    align-items: center;
    gap: 20px;
    flex: 1;
    
    .batch-actions {
      display: flex;
      align-items: center;
      gap: 12px;
      padding-left: 20px;
      border-left: 1px solid #e4e7ed;
    }
  }
}
</style>
