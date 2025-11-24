import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:5001/api'

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
})

// 헬스 체크
export const healthCheck = () => api.get('/health').then(res => res.data)

// 인증 관련
export const login = (username, password) => api.post('/auth/login', { username, password }).then(res => res.data)
export const logout = () => api.post('/auth/logout').then(res => res.data)
export const checkAuth = () => api.get('/auth/check').then(res => res.data)
export const changeCredentials = (data) => api.post('/auth/change-credentials', data).then(res => res.data)

// 캠핑장 관리
export const getCampingSites = () => api.get('/camping-sites').then(res => res.data)
export const createCampingSite = (data) => api.post('/camping-sites', data).then(res => res.data)
export const updateCampingSite = (id, data) => api.put(`/camping-sites/${id}`, data).then(res => res.data)
export const deleteCampingSite = (id) => api.delete(`/camping-sites/${id}`).then(res => res.data)

// 캠핑장 계정 관리
export const getSiteAccounts = (siteId) => api.get(`/camping-sites/${siteId}/accounts`).then(res => res.data)
export const createSiteAccount = (siteId, data) => api.post(`/camping-sites/${siteId}/accounts`, data).then(res => res.data)
export const updateSiteAccount = (siteId, accountId, data) => api.put(`/camping-sites/${siteId}/accounts/${accountId}`, data).then(res => res.data)
export const deleteSiteAccount = (siteId, accountId) => api.delete(`/camping-sites/${siteId}/accounts/${accountId}`).then(res => res.data)
export const toggleSiteAccount = (siteId, accountId) => api.post(`/camping-sites/${siteId}/accounts/${accountId}/toggle`).then(res => res.data)

// 모니터링 관리
export const getMonitoringTargets = () => api.get('/monitoring/targets').then(res => res.data)
export const createMonitoringTarget = (data) => api.post('/monitoring/targets', data).then(res => res.data)
export const startMonitoring = () => api.post('/monitoring/start').then(res => res.data)
export const stopMonitoring = () => api.post('/monitoring/stop').then(res => res.data)
export const getMonitoringStatus = () => api.get('/monitoring/status').then(res => res.data)

// 스케줄 관리
export const getSchedules = () => api.get('/monitoring/schedules').then(res => res.data)
export const createSchedule = (data) => api.post('/monitoring/schedule', data).then(res => res.data)
export const deleteSchedule = (jobId) => api.delete(`/monitoring/schedule/${jobId}`).then(res => res.data)
export const getServerTimeInfo = () => api.get('/monitoring/server-time').then(res => res.data)

// 예약 관리
export const getReservations = () => api.get('/reservations').then(res => res.data)
export const getReservation = (id) => api.get(`/reservations/${id}`).then(res => res.data)
export const createReservation = (data) => api.post('/reservations', data).then(res => res.data)
export const createMultiAccountReservation = (data) => api.post('/reservations/multi-account', data).then(res => res.data)

// 통계
export const getStatistics = () => api.get('/statistics').then(res => res.data)

// XTicket 좌석 조회
export const getXTicketSites = (targetDate, productGroupCode = '0004') =>
  api.post('/xticket/sites', { target_date: targetDate, product_group_code: productGroupCode }).then(res => res.data)

export default {
  healthCheck,
  getCampingSites,
  createCampingSite,
  deleteCampingSite,
  getSiteAccounts,
  createSiteAccount,
  updateSiteAccount,
  deleteSiteAccount,
  toggleSiteAccount,
  getMonitoringTargets,
  createMonitoringTarget,
  startMonitoring,
  stopMonitoring,
  getMonitoringStatus,
  getReservations,
  getReservation,
  createReservation,
  createMultiAccountReservation,
  getStatistics,
  getXTicketSites
}
