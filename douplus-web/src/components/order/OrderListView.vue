<template>
  <div class="order-list-view">
    <!-- 筛选器 -->
    <el-card v-if="!hideFilters" class="filter-card" shadow="never">
      <OrderFilters 
        v-model="filters" 
        :members="members"
        :show-member-filter="showMemberFilter"
        @change="handleFilterChange"
        @export="exportData" 
      />
    </el-card>
    
    <!-- 订单表格 -->
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
        <div class="header-right">
          <SortCascader v-model="sortOption" @change="handleSortChange" />
          <el-button 
            :icon="Setting" 
            circle 
            @click="showColumnConfig = true"
            title="自定义列"
            class="column-config-btn"
          />
        </div>
      </div>
      
      <!-- 使用共享订单表格组件 -->
      <OrderTable 
        ref="orderTableRef"
        :tasks="tasks"
        :loading="loading"
        :show-account-column="showAccountColumn"
        :show-cancel-button="true"
        :show-renew-button="true"
        :selectable="true"
        :visible-columns="visibleColumns"
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
    <el-dialog v-model="detailVisible" title="任务详情" width="600px">
      <div v-if="currentTask" class="task-detail">
        <el-descriptions :column="2" border>
          <el-descriptions-item label="任务ID">{{ currentTask.id }}</el-descriptions-item>
          <el-descriptions-item label="订单ID">{{ currentTask.orderId }}</el-descriptions-item>
          <el-descriptions-item label="视频ID">{{ currentTask.itemId }}</el-descriptions-item>
          <el-descriptions-item label="账号ID">{{ currentTask.accountId }}</el-descriptions-item>
          <el-descriptions-item label="营销目标">{{ formatTargetType(currentTask.targetType) }}</el-descriptions-item>
          <el-descriptions-item label="预算">¥{{ currentTask.budget }}</el-descriptions-item>
          <el-descriptions-item label="时长">{{ currentTask.duration }}小时</el-descriptions-item>
          <el-descriptions-item v-if="currentTask.renewCount" label="成功续费次数">{{ currentTask.renewCount }}次</el-descriptions-item>
        </el-descriptions>
      </div>
    </el-dialog>
    
    <!-- 续费对话框 -->
    <RenewDialog 
      v-model="renewVisible"
      :task="currentRenewTask"
      :mode="renewMode"
      @submit="confirmRenewOrReorder"
    />
    
    <!-- 批量续费对话框 -->
    <BatchRenewDialog 
      v-model="batchRenewVisible"
      :tasks="selectedTasks"
      @submit="handleBatchRenewSubmit"
    />
    
    <!-- 列配置对话框 -->
    <ColumnConfig 
      v-model="showColumnConfig"
      :columns="availableColumns"
      :selected-keys="visibleColumns"
      @confirm="handleColumnConfigChange"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Setting } from '@element-plus/icons-vue'
import type { DouplusTaskVO } from '@/api/types'
import { getTaskPage, cancelTask as cancelTaskApi, deleteTask as deleteTaskApi, getTaskDetail, renewTask } from '@/api/douplus'
import { getAccountList } from '@/api/account'
import { OrderTable, OrderFilters, SortCascader, RenewDialog, BatchRenewDialog } from '@/components/order'
import ColumnConfig, { type ColumnDefinition } from '@/components/order/ColumnConfig.vue'
import type { OrderFiltersType, MemberOption, SortOption } from '@/components/order'

const COLUMN_STORAGE_KEY = 'douplus_order_visible_columns'

// Props
interface Props {
  accountId?: number  // 可选：指定账号ID进行筛选
  showMemberFilter?: boolean  // 是否显示账号筛选器
  showAccountColumn?: boolean  // 是否显示账号列
  hideFilters?: boolean  // 是否隐藏筛选器
}

const props = withDefaults(defineProps<Props>(), {
  showMemberFilter: true,
  showAccountColumn: true,
  hideFilters: false
})

// Emits
const emit = defineEmits<{
  (e: 'export'): void
}>()

interface Pagination {
  currentPage: number
  pageSize: number
  total: number
}

const loading = ref(false)
const tasks = ref<any[]>([])
const detailVisible = ref(false)
const currentTask = ref<DouplusTaskVO | null>(null)
const members = ref<MemberOption[]>([])

// 续费相关
const renewVisible = ref(false)
const currentRenewTask = ref<any>(null)
const renewMode = ref<'renew' | 'reorder'>('renew')

// 批量续费相关
const selectedTasks = ref<any[]>([])
const batchRenewVisible = ref(false)
const orderTableRef = ref<any>(null)

// 列配置相关
const showColumnConfig = ref(false)
const availableColumns: ColumnDefinition[] = [
  { key: 'status', label: '投放状态', fixed: true, defaultVisible: true },
  { key: 'amount', label: '投放金额', defaultVisible: true },
  { key: 'hundredPlayRate', label: '百播放量', defaultVisible: true },
  { key: 'convertCost', label: '转化成本', defaultVisible: true },
  { key: 'hundredShareRate', label: '百转发率', defaultVisible: true },
  { key: 'likeRate', label: '点赞比', defaultVisible: false },
  { key: 'shareRate', label: '转发比', defaultVisible: false },
  { key: 'playCount', label: '播放量', defaultVisible: true },
  { key: 'likeCount', label: '点赞', defaultVisible: false },
  { key: 'shareCount', label: '转发', defaultVisible: false },
  { key: 'convertCount', label: '转化', defaultVisible: true },
  { key: 'fiveSecRate', label: '5S完播率', defaultVisible: false },
  { key: 'endTime', label: '结束时间', defaultVisible: true }
]

// 从localStorage加载列配置
const loadColumnConfig = (): string[] => {
  try {
    const saved = localStorage.getItem(COLUMN_STORAGE_KEY)
    if (saved) {
      return JSON.parse(saved)
    }
  } catch (e) {
    console.error('加载列配置失败', e)
  }
  // 返回默认可见列
  return availableColumns.filter(col => col.defaultVisible !== false).map(col => col.key)
}

const visibleColumns = ref<string[]>(loadColumnConfig())

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
  dateRange: getDefaultDateRange()
})

const sortOption = ref<SortOption>({
  field: 'createTime',
  order: 'desc'
})

const pagination = reactive<Pagination>({
  currentPage: 1,
  pageSize: 20,
  total: 0
})

// 监听accountId变化，自动刷新数据
watch(() => props.accountId, () => {
  pagination.currentPage = 1
  loadTasks()
}, { immediate: false })

// 加载账号列表（用于筛选）
const loadMembers = async () => {
  try {
    const res = await getAccountList()
    if (res.code === 200 && res.data) {
      members.value = res.data.map((account: any) => ({
        value: account.id,
        label: account.nickname || account.douyinId
      }))
    }
  } catch (error) {
    console.error('加载账号列表失败', error)
  }
}

// 加载订单列表
const loadTasks = async () => {
  loading.value = true
  try {
    const params: any = {
      pageNum: pagination.currentPage,
      pageSize: pagination.pageSize,
      sortField: sortOption.value.field,  // 修复：后端期望sortField而不是sortBy
      sortOrder: sortOption.value.order
    }
    
    // 如果传入了accountId，添加到筛选条件
    if (props.accountId) {
      params.accountId = props.accountId
    } else if (filters.value.accountId) {
      // 否则使用筛选器中的accountId
      params.accountId = filters.value.accountId
    }
    
    // 添加其他筛选条件
    if (filters.value.status) {
      params.status = filters.value.status
    }
    if (filters.value.dateRange && filters.value.dateRange.length === 2) {
      params.startDate = filters.value.dateRange[0]
      params.endDate = filters.value.dateRange[1]
    }
    if (filters.value.keyword) {
      params.keyword = filters.value.keyword
    }
    
    const res = await getTaskPage(params)
    if (res.code === 200) {
      tasks.value = res.data.records || []  // 修复：使用records而不是list
      pagination.total = res.data.total || 0
    }
  } catch (error) {
    console.error('加载订单失败', error)
    ElMessage.error('加载订单失败')
  } finally {
    loading.value = false
  }
}

// 筛选条件变化
const handleFilterChange = () => {
  pagination.currentPage = 1
  loadTasks()
}

// 排序变化
const handleSortChange = () => {
  loadTasks()
}

// 分页变化
const handleSizeChange = (val: number) => {
  pagination.pageSize = val
  pagination.currentPage = 1
  loadTasks()
}

const handleCurrentChange = (val: number) => {
  pagination.currentPage = val
  loadTasks()
}

// 导出
const exportData = () => {
  emit('export')
}

// 查看详情
const viewDetails = async (task: any) => {
  try {
    const res = await getTaskDetail(task.id)
    if (res.code === 200) {
      currentTask.value = res.data
      detailVisible.value = true
    }
  } catch (error) {
    console.error('查看详情失败', error)
  }
}

// 取消订单
const cancelTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确认取消订单 ${task.id}？取消后无法恢复。`,
      '取消订单',
      { type: 'warning' }
    )
    
    await cancelTaskApi(task.id)
    ElMessage.success('订单已取消')
    loadTasks()
  } catch (error) {
    console.error('取消订单失败', error)
  }
}

// 删除订单
const deleteTask = async (task: any) => {
  try {
    await ElMessageBox.confirm(
      `确认删除任务 ${task.id}？删除后无法恢复。`,
      '删除任务',
      { type: 'warning' }
    )
    
    await deleteTaskApi(task.id)
    ElMessage.success('任务已删除')
    loadTasks()
  } catch (error) {
    console.error('删除任务失败', error)
  }
}

// 续费 - 打开弹窗
const handleRenew = (task: any) => {
  currentRenewTask.value = task
  renewMode.value = 'renew'
  renewVisible.value = true
}

// 再次下单 - 打开弹窗
const handleReorder = (task: any) => {
  currentRenewTask.value = task
  renewMode.value = 'reorder'
  renewVisible.value = true
}

// 续费/再次下单 - 确认提交
const confirmRenewOrReorder = async (data: { 
  task: any, 
  budget: number, 
  duration: number,
  investPassword?: string,
  fixedTimeStart?: string,
  fixedTimeEnd?: string
}) => {
  try {
    await renewTask({
      orderId: data.task.orderId,
      budget: data.budget,
      duration: data.duration,
      investPassword: data.investPassword,
      fixedTimeStart: data.fixedTimeStart,
      fixedTimeEnd: data.fixedTimeEnd
    })
    
    ElMessage.success(`${renewMode.value === 'renew' ? '续费' : '下单'}成功！`)
    renewVisible.value = false
    loadTasks()
  } catch (error: any) {
    console.error('操作失败', error)
    ElMessage.error(error.message || `${renewMode.value === 'renew' ? '续费' : '下单'}失败`)
  }
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
    
    const orderIds = tasks.map(t => t.orderId).filter(Boolean)
    
    if (orderIds.length === 0) {
      ElMessage.error('选中的订单缺少订单ID')
      return
    }
    
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
      loadTasks()
    } else {
      ElMessage.error(result.message || '批量续费失败')
    }
  } catch (error: any) {
    console.error('批量续费失败', error)
    ElMessage.error(error.message || '批量续费失败')
  }
}

// 列配置变化处理
const handleColumnConfigChange = (selectedKeys: string[]) => {
  visibleColumns.value = selectedKeys
  // 保存到localStorage
  try {
    localStorage.setItem(COLUMN_STORAGE_KEY, JSON.stringify(selectedKeys))
    ElMessage.success('列配置已保存')
  } catch (e) {
    console.error('保存列配置失败', e)
    ElMessage.warning('保存列配置失败')
  }
}

// 格式化营销目标
const formatTargetType = (targetType: string) => {
  const typeMap: Record<string, string> = {
    'VIDEO': '视频推广',
    'LIVE': '直播推广',
    'GOODS': '商品推广',
    'AWEME': '内容加热',
    'USER': '粉丝增长',
    'APP': '应用推广'
  }
  return typeMap[targetType] || targetType || '-'
}

// 暴露刷新方法给父组件
defineExpose({
  refresh: loadTasks
})

// 初始化
onMounted(() => {
  if (props.showMemberFilter && !props.accountId) {
    loadMembers()
  }
  loadTasks()
})
</script>

<style scoped lang="scss">
.order-list-view {
  .filter-card {
    margin-bottom: 16px;
  }
  
  .table-card {
    .table-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 16px 0;
      
      .header-left {
        display: flex;
        align-items: center;
        gap: 20px;
        flex: 1;
        
        .order-count {
          font-size: 14px;
          color: #1890ff;
          font-weight: 500;
        }
        
        .batch-actions {
          display: flex;
          align-items: center;
          gap: 12px;
          padding-left: 20px;
          border-left: 1px solid #e4e7ed;
        }
      }
      
      .header-right {
        display: flex;
        align-items: center;
        gap: 12px;
        
        .column-config-btn {
          color: #606266;
          transition: all 0.3s;
          
          &:hover {
            color: #409eff;
            background: #ecf5ff;
            border-color: #c6e2ff;
          }
        }
      }
    }
  }
}
</style>
