<template>
  <el-dialog
    v-model="visible"
    :title="dialogTitle"
    width="560px"
    :close-on-click-modal="false"
    @close="handleClose"
  >
    <div class="dialog-content">
      <!-- 订单信息摘要 -->
      <div class="order-summary">
        <div class="video-preview">
          <el-image :src="convertToHttps(task?.videoCoverUrl || task?.videoCover)" class="video-cover" fit="cover">
            <template #error>
              <div class="video-placeholder">
                <el-icon><VideoCamera /></el-icon>
              </div>
            </template>
          </el-image>
          <div class="video-info">
            <div class="video-title">{{ task?.videoTitle || task?.itemId }}</div>
            <div class="video-account">{{ task?.accountNickname || task?.awemeNick }}</div>
          </div>
        </div>
        <div class="order-original">
          <div class="info-item">
            <span class="label">原投放金额：</span>
            <span class="value">¥{{ task?.budget }}</span>
          </div>
          <div class="info-item">
            <span class="label">原投放时长：</span>
            <span class="value">{{ task?.duration || 24 }}小时</span>
          </div>
        </div>
      </div>
      
      <el-divider />
      
      <!-- 表单设置 -->
      <el-form :model="form" label-width="100px" class="setting-form">
        <!-- 投放金额 -->
        <el-form-item label="投放金额">
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
            :max="5000000" 
            :step="10"
            style="width: 150px; margin-top: 10px;"
          />
        </el-form-item>
        
        <!-- 投放时长 -->
        <el-form-item label="投放时长">
          <div class="option-group">
            <div 
              v-for="item in DURATION_OPTIONS" 
              :key="item.value"
              :class="['option-btn', { active: !customDuration && form.duration === item.value || (item.value === -1 && customDuration) }]"
              @click="selectDuration(item.value)"
            >
              {{ item.label }}
            </div>
          </div>
          <div v-if="customDuration" class="custom-duration-row">
            <el-input-number 
              v-model="form.duration" 
              :min="0" 
              :max="720" 
              :step="12"
              style="width: 120px; margin-top: 10px;"
            />
            <span class="duration-unit">小时（12的倍数，最大720小时）</span>
          </div>
        </el-form-item>
        
        <!-- 自定义投放时段（仅再次下单模式且>=2天可用） -->
        <el-form-item v-if="mode === 'reorder'" label="投放时段">
          <div class="time-range-row">
            <el-switch 
              v-model="form.customTimeEnabled" 
              :disabled="!canEnableCustomTime"
            />
            <span class="switch-label">{{ canEnableCustomTime ? '自定义投放时段' : '需2天以上才能设置' }}</span>
          </div>
          
          <div v-if="form.customTimeEnabled && canEnableCustomTime" class="time-slot-setting">
            <div class="time-slot-row">
              <span class="row-label">每天</span>
              <el-select v-model="form.fixedTimeStart" style="width: 80px;">
                <el-option v-for="h in 24" :key="'s'+h" :value="h-1" :label="String(h-1).padStart(2,'0')+':00'" />
              </el-select>
              <span class="time-separator">~</span>
              <el-select v-model="form.fixedTimeEnd" style="width: 80px;">
                <el-option 
                  v-for="h in 24" 
                  :key="'e'+h" 
                  :value="h" 
                  :label="String(h).padStart(2,'0')+':00'"
                  :disabled="h <= form.fixedTimeStart"
                />
              </el-select>
              <span class="time-hint">投放</span>
            </div>
          </div>
        </el-form-item>
        
        <!-- 投放密码 -->
        <el-form-item label="投放密码">
          <el-input
            v-model="form.investPassword"
            type="password"
            placeholder="请输入投放密码"
            show-password
            style="width: 200px;"
          />
        </el-form-item>
        
        <!-- 费用预估 -->
        <div class="cost-summary">
          <div class="cost-row total">
            <span>预计金额</span>
            <span class="total-value">¥{{ form.budget }}</span>
          </div>
        </div>
      </el-form>
    </div>
    
    <template #footer>
      <el-button @click="handleClose">取消</el-button>
      <el-button type="primary" :loading="loading" @click="handleConfirm">
        {{ mode === 'renew' ? '确认续费' : '确认下单' }}
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { VideoCamera } from '@element-plus/icons-vue'
import { convertToHttps } from '@/utils/url'

// 预算选项（抖音开放平台API官方要求最低100元）
const BUDGET_OPTIONS = [
  { label: '¥100', value: 100 },
  { label: '¥200', value: 200 },
  { label: '¥500', value: 500 },
  { label: '¥1000', value: 1000 },
  { label: '自定义', value: 0 }
]

// 时长选项（抖音API规则：0、2、6、12、24或12的倍数，最大720小时）
const DURATION_OPTIONS = [
  { label: '不延长', value: 0 },  // 仅续费预算，不延长时间
  { label: '2小时', value: 2 },
  { label: '6小时', value: 6 },
  { label: '12小时', value: 12 },
  { label: '24小时', value: 24 },
  { label: '自定义', value: -1 }  // 使用-1区分自定义模式，实际提交时用form.duration
]

// 订单任务接口
interface OrderTask {
  id: number
  accountId?: number
  itemId?: string
  videoTitle?: string
  videoCoverUrl?: string
  videoCover?: string
  accountNickname?: string
  awemeNick?: string
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
  mode?: 'renew' | 'reorder'  // 续费 或 再次下单
}>()

// Emits
const emit = defineEmits<{
  (e: 'update:modelValue', value: boolean): void
  (e: 'submit', data: { 
    task: OrderTask, 
    budget: number,
    duration: number,
    investPassword: string,
    customTimeEnabled?: boolean,
    fixedTimeStart?: number,
    fixedTimeEnd?: number
  }): void
}>()

const loading = ref(false)
const customBudget = ref(false)
const customDuration = ref(false)

const form = reactive({
  budget: 100,
  duration: 6,
  investPassword: '',
  customTimeEnabled: false,
  fixedTimeStart: 8,
  fixedTimeEnd: 22
})

// 计算属性 - 弹窗可见性
const visible = computed({
  get: () => props.modelValue,
  set: (val) => emit('update:modelValue', val)
})

// 弹窗标题
const dialogTitle = computed(() => {
  return props.mode === 'renew' ? '续费投放' : '再次下单'
})

// 是否可启用自定义时段
const canEnableCustomTime = computed(() => {
  return customDuration.value && form.duration >= 48
})

// 监听弹窗打开，重置表单
watch(() => props.modelValue, (val) => {
  if (val && props.task) {
    // 使用原订单的预算和时长作为默认值
    form.budget = props.task.budget || 100
    form.duration = props.task.duration || 24
    form.investPassword = ''
    form.customTimeEnabled = false
    form.fixedTimeStart = 8
    form.fixedTimeEnd = 22
    
    // 检查是否匹配预设选项
    customBudget.value = !BUDGET_OPTIONS.some(o => o.value === form.budget && o.value !== 0)
    customDuration.value = !DURATION_OPTIONS.some(o => o.value === form.duration && o.value !== -1)
  }
})

// 选择预算
const selectBudget = (value: number) => {
  if (value === 0) {
    customBudget.value = true
    form.budget = 10
  } else {
    customBudget.value = false
    form.budget = value
  }
}

// 选择时长
const selectDuration = (value: number) => {
  if (value === -1) {  // 自定义模式
    customDuration.value = true
    form.duration = 12  // 默认值12小时，符合12的倍数规则
  } else {
    customDuration.value = false
    form.duration = value
    form.customTimeEnabled = false
  }
}

// 关闭弹窗
const handleClose = () => {
  visible.value = false
}

// 确认
const handleConfirm = () => {
  if (!props.task) return
  
  if (!form.investPassword) {
    ElMessage.warning('请输入投放密码')
    return
  }
  
  emit('submit', {
    task: props.task,
    budget: form.budget,
    duration: form.duration,
    investPassword: form.investPassword,
    customTimeEnabled: form.customTimeEnabled,
    fixedTimeStart: form.fixedTimeStart,
    fixedTimeEnd: form.fixedTimeEnd
  })
}

// 设置加载状态（供父组件调用）
const setLoading = (val: boolean) => {
  loading.value = val
}

defineExpose({ setLoading })
</script>

<style scoped>
.dialog-content {
  padding: 0 10px;
}

.order-summary {
  background: #f9f9f9;
  border-radius: 8px;
  padding: 16px;
}

.video-preview {
  display: flex;
  gap: 12px;
  margin-bottom: 12px;
}

.video-cover {
  width: 60px;
  height: 80px;
  border-radius: 4px;
  flex-shrink: 0;
}

.video-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #e5e7eb;
  color: #9ca3af;
  font-size: 24px;
}

.video-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.video-title {
  font-size: 14px;
  color: #333;
  line-height: 1.4;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}

.video-account {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.order-original {
  display: flex;
  gap: 24px;
}

.info-item {
  display: flex;
  align-items: center;
}

.info-item .label {
  color: #666;
  font-size: 13px;
}

.info-item .value {
  color: #ff6b35;
  font-weight: 600;
  font-size: 14px;
}

.setting-form {
  margin-top: 16px;
}

.option-group {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.option-btn {
  padding: 6px 14px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  color: #333;
  font-size: 13px;
}

.option-btn:hover {
  border-color: #1890ff;
}

.option-btn.active {
  border-color: #1890ff;
  color: #1890ff;
  background: #e6f4ff;
}

.custom-duration-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.duration-unit {
  color: #666;
  font-size: 13px;
}

.time-range-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.switch-label {
  font-size: 13px;
  color: #666;
}

.time-slot-setting {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 4px;
}

.time-slot-row {
  display: flex;
  align-items: center;
  gap: 8px;
}

.row-label {
  font-size: 13px;
  color: #666;
}

.time-separator {
  color: #999;
}

.time-hint {
  font-size: 13px;
  color: #666;
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

.cost-summary {
  background: #fffbf0;
  border: 1px solid #ffe7ba;
  border-radius: 8px;
  padding: 16px;
  margin-top: 16px;
}

.cost-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 0;
  font-size: 14px;
  color: #666;
}

.cost-row.total {
  border-top: 1px dashed #e5e7eb;
  margin-top: 8px;
  padding-top: 12px;
  font-weight: 500;
  color: #333;
}

.total-value {
  color: #ff6b35;
  font-size: 20px;
  font-weight: 600;
}
</style>
