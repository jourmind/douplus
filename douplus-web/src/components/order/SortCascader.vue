<template>
  <el-popover
    placement="bottom-end"
    :width="280"
    trigger="click"
    v-model:visible="popoverVisible"
    :hide-after="0"
    :show-arrow="false"
    :teleported="true"
    popper-class="sort-cascader-popover"
    :popper-options="{ modifiers: [{ name: 'offset', options: { offset: [0, 4] } }] }"
  >
    <template #reference>
      <div class="sort-trigger">
        <span class="sort-label">{{ currentSortLabel }}</span>
        <el-icon class="sort-arrow" :class="{ 'is-reverse': popoverVisible }">
          <ArrowUp />
        </el-icon>
      </div>
    </template>
    
    <div class="sort-panel">
      <div class="sort-fields">
        <div 
          v-for="field in sortFields" 
          :key="field.value"
          :class="['sort-field-item', { active: localSort.field === field.value }]"
          @click="selectField(field.value)"
        >
          {{ field.label }}
          <el-icon v-if="localSort.field === field.value" class="check-icon"><Check /></el-icon>
        </div>
      </div>
      <div class="sort-divider"></div>
      <div class="sort-orders">
        <div 
          v-for="order in sortOrders" 
          :key="order.value"
          :class="['sort-order-item', { active: localSort.order === order.value }]"
          @click="selectOrder(order.value)"
        >
          {{ order.label }}
        </div>
      </div>
    </div>
  </el-popover>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { ArrowUp, Check } from '@element-plus/icons-vue'

// 排序接口
export interface SortOption {
  field: string
  order: 'asc' | 'desc'
}

// Props
const props = withDefaults(defineProps<{
  modelValue?: SortOption
}>(), {
  modelValue: () => ({ field: 'createTime', order: 'desc' })
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', sort: SortOption): void
  (e: 'change', sort: SortOption): void
}>()

const popoverVisible = ref(false)

// 排序字段选项
const sortFields = [
  { value: 'createTime', label: '按下单时间' },
  { value: 'actualCost', label: '按消耗' },
  { value: 'playCount', label: '按百播放量' },
  { value: 'costPerPlay', label: '按转化成本' },
  { value: 'shareRate', label: '按百转发率' }
]

// 排序方向选项
const sortOrders = [
  { value: 'desc', label: '降序' },
  { value: 'asc', label: '升序' }
]

// 本地排序状态
const localSort = ref<SortOption>({
  field: props.modelValue?.field || 'createTime',
  order: props.modelValue?.order || 'desc'
})

// 当前排序显示文本
const currentSortLabel = computed(() => {
  const field = sortFields.find(f => f.value === localSort.value.field)
  
  if (localSort.value.field === 'createTime') {
    const order = localSort.value.order === 'desc' ? '最新' : '最早'
    return `${field?.label || '按下单时间'}：${order}`
  }
  
  const orderLabel = localSort.value.order === 'desc' ? '高到低' : '低到高'
  return `${field?.label || ''}：${orderLabel}`
})

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    localSort.value = { ...newVal }
  }
}, { deep: true })

// 选择排序字段
const selectField = (field: string) => {
  localSort.value.field = field
  emitChange()
  // 选择字段后延迟关闭，给用户时间看到选中状态
  setTimeout(() => {
    popoverVisible.value = false
  }, 150)
}

// 选择排序方向
const selectOrder = (order: 'asc' | 'desc') => {
  localSort.value.order = order
  emitChange()
  setTimeout(() => {
    popoverVisible.value = false
  }, 150)
}

// 发送变化
const emitChange = () => {
  emit('update:modelValue', { ...localSort.value })
  emit('change', { ...localSort.value })
}
</script>

<style scoped>
.sort-trigger {
  display: flex;
  align-items: center;
  gap: 4px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  padding: 6px 12px;
  border-radius: 4px;
  transition: background 0.2s;
}

.sort-trigger:hover {
  background: #f5f5f5;
}

.sort-label {
  white-space: nowrap;
}

.sort-arrow {
  transition: transform 0.3s;
}

.sort-arrow.is-reverse {
  transform: rotate(180deg);
}

.sort-panel {
  display: flex;
  gap: 0;
}

.sort-fields {
  flex: 1;
  border-right: 1px solid #f0f0f0;
}

.sort-field-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.sort-field-item:hover {
  background: #f5f5f5;
}

.sort-field-item.active {
  color: #ff6b35;
  font-weight: 500;
}

.check-icon {
  color: #ff6b35;
}

.sort-divider {
  width: 1px;
  background: #f0f0f0;
}

.sort-orders {
  flex: 0 0 80px;
}

.sort-order-item {
  padding: 10px 16px;
  cursor: pointer;
  font-size: 14px;
  color: #333;
  transition: all 0.2s;
}

.sort-order-item:hover {
  background: #f5f5f5;
}

.sort-order-item.active {
  color: #ff6b35;
  font-weight: 500;
}
</style>

<!-- 全局样式用于popover（因为teleported到body） -->
<style>
.sort-cascader-popover {
  padding: 0 !important;
  border-radius: 8px !important;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15) !important;
}

.sort-cascader-popover .el-popover__title {
  display: none;
}
</style>
