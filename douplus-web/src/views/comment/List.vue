<template>
  <div class="comment-list">
    <div class="card">
      <div class="card-header">
        <div class="card-title">评论列表</div>
        <div>
          <el-select v-model="accountId" placeholder="选择账号" clearable style="width: 150px; margin-right: 10px;">
            <el-option v-for="acc in accounts" :key="acc.id" :label="acc.nickname" :value="acc.id" />
          </el-select>
          <el-button @click="loadData">刷新</el-button>
        </div>
      </div>
      
      <el-table :data="comments" v-loading="loading" stripe>
        <el-table-column type="selection" width="50" />
        <el-table-column label="评论者" width="180">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="32" :src="convertToHttps(row.avatar)">{{ row.nickname?.charAt(0) }}</el-avatar>
              <span>{{ row.nickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="评论内容" min-width="300" show-overflow-tooltip />
        <el-table-column prop="likeCount" label="点赞" width="80" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.isNegative" type="danger">负面</el-tag>
            <el-tag v-else type="success">正常</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="commentTime" label="评论时间" width="170" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" text @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      
      <div style="display: flex; justify-content: space-between; margin-top: 20px;">
        <el-button type="danger" :disabled="!selectedIds.length" @click="handleBatchDelete">
          批量删除 ({{ selectedIds.length }})
        </el-button>
        <el-pagination
          v-model:current-page="pageNum"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[20, 50, 100]"
          layout="total, sizes, prev, pager, next"
          @change="loadData"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { convertToHttps } from '@/utils/url'
import { ElMessage, ElMessageBox } from 'element-plus'
import { getAccountList } from '@/api/account'
import type { DouyinAccount, Comment } from '@/api/types'

const loading = ref(false)
const comments = ref<Comment[]>([])
const accounts = ref<DouyinAccount[]>([])
const accountId = ref<number | null>(null)
const pageNum = ref(1)
const pageSize = ref(20)
const total = ref(0)
const selectedIds = ref<number[]>([])

const loadAccounts = async () => {
  try {
    const res = await getAccountList()
    if (res.code === 200) {
      accounts.value = res.data || []
    }
  } catch (error) {
    console.error('加载账号失败', error)
  }
}

const loadData = async () => {
  loading.value = true
  // TODO: 调用实际API
  // 模拟数据
  setTimeout(() => {
    comments.value = [
      { id: 1, nickname: '用户A', avatar: '', content: '很棒的视频！', likeCount: 10, isNegative: 0, commentTime: '2026-01-16 10:00:00' } as any,
      { id: 2, nickname: '用户B', avatar: '', content: '太好看了', likeCount: 5, isNegative: 0, commentTime: '2026-01-16 09:30:00' } as any
    ]
    total.value = 2
    loading.value = false
  }, 500)
}

const handleDelete = async (row: Comment) => {
  await ElMessageBox.confirm('确认删除该评论？', '提示', { type: 'warning' })
  ElMessage.success('已标记删除')
}

const handleBatchDelete = async () => {
  await ElMessageBox.confirm(`确认删除选中的 ${selectedIds.value.length} 条评论？`, '提示', { type: 'warning' })
  ElMessage.success('已标记删除')
}

watch(accountId, () => {
  pageNum.value = 1
  loadData()
})

onMounted(() => {
  loadAccounts()
  loadData()
})
</script>
