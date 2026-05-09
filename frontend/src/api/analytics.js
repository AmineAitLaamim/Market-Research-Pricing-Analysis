import api from './axios'

export const analyticsApi = {
  searchProducts(q) {
    return api.get(`analytics/products/`, { params: { q } })
  },

  getRecentProducts() {
    return api.get(`analytics/products/`, { params: { q: '' } })
  },

  getTopDrops() {
    return api.get(`analytics/top-drops/`)
  },

  getProductHistory(normalizedTitle, platform) {
    return api.get(`analytics/product-history/`, { params: { title: normalizedTitle, platform } })
  },

  getSimilarProducts(normalizedTitle, platform) {
    return api.get(`analytics/similar/`, { params: { title: normalizedTitle, platform } })
  },

  setThreshold(normalizedTitle, platform, thresholdMad) {
    return api.post(`analytics/threshold/`, {
      normalized_title: normalizedTitle,
      platform,
      threshold_mad: thresholdMad,
    })
  },
}
