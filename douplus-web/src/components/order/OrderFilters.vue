<template>
  <div class="order-filters">
    <div class="filter-left">
      <el-input 
        v-model="localFilters.keyword" 
        placeholder="视频标题" 
        prefix-icon="Search" 
        clearable 
        style="width: 180px"
        @input="emitChange"
      />
      
      <!-- 成员筛选 -->
      <el-select 
        v-if="showMemberFilter && members.length > 0"
        v-model="localFilters.memberId" 
        placeholder="成员 请选择" 
        clearable 
        style="width: 140px"
        @change="emitChange"
      >
        <el-option 
          v-for="member in members" 
          :key="member.id" 
          :label="member.nickname" 
          :value="member.id" 
        />
      </el-select>
      
      <el-select 
        v-model="localFilters.status" 
        placeholder="投放状态 请选择" 
        clearable 
        style="width: 140px"
        @change="emitChange"
      >
        <el-option label="未支付" value="UNPAID" />
        <el-option label="审核中" value="AUDITING" />
        <el-option label="投放中" value="DELIVERING" />
        <el-option label="已完成" value="DELIVERIED" />
        <el-option label="投放终止" value="UNDELIVERIED" />
        <el-option label="审核暂停" value="AUDIT_PAUSE" />
        <el-option label="审核不通过" value="AUDIT_REJECTED" />
      </el-select>
      
      <el-select 
        v-model="localFilters.objective" 
        placeholder="投放目标 请选择" 
        clearable 
        style="width: 140px"
        @change="emitChange"
      >
        <el-option label="评论链接点击" value="LINK_CLICK" />
        <el-option label="点赞评论" value="LIKE_COMMENT" />
        <el-option label="粉丝增长" value="FANS_GROWTH" />
        <el-option label="主页浏览" value="HOMEPAGE_VIEW" />
      </el-select>
    </div>
    
    <div class="filter-right">
      <span class="date-label">下单时间</span>
      <el-date-picker
        v-model="localFilters.dateRange"
        type="daterange"
        range-separator="~"
        start-placeholder="开始日期"
        end-placeholder="结束日期"
        format="YYYY-MM-DD"
        value-format="YYYY-MM-DD"
        style="width: 220px"
        @change="emitChange"
      />
      <el-button @click="emit('export')">数据导出</el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, watch } from 'vue'

// 成员接口
export interface MemberOption {
  id: number
  nickname: string
}

// 筛选条件接口
export interface OrderFiltersType {
  keyword?: string
  memberId?: number
  status?: string
  objective?: string
  dateRange?: [string, string]
}

// Props
const props = withDefaults(defineProps<{
  modelValue?: OrderFiltersType
  members?: MemberOption[]
  showMemberFilter?: boolean
}>(), {
  modelValue: () => ({}),
  members: () => [],
  showMemberFilter: false
})

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', filters: OrderFiltersType): void
  (e: 'change', filters: OrderFiltersType): void
  (e: 'export'): void
}>()

// 本地筛选条件
const localFilters = reactive<OrderFiltersType>({
  keyword: props.modelValue?.keyword || '',
  memberId: props.modelValue?.memberId || undefined,
  status: props.modelValue?.status || '',
  objective: props.modelValue?.objective || '',
  dateRange: props.modelValue?.dateRange || undefined
})

// 监听外部变化
watch(() => props.modelValue, (newVal) => {
  if (newVal) {
    localFilters.keyword = newVal.keyword || ''
    localFilters.memberId = newVal.memberId || undefined
    localFilters.status = newVal.status || ''
    localFilters.objective = newVal.objective || ''
    localFilters.dateRange = newVal.dateRange || undefined
  }
}, { deep: true })

// 发送变化
const emitChange = () => {
  emit('update:modelValue', { ...localFilters })
  emit('change', { ...localFilters })
}
</script>

<style scoped>
.order-filters {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.filter-left {
  display: flex;
  gap: 12px;
}

.filter-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.date-label {
  font-size: 13px;
  color: #666;
}
</style>
