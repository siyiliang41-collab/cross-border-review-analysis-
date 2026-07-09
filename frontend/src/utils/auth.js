// 认证工具 — token 存储/读取/清除
const KEY = 'bipt_auth'

export function getAuth() {
  try { return JSON.parse(localStorage.getItem(KEY)) || {} }
  catch { return {} }
}

export function setAuth(token, role, username) {
  localStorage.setItem(KEY, JSON.stringify({ token, role, username }))
}

export function clearAuth() {
  localStorage.removeItem(KEY)
}

export function isLoggedIn() {
  return !!getAuth().token
}

export function isAdmin() {
  return getAuth().role === 'admin'
}

export function getToken() {
  return getAuth().token || ''
}

export function getUsername() {
  return getAuth().username || ''
}
