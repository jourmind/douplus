<template>
  <div class="douplus-create">
    <div class="card">
      <div class="card-header">
        <div class="card-title">
          <el-radio-group v-model="form.taskType" size="default">
            <el-radio-button :value="1">视频投放</el-radio-button>
            <el-radio-button :value="2">直播投放</el-radio-button>
          </el-radio-group>
        </div>
      </div>
      
      <el-form 
        ref="formRef"
        :model="form" 
        :rules="rules" 
        label-width="120px"
        style="max-width: 800px;"
      >
        <div class="form-section">
          <div class="section-title">DOU+投放</div>
          
          <el-form-item label="付款抖音号" prop="accountId">
            <el-select v-model="form.accountId" placeholder="输入或选择付款抖音号" style="width: 100%;">
              <el-option 
                v-for="account in accounts" 
                :key="account.id" 
                :label="account.nickname" 
                :value="account.id"
              >
                <div style="display: flex; align-items: center; gap: 10px;">
                  <el-avatar :size="24" :src="account.avatar">{{ account.nickname?.charAt(0) }}</el-avatar>
                  <span>{{ account.nickname }}</span>
                  <el-tag v-if="account.status !== 1" type="danger" size="small">授权失效</el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>
          
          <el-form-item label="被投抖音号" prop="targetAccountId">
            <el-select v-model="form.targetAccountId" placeholder="输入或选择要投放的抖音号" style="width: 100%;">
              <el-option 
                v-for="account in accounts" 
                :key="account.id" 
                :label="account.nickname" 
                :value="account.id"
              />
            </el-select>
          </el-form-item>
          
          <el-form-item label="被投视频名称" prop="itemId">
            <el-input v-model="form.itemId" placeholder="请选择投放视频" />
          </el-form-item>
          
          <el-form-item label="期望投放类型">
            <el-select v-model="form.targetType" style="width: 200px;">
              <el-option :value="1" label="涨粉" />
              <el-option :value="2" label="点赞评论" />
              <el-option :value="3" label="主页浏览" />
            </el-select>
            <el-select v-model="form.duration" style="width: 150px; margin-left: 20px;">
              <el-option :value="6" label="6小时" />
              <el-option :value="12" label="12小时" />
              <el-option :value="24" label="24小时" />
              <el-option :value="48" label="48小时" />
            </el-select>
          </el-form-item>
          
          <el-form-item label="选择潜在用户">
            <el-radio-group v-model="form.audienceType">
              <el-radio :value="1">
                <span style="color: #ff6b35;">系统智能推荐</span>
              </el-radio>
              <el-radio :value="2">自定义定向推荐</el-radio>
            </el-radio-group>
          </el-form-item>
          
          <el-form-item label="单笔投放金额" prop="budget">
            <el-select v-model="form.budget" style="width: 150px;">
              <el-option :value="100" label="100" />
              <el-option :value="200" label="200" />
              <el-option :value="500" label="500" />
              <el-option :value="1000" label="1000" />
              <el-option :value="2000" label="2000" />
            </el-select>
            <el-link type="primary" style="margin-left: 10px;">自定义</el-link>
            <span style="margin-left: 20px; color: #9ca3af;">
              预计带来转化数 <el-tag type="warning">0-0</el-tag>
            </span>
          </el-form-item>
          
          <el-form-item label="投放笔数" prop="count">
            <el-input-number v-model="form.count" :min="1" :max="100" />
          </el-form-item>
          
          <el-form-item label="预定投放时间">
            <el-radio-group v-model="form.scheduleType">
              <el-radio :value="1">当前时间</el-radio>
              <el-radio :value="2">指定时间</el-radio>
            </el-radio-group>
            <el-date-picker
              v-if="form.scheduleType === 2"
              v-model="form.scheduledTime"
              type="datetime"
              placeholder="选择时间"
              style="margin-left: 20px;"
            />
          </el-form-item>
          
          <el-form-item label="DOU+投放密码" prop="investPassword">
            <el-input 
              v-model="form.investPassword" 
              type="password" 
              placeholder="请输入投放密码"
              style="width: 300px;"
              show-password
            />
            <el-button type="warning" style="margin-left: 10px;">设置投放密码</el-button>
          </el-form-item>
        </div>
        
        <el-form-item>
          <el-button type="primary" size="large" :loading="loading" @click="handleSubmit">
            确认投放
          </el-button>
          <el-button size="large" @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { getAccountList } from '@/api/account'
import { createTask } from '@/api/douplus'
import type { DouyinAccount } from '@/api/types'

const formRef = ref<FormInstance>()
const loading = ref(false)
const accounts = ref<DouyinAccount[]>([])

const form = reactive({
  taskType: 1,
  accountId: null as number | null,
  targetAccountId: null as number | null,
  itemId: '',
  targetType: 1,
  duration: 24,
  audienceType: 1,
  budget: 100,
  count: 1,
  scheduleType: 1,
  scheduledTime: null as Date | null,
  investPassword: ''
})

const rules: FormRules = {
  accountId: [{ required: true, message: '请选择付款抖音号', trigger: 'change' }],
  itemId: [{ required: true, message: '请输入被投视频ID', trigger: 'blur' }],
  budget: [{ required: true, message: '请选择投放金额', trigger: 'change' }],
  investPassword: [{ required: true, message: '请输入投放密码', trigger: 'blur' }]
}

// 加载账号列表
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

// 提交投放
const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return
    
    // 二次确认
    const totalAmount = form.budget * form.count
    await ElMessageBox.confirm(
      `确认投放 ${form.count} 笔，共计 ${totalAmount} 元？`,
      '投放确认',
      { type: 'warning' }
    )
    
    loading.value = true
    try {
      const res = await createTask({
        accountId: form.accountId!,
        itemId: form.itemId,
        taskType: form.taskType,
        targetType: form.targetType,
        duration: form.duration,
        budget: form.budget,
        count: form.count,
        scheduledTime: form.scheduleType === 2 && form.scheduledTime 
          ? form.scheduledTime.toISOString() 
          : undefined,
        investPassword: form.investPassword
      })
      
      if (res.code === 200) {
        ElMessage.success(`投放任务创建成功，共 ${res.data?.length || form.count} 个任务`)
        handleReset()
      }
    } catch (error) {
      // 错误已在拦截器处理
    } finally {
      loading.value = false
    }
  })
}

// 重置表单
const handleReset = () => {
  formRef.value?.resetFields()
  form.investPassword = ''
}

onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.douplus-create {
  max-width: 1000px;
}
</style>
