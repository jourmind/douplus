<template>
  <div class="account-dashboard">
    <!-- 顶部导航 -->
    <div class="top-nav">
      <div class="nav-logo">
        <span class="logo-text">DOU<span class="logo-plus">+</span></span>
      </div>
      <div class="nav-menu">
        <span 
          v-for="item in navItems" 
          :key="item.key" 
          :class="['nav-item', { active: activeNav === item.key }]"
          @click="handleNavClick(item.key)"
        >
          {{ item.label }}
        </span>
      </div>
    </div>

    <!-- 账户信息卡片 -->
    <div class="account-header">
      <div class="account-info-section">
        <div class="account-avatar-info">
          <el-avatar :size="60" :src="convertToHttps(account?.avatar)">
            <span class="avatar-text">{{ getAvatarText(account?.remark || account?.nickname) }}</span>
          </el-avatar>
          <div class="account-basic">
            <div class="name-row">
              <span class="nickname">{{ account?.remark || account?.nickname || '未知账号' }}</span>
            </div>
          </div>
        </div>
        
        <!-- 注释：账户余额功能暂未从抖音API获取，需要后续对接广告主账户API -->
        <!-- <div class="wallet-section">
          <div class="wallet-header">
            <span class="wallet-title">
              钱包 
              <el-icon class="help-icon"><QuestionFilled /></el-icon>
            </span>
            <div class="wallet-actions">
              <a href="#" class="action-link">立即充值</a>
              <a href="#" class="action-link">对公转账</a>
            </div>
          </div>
          <div class="wallet-content">
            <div class="wallet-item">
              <span class="wallet-value">{{ account?.balance?.toFixed(2) || '0.00' }}</span>
              <span class="wallet-label">账户总余额（元）</span>
            </div>
          </div>
        </div> -->
      </div>
    </div>

    <!-- 首页概览内容 -->
    <div v-if="activeNav === 'overview'" class="overview-content">
      <!-- 数据总览 -->
      <div class="data-overview card">
        <div class="card-header">
          <h3 class="card-title">数据总览</h3>
          <div class="card-actions">
            <span class="period-label">时间周期</span>
            <el-select v-model="dataPeriod" size="small" style="width: 100px;" @change="handlePeriodChange">
              <el-option label="今天" value="today" />
              <el-option label="近7天" value="7d" />
              <el-option label="近30天" value="30d" />
              <el-option label="全部" value="all" />
            </el-select>
          </div>
        </div>
        
        <div class="stats-cards">
          <div class="stat-card highlight">
            <span class="stat-name">消耗(元)</span>
            <span class="stat-number">{{ formatNumber(statsData.cost) }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频播放量</span>
            <span class="stat-number">{{ formatNumber(statsData.playCount) }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频点赞量</span>
            <span class="stat-number">{{ formatNumber(statsData.likeCount) }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频评论量</span>
            <span class="stat-number">{{ formatNumber(statsData.commentCount) }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频分享量</span>
            <span class="stat-number">{{ formatNumber(statsData.shareCount) }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">粉丝量</span>
            <span class="stat-number">{{ formatNumber(statsData.fansCount) }}</span>
          </div>
        </div>
        
        <!-- 视频排行榜 -->
        <div class="video-ranking">
          <div class="ranking-header">
            <h3 class="ranking-title">视频排行榜</h3>
            <el-select v-model="rankingSort" size="small" style="width: 120px;" @change="loadVideoStats">
              <el-option label="按消耗" value="cost" />
              <el-option label="按播放量" value="playCount" />
              <el-option label="按点赞数" value="likeCount" />
              <el-option label="按转发数" value="shareCount" />
            </el-select>
          </div>
          
          <div v-loading="videoStatsLoading" class="ranking-list">
            <div v-for="(video, index) in videoStats" :key="video.itemId" class="ranking-item">
              <div class="ranking-number">{{ index + 1 }}</div>
              <img :src="convertToHttps(video.cover) || '/default-cover.jpg'" class="video-cover" @error="handleImageError" />
              <div class="video-info">
                <div class="video-title">{{ video.title || '未知视频' }}</div>
                <div class="video-stats">
                  <span class="stat-item">消耗: ¥{{ video.totalCost }}</span>
                  <span class="stat-item">播放: {{ formatNumber(video.totalPlay) }}</span>
                  <span class="stat-item">点赞: {{ formatNumber(video.totalLike) }}</span>
                </div>
              </div>
            </div>
            <el-empty v-if="videoStats.length === 0 && !videoStatsLoading" description="暂无视频数据" />
          </div>
        </div>
      </div>
    </div>

    <!-- 我的订单内容 -->
    <div v-if="activeNav === 'orders'" class="orders-content">
      <!-- 顶部标题栏 -->
      <div class="orders-header">
        <div class="orders-title">
          <span class="title-text">我的订单</span>
          <span class="title-line"></span>
        </div>
        <el-button type="danger" @click="goToDouplus">
          去上热门
          <el-icon class="arrow-icon"><TopRight /></el-icon>
        </el-button>
      </div>

      <!-- 使用统一的订单列表组件 -->
      <OrderListView 
        :account-id="accountId"
        :show-member-filter="false"
        :show-account-column="false"
        @export="exportOrders"
      />
    </div>

    <!-- 返回按钮 -->
    <div class="back-button">
      <el-button @click="goBack">
        <el-icon><ArrowLeft /></el-icon>
        返回账号列表
      </el-button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, nextTick, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { getAccountById } from '@/api/account'
import { getAccountStats, getVideoStatsByAccount } from '@/api/douplus'
import type { DouyinAccount } from '@/api/types'
import * as echarts from 'echarts'
import { TopRight, ArrowLeft, QuestionFilled } from '@element-plus/icons-vue'
import { convertToHttps } from '@/utils/url'
import { OrderListView } from '@/components/order'

const route = useRoute()
const router = useRouter()
const accountId = Number(route.params.id)

const account = ref<DouyinAccount | null>(null)
const activeNav = ref('overview')
const dataPeriod = ref('all')
const chartRef = ref<HTMLElement | null>(null)

// 视频排行榜相关
const videoStats = ref<any[]>([])
const videoStatsLoading = ref(false)
const rankingSort = ref('cost')

// 导出订单
const exportOrders = () => {
  ElMessage.info('导出功能开发中')
}

const navItems = [
  { key: 'overview', label: '首页概览' },
  { key: 'orders', label: '我的订单' },
]

const statsData = reactive({
  cost: 0,
  playCount: 0,
  likeCount: 0,
  commentCount: 0,
  shareCount: 0,
  fansCount: 0,
})

// 格式化数字
const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

// 获取头像文字
const getAvatarText = (nickname?: string) => {
  if (!nickname) return '?'
  return nickname.charAt(0)
}

// 加载账号数据
const loadAccount = async () => {
  try {
    const res = await getAccountById(accountId)
    if (res.code === 200) {
      account.value = res.data
    }
  } catch (error) {
    console.error('加载账号失败', error)
  }
}

// 初始化图表
const initChart = () => {
  if (!chartRef.value) return
  
  const chart = echarts.init(chartRef.value)
  
  // 生成近7天日期
  const dates = []
  const now = new Date()
  for (let i = 6; i >= 0; i--) {
    const d = new Date(now)
    d.setDate(d.getDate() - i)
    dates.push(d.toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit' }))
  }
  
  const option = {
    grid: {
      left: '50',
      right: '30',
      top: '20',
      bottom: '30',
    },
    xAxis: {
      type: 'category',
      data: dates,
      axisLine: { lineStyle: { color: '#e8e8e8' } },
      axisLabel: { color: '#999' },
    },
    yAxis: {
      type: 'value',
      min: 0,
      max: 1,
      interval: 0.2,
      axisLine: { show: false },
      axisTick: { show: false },
      splitLine: { lineStyle: { color: '#f0f0f0' } },
      axisLabel: { color: '#999' },
    },
    series: [{
      type: 'line',
      data: [0, 0, 0, 0, 0, 0, 0],
      smooth: true,
      lineStyle: { color: '#ff6b35', width: 2 },
      areaStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: 'rgba(255, 107, 53, 0.3)' },
          { offset: 1, color: 'rgba(255, 107, 53, 0.05)' },
        ]),
      },
      symbol: 'circle',
      symbolSize: 6,
      itemStyle: { color: '#ff6b35' },
    }],
    tooltip: {
      trigger: 'axis',
      formatter: '{b}<br/>消耗: ¥{c}',
    },
  }
  
  chart.setOption(option)
  
  // 响应式
  window.addEventListener('resize', () => chart.resize())
}

// 加载订单统计数据
const loadStats = async () => {
  try {
    const res = await getAccountStats(accountId, { period: dataPeriod.value as any })
    if (res.code === 200 && res.data) {
      statsData.cost = Number(res.data.cost || 0)
      statsData.playCount = res.data.playCount || 0
      statsData.likeCount = res.data.likeCount || 0
      statsData.commentCount = res.data.commentCount || 0
      statsData.shareCount = res.data.shareCount || 0
      statsData.fansCount = res.data.fansCount || 0
    }
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

// 加载视频统计数据
const loadVideoStats = async () => {
  videoStatsLoading.value = true
  try {
    const res = await getVideoStatsByAccount(accountId, {
      period: dataPeriod.value as any,
      sortBy: rankingSort.value as any,
      sortOrder: 'desc',
      pageNum: 1,
      pageSize: 10
    })
    if (res.code === 200 && res.data) {
      videoStats.value = res.data.records || []
    }
  } catch (error) {
    console.error('加载视频统计失败', error)
  } finally {
    videoStatsLoading.value = false
  }
}

// 时间周期变化
const handlePeriodChange = () => {
  loadStats()
  loadVideoStats()
}

// 图片加载错误处理
const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement
  target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iODAiIHZpZXdCb3g9IjAgMCA4MCA4MCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAiIGhlaWdodD0iODAiIGZpbGw9IiNGNUY1RjUiLz48cGF0aCBkPSJNMzAgMzVINTBWNDVIMzBWMzVaIiBmaWxsPSIjQ0NDIi8+PC9zdmc+'
}

// 获取投放目标文本
const getTargetText = (objective?: string) => {
  const map: Record<string, string> = {
    'VIDEO_PROM_COMMENT_AND_LIKE': '点赞评论',
    'VIDEO_PROM_COMMENT_INTERACTION': '评论链接点击',
    'VIDEO_PROM_HOMEPAGE': '主页浏览',
    'VIDEO_PROM_FANS': '粉丝提升',
  }
  return map[objective || ''] || '评论链接点击'
}

// 格式化日期
const formatDate = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  }).replace(/\//g, '年').replace(/\//g, '月') + '下单'
}

// 格式化日期时间（订单结束时间用）
const formatDateTime = (dateStr?: string) => {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  const year = date.getFullYear()
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const hour = String(date.getHours()).padStart(2, '0')
  const minute = String(date.getMinutes()).padStart(2, '0')
  return `${year}-${month}-${day} ${hour}:${minute}`
}

// 导航点击
const handleNavClick = (key: string) => {
  activeNav.value = key
  if (key === 'orders') {
    loadOrders()
  } else if (key === 'overview') {
    loadStats()
    loadVideoStats()
  }
}

// 续费订单
const handleRenewOrder = (order: any) => {
  ElMessage.info('续费功能开发中')
}

// 跳转DOU+投放页面
const goToDouplus = () => {
  router.push('/douplus/create')
}

// 返回
const goBack = () => {
  router.push('/account')
}

onMounted(async () => {
  await loadAccount()
  await loadStats()
  await loadVideoStats()
  // 预加载订单列表，避免切换标签时等待
  loadOrders()
  await nextTick()
})
</script>

<style scoped lang="scss">
.account-dashboard {
  min-height: 100vh;
  background: #f5f7fa;
}

.top-nav {
  display: flex;
  align-items: center;
  background: #fff;
  padding: 0 30px;
  height: 56px;
  border-bottom: 1px solid #e8e8e8;
  
  .nav-logo {
    .logo-text {
      font-size: 24px;
      font-weight: 700;
      color: #ff6b35;
      
      .logo-plus {
        font-size: 20px;
      }
    }
  }
  
  .nav-menu {
    display: flex;
    margin-left: 60px;
    
    .nav-item {
      padding: 16px 20px;
      font-size: 14px;
      color: #666;
      cursor: pointer;
      position: relative;
      
      &:hover {
        color: #333;
      }
      
      &.active {
        color: #ff6b35;
        font-weight: 500;
        
        &::after {
          content: '';
          position: absolute;
          bottom: 0;
          left: 20px;
          right: 20px;
          height: 2px;
          background: #ff6b35;
        }
      }
    }
  }
}

.account-header {
  display: flex;
  padding: 30px;
  background: #fff;
  margin-bottom: 20px;
  gap: 30px;
  
  .account-info-section {
    flex: 1;
    display: flex;
    gap: 60px;
  }
  
  .account-avatar-info {
    display: flex;
    gap: 16px;
    
    :deep(.el-avatar) {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      
      .avatar-text {
        font-size: 24px;
        color: #fff;
      }
    }
    
    .account-basic {
      .name-row {
        display: flex;
        align-items: center;
        gap: 10px;
        margin-bottom: 12px;
        
        .nickname {
          font-size: 18px;
          font-weight: 600;
          color: #333;
        }
      }
      
      .stats-row {
        display: flex;
        gap: 30px;
        
        .stat-item {
          display: flex;
          flex-direction: column;
          align-items: center;
          
          .stat-value {
            font-size: 18px;
            font-weight: 600;
            color: #333;
          }
          
          .stat-label {
            font-size: 12px;
            color: #999;
            margin-top: 4px;
          }
        }
      }
    }
  }
  
  .wallet-section {
    .wallet-header {
      display: flex;
      align-items: center;
      gap: 20px;
      margin-bottom: 12px;
      
      .wallet-title {
        font-size: 14px;
        color: #333;
        display: flex;
        align-items: center;
        gap: 4px;
        
        .help-icon {
          font-size: 12px;
          color: #999;
        }
      }
      
      .wallet-actions {
        display: flex;
        gap: 12px;
        
        .action-link {
          font-size: 12px;
          color: #ff6b35;
          text-decoration: none;
          
          &:hover { text-decoration: underline; }
        }
      }
    }
    
    .wallet-content {
      display: flex;
      align-items: flex-end;
      gap: 30px;
      
      .wallet-divider {
        width: 1px;
        height: 40px;
        background: #e8e8e8;
      }
      
      .wallet-item {
        display: flex;
        flex-direction: column;
        
        .wallet-value {
          font-size: 28px;
          font-weight: 600;
          color: #333;
        }
        
        .wallet-label {
          font-size: 12px;
          color: #999;
          margin-top: 4px;
          
          .detail-link {
            color: #ff6b35;
            margin-left: 8px;
            text-decoration: none;
            
            &:hover { text-decoration: underline; }
          }
        }
      }
    }
  }
  
  .banner-section {
    width: 320px;
    
    .promo-banner {
      background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
      border-radius: 8px;
      padding: 20px;
      color: #fff;
      display: flex;
      justify-content: space-between;
      align-items: center;
      
      .banner-text {
        .banner-title {
          font-size: 14px;
          margin-bottom: 4px;
        }
        
        .banner-subtitle {
          font-size: 16px;
          font-weight: 600;
          margin-bottom: 8px;
        }
        
        .banner-highlight {
          font-size: 13px;
          opacity: 0.9;
        }
      }
    }
  }
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin: 0 20px 20px;
  
  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 20px;
    
    .card-title {
      font-size: 16px;
      font-weight: 600;
      color: #333;
    }
    
    .card-actions {
      display: flex;
      align-items: center;
      gap: 10px;
      
      .period-label {
        font-size: 13px;
        color: #999;
      }
    }
  }
}

.data-overview {
  .stats-cards {
    display: grid;
    grid-template-columns: repeat(6, 1fr);
    gap: 16px;
    margin-bottom: 30px;
    
    .stat-card {
      padding: 16px 20px;
      border: 1px solid #e8e8e8;
      border-radius: 8px;
      
      &.highlight {
        background: #fff8f5;
        border-color: #ffebe0;
        
        .stat-name, .stat-number {
          color: #ff6b35;
        }
      }
      
      .stat-name {
        font-size: 13px;
        color: #666;
        display: block;
        margin-bottom: 8px;
      }
      
      .stat-number {
        font-size: 24px;
        font-weight: 600;
        color: #333;
      }
    }
  }
  
  .chart-section {
    .chart-title {
      font-size: 13px;
      color: #999;
      margin-bottom: 10px;
    }
    
    .chart-container {
      height: 250px;
    }
  }
  
  .video-ranking {
    margin-top: 30px;
    
    .ranking-header {
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 20px;
      
      .ranking-title {
        font-size: 16px;
        font-weight: 600;
        color: #333;
      }
    }
    
    .ranking-list {
      .ranking-item {
        display: flex;
        align-items: center;
        gap: 16px;
        padding: 12px;
        border: 1px solid #e8e8e8;
        border-radius: 8px;
        margin-bottom: 12px;
        transition: all 0.3s;
        
        &:hover {
          background: #fafafa;
          border-color: #ff6b35;
        }
        
        .ranking-number {
          width: 30px;
          height: 30px;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f5f5;
          border-radius: 4px;
          font-size: 16px;
          font-weight: 600;
          color: #666;
          flex-shrink: 0;
        }
        
        .video-cover {
          width: 80px;
          height: 80px;
          object-fit: cover;
          border-radius: 4px;
          flex-shrink: 0;
          background: #f5f5f5;
        }
        
        .video-info {
          flex: 1;
          min-width: 0;
          
          .video-title {
            font-size: 14px;
            color: #333;
            margin-bottom: 8px;
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
          }
          
          .video-stats {
            display: flex;
            gap: 20px;
            
            .stat-item {
              font-size: 12px;
              color: #999;
            }
          }
        }
      }
    }
  }
}

// 订单列表样式 - 与History.vue统一
.orders-content {
  .orders-card {
    margin: 0 20px;
  }
}

.orders-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px;
  background: #fff;
  margin: 0 20px 16px;
  border-radius: 8px;
  
  .orders-title {
    display: flex;
    flex-direction: column;
    
    .title-text {
      font-size: 18px;
      font-weight: 600;
      color: #ff6b35;
    }
    
    .title-line {
      width: 24px;
      height: 3px;
      background: #ff6b35;
      border-radius: 2px;
      margin-top: 6px;
    }
  }
  
  .el-button {
    .arrow-icon {
      margin-left: 4px;
    }
  }
}

.back-button {
  padding: 0 20px 20px;
}
</style>
