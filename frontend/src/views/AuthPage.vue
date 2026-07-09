<script setup>
import { ref } from 'vue'
import axios from 'axios'
import { setAuth } from '../utils/auth.js'
import { ElMessage } from 'element-plus'

const API = import.meta.env.VITE_API_BASE_URL || '/api'
const emit = defineEmits(['login'])

const isLogin = ref(true)
const loading = ref(false)
const form = ref({ username: '', password: '', confirmPassword: '' })

async function submit() {
  const { username, password, confirmPassword } = form.value
  if (!username.trim() || !password.trim()) {
    ElMessage.warning('用户名和密码不能为空')
    return
  }
  if (!isLogin.value && password !== confirmPassword) {
    ElMessage.warning('两次密码不一致')
    return
  }
  loading.value = true
  try {
    const url = isLogin.value ? '/auth/login' : '/auth/register'
    const r = await axios.post(API + url, { username: username.trim(), password })
    if (r.data.code === 200) {
      setAuth(r.data.token, r.data.role, r.data.username)
      ElMessage.success(isLogin.value ? '登录成功' : '注册成功')
      emit('login')
    } else {
      ElMessage.error(r.data.message || '操作失败')
    }
  } catch (e) {
    ElMessage.error(e.response?.data?.message || '网络错误')
  } finally {
    loading.value = false
  }
}
</script>

<template>
<div class="auth-page">
  <div class="auth-card">
    <h1 class="auth-title">跨境电商评论分析系统</h1>
    <p class="auth-sub">{{ isLogin ? '登录' : '注册' }}账号</p>

    <el-form @keyup.enter="submit" size="large">
      <el-form-item>
        <el-input v-model="form.username" placeholder="用户名" clearable />
      </el-form-item>
      <el-form-item>
        <el-input v-model="form.password" type="password" placeholder="密码" show-password />
      </el-form-item>
      <el-form-item v-if="!isLogin">
        <el-input v-model="form.confirmPassword" type="password" placeholder="确认密码" show-password />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="submit" style="width:100%">
          {{ isLogin ? '登 录' : '注 册' }}
        </el-button>
      </el-form-item>
    </el-form>

    <p class="auth-switch">
      {{ isLogin ? '没有账号？' : '已有账号？' }}
      <a @click="isLogin = !isLogin; form = { username: '', password: '', confirmPassword: '' }">
        {{ isLogin ? '去注册' : '去登录' }}
      </a>
    </p>
  </div>
</div>
</template>

<style scoped>
.auth-page{display:flex;align-items:center;justify-content:center;min-height:100vh;background:linear-gradient(135deg,#0d1b2a,#1b2838)}
.auth-card{width:400px;padding:40px;background:#fff;border-radius:16px;box-shadow:0 8px 32px rgba(0,0,0,.3)}
.auth-title{font-size:20px;font-weight:700;color:#1E293B;text-align:center;margin:0 0 4px}
.auth-sub{text-align:center;color:#889;font-size:14px;margin:0 0 28px}
.auth-switch{text-align:center;font-size:13px;color:#889;margin-top:16px}
.auth-switch a{color:#1565c0;cursor:pointer;font-weight:600}
</style>
