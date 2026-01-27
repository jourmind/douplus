<template>
  <div class="dashboard">
    <!-- 筛选栏 -->
    <div class="filter-bar">
      <div class="filter-item">
        <div class="filter-label">时间周期：</div>
        <el-radio-group v-model="period" size="default" @change="handlePeriodChange">
          <el-radio-button label="today">今天</el-radio-button>
          <el-radio-button label="7d">近7天</el-radio-button>
          <el-radio-button label="30d">近30天</el-radio-button>
          <el-radio-button label="all">全部</el-radio-button>
        </el-radio-group>
      </div>
      
      <div class="filter-item">
        <div class="filter-label">用户筛选：</div>
        <el-select 
          v-model="filterAccountId" 
          placeholder="请选择账号" 
          clearable
          size="default"
          style="width: 200px;"
          @change="handleAccountChange"
        >
          <el-option label="全部账号" :value="null" />
          <el-option 
            v-for="account in accountList" 
            :key="account.id" 
            :label="account.nickname || account.douyinId" 
            :value="account.id" 
          />
        </el-select>
      </div>
    </div>
    
    <!-- 统计卡片 -->
    <div class="stat-cards">
      <div class="stat-card">
        <div class="icon primary">
          <el-icon><Money /></el-icon>
        </div>
        <div class="content">
          <div class="label">消耗(元)</div>
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
    
    <!-- 视频排行 -->
    <div class="card">
      <div class="card-header">
        <div class="card-title">视频排行榜{{ videoRankTitle }}</div>
        <el-select v-model="rankingSort" size="small" style="width: 120px;" @change="loadAllVideoStats">
          <el-option label="按消耗" value="cost" />
          <el-option label="按播放量" value="playCount" />
          <el-option label="按点赞数" value="likeCount" />
          <el-option label="按转发数" value="shareCount" />
        </el-select>
      </div>
      <el-table v-loading="videoLoading" :data="videoRank" stripe>
        <el-table-column type="index" label="排名" width="60" />
        <el-table-column label="视频" min-width="300">
          <template #default="{ row }">
            <div style="display: flex; gap: 12px; align-items: center;">
              <img 
                :src="row.cover || '/default-cover.jpg'" 
                style="width: 80px; height: 45px; object-fit: cover; background: #f0f0f0; border-radius: 4px;"
                @error="handleImageError"
              />
              <span>{{ row.title || '未知视频' }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="消耗" width="120">
          <template #default="{ row }">
            ¥{{ row.totalCost }}
          </template>
        </el-table-column>
        <el-table-column label="播放量" width="120">
          <template #default="{ row }">
            {{ formatNumber(row.totalPlay) }}
          </template>
        </el-table-column>
        <el-table-column label="点赞" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.totalLike) }}
          </template>
        </el-table-column>
        <el-table-column label="评论" width="100">
          <template #default="{ row }">
            {{ formatNumber(row.totalComment) }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="videoRank.length === 0 && !videoLoading" description="暂无视频数据" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { getAllAccountsStats, getAllVideoStats } from '@/api/douplus'
import { getAccountList } from '@/api/account'

const period = ref('all')
const filterAccountId = ref<number | null>(null)
const rankingSort = ref('cost')
const videoLoading = ref(false)
const accountList = ref<any[]>([])

const stats = ref({
  totalCost: 0,
  totalPlay: 0,
  totalLike: 0,
  totalComment: 0,
  totalShare: 0,
  fans: 0
})

const videoRank = ref<any[]>([])

// 计算视频排行榜标题
const videoRankTitle = computed(() => {
  if (!filterAccountId.value) {
    return ''  // 不显示后缀
  }
  const account = accountList.value.find(a => a.id === filterAccountId.value)
  if (account) {
    return `（${account.nickname || account.douyinId}）`
  }
  return ''
})

// 加载账号列表
const loadAccounts = async () => {
  try {
    const res = await getAccountList()
    if (res.code === 200 && res.data) {
      accountList.value = res.data
    }
  } catch (error) {
    console.error('加载账号列表失败', error)
  }
}

// 加载统计数据
const loadStats = async () => {
  try {
    const params: any = { period: period.value }
    if (filterAccountId.value) {
      params.accountId = filterAccountId.value
    }
    
    const res = await getAllAccountsStats(params)
    if (res.code === 200 && res.data) {
      stats.value = {
        totalCost: res.data.cost || 0,
        totalPlay: res.data.playCount || 0,
        totalLike: res.data.likeCount || 0,
        totalComment: res.data.commentCount || 0,
        totalShare: res.data.shareCount || 0,
        fans: res.data.fansCount || 0
      }
    }
  } catch (error) {
    console.error('加载统计数据失败', error)
  }
}

// 加载所有账号的视频统计
const loadAllVideoStats = async () => {
  videoLoading.value = true
  try {
    const params: any = {
      period: period.value,
      sortBy: rankingSort.value,
      sortOrder: 'desc',
      pageNum: 1,
      pageSize: 10
    }
    
    if (filterAccountId.value) {
      params.accountId = filterAccountId.value
    }
    
    const res = await getAllVideoStats(params)
    if (res.code === 200 && res.data) {
      videoRank.value = res.data.records || []
    }
  } catch (error) {
    console.error('加载视频统计失败', error)
  } finally {
    videoLoading.value = false
  }
}

// 时间周期变化
const handlePeriodChange = () => {
  loadStats()
  loadAllVideoStats()
}

// 账号筛选变化
const handleAccountChange = () => {
  loadStats()
  loadAllVideoStats()
}

// 图片加载错误处理
const handleImageError = (e: Event) => {
  const target = e.target as HTMLImageElement
  target.src = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODAiIGhlaWdodD0iNDUiIHZpZXdCb3g9IjAgMCA4MCA0NSIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iODAiIGhlaWdodD0iNDUiIGZpbGw9IiNGNUY1RjUiLz48L3N2Zz4='
}

const formatNumber = (num: number) => {
  if (!num) return '0'
  if (num >= 10000) {
    return (num / 10000).toFixed(1) + 'w'
  }
  return num.toString()
}

onMounted(() => {
  loadAccounts()
  loadStats()
  loadAllVideoStats()
})
</script>

<style scoped lang="scss">
.dashboard {
  padding: 20px;
}

.filter-bar {
  display: flex;
  align-items: center;
  gap: 32px;
  margin-bottom: 20px;
  padding: 16px 20px;
  background: #fff;
  border-radius: 8px;
  flex-wrap: wrap;
  
  .filter-item {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  
  .filter-label {
    font-size: 14px;
    color: #666;
    white-space: nowrap;
  }
}

.stat-cards {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
  gap: 20px;
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  display: flex;
  align-items: center;
  gap: 16px;
  
  .icon {
    width: 48px;
    height: 48px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 24px;
    
    &.primary {
      background: #fff8f5;
      color: #ff6b35;
    }
    
    &.success {
      background: #f0f9ff;
      color: #0ea5e9;
    }
    
    &.warning {
      background: #fffbeb;
      color: #f59e0b;
    }
    
    &.info {
      background: #f5f3ff;
      color: #8b5cf6;
    }
  }
  
  .content {
    flex: 1;
    
    .label {
      font-size: 13px;
      color: #999;
      margin-bottom: 8px;
    }
    
    .value {
      font-size: 24px;
      font-weight: 600;
      color: #333;
    }
  }
}

.card {
  background: #fff;
  border-radius: 8px;
  padding: 20px;
  margin-bottom: 20px;
  
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
  }
}
</style>
