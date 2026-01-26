// 通用响应类型
export interface ApiResponse<T = any> {
  code: number
  message: string
  data: T
  timestamp: number
}

// 分页响应
export interface PageResult<T> {
  records: T[]
  total: number
  size: number
  current: number
  pages: number
}

// 用户信息
export interface UserInfo {
  id: number
  username: string
  nickname: string
  avatar: string
  email: string
  phone: string
  status: number
  lastLoginTime: string
  hasInvestPassword: boolean
}

// 登录响应
export interface LoginResponse {
  accessToken: string
  tokenType: string
  expiresIn: number
  user: UserInfo
}

// 抖音账号
export interface DouyinAccount {
  id: number
  openId: string
  advertiserId: string
  douyinId: string
  nickname: string
  avatar: string
  fansCount: number
  followingCount: number
  totalFavorited: number
  status: number
  dailyLimit: number
  balance: number
  couponCount: number
  remark: string
  companyName: string
  tokenExpiresAt: string
  createTime: string
  tokenExpiringSoon: boolean
}

// 视频信息
export interface VideoInfo {
  id: string
  itemId: string
  title: string
  coverUrl: string
  videoUrl: string
  duration: number
  playCount: number
  likeCount: number
  commentCount: number
  shareCount: number
  publishTime: string
}

// 投放任务
export interface DouplusTask {
  id: number
  accountId: number
  accountNickname: string
  accountAvatar: string
  itemId: string
  videoTitle: string
  videoCover: string
  videoCoverUrl: string
  taskType: number
  targetType: number
  wantType: string
  objective: string
  strategy: string
  duration: number
  budget: number
  actualCost: number
  expectedExposure: number
  actualExposure: number
  // 基础指标字段
  playCount: number          // 播放量
  likeCount: number          // 点赞量
  commentCount: number       // 评论量
  shareCount: number         // 转发量
  followCount: number        // 新增粉丝
  clickCount: number         // 点击量
  // 新增视频指标
  playDuration5sRank: number // 5秒完播率
  dyHomeVisited: number      // 主页访问次数
  dpTargetConvertCnt: number // 转化数
  customConvertCost: number  // 转化成本
  // 直播相关指标
  showCnt: number            // 直播间展示数
  liveClickSourceCnt: number // 直播间新增观看次数
  liveGiftUv: number         // 直播间打赏观看人数
  liveGiftAmount: number     // 直播间音浪收入
  liveCommentCnt: number     // 直播间评论次数
  douplusLiveFollowCount: number // 直播间新增粉丝数
  liveGiftCnt: number        // 直播间打赏次数
  // 任务状态
  status: string
  statusText: string
  orderId: string
  retryCount: number
  errorMsg: string
  scheduledTime: string
  executedTime: string
  completedTime: string
  orderEndTime: string     // 订单结束时间 = 生效时间 + 投放时长
  createTime: string
}

// 投放任务VO（视图对象）
export type DouplusTaskVO = DouplusTask

// 创建投放任务请求
export interface CreateTaskRequest {
  accountId: number
  targetAccountId?: number
  itemId: string
  taskType?: number
  targetType?: number
  wantType?: string
  objective?: string
  strategy?: string
  duration?: number
  budget: number
  count?: number
  scheduledTime?: string
  customTimeStart?: string
  customTimeEnd?: string
  targetConfig?: string | TargetConfig
  investPassword: string
}

// 定向配置
export interface TargetConfig {
  gender: string
  age: string[]
  crowd: string[]
  regionType: string
  regions: string[]
  interest: string[]
  similarFans: string
  industry: string[]
}

// 评论
export interface Comment {
  id: number
  accountId: number
  videoId: number
  itemId: string
  commentId: string
  content: string
  nickname: string
  avatar: string
  likeCount: number
  replyCount: number
  isTop: number
  status: number
  isNegative: number
  keywordHit: string
  commentTime: string
  createTime: string
}

// 黑名单/敏感词
export interface KeywordBlacklist {
  id: number
  userId: number
  keyword: string
  type: number
  autoDelete: number
  createTime: string
}
