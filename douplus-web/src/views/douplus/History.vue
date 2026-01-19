<template>
  <div class="douplus-history">
    <div class="page-header">
      <h2>投放记录</h2>
      <p class="subtitle">查看历史投放任务及效果数据</p>
    </div>
    
    <el-card class="filter-card">
      <el-form :model="filters" inline size="default">
        <el-form-item label="任务状态">
          <el-select v-model="filters.status" placeholder="全部状态" clearable>
            <el-option label="待执行" value="WAIT" />
            <el-option label="执行中" value="RUNNING" />
            <el-option label="成功" value="SUCCESS" />
            <el-option label="失败" value="FAIL" />
            <el-option label="已取消" value="CANCELLED" />
          </el-select>
        </el-form-item>
        
        <el-form-item label="投放时间">
          <el-date-picker
            v-model="filters.dateRange"
            type="daterange"
            range-separator="至"
            start-placeholder="开始日期"
            end-placeholder="结束日期"
            format="YYYY-MM-DD"
            value-format="YYYY-MM-DD"
          />
        </el-form-item>
        
        <el-form-item>
          <el-button type="primary" @click="loadTasks">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
        </el-form-item>
      </el-form>
    </el-card>
    
    <el-card class="table-card">
      <el-table 
        :data="tasks" 
        v-loading="loading"
        style="width: 100%"
      >
        <el-table-column prop="id" label="任务ID" width="100" />
        
        <el-table-column label="投放账号" width="200">
          <template #default="{ row }">
            <div class="account-cell">
              <el-avatar :size="30" :src="row.accountAvatar" />
              <span>{{ row.accountNickname }}</span>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column prop="itemId" label="视频ID" width="150" show-overflow-tooltip />
        
        <el-table-column label="投放金额" width="100">
          <template #default="{ row }">
            <span class="amount">¥{{ row.budget }}</span>
          </template>
        </el-table-column>
        
        <el-table-column label="预计效果" width="120">
          <template #default="{ row }">
            <div class="effect-info">
              <div>曝光: {{ row.expectedExposure }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="实际效果" width="120">
          <template #default="{ row }">
            <div class="effect-info">
              <div>曝光: {{ row.actualExposure || 0 }}</div>
            </div>
          </template>
        </el-table-column>
        
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">
              {{ getStatusText(row.status) }}
            </el-tag>
          </template>
        </el-table-column>
        
        <el-table-column label="创建时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.createTime) }}
          </template>
        </el-table-column>
        
        <el-table-column label="计划执行时间" width="160">
          <template #default="{ row }">
            {{ formatDate(row.scheduledTime) }}
          </template>
        </el-table-column>
        
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button 
              size="small" 
              @click="viewDetails(row)"
              v-if="row.status !== 'WAIT'"
            >
              查看详情
            </el-button>
            <el-button 
              size="small" 
              type="danger" 
              @click="cancelTask(row)"
              v-if="row.status === 'WAIT'"
            >
              取消任务
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      
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
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { DouplusTaskVO } from '@/api/types'
import { getTaskPage, cancelTask as cancelTaskApi, getTaskDetail } from '@/api/douplus'

interface Filters {
  status?: string
  dateRange?: [string, string]
}

interface Pagination {
  currentPage: number
  pageSize: number
  total: number
}

const loading = ref(false)
const tasks = ref<DouplusTaskVO[]>([])
const detailVisible = ref(false)
const currentTask = ref<DouplusTaskVO | null>(null)

const filters = reactive<Filters>({
  status: '',
  dateRange: undefined
})

const pagination = reactive<Pagination>({
  currentPage: 1,
  pageSize: 10,
  total: 0
})

// 加载任务列表
const loadTasks = async () => {
  loading.value = true
  try {
    const res = await getTaskPage({
      pageNum: pagination.currentPage,
      pageSize: pagination.pageSize,
      status: filters.status
    })
    
    if (res.code === 200) {
      tasks.value = res.data?.records || []
      pagination.total = res.data?.total || 0
    }
  } catch (error) {
    console.error('加载任务失败', error)
  } finally {
    loading.value = false
  }
}

// 重置筛选条件
const resetFilters = () => {
  filters.status = ''
  filters.dateRange = undefined
  pagination.currentPage = 1
  loadTasks()
}

// 分页大小变化
const handleSizeChange = (size: number) => {
  pagination.pageSize = size
  pagination.currentPage = 1
  loadTasks()
}

// 当前页变化
const handleCurrentChange = (page: number) => {
  pagination.currentPage = page
  loadTasks()
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
const viewDetails = async (task: DouplusTaskVO) => {
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
const cancelTask = async (task: DouplusTaskVO) => {
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

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.douplus-history {
  max-width: 1400px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  margin-bottom: 20px;
}

.page-header h2 {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 8px;
}

.page-header .subtitle {
  color: #6b7280;
  font-size: 14px;
}

.filter-card {
  margin-bottom: 20px;
}

.table-card {
  margin-bottom: 20px;
}

.account-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}

.amount {
  color: #e74c3c;
  font-weight: 600;
}

.effect-info {
  font-size: 12px;
  color: #6b7280;
}

.task-detail {
  max-height: 60vh;
  overflow-y: auto;
}
</style>