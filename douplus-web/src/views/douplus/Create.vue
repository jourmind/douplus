<template>
  <div class="douplus-create">
    <!-- 右侧主内容 -->
    <div class="main-panel">
      <el-form ref="formRef" :model="form" :rules="rules" label-position="top" size="small">
        
        <!-- 我想要 -->
        <div class="card">
          <div class="card-title">我想要</div>
          <div class="option-group">
            <div 
              v-for="item in WANT_TYPES" 
              :key="item.value"
              :class="['option-btn', { active: form.wantType === item.value, disabled: item.value !== 'CONTENT_HEAT' }]"
              @click="item.value === 'CONTENT_HEAT' && (form.wantType = item.value)"
            >
              {{ item.label }}
            </div>
          </div>
        </div>

        <!-- 更想获得什么 -->
        <div class="card">
          <div class="card-title">更想获得什么 <el-icon><QuestionFilled /></el-icon></div>
          <div class="objective-group">
            <div 
              v-for="item in OBJECTIVES" 
              :key="item.value"
              :class="['objective-item', { active: form.objective === item.value, disabled: item.value !== 'LINK_CLICK' }]"
              @click="item.value === 'LINK_CLICK' && (form.objective = item.value)"
            >
              <div class="icon-wrapper">
                <el-icon :size="20"><component :is="item.icon" /></el-icon>
              </div>
              <span>{{ item.label }}</span>
            </div>
          </div>
          <div class="switch-row">
            <span>优先触达潜客人群</span>
            <el-switch v-model="form.priorityCustomer" size="small" />
          </div>
        </div>

        <!-- 推广内容 -->
        <div class="card">
          <div class="card-title">推广内容</div>
          <div class="hint">您可选择1-5个无营销属性视频进行投放，已选 {{ selectedVideos.length }} 个</div>
          
          <el-form-item label="付款抖音号" prop="accountId">
            <el-select v-model="form.accountId" placeholder="选择付款抖音号" style="width: 100%;" @change="onAccountChange">
              <el-option 
                v-for="account in accounts" 
                :key="account.id" 
                :label="account.nickname" 
                :value="account.id"
              >
                <div class="account-option">
                  <el-avatar :size="20" :src="convertToHttps(account.avatar)">{{ account.nickname?.charAt(0) }}</el-avatar>
                  <span>{{ account.nickname }}</span>
                  <el-tag v-if="account.status !== 1" type="danger" size="small">授权失效</el-tag>
                </div>
              </el-option>
            </el-select>
          </el-form-item>

          <!-- 视频列表（选择账号后显示） -->
          <div v-if="form.accountId" class="video-list-section" v-loading="videoLoading">
            <div class="video-list-header">
              <span>选择要投放的视频（最多5个）</span>
              <el-input v-model="videoSearch" placeholder="搜索视频" prefix-icon="Search" style="width: 200px;" clearable />
            </div>
            <div class="video-grid">
              <div 
                v-for="video in filteredVideos" 
                :key="video.id" 
                :class="['video-grid-item', { selected: isVideoSelected(video) }]"
                @click="toggleVideoSelection(video)"
              >
                <div class="video-thumb-wrapper">
                  <img :src="convertToHttps(video.coverUrl)" class="video-thumb" />
                  <div class="video-duration">{{ formatDuration(video.duration) }}</div>
                  <div v-if="isVideoSelected(video)" class="video-check">
                    <el-icon><Check /></el-icon>
                  </div>
                </div>
                <div class="video-grid-info">
                  <div class="video-grid-title">{{ video.title || '无标题' }}</div>
                  <div class="video-grid-meta">
                    <span>{{ formatNumber(video.playCount) }}播放</span>
                    <span>{{ formatNumber(video.likeCount) }}赞</span>
                  </div>
                </div>
              </div>
              <el-empty v-if="filteredVideos.length === 0 && !videoLoading" description="暂无视频" :image-size="60" />
            </div>
          </div>

          <!-- 已选视频列表 -->
          <div v-if="selectedVideos.length > 0" class="selected-videos">
            <div class="selected-label">已选择 {{ selectedVideos.length }} 个视频：</div>
            <div v-for="(video, index) in selectedVideos" :key="video.id" class="video-card">
              <img :src="convertToHttps(video.coverUrl)" class="video-cover" />
              <div class="video-info">
                <div class="video-title">{{ video.title || '无标题' }}</div>
                <div class="video-meta">
                  <span>时长 {{ formatDuration(video.duration) }}</span>
                  <span>播放 {{ formatNumber(video.playCount) }}</span>
                  <span>点赞 {{ formatNumber(video.likeCount) }}</span>
                </div>
              </div>
              <el-button type="danger" link size="small" @click="removeVideo(index)">
                <el-icon><Close /></el-icon>
              </el-button>
            </div>
          </div>
        </div>

        <!-- 自定义推广 -->
        <div class="card">
          <div class="card-title">自定义推广</div>
          
          <!-- 高质量互动推荐定向提示 -->
          <div v-if="form.objective === 'QUALITY_INTERACT'" class="recommend-tips">
            <span>帮您获得更优质的点赞评论</span>
            <div class="recommend-tags">
              <span class="tag"><el-icon><Check /></el-icon> 推荐覆盖不同人群</span>
              <span class="tag"><el-icon><Check /></el-icon> 加强定向设置</span>
              <span class="tag"><el-icon><Check /></el-icon> 有效评论更多</span>
            </div>
          </div>

          <!-- 投放时长 -->
          <el-form-item label="投放时长">
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
            <div v-if="customDuration" class="custom-duration-row">
              <el-input-number 
                v-model="form.durationDays" 
                :min="1" 
                :max="7" 
                style="width: 120px; margin-top: 10px;"
                @change="onDurationDaysChange"
              />
              <span class="duration-unit">天</span>
            </div>
          </el-form-item>

          <!-- 自定义投放时段（仅2天以上可用） -->
          <div class="time-range-section">
            <div class="time-range-row">
              <span>自定义投放时段</span>
              <el-tag type="danger" size="small">上新</el-tag>
              <el-switch 
                v-model="form.customTimeEnabled" 
                :disabled="!canEnableCustomTime"
                style="margin-left: auto;" 
              />
            </div>
            <div v-if="!canEnableCustomTime" class="time-range-hint">
              自定义投放时长至少2天才能使用自定义时段
            </div>
            
            <!-- 自定义时段详细设置 -->
            <div v-if="form.customTimeEnabled && canEnableCustomTime" class="time-slot-config">
              <div class="time-slot-tabs">
                <span 
                  :class="['tab', { active: form.timeSlotType === 'fixed' }]"
                  @click="form.timeSlotType = 'fixed'"
                >固定投放时段</span>
                <span 
                  :class="['tab', { active: form.timeSlotType === 'schedule' }]"
                  @click="form.timeSlotType = 'schedule'"
                >预约投放</span>
              </div>
              
              <!-- 固定投放时段 -->
              <div v-if="form.timeSlotType === 'fixed'" class="fixed-time-section">
                <div class="time-slot-row">
                  <span class="row-label">投放时段 <el-icon class="help-icon"><QuestionFilled /></el-icon></span>
                  <el-popover
                    :visible="showTimePopover"
                    placement="bottom"
                    :width="280"
                    trigger="click"
                  >
                    <template #reference>
                      <div class="time-range-display" @click="showTimePopover = !showTimePopover">
                        <span>{{ form.fixedTimeStart }}:00 ~ {{ form.fixedTimeEnd }}:00</span>
                        <el-icon><Clock /></el-icon>
                      </div>
                    </template>
                    <div class="time-picker-popover">
                      <div class="time-picker-header">
                        <span>开始时间</span>
                        <span>结束时间</span>
                      </div>
                      <div class="time-picker-body">
                        <div class="time-picker-column">
                          <div class="time-scroll">
                            <div 
                              v-for="h in 24" 
                              :key="'start-' + (h - 1)"
                              :class="['time-option', { active: form.fixedTimeStart === h - 1 }]"
                              @click="form.fixedTimeStart = h - 1"
                            >{{ String(h - 1).padStart(2, '0') }}</div>
                          </div>
                          <div class="time-scroll minute-scroll">
                            <div class="time-option active">00</div>
                          </div>
                        </div>
                        <div class="time-picker-column">
                          <div class="time-scroll">
                            <div 
                              v-for="h in 24" 
                              :key="'end-' + h"
                              :class="['time-option', { active: form.fixedTimeEnd === h, disabled: h <= form.fixedTimeStart }]"
                              @click="h > form.fixedTimeStart && (form.fixedTimeEnd = h)"
                            >{{ String(h).padStart(2, '0') }}</div>
                          </div>
                          <div class="time-scroll minute-scroll">
                            <div class="time-option active">00</div>
                          </div>
                        </div>
                      </div>
                      <div class="time-picker-footer">
                        <el-button size="small" @click="showTimePopover = false">取消</el-button>
                        <el-button type="primary" size="small" @click="showTimePopover = false">确定</el-button>
                      </div>
                    </div>
                  </el-popover>
                </div>
                <div class="fixed-time-hint">
                  预计{{ fixedTimePreview.startDate }}-{{ fixedTimePreview.endDate }}，每天{{ form.fixedTimeStart }}点-{{ form.fixedTimeEnd }}点投放，累计投放时长{{ fixedTimePreview.totalHours }}小时
                </div>
              </div>
              
              <!-- 预约投放 -->
              <div v-if="form.timeSlotType === 'schedule'" class="schedule-section">
                <!-- 开始投放时间 -->
                <div class="schedule-row">
                  <el-radio v-model="form.startTimeType" label="datetime" class="schedule-radio">
                    <span class="radio-label">开始投放时间</span>
                  </el-radio>
                  <el-date-picker
                    v-model="form.scheduledStartTime"
                    type="datetime"
                    placeholder="选择时间"
                    format="YYYY-MM-DD HH:mm"
                    value-format="YYYY-MM-DD HH:mm"
                    :disabled="form.startTimeType !== 'datetime'"
                    style="width: 180px;"
                    :default-value="defaultScheduleTime"
                  />
                </div>
                
                <!-- 当视频播放量高于多少时开始投放 -->
                <div class="schedule-row">
                  <el-radio v-model="form.startTimeType" label="playcount" class="schedule-radio">
                    <span class="radio-label">当视频播放量高于多少时开始投放</span>
                  </el-radio>
                  <el-select 
                    v-model="form.playCountThreshold" 
                    placeholder="选择"
                    :disabled="form.startTimeType !== 'playcount'"
                    style="width: 100px;"
                  >
                    <el-option :value="200" label="200" />
                    <el-option :value="400" label="400" />
                    <el-option :value="600" label="600" />
                    <el-option :value="800" label="800" />
                    <el-option :value="1000" label="1000" />
                    <el-option :value="2000" label="2000" />
                  </el-select>
                </div>
              </div>
            </div>
          </div>

          <!-- 投放金额 -->
          <el-form-item label="投放金额" prop="budget">
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
            />
          </el-form-item>

          <!-- 投放笔数 -->
          <el-form-item label="投放笔数" prop="count">
            <div class="count-input-row">
              <el-input 
                v-model.number="form.count" 
                type="number"
                :min="1" 
                :max="100" 
                style="width: 100px;"
                @input="validateCount"
              />
              <span class="hint-text">将创建 {{ form.count }} 笔相同的投放订单</span>
            </div>
          </el-form-item>

          <!-- 投放策略（视频播放量目标时不显示） -->
          <el-form-item v-if="currentStrategies.length > 0" label="投放策略">
            <div class="hint-link">
              <span>该选哪个策略</span>
              <el-icon><ArrowRight /></el-icon>
            </div>
            <div class="option-group">
              <div 
                v-for="item in currentStrategies" 
                :key="item.value"
                :class="['option-btn', { active: form.strategy === item.value }]"
                @click="form.strategy = item.value"
              >
                {{ item.label }}
              </div>
            </div>
          </el-form-item>

          <!-- 投放给谁 -->
          <el-form-item label="投放给谁">
            <div class="option-group">
              <div 
                v-for="item in AUDIENCE_TYPES" 
                :key="item.value"
                :class="['option-btn', { active: form.audienceType === item.value }]"
                @click="form.audienceType = item.value"
              >
                {{ item.label }}
              </div>
            </div>
          </el-form-item>

          <!-- 定向设置（自定义人群时显示） -->
          <div v-if="form.audienceType === 'CUSTOM'" class="targeting-section">
            <div class="section-subtitle">定向设置</div>
            <div class="targeting-tabs">
              <span :class="{ active: targetingTab === 'new' }" @click="targetingTab = 'new'">新建定向</span>
              <span :class="{ active: targetingTab === 'saved' }" @click="targetingTab = 'saved'">已有定向</span>
              <el-button type="primary" link size="small">保存定向</el-button>
            </div>

            <!-- 性别 -->
            <div class="targeting-row">
              <span class="label">性别</span>
              <div class="option-group small">
                <div 
                  v-for="item in GENDER_OPTIONS" 
                  :key="item.value"
                  :class="['option-btn small', { active: form.targetConfig.gender === item.value }]"
                  @click="form.targetConfig.gender = item.value"
                >
                  {{ item.label }}
                </div>
              </div>
            </div>

            <!-- 年龄 -->
            <div class="targeting-row">
              <span class="label">年龄(多选)</span>
              <div class="option-group small">
                <div 
                  v-for="item in AGE_OPTIONS" 
                  :key="item.value"
                  :class="['option-btn small', { active: form.targetConfig.age.includes(item.value) }]"
                  @click="toggleArrayItem(form.targetConfig.age, item.value)"
                >
                  {{ item.label }}
                </div>
              </div>
            </div>

            <!-- 八大人群 -->
            <div class="targeting-row">
              <span class="label">八大人群(多选)</span>
              <div class="option-group small wrap">
                <div 
                  v-for="item in CROWD_OPTIONS" 
                  :key="item.value"
                  :class="['option-btn small', { active: form.targetConfig.crowd.includes(item.value) }]"
                  @click="toggleArrayItem(form.targetConfig.crowd, item.value)"
                >
                  {{ item.label }}
                </div>
              </div>
            </div>

            <!-- 地域 -->
            <div class="targeting-row">
              <span class="label">地域</span>
              <div class="option-group small">
                <div 
                  v-for="item in REGION_TYPES" 
                  :key="item.value"
                  :class="['option-btn small', { active: form.targetConfig.regionType === item.value }]"
                  @click="form.targetConfig.regionType = item.value"
                >
                  {{ item.label }}
                </div>
              </div>
            </div>

            <!-- 兴趣定向 -->
            <div class="targeting-row">
              <span class="label">兴趣定向</span>
              <el-select v-model="form.targetConfig.interest" multiple placeholder="不限" style="width: 200px;">
                <el-option v-for="item in INTEREST_OPTIONS" :key="item.value" :label="item.label" :value="item.value" />
              </el-select>
            </div>

            <!-- 达人相似粉丝 -->
            <div class="targeting-row">
              <span class="label">达人相似粉丝</span>
              <div class="option-group small">
                <div 
                  v-for="item in SIMILAR_FANS_OPTIONS" 
                  :key="item.value"
                  :class="['option-btn small', { active: form.targetConfig.similarFans === item.value }]"
                  @click="form.targetConfig.similarFans = item.value"
                >
                  {{ item.label }}
                </div>
              </div>
            </div>

            <!-- 行业潜在购买人群 -->
            <div class="targeting-row">
              <span class="label">行业潜在购买人群(多选)</span>
              <div class="option-group small wrap">
                <div 
                  v-for="item in INDUSTRY_OPTIONS" 
                  :key="item.value"
                  :class="['option-btn small', { active: form.targetConfig.industry.includes(item.value) }]"
                  @click="toggleArrayItem(form.targetConfig.industry, item.value)"
                >
                  {{ item.label }}
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 投放密码 -->
        <div class="card">
          <el-form-item label="DOU+投放密码" prop="investPassword">
            <div class="password-input-row">
              <el-input 
                v-model="form.investPassword" 
                type="password" 
                placeholder="请输入投放密码"
                style="width: 200px;"
                show-password
              />
              <el-button type="warning" link @click="showSetPasswordDialog = true">设置投放密码</el-button>
            </div>
          </el-form-item>
        </div>

        <!-- 费用结算 -->
        <div class="card cost-card">
          <div class="cost-row">
            <span>投放金额</span>
            <span>¥{{ form.budget }}</span>
          </div>
          <div class="cost-row">
            <span>投放笔数</span>
            <span>× {{ form.count }}</span>
          </div>
          <div class="cost-row">
            <span>账户余额抵扣</span>
            <span class="discount">-¥{{ Math.min(accountBalance, totalAmount) }}</span>
          </div>
          <div class="cost-row total">
            <span>合计</span>
            <span class="amount">¥{{ Math.max(0, totalAmount - accountBalance) }}</span>
          </div>
        </div>

        <!-- 提交按钮 -->
        <div class="submit-section">
          <div class="agreement">
            已阅读并同意内<el-link type="primary">容加热服务协议</el-link>及<el-link type="primary">营销服务协议</el-link>
          </div>
          <div class="submit-row">
            <div class="total-info">
              <span class="label">¥{{ Math.max(0, totalAmount - accountBalance) }}</span>
              <span class="sub">已省¥{{ Math.min(accountBalance, totalAmount) }}</span>
            </div>
            <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
              支付
            </el-button>
          </div>
        </div>
      </el-form>
    </div>

    <!-- 设置投放密码对话框 -->
    <el-dialog v-model="showSetPasswordDialog" title="设置投放密码" width="400px">
      <el-form :model="passwordForm" label-width="100px">
        <el-form-item label="新投放密码">
          <el-input 
            v-model="passwordForm.investPassword" 
            type="password" 
            placeholder="设置投放密码"
            show-password
          />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input 
            v-model="passwordForm.confirmPassword" 
            type="password" 
            placeholder="再次输入密码"
            show-password
          />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSetPasswordDialog = false">取消</el-button>
        <el-button type="primary" :loading="settingPassword" @click="handleSetPassword">确定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { convertToHttps } from '@/utils/url'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { 
  VideoCamera, Close, QuestionFilled, ArrowRight, Check,
  ChatDotRound, Connection, House, Link, VideoPlay, Mic, Clock
} from '@element-plus/icons-vue'
import { getAccountList } from '@/api/account'
import { getVideoList } from '@/api/video'
import { createTask } from '@/api/douplus'
import { setInvestPassword } from '@/api/auth'
import type { DouyinAccount, VideoInfo, CreateTaskRequest } from '@/api/types'
import {
  WANT_TYPES,
  OBJECTIVES,
  DURATION_OPTIONS,
  BUDGET_OPTIONS,
  AUDIENCE_TYPES,
  GENDER_OPTIONS,
  AGE_OPTIONS,
  CROWD_OPTIONS,
  REGION_TYPES,
  INTEREST_OPTIONS,
  SIMILAR_FANS_OPTIONS,
  INDUSTRY_OPTIONS,
  estimateExposure,
  getStrategiesByObjective
} from '@/constants/targeting'

const formRef = ref<FormInstance>()
const submitting = ref(false)
const accounts = ref<DouyinAccount[]>([])
const videos = ref<VideoInfo[]>([])
const selectedVideos = ref<VideoInfo[]>([])
const videoLoading = ref(false)
const videoSearch = ref('')
const customDuration = ref(false)
const customBudget = ref(false)
const targetingTab = ref('new')
const accountBalance = ref(0)
const showSetPasswordDialog = ref(false)
const settingPassword = ref(false)
const showTimePopover = ref(false)
const passwordForm = reactive({
  investPassword: '',
  confirmPassword: ''
})

const form = reactive({
  accountId: null as number | null,
  targetAccountId: null as number | null,
  wantType: 'CONTENT_HEAT',
  objective: 'LINK_CLICK',
  priorityCustomer: false,
  duration: 6,
  durationDays: 2,
  customTimeEnabled: false,
  timeSlotType: 'fixed',  // 'fixed' | 'schedule'
  fixedTimeStart: 12,  // 固定投放开始小时
  fixedTimeEnd: 24,    // 固定投放结束小时
  startTimeType: 'datetime',      // 'datetime' | 'playcount'
  scheduledStartTime: '',
  playCountThreshold: 200,
  budget: 100,
  count: 1,
  strategy: 'GUARANTEE_PLAY',
  audienceType: 'SMART',
  targetConfig: {
    gender: 'ALL',
    age: ['ALL'] as string[],
    crowd: ['ALL'] as string[],
    regionType: 'ALL',
    regions: [] as string[],
    interest: [] as string[],
    similarFans: 'ALL',
    industry: ['ALL'] as string[]
  },
  investPassword: ''
})

const rules: FormRules = {
  accountId: [{ required: true, message: '请选择付款抖音号', trigger: 'change' }],
  budget: [{ required: true, message: '请选择投放金额', trigger: 'change' }],
  investPassword: [{ required: true, message: '请输入投放密码', trigger: 'blur' }]
}

// 计算属性
const filteredVideos = computed(() => {
  if (!videoSearch.value) return videos.value
  return videos.value.filter(v => v.title.toLowerCase().includes(videoSearch.value.toLowerCase()))
})

const estimatedExposure = computed(() => {
  return estimateExposure(form.budget, form.duration, form.objective)
})

const currentStrategies = computed(() => {
  return getStrategiesByObjective(form.objective)
})

const totalAmount = computed(() => {
  return form.budget * form.count
})

// 是否可以启用自定义投放时段
const canEnableCustomTime = computed(() => {
  return customDuration.value && form.durationDays >= 2
})

// 预约投放默认时间
const defaultScheduleTime = computed(() => {
  const now = new Date()
  now.setMinutes(Math.ceil(now.getMinutes() / 30) * 30, 0, 0)
  return now
})

// 固定时段投放预览信息
const fixedTimePreview = computed(() => {
  const now = new Date()
  const startDate = `${now.getMonth() + 1}月${now.getDate()}日`
  const endDate = new Date(now.getTime() + (form.durationDays - 1) * 24 * 60 * 60 * 1000)
  const endDateStr = `${endDate.getMonth() + 1}月${endDate.getDate()}日`
  
  // 计算每天投放小时数
  const hoursPerDay = form.fixedTimeEnd - form.fixedTimeStart
  const totalHours = hoursPerDay * form.durationDays
  
  return {
    startDate,
    endDate: endDateStr,
    totalHours
  }
})

// 方法
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

const onAccountChange = async (accountId: number) => {
  if (!accountId) return
  const account = accounts.value.find(a => a.id === accountId)
  if (account) {
    accountBalance.value = account.balance || 0
  }
  // 清空已选视频
  selectedVideos.value = []
  videos.value = []
  
  videoLoading.value = true
  try {
    const res = await getVideoList(accountId, 1, 100)
    if (res.code === 200) {
      const list = res.data?.list || res.data || []
      // 按创建时间倒序排列
      videos.value = list.sort((a: VideoInfo, b: VideoInfo) => {
        const timeA = new Date(a.createTime || 0).getTime()
        const timeB = new Date(b.createTime || 0).getTime()
        return timeB - timeA
      })
    }
  } catch (error) {
    console.error('加载视频失败', error)
  } finally {
    videoLoading.value = false
  }
}

const selectDuration = (value: number) => {
  if (value === 0) {
    customDuration.value = true
    form.durationDays = 2
    form.duration = 48  // 2天 = 48小时
  } else {
    customDuration.value = false
    form.duration = value
    form.customTimeEnabled = false  // 切换为预设时长时关闭自定义时段
  }
}

const onDurationDaysChange = (days: number) => {
  form.duration = days * 24  // 天数转换为小时
  if (days < 2) {
    form.customTimeEnabled = false  // 不足2天关闭自定义时段
  }
}

const selectBudget = (value: number) => {
  if (value === 0) {
    customBudget.value = true
    form.budget = 100
  } else {
    customBudget.value = false
    form.budget = value
  }
}

const toggleArrayItem = (arr: string[], value: string) => {
  if (value === 'ALL') {
    arr.length = 0
    arr.push('ALL')
  } else {
    const allIndex = arr.indexOf('ALL')
    if (allIndex > -1) arr.splice(allIndex, 1)
    const index = arr.indexOf(value)
    if (index > -1) {
      arr.splice(index, 1)
      if (arr.length === 0) arr.push('ALL')
    } else {
      arr.push(value)
    }
  }
}

const isVideoSelected = (video: VideoInfo) => {
  return selectedVideos.value.some(v => v.id === video.id)
}

const toggleVideoSelection = (video: VideoInfo) => {
  const index = selectedVideos.value.findIndex(v => v.id === video.id)
  if (index > -1) {
    selectedVideos.value.splice(index, 1)
  } else if (selectedVideos.value.length < 5) {
    selectedVideos.value.push(video)
  } else {
    ElMessage.warning('最多选择5个视频')
  }
}

const removeVideo = (index: number) => {
  selectedVideos.value.splice(index, 1)
}

const validateCount = () => {
  if (form.count < 1) form.count = 1
  if (form.count > 100) form.count = 100
  form.count = Math.floor(form.count)
}

const handleSetPassword = async () => {
  if (!passwordForm.investPassword) {
    ElMessage.warning('请输入投放密码')
    return
  }
  if (passwordForm.investPassword !== passwordForm.confirmPassword) {
    ElMessage.warning('两次输入的密码不一致')
    return
  }
  if (passwordForm.investPassword.length < 6) {
    ElMessage.warning('密码长度不能小于6位')
    return
  }
  
  settingPassword.value = true
  try {
    const res = await setInvestPassword(passwordForm.investPassword)
    if (res.code === 200) {
      ElMessage.success('投放密码设置成功')
      showSetPasswordDialog.value = false
      passwordForm.investPassword = ''
      passwordForm.confirmPassword = ''
    }
  } catch (error) {
    console.error('设置密码失败', error)
  } finally {
    settingPassword.value = false
  }
}

const formatDuration = (seconds: number) => {
  if (!seconds) return '0:00'
  const mins = Math.floor(seconds / 60)
  const secs = seconds % 60
  return `${mins}:${secs.toString().padStart(2, '0')}`
}

const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 10000) return (num / 10000).toFixed(1) + '万'
  return num.toString()
}

const handleSubmit = async () => {
  if (!formRef.value) return
  
  await formRef.value.validate(async (valid) => {
    if (!valid) return

    if (selectedVideos.value.length === 0) {
      ElMessage.warning('请选择至少一个视频')
      return
    }

    const totalCost = totalAmount.value
    await ElMessageBox.confirm(
      `确认投放 ${form.count} 笔订单，共计 ¥${totalCost}？`,
      '投放确认',
      { type: 'warning' }
    )

    submitting.value = true
    try {
      // 为每个选中的视频创建任务
      const requests: CreateTaskRequest[] = selectedVideos.value.map(video => ({
        accountId: form.accountId!,
        targetAccountId: form.targetAccountId || form.accountId!,
        itemId: video.itemId || video.id,
        taskType: 1,
        targetType: form.audienceType === 'SMART' ? 1 : 2,
        wantType: form.wantType,
        objective: form.objective,
        strategy: form.strategy,
        duration: form.duration,
        budget: form.budget,
        count: form.count,
        targetConfig: JSON.stringify(form.targetConfig),
        investPassword: form.investPassword
      }))

      const res = await createTask(requests)
      if (res.code === 200) {
        const taskCount = res.data?.length || (form.count * selectedVideos.value.length)
        ElMessage.success(`投放任务创建成功，共 ${taskCount} 个任务`)
        resetForm()
      }
    } catch (error) {
      console.error('投放失败', error)
    } finally {
      submitting.value = false
    }
  })
}

const resetForm = () => {
  formRef.value?.resetFields()
  selectedVideos.value = []
  customDuration.value = false
  customBudget.value = false
  Object.assign(form, {
    wantType: 'CONTENT_HEAT',
    objective: 'LINK_CLICK',
    priorityCustomer: false,
    duration: 6,
    durationDays: 2,
    customTimeEnabled: false,
    timeSlotType: 'fixed',
    fixedTimeStart: 12,
    fixedTimeEnd: 24,
    startTimeType: 'datetime',
    scheduledStartTime: '',
    playCountThreshold: 200,
    budget: 100,
    count: 1,
    strategy: 'GUARANTEE_PLAY',
    audienceType: 'SMART',
    investPassword: ''
  })
}

onMounted(() => {
  loadAccounts()
})
</script>

<style scoped>
.douplus-create {
  max-width: 900px;
  margin: 0 auto;
  padding: 12px;
  font-size: 13px;
}

.main-panel {
  width: 100%;
}

.card {
  background: #fff;
  border-radius: 6px;
  padding: 14px;
  margin-bottom: 12px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.card-title {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  display: flex;
  align-items: center;
  gap: 6px;
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
  color: #1f2937;
  font-size: 12px;
}

.option-btn.small {
  padding: 4px 10px;
  font-size: 12px;
}

.option-btn:hover {
  border-color: #1890ff;
}

.option-btn.active {
  border-color: #1890ff;
  color: #1890ff;
  background: #e6f4ff;
}

.option-btn.disabled {
  color: #c0c4cc;
  background: #f5f7fa;
  border-color: #e4e7ed;
  cursor: not-allowed;
}

.option-btn.disabled:hover {
  border-color: #e4e7ed;
}

.objective-group {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
  margin-bottom: 12px;
}

.objective-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;
  padding: 10px 14px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.2s;
  min-width: 80px;
}

.objective-item:hover {
  border-color: #1890ff;
}

.objective-item.active {
  border-color: #ff6b35;
  background: #fff5f0;
}

.objective-item.active .icon-wrapper {
  color: #ff6b35;
}

.objective-item.disabled {
  color: #c0c4cc;
  background: #f5f7fa;
  border-color: #e4e7ed;
  cursor: not-allowed;
}

.objective-item.disabled:hover {
  border-color: #e4e7ed;
}

.objective-item.disabled .icon-wrapper {
  color: #c0c4cc;
}

.icon-wrapper {
  width: 36px;
  height: 36px;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f3f4f6;
  border-radius: 50%;
  color: #6b7280;
}

.switch-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 0;
  color: #6b7280;
  font-size: 13px;
}

.hint {
  color: #9ca3af;
  font-size: 12px;
  margin-bottom: 10px;
}

.hint-text {
  color: #9ca3af;
  font-size: 12px;
  margin-left: 10px;
}

.hint-link {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #1890ff;
  font-size: 12px;
  margin-bottom: 8px;
  cursor: pointer;
}

.account-option {
  display: flex;
  align-items: center;
  gap: 8px;
}

/* 视频列表区域 */
.video-list-section {
  margin-top: 12px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 12px;
}

.video-list-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
  font-size: 13px;
  color: #6b7280;
}

.video-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
  gap: 10px;
  max-height: 280px;
  overflow-y: auto;
}

.video-grid-item {
  cursor: pointer;
  border: 2px solid transparent;
  border-radius: 6px;
  transition: all 0.2s;
  overflow: hidden;
}

.video-grid-item:hover {
  border-color: #1890ff;
}

.video-grid-item.selected {
  border-color: #1890ff;
  background: #e6f4ff;
}

.video-thumb-wrapper {
  position: relative;
  width: 100%;
  padding-top: 133%;
  background: #f0f0f0;
}

.video-thumb-wrapper .video-thumb {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.video-duration {
  position: absolute;
  bottom: 4px;
  right: 4px;
  background: rgba(0,0,0,0.6);
  color: #fff;
  font-size: 11px;
  padding: 2px 4px;
  border-radius: 2px;
}

.video-check {
  position: absolute;
  top: 4px;
  right: 4px;
  width: 20px;
  height: 20px;
  background: #1890ff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #fff;
}

.video-grid-info {
  padding: 6px;
}

.video-grid-title {
  font-size: 12px;
  color: #1f2937;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-grid-meta {
  display: flex;
  gap: 8px;
  font-size: 11px;
  color: #9ca3af;
  margin-top: 2px;
}

/* 已选视频 */
.selected-videos {
  margin-top: 12px;
}

.selected-label {
  font-size: 12px;
  color: #6b7280;
  margin-bottom: 8px;
}

.video-card {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  background: #f9fafb;
  margin-bottom: 6px;
}

.video-cover {
  width: 60px;
  height: 45px;
  object-fit: cover;
  border-radius: 3px;
}

.video-info {
  flex: 1;
  min-width: 0;
}

.video-title {
  font-size: 12px;
  font-weight: 500;
  color: #1f2937;
  margin-bottom: 3px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.video-meta {
  display: flex;
  gap: 10px;
  font-size: 11px;
  color: #9ca3af;
}

/* 预计播放量 */
.exposure-estimate {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 16px;
  background: #fff;
  border-radius: 6px;
  margin-bottom: 14px;
}

.exposure-estimate .label {
  color: #6b7280;
  font-size: 13px;
  margin-bottom: 8px;
}

.exposure-estimate .value {
  color: #ff2c55;
  font-size: 28px;
  font-weight: 600;
  margin-bottom: 6px;
}

.exposure-estimate .guarantee {
  color: #00b578;
  font-size: 12px;
}

.time-range-section {
  margin-bottom: 14px;
}

.time-range-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
}

.time-range-hint {
  color: #9ca3af;
  font-size: 12px;
  padding: 6px 0;
}

.time-slot-config {
  padding: 12px;
  background: #f9fafb;
  border-radius: 6px;
  margin-top: 10px;
}

.time-slot-tabs {
  display: flex;
  gap: 12px;
  margin-bottom: 14px;
}

.time-slot-tabs .tab {
  padding: 6px 16px;
  border: 1px solid #d9d9d9;
  border-radius: 4px;
  cursor: pointer;
  font-size: 13px;
  color: #6b7280;
}

.time-slot-tabs .tab.active {
  border-color: #ff2c55;
  color: #ff2c55;
  background: #fff5f5;
}

.time-slot-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 0;
}

/* 推荐定向提示 */
.recommend-tips {
  background: #fff5f0;
  border-radius: 6px;
  padding: 12px;
  margin-bottom: 14px;
  font-size: 13px;
  color: #ff6b35;
}

.recommend-tags {
  display: flex;
  gap: 16px;
  margin-top: 8px;
}

.recommend-tags .tag {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #00b578;
  font-size: 12px;
}

/* 定向设置 */
.targeting-section {
  margin-top: 14px;
  padding-top: 14px;
  border-top: 1px solid #f0f0f0;
}

.section-subtitle {
  font-weight: 600;
  color: #1f2937;
  margin-bottom: 12px;
  font-size: 13px;
}

.targeting-tabs {
  display: flex;
  gap: 16px;
  margin-bottom: 14px;
  padding-bottom: 8px;
  border-bottom: 1px solid #f0f0f0;
}

.targeting-tabs span {
  cursor: pointer;
  color: #6b7280;
  padding: 4px 0;
  font-size: 13px;
}

.targeting-tabs span.active {
  color: #1890ff;
  border-bottom: 2px solid #1890ff;
}

.targeting-row {
  display: flex;
  align-items: flex-start;
  margin-bottom: 12px;
}

.targeting-row .label {
  width: 120px;
  flex-shrink: 0;
  color: #6b7280;
  padding-top: 4px;
  font-size: 12px;
}

/* 输入行 */
.count-input-row,
.password-input-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

/* 费用结算 */
.cost-card {
  background: #fafafa;
}

.cost-row {
  display: flex;
  justify-content: space-between;
  padding: 8px 0;
  color: #6b7280;
  font-size: 13px;
}

.cost-row.total {
  border-top: 1px solid #e5e7eb;
  margin-top: 8px;
  padding-top: 12px;
  font-weight: 600;
  color: #1f2937;
}

.cost-row .discount {
  color: #ff6b35;
}

.cost-row .amount {
  color: #ff6b35;
  font-size: 18px;
}

/* 提交区域 */
.submit-section {
  padding: 14px;
  background: #fff;
  border-radius: 6px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.08);
}

.agreement {
  color: #9ca3af;
  font-size: 12px;
  margin-bottom: 12px;
}

.submit-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.total-info .label {
  font-size: 20px;
  font-weight: 600;
  color: #ff6b35;
}

.total-info .sub {
  color: #ff6b35;
  font-size: 12px;
  margin-left: 8px;
}

/* 自定义时长输入 */
.custom-duration-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
}

.duration-unit {
  color: #666;
  font-size: 13px;
}

/* 固定投放时段 */
.fixed-time-section {
  padding: 8px 0;
}

.fixed-time-section .row-label {
  color: #6b7280;
  font-size: 13px;
  display: flex;
  align-items: center;
  gap: 4px;
}

.fixed-time-section .help-icon {
  color: #9ca3af;
  cursor: pointer;
}

.fixed-time-hint {
  color: #ff6b35;
  font-size: 12px;
  margin-top: 10px;
}

/* 预约投放 */
.schedule-section {
  padding: 8px 0;
}

.schedule-row {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 0;
}

.schedule-radio {
  flex-shrink: 0;
}

.radio-label {
  color: #333;
}

/* 时间选择器样式 */
.time-range-display {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 8px 12px;
  border: 1px solid #dcdfe6;
  border-radius: 4px;
  cursor: pointer;
  min-width: 160px;
  background: #fff;
  transition: border-color 0.2s;
}

.time-range-display:hover {
  border-color: #1890ff;
}

.time-range-display span {
  color: #333;
  font-size: 13px;
}

.time-range-display .el-icon {
  color: #9ca3af;
}

.time-picker-popover {
  padding: 0;
}

.time-picker-header {
  display: flex;
  justify-content: space-around;
  padding: 10px;
  border-bottom: 1px solid #f0f0f0;
  font-size: 13px;
  color: #6b7280;
}

.time-picker-body {
  display: flex;
}

.time-picker-column {
  flex: 1;
  display: flex;
  border-right: 1px solid #f0f0f0;
}

.time-picker-column:last-child {
  border-right: none;
}

.time-scroll {
  flex: 1;
  max-height: 200px;
  overflow-y: auto;
  padding: 4px 0;
}

.time-scroll::-webkit-scrollbar {
  width: 4px;
}

.time-scroll::-webkit-scrollbar-thumb {
  background: #ddd;
  border-radius: 2px;
}

.minute-scroll {
  background: #f9fafb;
}

.time-option {
  padding: 6px 12px;
  text-align: center;
  cursor: pointer;
  font-size: 13px;
  color: #333;
  transition: all 0.2s;
}

.time-option:hover {
  background: #f0f0f0;
}

.time-option.active {
  color: #ff2c55;
  font-weight: 600;
}

.time-option.disabled {
  color: #c0c4cc;
  cursor: not-allowed;
}

.time-option.disabled:hover {
  background: transparent;
}

.time-picker-footer {
  display: flex;
  justify-content: flex-end;
  gap: 8px;
  padding: 10px;
  border-top: 1px solid #f0f0f0;
}
</style>
