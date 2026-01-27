/**
 * URL工具函数
 */

/**
 * 将HTTP URL转换为HTTPS
 * 用于解决Mixed Content问题（HTTPS页面加载HTTP资源）
 * 
 * @param url - 原始URL
 * @returns 转换后的HTTPS URL
 */
export function convertToHttps(url: string | null | undefined): string {
  if (!url) {
    return ''
  }
  
  // 如果是HTTP协议，转换为HTTPS
  if (url.startsWith('http://')) {
    return url.replace('http://', 'https://')
  }
  
  // 如果是协议相对URL（//开头），添加https:
  if (url.startsWith('//')) {
    return 'https:' + url
  }
  
  return url
}

/**
 * 批量转换对象中的URL字段为HTTPS
 * 
 * @param obj - 包含URL字段的对象
 * @param urlFields - 需要转换的字段名数组
 * @returns 转换后的对象
 */
export function convertObjectUrls<T extends Record<string, any>>(
  obj: T,
  urlFields: (keyof T)[]
): T {
  const result = { ...obj }
  
  for (const field of urlFields) {
    if (typeof result[field] === 'string') {
      result[field] = convertToHttps(result[field] as string) as any
    }
  }
  
  return result
}

/**
 * 批量转换数组中对象的URL字段为HTTPS
 * 
 * @param arr - 对象数组
 * @param urlFields - 需要转换的字段名数组
 * @returns 转换后的数组
 */
export function convertArrayUrls<T extends Record<string, any>>(
  arr: T[],
  urlFields: (keyof T)[]
): T[] {
  return arr.map(item => convertObjectUrls(item, urlFields))
}
