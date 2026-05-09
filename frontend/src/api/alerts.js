import api from './axios'

export const alertsApi = {
  /** GET /api/search/alerts/ */
  getAlerts() {
    return api.get('search/alerts/')
  },

  /** PATCH /api/search/alerts/{id}/read/ */
  markAlertRead(id) {
    return api.patch(`search/alerts/${id}/read/`)
  },

  /** PATCH /api/search/alerts/read-all/ */
  markAllRead() {
    return api.patch('search/alerts/read-all/')
  },
}
