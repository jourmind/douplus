<template>
  <el-dialog 
    v-model="visible" 
    title="自定义列" 
    width="600px"
    @closed="handleClose"
  >
    <div class="column-config">
      <div class="tip">
        <el-icon><InfoFilled /></el-icon>
        <span>勾选需要显示的列，拖动可调整顺序</span>
      </div>
      
      <el-scrollbar max-height="400px">
        <el-checkbox-group v-model="selectedColumns">
          <div v-for="column in availableColumns" :key="column.key" class="column-item">
            <el-checkbox :label="column.key" :disabled="column.fixed">
              <span class="column-label">{{ column.label }}</span>
              <el-tag v-if="column.fixed" size="small" type="info">必选</el-tag>
            </el-checkbox>
          </div>
        </el-checkbox-group>
      </el-scrollbar>
    </div>
    
    <template #footer>
      <div class="dialog-footer">
        <el-button @click="handleReset">恢复默认</el-button>
        <el-button type="primary" @click="handleConfirm">确定</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { InfoFilled } from '@element-plus/icons-vue'

export interface ColumnDefinition {
  key: string
  label: string
  fixed?: boolean  // 固定列，不可取消
  defaultVisible?: boolean  // 默认是否显示
}

// Props
const props = defineProps<{
  modelValue: boolean
  columns: ColumnDefinition[]
  selectedKeys: string[]
}>()

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'update:selectedKeys', keys: string[]): void
  (e: 'confirm', keys: string[]): void
}>()

const visible = ref(props.modelValue)
const selectedColumns = ref<string[]>([...props.selectedKeys])
const availableColumns = ref<ColumnDefinition[]>([...props.columns])

// 监听外部变化
watch(() => props.modelValue, (val) => {
  visible.value = val
  if (val) {
    selectedColumns.value = [...props.selectedKeys]
  }
})

watch(() => props.selectedKeys, (val) => {
  selectedColumns.value = [...val]
}, { deep: true })

// 监听visible变化
watch(visible, (val) => {
  emit('update:modelValue', val)
})

// 确定
const handleConfirm = () => {
  emit('update:selectedKeys', selectedColumns.value)
  emit('confirm', selectedColumns.value)
  visible.value = false
}

// 恢复默认
const handleReset = () => {
  selectedColumns.value = availableColumns.value
    .filter(col => col.defaultVisible !== false)
    .map(col => col.key)
}

// 关闭
const handleClose = () => {
  emit('update:modelValue', false)
}
</script>

<style scoped>
.column-config {
  padding: 10px 0;
}

.tip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px;
  background: #f0f9ff;
  border-radius: 4px;
  color: #0369a1;
  font-size: 14px;
  margin-bottom: 20px;
}

.column-item {
  padding: 10px 16px;
  border-bottom: 1px solid #f0f0f0;
  transition: background 0.2s;
}

.column-item:hover {
  background: #f5f7fa;
}

.column-item:last-child {
  border-bottom: none;
}

.column-label {
  margin-right: 8px;
}

.dialog-footer {
  display: flex;
  justify-content: flex-end;
  gap: 10px;
}
</style>
