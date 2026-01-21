<template>
  <el-dialog
    v-model="visible"
    title="续费投放"
    width="500px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="renew-content">
      <!-- 订单信息摘要 -->
      <div class="order-summary">
        <div class="summary-row">
          <span class="label">视频：</span>
          <span class="value">{{ task?.videoTitle || task?.itemId }}</span>
        </div>
        <div class="summary-row">
          <span class="label">账号：</span>
          <span class="value">{{ task?.accountNickname }}</span>
        </div>
        <div class="summary-row">
          <span class="label">单笔金额：</span>
          <span class="value highlight">¥{{ task?.budget }}</span>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 续费设置 -->
      <el-form :model="form" label-width="100px" class="renew-form">
        <el-form-item label="投放笔数">
          <div class="count-input">
            <el-input-number 
              v-model="form.count" 
              :min="1" 
              :max="10"
              controls-position="right"
            />
            <span class="count-hint">笔（最多10笔）</span>
          </div>
        </el-form-item>
        
        <el-form-item label="投放密码">
          <el-input
            v-model="form.investPassword"
            type="password"
            placeholder="请输入投放密码"
            show-password
          />
        </el-form-item>
        
        <div class="total-info">
          <span class="total-label">预计总投放金额：</span>
          <span class="total-value">¥{{ totalAmount }}</span>
        </div>
      </el-form>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleConfirm">
        确认续费
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'

// 订单任务接口
interface OrderTask {
  id: number
  accountId?: number
  itemId?: string
  videoTitle?: string
  accountNickname?: string
  budget?: number
  duration?: number
  objective?: string
  strategy?: string
  wantType?: string
  targetConfig?: string
}

// Props
const props = defineProps<{
  modelValue: boolean
  task: OrderTask | null
}>()

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'confirm', data: { task: OrderTask, count: number, investPassword: string }): void
}>()

const loading = ref(false)

const form = reactive({
  count: 1,
  investPassword: ''
})

// 计算属性 - 弹窗可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 计算属性 - 总金额
const totalAmount = computed(() => {
  const budget = props.task?.budget || 0
  return (budget * form.count).toFixed(2)
})

// 监听弹窗打开，重置表单
watch(() => props.modelValue, (val) => {
  if (val) {
    form.count = 1
    form.investPassword = ''
  }
})

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 确认续费
const handleConfirm = () => {
  if (!props.task) return
  
  if (!form.investPassword) {
    ElMessage.warning('请输入投放密码')
    return
  }
  
  emit('confirm', {
    task: props.task,
    count: form.count,
    investPassword: form.investPassword
  })
}

// 设置加载状态（供父组件调用）
const setLoading = (val: boolean) => {
  loading.value = val
}

defineExpose({ setLoading })
</script>

<script lang="ts">
import { ElMessage } from 'element-plus'
</script>

<style scoped>
.renew-content {
  padding: 0 10px;
}

.order-summary {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.summary-row {
  display: flex;
  margin-bottom: 8px;
}

.summary-row:last-child {
  margin-bottom: 0;
}

.summary-row .label {
  color: #666;
  width: 80px;
  flex-shrink: 0;
}

.summary-row .value {
  color: #333;
  flex: 1;
}

.summary-row .value.highlight {
  color: #ff6b35;
  font-weight: 600;
}

.renew-form {
  margin-top: 16px;
}

.count-input {
  display: flex;
  align-items: center;
  gap: 12px;
}

.count-hint {
  color: #999;
  font-size: 13px;
}

.total-info {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  padding: 16px 0;
  border-top: 1px dashed #e5e7eb;
  margin-top: 16px;
}

.total-label {
  color: #666;
  font-size: 14px;
}

.total-value {
  color: #ff6b35;
  font-size: 24px;
  font-weight: 600;
  margin-left: 8px;
}
</style>
