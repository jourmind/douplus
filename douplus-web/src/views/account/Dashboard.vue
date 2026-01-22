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
          <el-avatar :size="60" :src="account?.avatar">
            <span class="avatar-text">{{ getAvatarText(account?.remark || account?.nickname) }}</span>
          </el-avatar>
          <div class="account-basic">
            <div class="name-row">
              <span class="nickname">{{ account?.remark || account?.nickname || '未知账号' }}</span>
              <el-tag type="danger" size="small">企业升级</el-tag>
            </div>
            <div class="stats-row">
              <div class="stat-item">
                <span class="stat-value">{{ formatNumber(account?.totalFavorited || 0) }}</span>
                <span class="stat-label">获赞</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ formatNumber(account?.followingCount || 0) }}</span>
                <span class="stat-label">关注</span>
              </div>
              <div class="stat-item">
                <span class="stat-value">{{ formatNumber(account?.fansCount || 0) }}</span>
                <span class="stat-label">粉丝</span>
              </div>
            </div>
          </div>
        </div>
        
        <div class="wallet-section">
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
            <div class="wallet-divider"></div>
            <div class="wallet-item">
              <span class="wallet-value">{{ account?.couponCount || 0 }}</span>
              <span class="wallet-label">优惠券（张）<a href="#" class="detail-link">查看详情</a></span>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 首页概览内容 -->
    <div v-if="activeNav === 'overview'" class="overview-content">
      <!-- 数据总览 -->
      <div class="data-overview card">
        <div class="card-header">
          <h3 class="card-title">数据总览</h3>
          <div class="card-actions">
            <span class="period-label">当前周期</span>
            <el-select v-model="dataPeriod" size="small" style="width: 100px;">
              <el-option label="近7天" value="7d" />
              <el-option label="近30天" value="30d" />
              <el-option label="本月" value="month" />
            </el-select>
          </div>
        </div>
        
        <div class="stats-cards">
          <div class="stat-card highlight">
            <span class="stat-name">消耗</span>
            <span class="stat-number">{{ statsData.cost }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频播放量</span>
            <span class="stat-number">{{ statsData.playCount }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频点赞量</span>
            <span class="stat-number">{{ statsData.likeCount }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频评论量</span>
            <span class="stat-number">{{ statsData.commentCount }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">视频分享量</span>
            <span class="stat-number">{{ statsData.shareCount }}</span>
          </div>
          <div class="stat-card">
            <span class="stat-name">粉丝量</span>
            <span class="stat-number">{{ statsData.fansCount }}</span>
          </div>
        </div>
        
        <!-- 消耗图表 -->
        <div class="chart-section">
          <div class="chart-title">消耗(元)</div>
          <div ref="chartRef" class="chart-container"></div>
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

      <div class="orders-card card">
        <!-- 使用共享筛选组件 -->
        <OrderFilters 
          v-model="orderFilters" 
          @change="handleFilterChange"
          @export="exportOrders" 
        />

        <!-- 订单统计和排序 -->
        <div class="orders-toolbar">
          <span class="orders-count">共 {{ orderList.length }} 个订单</span>
          <SortCascader v-model="sortOption" @change="handleSortChange" />
        </div>

        <!-- 使用共享订单表格组件 -->
        <OrderTable 
          :tasks="orderList"
          :loading="ordersLoading"
          :show-account-column="false"
          :show-cancel-button="false"
          @view-details="viewOrderDetails"
        />
        
        <el-empty v-if="orderList.length === 0 && !ordersLoading" description="暂无订单数据" />
      </div>
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
import { getTaskList, getAccountStats } from '@/api/douplus'
import type { DouyinAccount, DouplusTask } from '@/api/types'
import * as echarts from 'echarts'
import { TopRight, ArrowLeft, QuestionFilled } from '@element-plus/icons-vue'
import { OrderTable, OrderFilters, SortCascader } from '@/components/order'
import type { OrderFiltersType, SortOption } from '@/components/order'

const route = useRoute()
const router = useRouter()
const accountId = Number(route.params.id)

const account = ref<DouyinAccount | null>(null)
const activeNav = ref('overview')
const dataPeriod = ref('7d')
const chartRef = ref<HTMLElement | null>(null)

// 订单相关
const ordersLoading = ref(false)
const orderFilters = ref<OrderFiltersType>({})
const sortOption = ref<SortOption>({
  field: 'createTime',
  order: 'desc'
})
const orderList = ref<any[]>([])
const allOrders = ref<any[]>([])  // 存储所有订单数据，用于前端排序

// 前端排序函数
const sortOrders = (data: any[], field: string, order: 'asc' | 'desc') => {
  return [...data].sort((a, b) => {
    let valA: number, valB: number
    
    switch (field) {
      case 'actualCost':
        valA = a.actualCost || 0
        valB = b.actualCost || 0
        break
      case 'playCount':
        valA = a.playCount || 0
        valB = b.playCount || 0
        break
      case 'costPerPlay':
        valA = (a.playCount > 0) ? (a.actualCost || 0) / a.playCount : 0
        valB = (b.playCount > 0) ? (b.actualCost || 0) / b.playCount : 0
        break
      case 'shareRate':
        valA = (a.playCount > 0) ? (a.shareCount || 0) / a.playCount : 0
        valB = (b.playCount > 0) ? (b.shareCount || 0) / b.playCount : 0
        break
      case 'createTime':
      default:
        valA = new Date(a.createTimeRaw || 0).getTime()
        valB = new Date(b.createTimeRaw || 0).getTime()
        break
    }
    
    return order === 'asc' ? valA - valB : valB - valA
  })
}

// 应用前端排序
const applyOrderSort = () => {
  orderList.value = sortOrders(allOrders.value, sortOption.value.field, sortOption.value.order)
}

// 筛选条件变化
const handleFilterChange = () => {
  loadOrders()
}

// 排序变化 - 前端排序，无需请求后端
const handleSortChange = () => {
  applyOrderSort()
}

// 导出订单
const exportOrders = () => {
  ElMessage.info('导出功能开发中')
}

// 查看订单详情
const viewOrderDetails = (order: any) => {
  ElMessage.info('查看详情功能开发中')
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
    const res = await getAccountStats(accountId)
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

// 加载订单列表 - 获取全部数据
const loadOrders = async () => {
  ordersLoading.value = true
  try {
    const res = await getTaskList({
      accountId: accountId,
      pageNum: 1,
      pageSize: -1  // 获取全部数据，排序在前端处理
    })
    if (res.code === 200) {
      // 转换订单数据格式，与History.vue统一
      allOrders.value = (res.data.records || []).map((task: DouplusTask) => ({
        id: task.id,
        videoCover: task.videoCoverUrl,
        videoTitle: task.videoTitle || '视频标题',
        itemId: task.itemId,
        accountNickname: account.value?.nickname || '',
        status: task.status,
        actualCost: task.actualCost || 0,
        budget: task.budget,
        actualExposure: task.actualExposure || 0,
        playCount: task.playCount || task.actualExposure || 0,
        likeCount: task.likeCount || 0,
        shareCount: task.shareCount || 0,
        clickCount: task.clickCount || 0,
        followCount: task.followCount || 0,
        componentClickCount: task.clickCount || 0,
        play5sRate: 0,
        orderEndTime: task.orderEndTime ? formatDateTime(task.orderEndTime) : '-',
        createTime: formatDate(task.createTime),
        createTimeRaw: task.createTime,  // 保留原始时间用于排序
      }))
      // 应用前端排序
      applyOrderSort()
    }
  } catch (error) {
    console.error('加载订单失败', error)
  } finally {
    ordersLoading.value = false
  }
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
  await loadStats()  // 加载统计数据
  await nextTick()
  initChart()
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

.orders-toolbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 0;
  margin-bottom: 12px;
  
  .orders-count {
    font-size: 13px;
    color: #1890ff;
  }
}

.back-button {
  padding: 0 20px 20px;
}
</style>
