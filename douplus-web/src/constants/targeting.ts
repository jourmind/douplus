/**
 * DOU+投放定向常量配置
 */

// 我想要 - 投放类型
export const WANT_TYPES = [
  { value: 'CONTENT_HEAT', label: '内容加热', icon: 'Promotion' },
  { value: 'FANS', label: '粉丝经营', icon: 'User' },
  { value: 'CUSTOMER', label: '获取客户', icon: 'Avatar' },
  { value: 'PRODUCT', label: '商品营销', icon: 'ShoppingCart' },
  { value: 'APP', label: '应用营销', icon: 'Monitor' }
]

// 更想获得什么 - 投放目标
export const OBJECTIVES = [
  { value: 'LIKE_COMMENT', label: '点赞评论量', icon: 'ChatDotRound', color: '#ff6b35' },
  { value: 'QUALITY_INTERACT', label: '高质量互动', icon: 'Connection', color: '#909399' },
  { value: 'HOME_VIEW', label: '主页浏览量', icon: 'House', color: '#909399' },
  { value: 'LINK_CLICK', label: '评论链接点击', icon: 'Link', color: '#909399' },
  { value: 'VIDEO_PLAY', label: '视频播放量', icon: 'VideoPlay', color: '#909399' },
  { value: 'LIVE_POPULARITY', label: '直播间人气', icon: 'Mic', color: '#909399' }
]

// 投放时长选项
export const DURATION_OPTIONS = [
  { value: 2, label: '2小时' },
  { value: 6, label: '6小时' },
  { value: 12, label: '12小时' },
  { value: 18, label: '18小时' },
  { value: 24, label: '24小时' },
  { value: 0, label: '自定义' }
]

// 投放金额选项
export const BUDGET_OPTIONS = [
  { value: 100, label: '¥ 100' },
  { value: 200, label: '¥ 200' },
  { value: 300, label: '¥ 300' },
  { value: 500, label: '¥ 500' },
  { value: 1000, label: '¥ 1000' },
  { value: 0, label: '自定义' }
]

// 投放策略 - 根据目标不同显示不同选项
export const STRATEGIES = {
  // 默认策略（点赞评论量、高质量互动）
  DEFAULT: [
    { value: 'GUARANTEE_PLAY', label: '保证播放量' },
    { value: 'MAX_LIKE_COMMENT', label: '最大点赞评论量' }
  ],
  // 主页浏览量
  HOME_VIEW: [
    { value: 'GUARANTEE_PLAY', label: '保证播放量' },
    { value: 'MAX_HOME_VIEW', label: '最大进入主页量' }
  ],
  // 评论链接点击
  LINK_CLICK: [
    { value: 'GUARANTEE_PLAY', label: '保证播放量' },
    { value: 'MAX_LINK_CLICK', label: '最大链接点击量' }
  ],
  // 直播间人气
  LIVE_POPULARITY: [
    { value: 'GUARANTEE_PLAY', label: '保证播放量' },
    { value: 'MAX_LIVE_VIEW', label: '最大进入直播间量' }
  ]
}

// 获取目标对应的策略选项
export function getStrategiesByObjective(objective: string) {
  switch (objective) {
    case 'HOME_VIEW':
      return STRATEGIES.HOME_VIEW
    case 'LINK_CLICK':
      return STRATEGIES.LINK_CLICK
    case 'LIVE_POPULARITY':
      return STRATEGIES.LIVE_POPULARITY
    case 'VIDEO_PLAY':
      return [] // 视频播放量目标不显示策略选项
    default:
      return STRATEGIES.DEFAULT
  }
}

// 判断是否显示播放量保障（只有视频播放量目标显示）
export function showPlayGuarantee(objective: string) {
  return objective === 'VIDEO_PLAY'
}

// 投放给谁
export const AUDIENCE_TYPES = [
  { value: 'SMART', label: '智能投放' },
  { value: 'CUSTOM', label: '自定义人群' }
]

// 性别选项
export const GENDER_OPTIONS = [
  { value: 'ALL', label: '不限' },
  { value: 'MALE', label: '男' },
  { value: 'FEMALE', label: '女' }
]

// 年龄段选项
export const AGE_OPTIONS = [
  { value: 'ALL', label: '不限' },
  { value: '18-23', label: '18-23岁' },
  { value: '24-30', label: '24-30岁' },
  { value: '31-40', label: '31-40岁' },
  { value: '41-50', label: '41-50岁' },
  { value: '50+', label: '50岁以上' }
]

// 八大人群选项
export const CROWD_OPTIONS = [
  { value: 'ALL', label: '不限' },
  { value: 'TOWN_YOUTH', label: '小镇青年' },
  { value: 'TOWN_ELDER', label: '小镇中老年' },
  { value: 'GEN_Z', label: 'Z世代' },
  { value: 'URBAN_WORKER', label: '都市蓝领' },
  { value: 'REFINED_MOM', label: '精致妈妈' },
  { value: 'NEW_WHITE', label: '新锐白领' },
  { value: 'SENIOR_MIDDLE', label: '资深中产' },
  { value: 'URBAN_SILVER', label: '都市银发' }
]

// 地域类型
export const REGION_TYPES = [
  { value: 'ALL', label: '不限' },
  { value: 'PROVINCE', label: '按省市' },
  { value: 'DISTRICT', label: '按区县' },
  { value: 'NEARBY', label: '按附近区域' }
]

// 兴趣分类
export const INTEREST_OPTIONS = [
  { value: 'ENTERTAINMENT', label: '娱乐' },
  { value: 'GAME', label: '游戏' },
  { value: 'FOOD', label: '美食' },
  { value: 'TRAVEL', label: '旅游' },
  { value: 'SPORTS', label: '运动健身' },
  { value: 'BEAUTY', label: '美妆' },
  { value: 'FASHION', label: '时尚' },
  { value: 'TECH', label: '科技数码' },
  { value: 'CAR', label: '汽车' },
  { value: 'EDUCATION', label: '教育' },
  { value: 'PARENTING', label: '母婴亲子' },
  { value: 'PET', label: '宠物' },
  { value: 'HOME', label: '家居' },
  { value: 'FINANCE', label: '金融理财' }
]

// 达人相似粉丝
export const SIMILAR_FANS_OPTIONS = [
  { value: 'ALL', label: '不限' },
  { value: 'MORE', label: '更多' }
]

// 行业潜在购买人群
export const INDUSTRY_OPTIONS = [
  { value: 'ALL', label: '不限' },
  { value: '3C', label: '3C及电器' },
  { value: 'FOOD', label: '食品饮料' },
  { value: 'CLOTHING', label: '服装配饰' },
  { value: 'HOME', label: '家居建材' },
  { value: 'CAR', label: '汽车' },
  { value: 'BEAUTY', label: '美妆' },
  { value: 'HEALTH', label: '医疗健康' },
  { value: 'EDUCATION', label: '教育培训' },
  { value: 'FINANCE', label: '金融服务' },
  { value: 'GAME', label: '游戏' }
]

// 省份数据
export const PROVINCES = [
  { value: 'beijing', label: '北京' },
  { value: 'shanghai', label: '上海' },
  { value: 'guangdong', label: '广东' },
  { value: 'jiangsu', label: '江苏' },
  { value: 'zhejiang', label: '浙江' },
  { value: 'shandong', label: '山东' },
  { value: 'henan', label: '河南' },
  { value: 'sichuan', label: '四川' },
  { value: 'hubei', label: '湖北' },
  { value: 'hunan', label: '湖南' },
  { value: 'fujian', label: '福建' },
  { value: 'anhui', label: '安徽' },
  { value: 'hebei', label: '河北' },
  { value: 'shaanxi', label: '陕西' },
  { value: 'liaoning', label: '辽宁' },
  { value: 'jiangxi', label: '江西' },
  { value: 'chongqing', label: '重庆' },
  { value: 'yunnan', label: '云南' },
  { value: 'guangxi', label: '广西' },
  { value: 'shanxi', label: '山西' },
  { value: 'guizhou', label: '贵州' },
  { value: 'heilongjiang', label: '黑龙江' },
  { value: 'jilin', label: '吉林' },
  { value: 'gansu', label: '甘肃' },
  { value: 'neimenggu', label: '内蒙古' },
  { value: 'xinjiang', label: '新疆' },
  { value: 'tianjin', label: '天津' },
  { value: 'hainan', label: '海南' },
  { value: 'ningxia', label: '宁夏' },
  { value: 'qinghai', label: '青海' },
  { value: 'xizang', label: '西藏' }
]

// 预估提升计算（与抖音官方一致）
export function estimateExposure(budget: number, duration: number, objective: string) {
  // 视频播放量目标：每100元约5000播放量
  if (objective === 'VIDEO_PLAY') {
    const basePlayPerHundred = 5000
    let durationFactor = 1
    if (duration <= 2) durationFactor = 0.6
    else if (duration <= 6) durationFactor = 1.0
    else if (duration <= 12) durationFactor = 1.4
    else if (duration <= 18) durationFactor = 1.7
    else if (duration <= 24) durationFactor = 2.0
    else durationFactor = 2.0 + (duration - 24) / 48
    
    const basePlay = (budget / 100) * basePlayPerHundred * durationFactor
    return {
      type: 'play',
      label: '预计提升播放量(仅供参考)',
      value: Math.floor(basePlay / 100) * 100,
      showGuarantee: true,
      isRange: false
    }
  }
  
  // 其他目标：显示转化数范围
  // 根据目标不同，转化率不同
  let conversionRate = { min: 0.02, max: 0.04 } // 默认2-4%
  
  switch (objective) {
    case 'LIKE_COMMENT':
      conversionRate = { min: 0.03, max: 0.05 } // 点赞评论3-5%
      break
    case 'QUALITY_INTERACT':
      conversionRate = { min: 0.02, max: 0.04 } // 高质量互动2-4%
      break
    case 'HOME_VIEW':
      conversionRate = { min: 0.018, max: 0.034 } // 主页浏览1.8-3.4%
      break
    case 'LINK_CLICK':
      conversionRate = { min: 0.01, max: 0.02 } // 链接点击1-2%
      break
    case 'LIVE_POPULARITY':
      conversionRate = { min: 0.015, max: 0.03 } // 直播间人气1.5-3%
      break
  }
  
  // 基础曝光量计算
  const baseExposure = budget * 50 // 约50曝光/元
  let durationFactor = 1
  if (duration <= 2) durationFactor = 0.6
  else if (duration <= 6) durationFactor = 1.0
  else if (duration <= 12) durationFactor = 1.4
  else if (duration <= 24) durationFactor = 1.8
  else durationFactor = 2.0
  
  const exposure = baseExposure * durationFactor
  
  return {
    type: 'conversion',
    label: '预计提升转化数(仅供参考)',
    min: Math.floor(exposure * conversionRate.min),
    max: Math.floor(exposure * conversionRate.max),
    showGuarantee: false,
    isRange: true
  }
}
