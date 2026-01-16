<template>
  <div class="records-page">
    <div class="card">
      <div class="card-header">
        <div class="card-title">投放记录</div>
        <div>
          <el-select v-model="status" placeholder="全部状态" clearable style="width: 120px; margin-right: 10px;">
            <el-option value="" label="全部" />
            <el-option value="WAIT" label="待执行" />
            <el-option value="RUNNING" label="执行中" />
            <el-option value="SUCCESS" label="已完成" />
            <el-option value="FAIL" label="失败" />
          </el-select>
          <el-button @click="loadData">刷新</el-button>
        </div>
      </div>
      
      <el-table :data="records" v-loading="loading" stripe>
        <el-table-column label="账号" width="180">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="32" :src="row.accountAvatar">{{ row.accountNickname?.charAt(0) }}</el-avatar>
              <span>{{ row.accountNickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="itemId" label="视频ID" width="180" show-overflow-tooltip />
        <el-table-column prop="budget" label="投放金额" width="100">
          <template #default="{ row }">
            ¥{{ row.budget }}
          </template>
        </el-table-column>
        <el-table-column prop="duration" label="时长" width="80">
          <template #default="{ row }">
            {{ row.duration }}h
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="getStatusType(row.status)">{{ row.statusText }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="actualExposure" label="曝光量" width="100" />
        <el-table-column prop="createTime" label="创建时间" width="170" />
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <el-button 
              v-if="row.status === 'WAIT'"
              type="danger" 
              size="small" 
              text
              @click="handleCancel(row)"
            >
              取消
            </el-button>
            <el-button type="primary" size="small" text @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div style="display: flex; justify-content: flex-end; margin-top: 20px;">
        <el-pagination
          v-model:current-page="pageNum"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[10, 20, 50]"
          layout="total, sizes, prev, pager, next"
          @change="loadData"
        />
      </div>
    </div>
    
    <!-- 详情对话框 -->
    <el-dialog v-model="showDetailDialog" title="投放详情" width="500px">
      <el-descriptions :column="1" border v-if="currentRecord">
        <el-descriptions-item label="任务ID">{{ currentRecord.id }}</el-descriptions-item>
        <el-descriptions-item label="抖音账号">{{ currentRecord.accountNickname }}</el-descriptions-item>
        <el-descriptions-item label="视频ID">{{ currentRecord.itemId }}</el-descriptions-item>
        <el-descriptions-item label="投放金额">¥{{ currentRecord.budget }}</el-descriptions-item>
        <el-descriptions-item label="投放时长">{{ currentRecord.duration }}小时</el-descriptions-item>
        <el-descriptions-item label="状态">
          <el-tag :type="getStatusType(currentRecord.status)">{{ currentRecord.statusText }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="订单号">{{ currentRecord.orderId || '-' }}</el-descriptions-item>
        <el-descriptions-item label="实际曝光">{{ currentRecord.actualExposure || 0 }}</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ currentRecord.createTime }}</el-descriptions-item>
        <el-descriptions-item label="执行时间">{{ currentRecord.executedTime || '-' }}</el-descriptions-item>
        <el-descriptions-item v-if="currentRecord.errorMsg" label="错误信息">
          <span style="color: #f56c6c;">{{ currentRecord.errorMsg }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getTaskPage, cancelTask } from '@/api/douplus'
import type { DouplusTask } from '@/api/types'

const loading = ref(false)
const records = ref<DouplusTask[]>([])
const pageNum = ref(1)
const pageSize = ref(10)
const total = ref(0)
const status = ref('')

const showDetailDialog = ref(false)
const currentRecord = ref<DouplusTask | null>(null)

const getStatusType = (status: string) => {
  const map: Record<string, string> = {
    WAIT: 'info',
    RUNNING: 'warning',
    SUCCESS: 'success',
    FAIL: 'danger',
    CANCELLED: 'info'
  }
  return map[status] || 'info'
}

const loadData = async () => {
  loading.value = true
  try {
    const res = await getTaskPage(pageNum.value, pageSize.value, status.value || undefined)
    if (res.code === 200 && res.data) {
      records.value = res.data.records || []
      total.value = res.data.total || 0
    }
  } catch (error) {
    console.error('加载数据失败', error)
  } finally {
    loading.value = false
  }
}

const handleCancel = async (row: DouplusTask) => {
  await ElMessageBox.confirm('确认取消该投放任务？', '提示', { type: 'warning' })
  try {
    await cancelTask(row.id)
    ElMessage.success('任务已取消')
    loadData()
  } catch (error) {
    // 错误已在拦截器处理
  }
}

const showDetail = (row: DouplusTask) => {
  currentRecord.value = row
  showDetailDialog.value = true
}

watch(status, () => {
  pageNum.value = 1
  loadData()
})

onMounted(() => {
  loadData()
})
</script>
