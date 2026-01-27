<template>
  <el-table 
    :data="tasks" 
    v-loading="loading"
    style="width: 100%"
    :max-height="600"
    :header-cell-style="{ background: '#fff', color: '#333', fontWeight: '500' }"
    @selection-change="handleSelectionChange"
  >
    <!-- 多选列 -->
    <el-table-column 
      v-if="selectable" 
      type="selection" 
      width="55"
      :selectable="isSelectableRow"
    />
    
    <el-table-column label="视频" min-width="280">
      <template #default="{ row }">
        <div class="video-cell">
          <el-image 
            :src="row.videoCoverUrl || row.videoCover" 
            class="video-cover"
            fit="cover"
          >
            <template #error>
              <div class="video-cover-placeholder">
                <el-icon><VideoCamera /></el-icon>
              </div>
            </template>
          </el-image>
          <div class="video-info">
            <span class="video-title">{{ row.videoTitle || row.itemId }}</span>
            <span v-if="showAccountColumn" class="account-name">{{ row.accountNickname || row.awemeNick }}</span>
            <span class="order-time">{{ formatDate(row.createTime) }} 下单</span>
          </div>
        </div>
      </template>
    </el-table-column>
    
    <!-- 投放状态 -->
    <el-table-column v-if="isColumnVisible('status')" label="投放状态" width="100">
      <template #default="{ row }">
        <el-tag :type="getStatusTagType(row.status)" size="small">{{ getStatusText(row.status) }}</el-tag>
      </template>
    </el-table-column>
    
    <!-- 投放金额：消耗/预算 -->
    <el-table-column v-if="isColumnVisible('amount')" width="140">
      <template #header>
        <div class="header-with-tooltip">
          <span>投放金额</span>
          <el-tooltip content="消耗/预算" placement="top">
            <el-icon class="info-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      <template #default="{ row }">
        <div class="amount-cell">
          <span class="amount-text">{{ row.actualCost || 0 }}/{{ row.budget }}</span>
          <el-progress 
            :percentage="calcBudgetPercent(row)" 
            :stroke-width="4"
            :show-text="false"
            class="amount-progress"
          />
        </div>
      </template>
    </el-table-column>
    
    <!-- 百播放量：播放量/消耗*100 -->
    <el-table-column v-if="isColumnVisible('hundredPlayRate')" width="110">
      <template #header>
        <div class="header-with-tooltip">
          <span class="header-red">百播放量</span>
          <el-tooltip content="播放量 / 消耗 × 100" placement="top">
            <el-icon class="info-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ calcHundredPlayRate(row) }}</span>
      </template>
    </el-table-column>
    
    <!-- 转化成本 -->
    <el-table-column v-if="isColumnVisible('convertCost')" width="100">
      <template #header>
        <div class="header-with-tooltip">
          <span class="header-red">转化成本</span>
          <el-tooltip content="从API直接获取" placement="top">
            <el-icon class="info-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ formatCurrency(row.customConvertCost) }}</span>
      </template>
    </el-table-column>
    
    <!-- 百转发率：转发/播放量*100 -->
    <el-table-column v-if="isColumnVisible('hundredShareRate')" width="110">
      <template #header>
        <div class="header-with-tooltip">
          <span class="header-red">百转发率</span>
          <el-tooltip content="转发 / 播放量 × 100" placement="top">
            <el-icon class="info-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ calcHundredShareRate(row) }}</span>
      </template>
    </el-table-column>
    
    <!-- 点赞比：点赞/播放量×100 -->
    <el-table-column v-if="isColumnVisible('likeRate')" width="100">
      <template #header>
        <div class="header-with-tooltip">
          <span class="header-red">点赞比</span>
          <el-tooltip content="点赞 / 播放量 × 100" placement="top">
            <el-icon class="info-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ calcLikeRate(row) }}</span>
      </template>
    </el-table-column>
    
    <!-- 转发比：转发/播放量×100 -->
    <el-table-column v-if="isColumnVisible('shareRate')" width="100">
      <template #header>
        <div class="header-with-tooltip">
          <span class="header-red">转发比</span>
          <el-tooltip content="转发 / 播放量 × 100" placement="top">
            <el-icon class="info-icon"><QuestionFilled /></el-icon>
          </el-tooltip>
        </div>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ calcShareRate(row) }}</span>
      </template>
    </el-table-column>
    
    <!-- 播放量 -->
    <el-table-column v-if="isColumnVisible('playCount')" width="100">
      <template #header>
        <span class="header-red">播放量</span>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ formatNumber(row.playCount || row.actualExposure) }}</span>
      </template>
    </el-table-column>
    
    <!-- 点赞 -->
    <el-table-column v-if="isColumnVisible('likeCount')" width="90">
      <template #header>
        <span class="header-red">点赞</span>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ formatNumber(row.likeCount) }}</span>
      </template>
    </el-table-column>
    
    <!-- 转发 -->
    <el-table-column v-if="isColumnVisible('shareCount')" width="90">
      <template #header>
        <span class="header-red">转发</span>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ formatNumber(row.shareCount) }}</span>
      </template>
    </el-table-column>
    
    <!-- 转化 -->
    <el-table-column v-if="isColumnVisible('convertCount')" width="90">
      <template #header>
        <span class="header-red">转化</span>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ formatNumber(row.dpTargetConvertCnt) }}</span>
      </template>
    </el-table-column>
    
    <!-- 5S完播率 -->
    <el-table-column v-if="isColumnVisible('fiveSecRate')" width="100">
      <template #header>
        <span class="header-red">5S完播率</span>
      </template>
      <template #default="{ row }">
        <span class="metric-value">{{ formatPercentage(row.playDuration5sRank) }}</span>
      </template>
    </el-table-column>
    
    <!-- 结束时间 -->
    <el-table-column v-if="isColumnVisible('endTime')" label="结束时间" width="160">
      <template #default="{ row }">
        <span class="time-text">{{ formatDate(row.completedTime || row.orderEndTime || row.scheduledTime) }}</span>
      </template>
    </el-table-column>
    
    <el-table-column label="操作" width="160" fixed="right">
      <template #default="{ row }">
        <el-button 
          link
          type="primary"
          size="small" 
          @click="emit('viewDetails', row)"
        >
          详情
        </el-button>
        <!-- 投放中显示续费按钮 -->
        <el-button 
          v-if="showRenewButton && isDelivering(row.status)"
          link
          type="warning"
          size="small" 
          @click="emit('renew', row)"
        >
          续费
        </el-button>
        <!-- 已完成/已终止显示再次下单按钮 -->
        <el-button 
          v-if="showRenewButton && isFinishedOrTerminated(row.status)"
          link
          type="success"
          size="small" 
          @click="emit('reorder', row)"
        >
          再次下单
        </el-button>
        <!-- 待执行状态可取消 -->
        <el-button 
          v-if="showCancelButton && row.status === 'WAIT'"
          link
          type="danger"
          size="small" 
          @click="emit('cancel', row)"
        >
          取消
        </el-button>
        <!-- 失败状态可删除 -->
        <el-button 
          v-if="showCancelButton && row.status === 'FAIL'"
          link
          type="danger"
          size="small" 
          @click="emit('delete', row)"
        >
          删除
        </el-button>
      </template>
    </el-table-column>
  </el-table>
</template>

<script setup lang="ts">
import { VideoCamera, QuestionFilled } from '@element-plus/icons-vue'

// Props
interface OrderTask {
  id: number
  videoCover?: string
  videoCoverUrl?: string
  videoTitle?: string
  itemId?: string
  accountNickname?: string
  awemeNick?: string
  status?: string
  actualCost?: number
  budget?: number
  playCount?: number
  actualExposure?: number
  likeCount?: number
  shareCount?: number
  clickCount?: number
  followCount?: number
  // 新增字段
  playDuration5sRank?: number       // 5秒完播率
  dyHomeVisited?: number            // 主页访问次数
  dpTargetConvertCnt?: number       // 转化数
  customConvertCost?: number        // 转化成本
  // 直播相关
  showCnt?: number
  liveClickSourceCnt?: number
  liveGiftUv?: number
  liveGiftAmount?: number
  liveCommentCnt?: number
  douplusLiveFollowCount?: number
  liveGiftCnt?: number
  // 时间
  orderEndTime?: string
  completedTime?: string
  scheduledTime?: string
  createTime?: string
}

const props = withDefaults(defineProps<{
  tasks: OrderTask[]
  loading?: boolean
  showAccountColumn?: boolean
  showCancelButton?: boolean
  showRenewButton?: boolean
  selectable?: boolean  // 新增：是否显示多选框
  visibleColumns?: string[]  // 新增：可见列配置
}>(), {
  loading: false,
  showAccountColumn: true,
  showCancelButton: true,
  showRenewButton: true,
  selectable: false,
  visibleColumns: () => []  // 默认全部显示
})

// Emits
const emit = defineEmits<{
  (e: 'viewDetails', task: OrderTask): void
  (e: 'cancel', task: OrderTask): void
  (e: 'delete', task: OrderTask): void
  (e: 'renew', task: OrderTask): void
  (e: 'reorder', task: OrderTask): void
  (e: 'selectionChange', tasks: OrderTask[]): void  // 新增：选择变化事件
}>()

// 判断列是否可见
const isColumnVisible = (columnKey: string) => {
  // 如果未配置，默认全部显示
  if (!props.visibleColumns || props.visibleColumns.length === 0) {
    return true
  }
  return props.visibleColumns.includes(columnKey)
}

// 判断行是否可选（只有投放中的订单可以批量续费）
const isSelectableRow = (row: OrderTask) => {
  return isDelivering(row.status)
}

// 处理选择变化
const handleSelectionChange = (selection: OrderTask[]) => {
  emit('selectionChange', selection)
}

// 判断是否投放中（可续费）
const isDelivering = (status?: string) => {
  return status === 'DELIVERING' || status === 'RUNNING'
}

// 判断是否已完成或已终止（可再次下单）
const isFinishedOrTerminated = (status?: string) => {
  return ['DELIVERED', 'DELIVERIED', 'FINISHED', 'SUCCESS', 'TERMINATED', 'UNDELIVERIED'].includes(status || '')
}

// 统一的指标计算方法
// 计算投放金额百分比（消耗/预算）
const calcBudgetPercent = (row: OrderTask) => {
  if (!row.budget || row.budget === 0) return 0
  const cost = row.actualCost || 0
  return Math.min(Math.round((cost / row.budget) * 100), 100)
}

// 计算百播放量（播放量 / 消耗 × 100）
const calcHundredPlayRate = (row: OrderTask) => {
  const cost = row.actualCost || 0
  const playCount = row.playCount || row.actualExposure || 0
  if (cost === 0) return '-'
  return ((playCount / cost) * 100).toFixed(2)
}

// 计算百转发率（转发 / 播放量 × 100）
const calcHundredShareRate = (row: OrderTask) => {
  const playCount = row.playCount || row.actualExposure || 0
  const shareCount = row.shareCount || 0
  if (playCount === 0) return '-'
  return ((shareCount / playCount) * 100).toFixed(2)
}

// 计算点赞比（点赞 / 播放量 × 100）
const calcLikeRate = (row: OrderTask) => {
  const playCount = row.playCount || row.actualExposure || 0
  const likeCount = row.likeCount || 0
  if (playCount === 0) return '-'
  return ((likeCount / playCount) * 100).toFixed(2) + '%'
}

// 计算转发比（转发 / 播放量 × 100）
const calcShareRate = (row: OrderTask) => {
  const playCount = row.playCount || row.actualExposure || 0
  const shareCount = row.shareCount || 0
  if (playCount === 0) return '-'
  return ((shareCount / playCount) * 100).toFixed(2) + '%'
}

// 格式化货币
const formatCurrency = (value?: number) => {
  if (value === undefined || value === null || value === 0) return '-'
  return '¥' + value.toFixed(2)
}

// 格式化百分比
const formatPercentage = (value?: number) => {
  if (value === undefined || value === null || value === 0) return '-'
  return (value * 100).toFixed(2) + '%'
}

// 格式化数字（带千分位）
const formatNumber = (num?: number) => {
  if (num === undefined || num === null) return '-'
  if (num === 0) return '0'
  return num.toLocaleString()
}

// 格式化日期
const formatDate = (dateString?: string) => {
  if (!dateString) return '-'
  const date = new Date(dateString)
  const month = date.getMonth() + 1
  const day = date.getDate()
  const hours = date.getHours().toString().padStart(2, '0')
  const minutes = date.getMinutes().toString().padStart(2, '0')
  return `${date.getFullYear()}年${month.toString().padStart(2, '0')}月${day.toString().padStart(2, '0')}日 ${hours}:${minutes}`
}

// 获取状态标签类型
const getStatusTagType = (status?: string) => {
  switch (status) {
    case 'UNPAID': return 'info'
    case 'AUDITING': return 'warning'
    case 'DELIVERING': return 'warning'
    case 'DELIVERED': return 'success'   // API返回的已投放完成
    case 'DELIVERIED': return 'success'  // API拼写错误的已完成
    case 'FINISHED': return 'success'
    case 'TERMINATED': return 'danger'
    case 'UNDELIVERIED': return 'danger' // API返回的投放终止
    case 'AUDIT_PAUSE': return 'warning'
    case 'AUDIT_REJECTED': return 'danger'
    // 兼容旧状态
    case 'WAIT': return 'info'
    case 'RUNNING': return 'warning'
    case 'SUCCESS': return 'success'
    case 'FAIL': return 'danger'
    case 'CANCELLED': return 'info'
    default: return 'info'
  }
}

// 获取状态文本
const getStatusText = (status?: string) => {
  switch (status) {
    case 'UNPAID': return '未支付'
    case 'AUDITING': return '审核中'
    case 'DELIVERING': return '投放中'
    case 'DELIVERED': return '已完成'     // API返回的已投放完成
    case 'DELIVERIED': return '已完成'   // API拼写错误的已完成
    case 'FINISHED': return '已完成'
    case 'TERMINATED': return '投放终止'
    case 'UNDELIVERIED': return '投放终止' // API返回的投放终止（未开始就终止）
    case 'AUDIT_PAUSE': return '审核暂停'
    case 'AUDIT_REJECTED': return '审核不通过'
    // 兼容旧状态
    case 'WAIT': return '待投放'
    case 'RUNNING': return '投放中'
    case 'SUCCESS': return '已完成'
    case 'FAIL': return '已失败'
    case 'CANCELLED': return '已取消'
    default: return status || '-'
  }
}
</script>

<style scoped>
/* 视频列 */
.video-cell {
  display: flex;
  align-items: center;
  gap: 12px;
}

.video-cover {
  width: 60px;
  height: 80px;
  border-radius: 4px;
  flex-shrink: 0;
}

.video-cover-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f5f5;
  color: #ccc;
  font-size: 24px;
}

.video-info {
  display: flex;
  flex-direction: column;
  gap: 4px;
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

.account-name {
  font-size: 12px;
  color: #999;
}

.order-time {
  font-size: 12px;
  color: #999;
}

/* 表头带tooltip */
.header-with-tooltip {
  display: flex;
  align-items: center;
  gap: 4px;
}

.info-icon {
  font-size: 14px;
  color: #999;
  cursor: help;
}

/* 表头样式（原header-red改为黑色） */
.header-red {
  color: #333;
  font-weight: 500;
}

/* 投放金额列 */
.amount-cell {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.amount-text {
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.amount-progress {
  width: 100%;
}

.amount-progress :deep(.el-progress-bar__outer) {
  background-color: #e5e7eb;
}

.amount-progress :deep(.el-progress-bar__inner) {
  background: linear-gradient(90deg, #ff6b35 0%, #ff8c5a 100%);
}

/* 指标值 */
.metric-value {
  font-size: 14px;
  color: #333;
  font-weight: 400;
}

/* 时间文本 */
.time-text {
  font-size: 13px;
  color: #666;
}
</style>
