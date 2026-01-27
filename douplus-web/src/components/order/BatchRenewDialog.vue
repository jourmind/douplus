<template>
  <el-dialog
    v-model="visible"
    title="批量续费"
    width="600px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="dialog-content">
      <!-- 选中的订单摘要 -->
      <el-alert
        :title="`已选择 ${tasks.length} 个投放中的订单`"
        type="info"
        :closable="false"
        style="margin-bottom: 20px;"
      />
      
      <!-- 订单列表预览 -->
      <div class="selected-orders">
        <div class="order-list-title">订单列表</div>
        <div class="order-list-content">
          <div v-for="task in tasks" :key="task.id" class="order-item">
            <el-image :src="task.videoCoverUrl || task.videoCover" class="order-cover" fit="cover">
              <template #error>
                <div class="cover-placeholder">
                  <el-icon><VideoCamera /></el-icon>
                </div>
              </template>
            </el-image>
            <div class="order-info">
              <div class="order-title">{{ task.videoTitle || task.itemId }}</div>
              <div class="order-budget">当前预算: ¥{{ task.budget }}</div>
            </div>
          </div>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 批量设置表单 -->
      <el-form :model="form" label-width="100px">
        <!-- 投放金额 -->
        <el-form-item label="追加金额">
          <div class="option-group">
            <div 
              v-for="item in BUDGET_OPTIONS" 
              :key="item.value"
              :class="['option-btn', { active: form.budget === item.value || (item.value === 0 && customBudget) }]"
              @click="selectBudget(item.value)"
            >
              {{ item.label }}
            </div>
          </div>
          <el-input-number 
            v-if="customBudget" 
            v-model="form.budget" 
            :min="100" 
            :max="50000" 
            :step="100"
            style="width: 150px; margin-top: 10px;"
          >
            <template #suffix>元</template>
          </el-input-number>
        </el-form-item>
        
        <!-- 投放时长 -->
        <el-form-item label="延长时长">
          <div class="option-group">
            <div 
              v-for="item in DURATION_OPTIONS" 
              :key="item.value"
              :class="['option-btn', { active: !customDuration && form.duration === item.value || (item.value === 0 && customDuration) }]"
              @click="selectDuration(item.value)"
            >
              {{ item.label }}
            </div>
          </div>
          <el-input-number 
            v-if="customDuration" 
            v-model="form.duration" 
            :min="1" 
            :max="168" 
            style="width: 150px; margin-top: 10px;"
          >
            <template #suffix>小时</template>
          </el-input-number>
        </el-form-item>
        
        <!-- 总计 -->
        <el-form-item label="预计总消耗">
          <div class="total-cost">
            <span class="cost-amount">¥{{ totalCost }}</span>
            <span class="cost-desc">（{{ tasks.length }} 个订单 × ¥{{ form.budget }}）</span>
          </div>
        </el-form-item>
      </el-form>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="submitting" @click="handleSubmit">
        确认续费（¥{{ totalCost }}）
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { VideoCamera } from '@element-plus/icons-vue'

interface Task {
  id: number
  orderId?: string
  videoTitle?: string
  itemId?: string
  videoCoverUrl?: string
  videoCover?: string
  budget: number
}

interface Props {
  modelValue: boolean
  tasks: Task[]
}

const props = withDefaults(defineProps<Props>(), {
  tasks: () => []
})

const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', data: { tasks: Task[], budget: number, duration: number }): void
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

const submitting = ref(false)
const customBudget = ref(false)
const customDuration = ref(false)

const form = ref({
  budget: 100,
  duration: 24
})

// 预设金额选项
const BUDGET_OPTIONS = [
  { label: '¥100', value: 100 },
  { label: '¥200', value: 200 },
  { label: '¥500', value: 500 },
  { label: '自定义', value: 0 }
]

// 预设时长选项
const DURATION_OPTIONS = [
  { label: '12小时', value: 12 },
  { label: '24小时', value: 24 },
  { label: '48小时', value: 48 },
  { label: '自定义', value: 0 }
]

// 计算总消耗
const totalCost = computed(() => {
  return form.value.budget * props.tasks.length
})

// 选择预算
const selectBudget = (value: number) => {
  if (value === 0) {
    customBudget.value = true
    form.value.budget = 100
  } else {
    customBudget.value = false
    form.value.budget = value
  }
}

// 选择时长
const selectDuration = (value: number) => {
  if (value === 0) {
    customDuration.value = true
    form.value.duration = 24
  } else {
    customDuration.value = false
    form.value.duration = value
  }
}

// 提交
const handleSubmit = () => {
  emit('submit', {
    tasks: props.tasks,
    budget: form.value.budget,
    duration: form.value.duration
  })
}

// 关闭
const handleClose = () => {
  visible.value = false
}
</script>

<style scoped lang="scss">
.dialog-content {
  .selected-orders {
    .order-list-title {
      font-size: 14px;
      font-weight: 500;
      color: #333;
      margin-bottom: 12px;
    }
    
    .order-list-content {
      max-height: 200px;
      overflow-y: auto;
      border: 1px solid #ebeef5;
      border-radius: 4px;
      padding: 8px;
      
      .order-item {
        display: flex;
        gap: 12px;
        padding: 8px;
        border-radius: 4px;
        
        &:hover {
          background: #f5f7fa;
        }
        
        .order-cover {
          width: 60px;
          height: 34px;
          border-radius: 4px;
          flex-shrink: 0;
          
          .cover-placeholder {
            width: 100%;
            height: 100%;
            display: flex;
            align-items: center;
            justify-content: center;
            background: #f5f7fa;
            color: #909399;
          }
        }
        
        .order-info {
          flex: 1;
          min-width: 0;
          
          .order-title {
            font-size: 13px;
            color: #333;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          
          .order-budget {
            font-size: 12px;
            color: #909399;
            margin-top: 4px;
          }
        }
      }
    }
  }
  
  .option-group {
    display: flex;
    gap: 10px;
    flex-wrap: wrap;
    
    .option-btn {
      padding: 8px 16px;
      border: 1px solid #dcdfe6;
      border-radius: 4px;
      cursor: pointer;
      transition: all 0.3s;
      font-size: 14px;
      
      &:hover {
        border-color: #409eff;
        color: #409eff;
      }
      
      &.active {
        background: #409eff;
        border-color: #409eff;
        color: #fff;
      }
    }
  }
  
  .total-cost {
    .cost-amount {
      font-size: 24px;
      font-weight: bold;
      color: #ff6b35;
    }
    
    .cost-desc {
      font-size: 12px;
      color: #909399;
      margin-left: 8px;
    }
  }
}
</style>
