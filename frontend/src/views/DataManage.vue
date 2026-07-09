<script setup>
import { ref, reactive, onMounted } from 'vue'
import axios from 'axios'
import { ElMessage, ElMessageBox } from 'element-plus'
import { Search, Refresh, Plus, Edit, Delete } from '@element-plus/icons-vue'

const API = import.meta.env.VITE_API_BASE_URL || '/api'

// 商品 & 国家映射（复用 App.vue 中的映射表）
const productNames = { '3256808363596774': '蓝牙耳机', '3256807406290815': '手机壳', '3256807087680846': 'LED小夜灯', '3256807145227935': '连衣裙', '3256805677493085': '油壶' }
const countryNames = { 'ES': '西班牙', 'UA': '乌克兰', 'FR': '法国', 'US': '美国', 'KR': '韩国', 'GB': '英国', 'IT': '意大利', 'BR': '巴西', 'MX': '墨西哥', 'PL': '波兰', 'DE': '德国', 'RU': '俄罗斯', 'NL': '荷兰', 'TR': '土耳其', 'JP': '日本', 'IL': '以色列', 'CL': '智利', 'CA': '加拿大', 'AU': '澳大利亚', 'PT': '葡萄牙', 'BE': '比利时', 'SE': '瑞典', 'AT': '奥地利' }
function getCountryName(code) { return countryNames[code] || code }

// ===== 搜索条件 =====
const searchForm = reactive({ keyword: '', productId: '', country: '' })
const productOptions = Object.entries(productNames).map(([id, name]) => ({ value: id, label: name }))
const countryOptions = Object.entries(countryNames).map(([code, name]) => ({ value: code, label: `${name} (${code})` }))

// ===== 分页 =====
const pagination = reactive({ page: 1, size: 20, total: 0 })

// ===== 表格数据 =====
const tableData = ref([])
const loading = ref(false)

// ===== 编辑弹窗 =====
const dialogVisible = ref(false)
const dialogTitle = ref('新增评论')
const isEdit = ref(false)
const formData = reactive({
  evaluationId: '', productId: '', buyerCountry: '', buyerName: '',
  starRating: '', feedbackTranslated: '', evalDate: '', skuInfo: '', logistics: '',
  buyerEval: '', feedback: '', hasImage: 0, hasFollowUp: 0,
})

// ===== 加载数据 =====
async function loadData() {
  loading.value = true
  try {
    const params = { page: pagination.page, size: pagination.size }
    if (searchForm.keyword) params.keyword = searchForm.keyword
    if (searchForm.productId) params.productId = searchForm.productId
    if (searchForm.country) params.country = searchForm.country
    const r = await axios.get(API + '/crud/reviews', { params, headers: { 'ngrok-skip-browser-warning': 'true' } })
    tableData.value = r.data.data || []
    pagination.total = r.data.total || 0
  } catch (e) {
    ElMessage.error('数据加载失败: ' + (e.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

// ===== 搜索 & 重置 =====
function handleSearch() { pagination.page = 1; loadData() }
function handleReset() { searchForm.keyword = ''; searchForm.productId = ''; searchForm.country = ''; pagination.page = 1; loadData() }
function handlePageChange(page) { pagination.page = page; loadData() }
function handleSizeChange(size) { pagination.size = size; pagination.page = 1; loadData() }

// ===== 新增 =====
function handleAdd() {
  isEdit.value = false
  dialogTitle.value = '新增评论'
  Object.keys(formData).forEach(k => formData[k] = '')
  formData.hasImage = 0; formData.hasFollowUp = 0
  dialogVisible.value = true
}

// ===== 编辑 =====
function handleEdit(row) {
  isEdit.value = true
  dialogTitle.value = '编辑评论 (' + row.evaluationId + ')'
  Object.assign(formData, {
    evaluationId: row.evaluationId, productId: row.productId, buyerCountry: row.buyerCountry,
    buyerName: row.buyerName, starRating: row.starRating, feedbackTranslated: row.feedbackTranslated,
    evalDate: row.evalDate, skuInfo: row.skuInfo, logistics: row.logistics,
    buyerEval: row.buyerEval, feedback: row.feedback,
    hasImage: row.hasImage || 0, hasFollowUp: row.hasFollowUp || 0,
  })
  dialogVisible.value = true
}

// ===== 提交 =====
async function handleSubmit() {
  if (!formData.evaluationId) { ElMessage.warning('评价ID不能为空'); return }
  try {
    if (isEdit.value) {
      await axios.put(API + '/crud/reviews/' + formData.evaluationId, formData, { headers: { 'ngrok-skip-browser-warning': 'true' } })
      ElMessage.success('更新成功')
    } else {
      await axios.post(API + '/crud/reviews', formData, { headers: { 'ngrok-skip-browser-warning': 'true' } })
      ElMessage.success('新增成功')
    }
    dialogVisible.value = false
    loadData()
  } catch (e) {
    ElMessage.error('操作失败: ' + (e.response?.data?.message || e.message))
  }
}

// ===== 删除 =====
function handleDelete(row) {
  ElMessageBox.confirm(
    `确定删除评价 ${row.evaluationId} 吗？此操作不可恢复。`,
    '删除确认',
    { confirmButtonText: '确定', cancelButtonText: '取消', type: 'warning' }
  ).then(async () => {
    try {
      await axios.delete(API + '/crud/reviews/' + row.evaluationId, { headers: { 'ngrok-skip-browser-warning': 'true' } })
      ElMessage.success('删除成功')
      loadData()
    } catch (e) {
      ElMessage.error('删除失败: ' + (e.response?.data?.message || e.message))
    }
  }).catch(() => { /* 用户取消 */ })
}

// ===== 格式化 =====
function fmtStar(val) { return val != null ? Number(val).toFixed(1) : '-' }
function fmtDate(val) { return val || '-' }
function truncate(val, max = 60) { if (!val) return '-'; return val.length > max ? val.substring(0, max) + '…' : val }

onMounted(() => loadData())
</script>

<template>
<div class="dm-root">
  <!-- 标题行 -->
  <div class="dm-header">
    <h2 class="dm-title">评论数据管理</h2>
    <span class="dm-subtitle">支持增删改查 + 关键词搜索 + 分页浏览</span>
  </div>

  <!-- 搜索栏 -->
  <div class="dm-search-bar">
    <el-input v-model="searchForm.keyword" placeholder="搜索评论文本（英文）…" clearable style="width:280px" :prefix-icon="Search" @keyup.enter="handleSearch" />
    <el-select v-model="searchForm.productId" placeholder="全部品类" clearable style="width:160px">
      <el-option v-for="p in productOptions" :key="p.value" :label="p.label" :value="p.value" />
    </el-select>
    <el-select v-model="searchForm.country" placeholder="全部国家" clearable filterable style="width:180px">
      <el-option v-for="c in countryOptions" :key="c.value" :label="c.label" :value="c.value" />
    </el-select>
    <el-button type="primary" :icon="Search" @click="handleSearch">搜索</el-button>
    <el-button :icon="Refresh" @click="handleReset">重置</el-button>
    <el-button type="success" :icon="Plus" @click="handleAdd" style="margin-left:auto">新增评论</el-button>
  </div>

  <!-- 数据表格 -->
  <el-table :data="tableData" v-loading="loading" stripe border style="width:100%" max-height="560">
    <el-table-column prop="evaluationId" label="评价ID" width="170" fixed />
    <el-table-column prop="productId" label="商品" width="110">
      <template #default="{row}">{{ productNames[row.productId] || row.productId?.substring(0,10) }}</template>
    </el-table-column>
    <el-table-column prop="buyerCountry" label="国家" width="80">
      <template #default="{row}">{{ getCountryName(row.buyerCountry) }}</template>
    </el-table-column>
    <el-table-column prop="starRating" label="星评" width="70" align="center">
      <template #default="{row}">
        <span :style="{color:row.starRating>=4?'#2e7d32':row.starRating>=3?'#e65100':'#c62828',fontWeight:'bold'}">{{ fmtStar(row.starRating) }}</span>
      </template>
    </el-table-column>
    <el-table-column prop="feedbackTranslated" label="评论内容（英文翻译）" min-width="280" show-overflow-tooltip>
      <template #default="{row}">{{ truncate(row.feedbackTranslated, 80) }}</template>
    </el-table-column>
    <el-table-column prop="evalDate" label="日期" width="110" :formatter="r=>fmtDate(r.evalDate)" />
    <el-table-column prop="skuInfo" label="SKU" width="160" show-overflow-tooltip />
    <el-table-column prop="logistics" label="物流" width="140" show-overflow-tooltip />
    <el-table-column label="操作" width="150" fixed="right" align="center">
      <template #default="{row}">
        <el-button type="primary" link :icon="Edit" @click="handleEdit(row)">编辑</el-button>
        <el-button type="danger" link :icon="Delete" @click="handleDelete(row)">删除</el-button>
      </template>
    </el-table-column>
  </el-table>

  <!-- 分页 -->
  <div class="dm-pagination">
    <span class="dm-total">共 {{ pagination.total.toLocaleString() }} 条</span>
    <el-pagination
      v-model:current-page="pagination.page"
      v-model:page-size="pagination.size"
      :page-sizes="[10, 20, 50, 100]"
      :total="pagination.total"
      layout="sizes, prev, pager, next, jumper"
      background
      @current-change="handlePageChange"
      @size-change="handleSizeChange"
    />
  </div>

  <!-- 新增/编辑弹窗 -->
  <el-dialog v-model="dialogVisible" :title="dialogTitle" width="650px" top="5vh" destroy-on-close>
    <el-form :model="formData" label-width="120px" label-position="right">
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="评价ID" required>
            <el-input v-model="formData.evaluationId" :disabled="isEdit" placeholder="速卖通 evaluationId" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="商品ID">
            <el-select v-model="formData.productId" style="width:100%">
              <el-option v-for="p in productOptions" :key="p.value" :label="p.label" :value="p.value" />
            </el-select>
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="买家国家">
            <el-select v-model="formData.buyerCountry" style="width:100%" filterable>
              <el-option v-for="c in countryOptions" :key="c.value" :label="c.label" :value="c.value" />
            </el-select>
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="星评 (0-5)">
            <el-input-number v-model="formData.starRating" :min="0" :max="5" :precision="1" :step="0.5" style="width:100%" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="评价日期">
            <el-input v-model="formData.evalDate" placeholder="如 10 Nov 2025" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="买家昵称">
            <el-input v-model="formData.buyerName" placeholder="买家昵称" />
          </el-form-item>
        </el-col>
      </el-row>
      <el-form-item label="SKU信息">
        <el-input v-model="formData.skuInfo" placeholder="如 Color:black" />
      </el-form-item>
      <el-form-item label="物流方式">
        <el-input v-model="formData.logistics" placeholder="如 Aliexpress Selection Standard" />
      </el-form-item>
      <el-form-item label="评论内容（英文）">
        <el-input v-model="formData.feedbackTranslated" type="textarea" :rows="3" placeholder="英文翻译评论文本" />
      </el-form-item>
      <el-row :gutter="16">
        <el-col :span="12">
          <el-form-item label="带图">
            <el-switch v-model="formData.hasImage" :active-value="1" :inactive-value="0" />
          </el-form-item>
        </el-col>
        <el-col :span="12">
          <el-form-item label="追评">
            <el-switch v-model="formData.hasFollowUp" :active-value="1" :inactive-value="0" />
          </el-form-item>
        </el-col>
      </el-row>
    </el-form>
    <template #footer>
      <el-button @click="dialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleSubmit">确定</el-button>
    </template>
  </el-dialog>
</div>
</template>

<style scoped>
.dm-root { padding: 8px 0; }
.dm-header { margin-bottom: 16px; }
.dm-title { display: inline-block; font-size: 20px; font-weight: 700; color: #1E293B; margin: 0 12px 0 0; }
.dm-subtitle { font-size: 13px; color: #889; }

.dm-search-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 14px; flex-wrap: wrap; }

.dm-pagination { display: flex; align-items: center; justify-content: space-between; margin-top: 14px; }
.dm-total { font-size: 13px; color: #666; }
</style>
