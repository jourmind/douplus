import { get } from '@/utils/request'

export interface VideoInfo {
  id: string
  title: string
  coverUrl: string
  duration: number
  createTime: string
  playCount: number
  likeCount: number
  commentCount: number
  shareCount?: number
}

export interface VideoListResponse {
  list: VideoInfo[]
  total: number
  page: number
  pageSize: number
}

/**
 * 获取抖音账号的视频列表
 */
export const getVideoList = (accountId: number, page: number = 1, pageSize: number = 20) => {
  return get<VideoListResponse>(`/video/list/${accountId}`, { page, pageSize })
}