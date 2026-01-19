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
          @click="activeNav = item.key"
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
            <span class="avatar-text">{{ getAvatarText(account?.nickname) }}</span>
          </el-avatar>
          <div class="account-basic">
            <div class="name-row">
              <span class="nickname">{{ account?.nickname || '未知账号' }}</span>
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
      
      <!-- 右侧广告banner -->
      <div class="banner-section">
        <div class="promo-banner">
          <div class="banner-text">
            <div class="banner-title">巨量营销 · 中小企业投放进阶</div>
            <div class="banner-subtitle">千万流量 助力生意新增长</div>
            <div class="banner-highlight">最高得 500元 红包</div>
          </div>
          <el-button type="danger" size="small">立即参加</el-button>
        </div>
      </div>
    </div>

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

    <!-- 视频排行榜 -->
    <div class="video-ranking card">
      <div class="card-header">
        <h3 class="card-title">视频排行榜</h3>
        <div class="card-actions">
          <span class="period-label">时间周期</span>
          <el-select v-model="rankingPeriod" size="small" style="width: 100px;">
            <el-option label="近7天" value="7d" />
            <el-option label="近30天" value="30d" />
          </el-select>
        </div>
      </div>
      
      <div class="ranking-filters">
        <span class="filter-label">视频类型：</span>
        <el-radio-group v-model="videoType" size="small">
          <el-radio-button label="hot">热度指数</el-radio-button>
          <el-radio-button label="lowFans">低粉爆款</el-radio-button>
          <el-radio-button label="highPlay">高完播率</el-radio-button>
          <el-radio-button label="highFans">高涨粉率</el-radio-button>
          <el-radio-button label="highLike">高点赞率</el-radio-button>
        </el-radio-group>
        <span class="filter-label" style="margin-left: 20px;">垂类领域：</span>
        <el-select v-model="videoCategory" size="small" style="width: 120px;">
          <el-option label="休闲娱乐" value="entertainment" />
          <el-option label="美食" value="food" />
          <el-option label="生活" value="life" />
        </el-select>
      </div>
      
      <el-table :data="videoRankingList" stripe>
        <el-table-column type="index" label="排名" width="60">
          <template #default="{ $index }">
            <span :class="['rank-num', { top: $index < 3 }]">{{ $index + 1 }}</span>
          </template>
        </el-table-column>
        <el-table-column label="视频信息" min-width="300">
          <template #default="{ row }">
            <div class="video-info">
              <el-icon class="video-icon"><VideoPlay /></el-icon>
              <div class="video-detail">
                <div class="video-title">{{ row.title }}</div>
                <div class="video-author">{{ row.author }} | 粉丝量: {{ formatNumber(row.fansCount) }}</div>
              </div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="热度指数" width="120">
          <template #default="{ row }">
            <span class="hot-value">{{ formatNumber(row.hotIndex) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="新增播放量" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.newPlayCount) }}
          </template>
        </el-table-column>
        <el-table-column label="新增点赞量" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.newLikeCount) }}
          </template>
        </el-table-column>
        <el-table-column label="新增粉丝量" width="100">
          <template #default="{ row }">
            {{ row.newFansCount }}
          </template>
        </el-table-column>
      </el-table>
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
import { ref, reactive, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getAccountById } from '@/api/account'
import type { DouyinAccount } from '@/api/types'
import * as echarts from 'echarts'

const route = useRoute()
const router = useRouter()
const accountId = Number(route.params.id)

const account = ref<DouyinAccount | null>(null)
const activeNav = ref('overview')
const dataPeriod = ref('7d')
const rankingPeriod = ref('7d')
const videoType = ref('hot')
const videoCategory = ref('entertainment')
const chartRef = ref<HTMLElement | null>(null)

const navItems = [
  { key: 'overview', label: '首页概览' },
  { key: 'orders', label: '我的订单' },
  { key: 'analysis', label: '数据分析' },
  { key: 'tools', label: '账户工具' },
  { key: 'help', label: '帮助中心' },
]

const statsData = reactive({
  cost: 0,
  playCount: 0,
  likeCount: 0,
  commentCount: 0,
  shareCount: 0,
  fansCount: 0,
})

// 模拟视频排行榜数据
const videoRankingList = ref([
  {
    title: '赶紧在评论区@你的续火花搭子看看...',
    author: '一口气泡水',
    fansCount: 56000,
    hotIndex: 165000,
    newPlayCount: 3933000,
    newLikeCount: 65000,
    newFansCount: 401,
  },
])

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

// 返回
const goBack = () => {
  router.push('/account')
}

onMounted(async () => {
  await loadAccount()
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

.video-ranking {
  .ranking-filters {
    display: flex;
    align-items: center;
    margin-bottom: 16px;
    
    .filter-label {
      font-size: 13px;
      color: #666;
      margin-right: 10px;
    }
    
    :deep(.el-radio-button__inner) {
      padding: 6px 12px;
      font-size: 12px;
    }
    
    :deep(.el-radio-button__original-radio:checked + .el-radio-button__inner) {
      background: #ff6b35;
      border-color: #ff6b35;
    }
  }
  
  .video-info {
    display: flex;
    align-items: center;
    gap: 12px;
    
    .video-icon {
      font-size: 32px;
      color: #999;
    }
    
    .video-detail {
      .video-title {
        font-size: 14px;
        color: #333;
        margin-bottom: 4px;
      }
      
      .video-author {
        font-size: 12px;
        color: #999;
      }
    }
  }
  
  .rank-num {
    display: inline-block;
    width: 24px;
    height: 24px;
    line-height: 24px;
    text-align: center;
    border-radius: 4px;
    font-size: 12px;
    color: #666;
    background: #f5f5f5;
    
    &.top {
      background: #ff6b35;
      color: #fff;
    }
  }
  
  .hot-value {
    color: #ff6b35;
    font-weight: 500;
  }
}

.back-button {
  padding: 0 20px 20px;
}
</style>
