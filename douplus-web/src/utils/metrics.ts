/**
 * 数据指标计算工具函数
 * 根据基础数据计算衍生指标
 */

import type { DouplusTask } from '@/api/types'

/**
 * 计算百播放量
 * 公式: (播放量 / 消耗) × 100
 * @param playCount 播放量
 * @param actualCost 实际消耗(元)
 * @returns 百播放量
 */
export function calculateHundredPlayRate(playCount: number, actualCost: number): number {
  if (!actualCost || actualCost === 0) return 0
  return (playCount / actualCost) * 100
}

/**
 * 计算百转发率
 * 公式: (转发 / 播放量) × 100
 * @param shareCount 转发数
 * @param playCount 播放量
 * @returns 百转发率(%)
 */
export function calculateHundredShareRate(shareCount: number, playCount: number): number {
  if (!playCount || playCount === 0) return 0
  return (shareCount / playCount) * 100
}

/**
 * 计算点赞比
 * 公式: 点赞 / 播放量
 * @param likeCount 点赞数
 * @param playCount 播放量
 * @returns 点赞比
 */
export function calculateLikeRate(likeCount: number, playCount: number): number {
  if (!playCount || playCount === 0) return 0
  return likeCount / playCount
}

/**
 * 计算转发比
 * 公式: 转发 / 播放量
 * @param shareCount 转发数
 * @param playCount 播放量
 * @returns 转发比
 */
export function calculateShareRate(shareCount: number, playCount: number): number {
  if (!playCount || playCount === 0) return 0
  return shareCount / playCount
}

/**
 * 扩展任务数据,添加计算指标
 * @param task 原始任务数据
 * @returns 包含计算指标的任务数据
 */
export interface DouplusTaskWithMetrics extends DouplusTask {
  // 计算指标
  hundredPlayRate: number    // 百播放量
  hundredShareRate: number   // 百转发率(%)
  likeRate: number          // 点赞比
  shareRate: number         // 转发比
}

/**
 * 为任务数据添加计算指标
 * @param task 原始任务数据
 * @returns 包含计算指标的任务数据
 */
export function enrichTaskWithMetrics(task: DouplusTask): DouplusTaskWithMetrics {
  const playCount = task.playCount || 0
  const actualCost = task.actualCost || 0
  const shareCount = task.shareCount || 0
  const likeCount = task.likeCount || 0

  return {
    ...task,
    hundredPlayRate: calculateHundredPlayRate(playCount, actualCost),
    hundredShareRate: calculateHundredShareRate(shareCount, playCount),
    likeRate: calculateLikeRate(likeCount, playCount),
    shareRate: calculateShareRate(shareCount, playCount)
  }
}

/**
 * 格式化百播放量显示
 * @param value 百播放量数值
 * @returns 格式化后的字符串
 */
export function formatHundredPlayRate(value: number): string {
  if (value === 0) return '-'
  return value.toFixed(2)
}

/**
 * 格式化百分比显示
 * @param value 百分比数值
 * @returns 格式化后的字符串(带%)
 */
export function formatPercentage(value: number): string {
  if (value === 0) return '-'
  return `${value.toFixed(2)}%`
}

/**
 * 格式化比率显示
 * @param value 比率数值
 * @returns 格式化后的字符串
 */
export function formatRate(value: number): string {
  if (value === 0) return '-'
  return value.toFixed(4)
}
