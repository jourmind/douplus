<template>
  <div class="dashboard">
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="icon primary">
          <el-icon><Money /></el-icon>
        </div>
        <div class="content">
          <div class="label">消耗</div>
          <div class="value">{{ formatNumber(stats.totalCost) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="icon success">
          <el-icon><View /></el-icon>
        </div>
        <div class="content">
          <div class="label">视频播放量</div>
          <div class="value">{{ formatNumber(stats.totalPlay) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="icon warning">
          <el-icon><Star /></el-icon>
        </div>
        <div class="content">
          <div class="label">视频点赞量</div>
          <div class="value">{{ formatNumber(stats.totalLike) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="icon info">
          <el-icon><ChatDotRound /></el-icon>
        </div>
        <div class="content">
          <div class="label">视频评论量</div>
          <div class="value">{{ formatNumber(stats.totalComment) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="icon primary">
          <el-icon><Share /></el-icon>
        </div>
        <div class="content">
          <div class="label">视频分享量</div>
          <div class="value">{{ formatNumber(stats.totalShare) }}</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="icon success">
          <el-icon><User /></el-icon>
        </div>
        <div class="content">
          <div class="label">粉丝量</div>
          <div class="value">{{ formatNumber(stats.fans) }}</div>
        </div>
      </div>
    </div>
    
    <!-- 数据图表 -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">数据总览</div>
        <el-radio-group v-model="dateRange" size="small">
          <el-radio-button label="7">近7天</el-radio-button>
          <el-radio-button label="30">近30天</el-radio-button>
        </el-radio-group>
      </div>
      <div ref="chartRef" style="height: 350px;"></div>
    </div>
    
    <!-- 视频排行 -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">视频排行榜</div>
      </div>
      <el-table :data="videoRank" stripe>
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column label="视频" min-width="300">
          <template #default="{ row }">
            <div style="display: flex; gap: 12px; align-items: center;">
              <div style="width: 80px; height: 45px; background: #f0f0f0; border-radius: 4px;"></div>
              <span>{{ row.title }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column prop="play" label="播放量" width="120" />
        <el-table-column prop="like" label="点赞" width="100" />
        <el-table-column prop="comment" label="评论" width="100" />
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import * as echarts from 'echarts'

const chartRef = ref<HTMLElement>()
const dateRange = ref('7')
let chartInstance: echarts.ECharts | null = null

const stats = ref({
  totalCost: 33000,
  totalPlay: 22772000,
  totalLike: 405000,
  totalComment: 32000,
  totalShare: 4006000,
  fans: 3489
})

const videoRank = ref([
  { title: '#酒吧 #网红 #美女', play: '584.4w', like: '4.6w', comment: '969' },
  { title: '今日份快乐分享', play: '120.5w', like: '2.1w', comment: '532' },
  { title: '生活记录vlog', play: '89.2w', like: '1.8w', comment: '421' }
])

const formatNumber = (num: number) => {
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

const initChart = () => {
  if (!chartRef.value) return
  
  if (!chartInstance) {
    chartInstance = echarts.init(chartRef.value)
  }
  
  const option = {
    tooltip: {
      trigger: 'axis'
    },
    legend: {
      data: ['消耗']
    },
    grid: {
      left: '3%',
      right: '4%',
      bottom: '3%',
      containLabel: true
    },
    xAxis: {
      type: 'category',
      boundaryGap: false,
      data: ['01.10', '01.11', '01.12', '01.13', '01.14', '01.15', '01.16']
    },
    yAxis: {
      type: 'value',
      axisLabel: {
        formatter: (value: number) => value >= 1000 ? value / 1000 + 'k' : value
      }
    },
    series: [
      {
        name: '消耗',
        type: 'line',
        smooth: true,
        data: [4500, 7000, 6800, 5500, 4200, 5800, 2000],
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: 'rgba(255, 107, 53, 0.3)' },
            { offset: 1, color: 'rgba(255, 107, 53, 0.05)' }
          ])
        },
        lineStyle: {
          color: '#ff6b35'
        },
        itemStyle: {
          color: '#ff6b35'
        }
      }
    ]
  }
  
  chartInstance.setOption(option)
}

watch(dateRange, () => {
  initChart()
})

onMounted(() => {
  initChart()
  
  window.addEventListener('resize', () => {
    chartInstance?.resize()
  })
})
</script>
