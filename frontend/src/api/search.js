import api from './axios'

export const searchApi = {
  /** Create a new search — POST /api/search/ */
  createSearch(query, platforms) {
    return api.post('search/', { query, platforms })
  },

  /** Get search status — GET /api/search/:id/ */
  getSearchStatus(id) {
    return api.get(`search/${id}/`)
  },

  /** Get paginated results — GET /api/search/:id/results/ */
  getResults(id, params = {}) {
    return api.get(`search/${id}/results/`, { params })
  },

  /** Get history (paginated list of searches) — GET /api/search/ */
  getHistory(page = 1) {
    return api.get('search/', { params: { page } })
  },

  /** Delete a search — DELETE /api/search/:id/ */
  deleteSearch(id) {
    return api.delete(`search/${id}/`)
  },

  /** Get PCA points — GET /api/search/:id/pca/ */
  getPCA(id) {
    return api.get(`search/${id}/pca/`)
  },

  /** Get association rules — GET /api/search/:id/rules/ */
  getRules(id) {
    return api.get(`search/${id}/rules/`)
  },

  /** Get a single item by its ID — GET /api/search/item/:itemId/ */
  getItem(itemId) {
    return api.get(`search/item/${itemId}/`)
  },
}
