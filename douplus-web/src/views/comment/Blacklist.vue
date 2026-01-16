<template>
  <div class="blacklist-page">
    <div class="card">
      <div class="card-header">
        <div class="card-title">敏感词/黑名单管理</div>
        <el-button type="primary" @click="showAddDialog = true">
          <el-icon><Plus /></el-icon>
          添加敏感词
        </el-button>
      </div>
      
      <el-tabs v-model="activeTab">
        <el-tab-pane label="敏感词" name="keyword">
          <el-table :data="keywords" stripe>
            <el-table-column prop="keyword" label="敏感词" />
            <el-table-column label="自动删除" width="100">
              <template #default="{ row }">
                <el-tag :type="row.autoDelete ? 'success' : 'info'">
                  {{ row.autoDelete ? '是' : '否' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="createTime" label="添加时间" width="170" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="danger" size="small" text @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
        
        <el-tab-pane label="用户黑名单" name="user">
          <el-table :data="blacklistUsers" stripe>
            <el-table-column prop="keyword" label="用户昵称/ID" />
            <el-table-column prop="createTime" label="添加时间" width="170" />
            <el-table-column label="操作" width="100">
              <template #default="{ row }">
                <el-button type="danger" size="small" text @click="handleDelete(row)">删除</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-tab-pane>
      </el-tabs>
    </div>
    
    <!-- 添加敏感词对话框 -->
    <el-dialog v-model="showAddDialog" title="添加敏感词" width="500px">
      <el-form :model="addForm" label-width="80px">
        <el-form-item label="类型">
          <el-radio-group v-model="addForm.type">
            <el-radio :value="1">敏感词</el-radio>
            <el-radio :value="2">用户黑名单</el-radio>
          </el-radio-group>
        </el-form-item>
        <el-form-item :label="addForm.type === 1 ? '敏感词' : '用户'">
          <el-input 
            v-model="addForm.keywords" 
            type="textarea" 
            :rows="4"
            :placeholder="addForm.type === 1 ? '输入敏感词，多个用换行分隔' : '输入用户昵称或ID，多个用换行分隔'"
          />
        </el-form-item>
        <el-form-item label="自动删除" v-if="addForm.type === 1">
          <el-switch v-model="addForm.autoDelete" />
          <span style="margin-left: 10px; color: #9ca3af; font-size: 12px;">
            开启后，命中敏感词的评论将自动删除
          </span>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddDialog = false">取消</el-button>
        <el-button type="primary" @click="handleAdd">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const activeTab = ref('keyword')
const showAddDialog = ref(false)

const allList = ref<any[]>([])

const keywords = computed(() => allList.value.filter(item => item.type === 1))
const blacklistUsers = computed(() => allList.value.filter(item => item.type === 2))

const addForm = reactive({
  type: 1,
  keywords: '',
  autoDelete: true
})

const loadData = async () => {
  // 模拟数据
  allList.value = [
    { id: 1, keyword: '垃圾', type: 1, autoDelete: 1, createTime: '2026-01-15 10:00:00' },
    { id: 2, keyword: '骗人', type: 1, autoDelete: 1, createTime: '2026-01-15 10:00:00' },
    { id: 3, keyword: '假货', type: 1, autoDelete: 0, createTime: '2026-01-14 09:00:00' },
    { id: 4, keyword: '黑粉用户A', type: 2, autoDelete: 0, createTime: '2026-01-13 08:00:00' }
  ]
}

const handleAdd = () => {
  const keywordList = addForm.keywords.split('\n').filter(k => k.trim())
  if (keywordList.length === 0) {
    ElMessage.warning('请输入内容')
    return
  }
  
  keywordList.forEach(keyword => {
    allList.value.unshift({
      id: Date.now() + Math.random(),
      keyword: keyword.trim(),
      type: addForm.type,
      autoDelete: addForm.autoDelete ? 1 : 0,
      createTime: new Date().toLocaleString()
    })
  })
  
  ElMessage.success(`已添加 ${keywordList.length} 条`)
  showAddDialog.value = false
  addForm.keywords = ''
}

const handleDelete = async (row: any) => {
  await ElMessageBox.confirm('确认删除？', '提示', { type: 'warning' })
  allList.value = allList.value.filter(item => item.id !== row.id)
  ElMessage.success('删除成功')
}

onMounted(() => {
  loadData()
})
</script>
