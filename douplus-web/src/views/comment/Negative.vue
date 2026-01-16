<template>
  <div class="negative-comments">
    <div class="card">
      <div class="card-header">
        <div class="card-title">负面评论管理</div>
        <div class="tips" style="color: #9ca3af; font-size: 12px;">
          系统会自动检测命中敏感词的评论，您可以手动删除
        </div>
      </div>
      
      <el-alert 
        title="负面评论将根据您设置的敏感词自动识别，建议及时处理以维护账号形象" 
        type="warning" 
        :closable="false"
        style="margin-bottom: 20px;"
      />
      
      <el-table :data="comments" v-loading="loading" stripe>
        <el-table-column type="selection" width="50" />
        <el-table-column label="评论者" width="150">
          <template #default="{ row }">
            <div style="display: flex; align-items: center; gap: 8px;">
              <el-avatar :size="28" :src="row.avatar">{{ row.nickname?.charAt(0) }}</el-avatar>
              <span>{{ row.nickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="content" label="评论内容" min-width="300">
          <template #default="{ row }">
            <span v-html="highlightKeyword(row.content, row.keywordHit)"></span>
          </template>
        </el-table-column>
        <el-table-column label="命中词" width="120">
          <template #default="{ row }">
            <el-tag type="danger" size="small">{{ row.keywordHit }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="commentTime" label="时间" width="150" />
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const loading = ref(false)
const comments = ref<any[]>([])

const highlightKeyword = (content: string, keyword: string) => {
  if (!keyword) return content
  return content.replace(new RegExp(keyword, 'g'), `<span style="color: #f56c6c; font-weight: bold;">${keyword}</span>`)
}

const loadData = async () => {
  loading.value = true
  // 模拟数据
  setTimeout(() => {
    comments.value = [
      { id: 1, nickname: '路人甲', avatar: '', content: '这个太垃圾了吧', keywordHit: '垃圾', commentTime: '2026-01-16 11:00:00' },
      { id: 2, nickname: '用户X', avatar: '', content: '骗人的，根本没用', keywordHit: '骗人', commentTime: '2026-01-16 10:30:00' }
    ]
    loading.value = false
  }, 500)
}

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm('确认删除该评论？', '提示', { type: 'warning' })
  ElMessage.success('已标记删除，将在下次同步时删除')
  comments.value = comments.value.filter(c => c.id !== row.id)
}

onMounted(() => {
  loadData()
})
</script>
