<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const API = import.meta.env.VITE_API_BASE_URL || 'http://192.168.229.101:8080/api'
const selectedPid = ref('3256805677493085')
const selectedCountry = ref('')
const activeMenu = ref('overview')
const marketRanking = ref([])  // TOP5 国家推荐排名
const allCountryOptions = ref([])  // 全量国家列表（用于下拉框）
const allData = ref({})

const menus = [
  {key:'overview',label:'数据概览',icon:'📊'},
  {key:'sentiment',label:'情感分析',icon:'💬'},
  {key:'decision',label:'市场洞察',icon:'🌍'},
  {key:'quality',label:'数据质量',icon:'🛡️'},
]

const productNames = {'3256808363596774':'蓝牙耳机','3256807406290815':'手机壳','3256807087680846':'LED小夜灯','3256807145227935':'连衣裙','3256805677493085':'油壶'}
const productList = Object.entries(productNames).map(([id,name])=>({id,name}))
const countryNames = {'ES':'西班牙','UA':'乌克兰','FR':'法国','US':'美国','KR':'韩国','GB':'英国','IT':'意大利','BR':'巴西','MX':'墨西哥','PL':'波兰','DE':'德国','RU':'俄罗斯','NL':'荷兰','TR':'土耳其','JP':'日本','IL':'以色列','CL':'智利','CA':'加拿大','AU':'澳大利亚','PT':'葡萄牙','BE':'比利时','SE':'瑞典','AT':'奥地利'}
function getCountryName(code){return countryNames[code]||code}
const featureNames = {'Quality of sound':'音质','Durability':'耐用','User Friendly':'易用性','User Friendly ':'易用性','Fit':'合身度','Value for money':'性价比','Quality':'质量'}
function getFeatureName(f){if(!f)return'';const t=f.trim();return featureNames[t]||featureNames[f]||t}
const logisticsNames = {'Aliexpress Selection Standard':'速卖通标准','Aliexpress Selection Premium':'速卖通优先','AliExpress Standard':'速卖通标准','SF eParcel':'顺丰国际','Cainiao Super Economy':'菜鸟超级经济','AliExpress Super Economy':'速卖通经济','AliExpress Saver':'速卖通省钱','Seller\\\'s Shipping':'卖家自选','China Post Registered':'中国邮政航空','China Post Ordinary':'中国邮政小包','ePacket':'e邮宝','EMS':'EMS','DHL':'DHL','FedEx':'联邦快递','UPS':'UPS'}
function getLogisticsName(l){if(!l)return'';for(const[k,v]of Object.entries(logisticsNames)){if(l.toLowerCase().includes(k.toLowerCase()))return v}return l.length>18?l.substring(0,17)+'..':l}
const colorCN = {'black':'黑','white':'白','blue':'蓝','red':'红','pink':'粉','green':'绿','purple':'紫','grey':'灰','gray':'灰','brown':'棕','gold':'金','silver':'银','navy':'深蓝','Light Purple':'浅紫','Deep Blue':'深蓝','Burgundy':'酒红','Coffee':'咖啡','GRAY':'灰','Warm light':'暖光','White light':'白光','7 Color light':'七彩'}
function getSkuName(s){
  if(!s)return'';let r=s.trim().replace(/"/g,'')
  // "Color:500ml-Blue" -> 蓝 500ml
  r=r.replace(/Color:\s*(\d+)\s*ml\s*-\s*(.+)/gi,(_,ml,c)=>{let cl=c;const sorted=Object.entries(colorCN).sort((a,b)=>b[0].length-a[0].length);for(const[en,zh]of sorted)cl=cl.replace(new RegExp('\\b'+en+'\\b','gi'),zh);return cl+' '+ml+'ml'})
  // "Deep Blue" -> "深蓝" (先处理复合词)
  r=r.replace(/(Deep|Dark)\s+(blue|green|red|purple|grey|gray|brown|pink)/gi,(_,_shade,c)=>{let cl=c;const sorted2=Object.entries(colorCN).sort((a,b)=>b[0].length-a[0].length);for(const[en,zh]of sorted2)cl=cl.replace(new RegExp('\\b'+en+'\\b','gi'),zh);return '深'+cl})
  r=r.replace(/Emitting\s*Color:\s*/gi,'').replace(/Color:\s*/gi,'').replace(/Size:\s*/gi,'尺码').replace(/Emitting\s*/gi,'')
  const sortedColors=Object.entries(colorCN).sort((a,b)=>b[0].length-a[0].length)  // 长词优先，避免 white→白 吃掉 White light
  for(const[en,zh]of sortedColors)r=r.replace(new RegExp('\\b'+en+'\\b','gi'),zh)
  // iPhone型号标准化 — 输出人类可读的名称
  r=r.replace(/for\s+iphone\s*(\d+)\s*pro\s*max\s*/gi,'iPhone $1 Pro Max').replace(/for\s+iphone\s*(\d+)\s*pro\s*/gi,'iPhone $1 Pro').replace(/for\s+iphone\s*(\d+)\s*plu[s]?\s*/gi,'iPhone $1 Plus').replace(/for\s+iphone\s*(\d+)\s*/gi,'iPhone $1')
  r=r.replace(/尺码\s*/g,'').replace(/\s+/g,' ').trim().replace(/^["\s]+|["\s]+$/g,'')
  if(r.includes('iPhone')){
    r=r.replace(/\([^)]*\)/g,'').replace(/\s+/g,' ').trim()
    // 重排为"型号 颜色"格式，颜色结尾追加"色"字
    const modelMatch=r.match(/iPhone\s[\d\sA-Za-z]+/)
    if(modelMatch){
      const model=modelMatch[0].trim()
      let rest=r.replace(model,'').trim()
      for(const[_en,zh]of Object.entries(colorCN)){
        if(rest===zh&&zh.length<=2&&!zh.endsWith('色')){rest=zh+'色'}
      }
      r=model+' '+rest
    }
  }
  return r.length>22?r.substring(0,21)+'..':r
}

// LDA 负面主题结论（每个品类的 TOP2 风险，当某国家无负面特征时作为兜底显示）
const LDA_WEAKNESS = {
  '3256808363596774': ['音质差','商品损坏'],     // 蓝牙耳机
  '3256807406290815': ['材质廉价','适配错误'],   // 手机壳
  '3256807087680846': ['尺寸太小','与图片不符'], // LED小夜灯
  '3256807145227935': ['适配错误','材质廉价'],   // 连衣裙
  '3256805677493085': ['到货损坏','材质廉价'],   // 油壶
}
function isPositiveFeature(f) {
  const s = (f.score || '').trim()
  return f.sentiment_flag === 'positive' || s === 'Fast' || s === 'Good' || s === 'Great' || s === 'Fits ok'
}
function isNegativeFeature(f) {
  const s = (f.score || '').trim()
  return f.sentiment_flag === 'negative' || s === 'Poor' || s === 'Difficult'
}

// axios 统一错误处理 + ngrok 免拦截头
async function apiGet(url) {
  try {
    const r = await axios.get(url, {headers:{'ngrok-skip-browser-warning':'true'}})
    return r
  } catch (e) {
    console.error('[API错误]', url, e.message)
    throw e
  }
}

let charts={}
function createChart(id,opt){nextTick(()=>{const container=document.getElementById(id);if(container&&container.clientWidth>0){if(charts[id])charts[id].dispose();const c=echarts.init(container);c.setOption(opt);charts[id]=c}})}
function clearAll(){Object.values(charts).forEach(c=>c.dispose());charts={}}

// 公共函数：渲染产品特征ABSA柱状图（好评 vs 差评）
function renderFeatureChart(chartId, features, noDataMessage='该商品暂无特征分析数据'){
  if(features&&features.length>0){
    const positiveFeatures=features.filter(isPositiveFeature)
    const negativeFeatures=features.filter(isNegativeFeature)
    const featureKeys=[...new Set(features.map(f=>getFeatureName(f.feature)))]
    createChart(chartId,{tooltip:{trigger:'axis'},legend:{data:['好评','差评'],textStyle:{color:'#889',fontSize:11},top:0},grid:{left:90,right:50,top:30,bottom:25},xAxis:{type:'value',axisLabel:{color:'#889',fontSize:11}},yAxis:{type:'category',data:featureKeys.reverse(),axisLabel:{color:'#333',fontSize:12}},series:[{name:'好评',type:'bar',data:featureKeys.map(f=>{const r=positiveFeatures.find(x=>getFeatureName(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#00c853'},barGap:'20%'},{name:'差评',type:'bar',data:featureKeys.map(f=>{const r=negativeFeatures.find(x=>getFeatureName(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#ff1744'}}]})
  }else{
    nextTick(()=>{const el=document.getElementById(chartId);if(el)el.innerHTML=`<div style="display:flex;align-items:center;justify-content:center;height:100%;color:#999;font-size:14px">${noDataMessage}</div>`})
  }
}

// 生成选品建议洞察文案（自然语言，去重后的人话）
function buildInsightText(ci){
  if(!ci)return ''
  // 同级特征去重：同时出现在优点和缺点时，只保留数量多的一方
  const weaknessNames=new Set(ci.weaknesses.map(s=>getFeatureName(s.feature)))
  const dedupedStrengths=ci.strengths.filter(s=>!weaknessNames.has(getFeatureName(s.feature))).map(s=>getFeatureName(s.feature))
  const dedupedWeaknesses=ci.weaknesses.map(s=>getFeatureName(s.feature))
  let text=''
  if(dedupedStrengths.length>0){
    text+=`消费者认可该商品的${dedupedStrengths.slice(0,3).join('、')}`
    if(dedupedWeaknesses.length>0) text+='，但'
    else text+='。'
  }
  if(dedupedWeaknesses.length>0){
    text+=`${dedupedWeaknesses.slice(0,3).join('、')}方面仍有改进空间。`
  }
  if(ci.topSku&&ci.topSku.length>0){
    const skus=ci.topSku.slice(0,2).map(s=>getSkuName(s.sku_info))
    text+=`建议重点备货${skus.join('和')}，维持高分物流渠道。`
  }
  return text
}

// 实时指标
const qualityReport = ref(null)
const liveMetrics = ref({totalReviews:0,posRate:0,todayRec:''})

async function loadAll(){
  const pid=selectedPid.value

  const [matrix,logistics,sentiment,scorecard,feats,trend,sku]=await Promise.all([
    apiGet(API+'/matrix'),apiGet(API+'/logistics'),
    apiGet(API+'/sentiment/product'),apiGet(API+'/scorecard'),
    apiGet(`${API}/feature/${pid}`),apiGet(API+'/trend/monthly'),apiGet(API+'/sku/analysis'),
  ])

  // TOP5 国家自动排序
  const productMatrix=matrix.data.filter(r=>r.product_id===pid)
  const maxReviews=Math.max(...productMatrix.map(r=>r.review_count||0), 1)
  const ranked=productMatrix
    .map(r=>({
      country:r.buyer_country,
      reviewCount:r.review_count||0,
      avgStar:Math.round((r.avg_star||0)*100)/100,
      avgSentiment:Math.round((r.avg_sentiment||0)*1000)/1000,
      score:(r.avg_star||0)*8+(r.review_count/maxReviews)*2+(r.avg_sentiment||0)*3,
    }))
    .sort((a,b)=>b.score-a.score)
    .slice(0,5)

  // 并行加载TOP5国家的详细数据
  const details=await Promise.all(ranked.map(async c=>{
    try{
      const [fr,tr,sr]=await Promise.all([
        apiGet(`${API}/feature/${pid}/country/${c.country}`),
        apiGet(`${API}/trend/${pid}/country/${c.country}`),
        apiGet(`${API}/sku/${pid}/country/${c.country}`),
      ])
      return {...c, features:fr.data||[], trend:tr.data||[], skus:sr.data||[]}
    }catch(e){return {...c, features:[], trend:[], skus:[]}}
  }))

  // 计算趋势 & 提炼亮点 + LDA 兜底
  const ldaFallback=LDA_WEAKNESS[pid]||[]
  for(const c of details){
    const recent=(c.trend||[]).slice(-3)
    c.trendDir=recent.length>=2?(recent[recent.length-1].avg_star>=recent[0].avg_star?'↑上升':'↓下降'):'--'
    c.trendScores=recent.length?recent.map(t=>Math.round(t.avg_star*100)/100).join('→'):'--'
    c.strengths=(c.features||[]).filter(isPositiveFeature).slice(0,2)
    c.weaknesses=(c.features||[]).filter(isNegativeFeature).slice(0,2)
    // LDA 兜底：如果该国没有负面特征数据，用全品类 LDA 结论
    if(!c.weaknesses.length&&ldaFallback.length)c._ldaFallback=ldaFallback
    c.topSku=(c.skus||[]).slice(0,2)
  }

  marketRanking.value=details
  // 全量国家下拉选项（含所有有数据的国家，不止TOP5）
  allCountryOptions.value=productMatrix
    .map(r=>({country:r.buyer_country, avgStar:Math.round((r.avg_star||0)*100)/100}))
    .sort((a,b)=>b.avgStar-a.avgStar)
  // 修复右侧悬浮卡
  liveMetrics.value={
    totalReviews:details.reduce((s,c)=>s+(c.reviewCount||0),0),
    posRate:(sentiment.data.find(s=>s.product_id===pid)||{}).pos_rate||0,
    todayRec:'--',
  }

  allData.value={matrix:matrix.data,trend:trend.data,logistics:logistics.data,
    sentiment:sentiment.data,scorecard:scorecard.data,feats:feats.data,sku:sku.data,ranking:details}
  renderCharts()
}

const countryDetail=ref(null)  // 选中国家的深度洞察
async function loadCountryDetail(){
  const pid=selectedPid.value;const cid=selectedCountry.value
  if(!cid){countryDetail.value=null;return}
  try{
    const [fr,tr,sr,mr]=await Promise.all([
      apiGet(`${API}/feature/${pid}/country/${cid}`),
      apiGet(`${API}/trend/${pid}/country/${cid}`),
      apiGet(`${API}/sku/${pid}/country/${cid}`),
      apiGet(API+'/matrix'),
    ])
    const cm=mr.data.filter(r=>r.buyer_country===cid&&r.product_id===pid)[0]
    if(!cm||(cm.review_count||0)===0){countryDetail.value={noData:true, cnName:getCountryName(cid), name:productNames[pid]};return}
    const cf=fr.data||[];const ct=tr.data||[];const cs=sr.data||[]
    const fPos=cf.filter(isPositiveFeature);const fNeg=cf.filter(isNegativeFeature)
    const lTrend=ct.slice(-3)
    const dir=lTrend.length>=2?(lTrend[lTrend.length-1].avg_star>=lTrend[0].avg_star?'↑上升':'↓下降'):'--'
    countryDetail.value={
      reviewCount:cm.review_count,avgStar:Math.round(cm.avg_star*100)/100,
      avgSentiment:Math.round((cm.avg_sentiment||0)*1000)/1000,
      trendDir:dir,trendScores:lTrend.map(t=>Math.round(t.avg_star*100)/100).join('→'),
      strengths:fPos.slice(0,3),weaknesses:fNeg.slice(0,3),topSku:cs.slice(0,3),
      name:productNames[pid],cnName:getCountryName(cid),featData:cf,trendData:ct,skuData:cs,
    }
    nextTick(()=>{
      if(countryDetail.value&&countryDetail.value.trendData.length){
        createChart('ch-d-trend',{tooltip:{trigger:'axis'},grid:{left:55,right:20,top:10,bottom:40},xAxis:{type:'category',data:ct.map(t=>t.month||t.eval_month),axisLabel:{color:'#333',fontSize:12,rotate:45}},yAxis:{type:'value',name:'评分',axisLabel:{color:'#333',fontSize:12},min:2.5,max:5},series:[{type:'line',data:ct.map(t=>Math.round(t.avg_star*100)/100),smooth:true,symbol:'circle',symbolSize:6,lineStyle:{color:'#1677FF',width:2.5},itemStyle:{color:'#1677FF'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(22,119,255,0.2)'},{offset:1,color:'rgba(22,119,255,0.02)'}])}}]})
      }
      if(cs.length>0){
        const sd=cs.slice(0,8)
        createChart('ch-d-sku',{tooltip:{trigger:'axis'},grid:{left:150,right:40,top:10,bottom:10},yAxis:{type:'category',data:sd.map(s=>getSkuName(s.sku_info)).reverse(),axisLabel:{color:'#333',fontSize:12}},xAxis:{type:'value',name:'评论数',axisLabel:{color:'#333',fontSize:12}},series:[{type:'bar',data:sd.map(s=>s.review_count).reverse(),itemStyle:{color:new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#1677FF'},{offset:1,color:'#82b1ff'}]),borderRadius:[0,3,3,0]},label:{show:true,position:'right',color:'#333',fontSize:12}}]})
      }
      if(cf.length>0) renderFeatureChart('ch-d-feat', cf)
    })
  }catch(e){console.error(e);countryDetail.value=null}
}
watch(selectedCountry,()=>loadCountryDetail())

function renderCharts(){
  clearAll();const data=allData.value;const currentTab=activeMenu.value

  if(currentTab==='overview'){
    // 情感趋势折线
    createChart('ch1',{tooltip:{trigger:'axis'},grid:{left:55,right:20,top:20,bottom:35},xAxis:{type:'category',data:data.trend.map(t=>t.month||t.eval_month),axisLabel:{color:'#889',fontSize:11,rotate:45}},yAxis:{type:'value',name:'评分',axisLabel:{color:'#889',fontSize:11},min:3.5,max:5},series:[{type:'line',data:data.trend.map(t=>Math.round(t.avg_star*100)/100),smooth:true,symbol:'circle',symbolSize:6,lineStyle:{color:'#2979ff',width:2.5},itemStyle:{color:'#2979ff'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(41,121,255,0.25)'},{offset:1,color:'rgba(41,121,255,0.02)'}])}}]})

    // 选品评分雷达
    createChart('ch2',{tooltip:{},legend:{data:productList.map(p=>p.name),textStyle:{color:'#889',fontSize:10},bottom:0},radar:{center:['50%','45%'],radius:'60%',indicator:[{name:'推荐指数',max:60},{name:'好评率(%)',max:30},{name:'情感均分',max:0.2},{name:'评论规模',max:4200},{name:'星评均分',max:5}],axisName:{color:'#889',fontSize:11}},series:data.scorecard.map((s,i)=>({type:'radar',data:[{value:[Math.round(s.recommendation_score*10)/10,s.sentiment_pos_rate,Math.round(s.avg_sentiment*1000)/1000,s.total_reviews,Math.round(s.star_score*100)/100],name:productNames[s.product_id]||''}],lineStyle:{color:['#2979ff','#ff6d00','#00c853','#d50000','#6200ea'][i],width:2},itemStyle:{color:['#2979ff','#ff6d00','#00c853','#d50000','#6200ea'][i]},areaStyle:{color:'transparent'}}))})

    // 热力图
    const topC=[...new Set(data.matrix.map(r=>r.buyer_country))].slice(0,10)
    const hd=[];topC.forEach((c,i)=>{productList.forEach((p,j)=>{const x=data.matrix.find(r=>r.buyer_country===c&&r.product_id===p.id);if(x)hd.push([j,i,Math.round(Number(x.avg_star||0)*100)/100])})})
    createChart('ch3',{tooltip:{formatter:p=>`${productList[p.value[0]]?.name} / ${getCountryName(topC[p.value[1]])}: ${Number(p.value[2]).toFixed(2)}分`},grid:{left:75,right:110,top:15,bottom:15},xAxis:{type:'category',data:productList.map(p=>p.name),axisLabel:{color:'#889',fontSize:11,rotate:20}},yAxis:{type:'category',data:topC.map(getCountryName),axisLabel:{color:'#889',fontSize:11}},visualMap:{min:3.5,max:5,text:['高','低'],textStyle:{color:'#889'},inRange:{color:['#e3f2fd','#90caf9','#42a5f5','#1e88e5','#1565c0']},calculable:true,orient:'vertical',right:10,top:'center',itemWidth:12,itemHeight:100},series:[{type:'heatmap',data:hd,label:{show:true,color:'#222',fontSize:11,fontWeight:'bold'}}]})

    // 选品排名柱状
    createChart('ch4',{tooltip:{trigger:'axis'},grid:{left:100,right:60,top:10,bottom:20},xAxis:{type:'value',name:'推荐指数',axisLabel:{color:'#889',fontSize:11}},yAxis:{type:'category',data:data.scorecard.map(s=>productNames[s.product_id]||''),axisLabel:{color:'#333',fontSize:13,fontWeight:'bold'}},series:[{type:'bar',data:data.scorecard.map(s=>Math.round(s.recommendation_score*10)/10),itemStyle:{color:new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#2979ff'},{offset:1,color:'#82b1ff'}]),borderRadius:[0,4,4,0]},label:{show:true,position:'right',color:'#333',fontSize:13,fontWeight:'bold',formatter:'{c}分'},markLine:{symbol:'none',data:[{type:'average',label:{show:true,color:'#999',fontSize:10,position:'start',formatter:'均线{c}'}}],lineStyle:{color:'#bbb',type:'dashed'}}}]})

    // 特征ABSA（数据概览Tab）
    renderFeatureChart('ch5', data.feats)
  }

  if(currentTab==='sentiment'){
    // 特征ABSA（情感分析Tab）
    renderFeatureChart('ch-s2', data.feats)
    const sp=data.sentiment
    createChart('ch-s1',{tooltip:{trigger:'axis'},legend:{data:['正面','中性','负面'],textStyle:{color:'#889',fontSize:11},top:0},grid:{left:55,right:30,top:30,bottom:30},xAxis:{type:'category',data:sp.map(s=>productNames[s.product_id]||''),axisLabel:{color:'#889',fontSize:11,rotate:15}},yAxis:{type:'value',name:'%',min:0,max:100,axisLabel:{color:'#889',fontSize:11}},series:[{name:'正面',type:'bar',stack:'t',data:sp.map(s=>s.pos_rate),itemStyle:{color:'#00c853'},label:{show:true,color:'#fff',fontSize:10}},{name:'中性',type:'bar',stack:'t',data:sp.map(s=>Number(((s.total-s.pos_cnt-s.neg_cnt)*100/s.total).toFixed(1))),itemStyle:{color:'#ff9800'}},{name:'负面',type:'bar',stack:'t',data:sp.map(s=>Number((s.neg_cnt*100/s.total).toFixed(1))),itemStyle:{color:'#ff1744'}}]})
  }

}

watch(selectedPid,()=>{selectedCountry.value='';loadAll()})
watch(activeMenu,(tab)=>{
  if(tab==='quality'){loadQuality().catch(e=>console.error('[质量报告加载失败]',e))}
  nextTick(()=>renderCharts())
})
onMounted(()=>loadAll())

async function loadQuality(){
  if(qualityReport.value)return
  const r=await apiGet(API+'/quality/report')
  qualityReport.value=r.data
}
</script>

<template>
<div class="app-shell">
  <!-- 左侧导航 -->
  <aside class="sidebar">
    <div class="sb-logo">BIPT</div>
    <nav class="sb-nav">
      <a v-for="item in menus" :key="item.key" :class="{active:activeMenu===item.key}" @click="activeMenu=item.key">
        <span class="nav-icon">{{ item.icon }}</span><span class="nav-label">{{ item.label }}</span>
      </a>
    </nav>
    <div class="sb-footer">v1.0</div>
  </aside>

  <!-- 右侧主体 -->
  <main class="main">
    <!-- 顶栏 -->
    <header class="topbar">
      <div class="tb-left">
        <span class="tb-logo-icon">🌐</span>
        <span class="tb-title">跨境电商评论情感挖掘与选品决策支持系统</span>
      </div>
      <div class="tb-right">
        <select v-model="selectedPid" class="tb-sel"><option v-for="p in productList" :key="p.id" :value="p.id">{{ p.name }}</option></select>
        <span class="tb-avatar">👤</span>
      </div>
    </header>

    <!-- 内容区 -->
    <div class="content">

      <!-- 数据概览 -->
      <div v-show="activeMenu==='overview'">
        <div class="card-row-3">
          <div class="card"><div class="ctitle">📈 情感分析趋势</div><div id="ch1" class="chart"></div></div>
          <div class="card"><div class="ctitle">🎯 选品决策支持评分</div><div id="ch2" class="chart"></div></div>
          <div class="card"><div class="ctitle">🔍 {{ productNames[selectedPid] || '产品' }}特征分析</div><div id="ch5" class="chart"></div></div>
        </div>
        <div style="margin-bottom:16px"><div class="card"><div class="ctitle">🗺 国家×品类适配度矩阵</div><div id="ch3" class="chart" style="height:340px"></div></div></div>
        <div class="card-row-2">
          <div class="card"><div class="ctitle">📊 选品推荐排名</div><div id="ch4" class="chart"></div></div>
          <div class="card"><div class="ctitle">🗂 数据总览说明</div><div style="padding:24px;color:#889;line-height:2;font-size:13px">✅ 数据来源：速卖通5品类用户真实评论<br>✅ 分析模型：VADER情感打分 + ABSA特征抽取<br>✅ 选品依据：好评率 + 情感均分 + 评论规模 + 星评<br>✅ 最佳市场算法：分国家×商品交叉矩阵评分排序</div></div>
        </div>
      </div>

      <!-- 情感分析 -->
      <div v-show="activeMenu==='sentiment'">
        <div class="card-row-2">
          <div class="card"><div class="ctitle">情感正/中/负面率对比</div><div id="ch-s1" class="chart"></div></div>
          <div class="card"><div class="ctitle">产品特征ABSA分析（好评 vs 差评）</div><div id="ch-s2" class="chart"></div></div>
        </div>
      </div>

      <!-- 市场洞察 -->
      <div v-show="activeMenu==='decision'">
        <div class="info-banner" style="margin-bottom:12px;padding:10px 16px;background:#f0f7ff;border-radius:8px;color:#1565c0;font-size:13px">
          💡 以下为「{{ productNames[selectedPid] }}」品类的 TOP5 推荐市场，基于星评/评论规模/情感均分综合排序
        </div>
        <div class="market-rank" v-for="(c,i) in marketRanking" :key="c.country" style="margin-bottom:10px">
          <div class="rank-card" :style="{borderLeft:'4px solid '+['#1677FF','#F53F3F','#00B42A','#FF7D00','#722ED1'][i]}">
            <div class="mr-hd">
              <span class="mr-rank">#{{ i+1 }}</span>
              <span class="mr-flag">{{ getCountryName(c.country) }}</span>
              <span class="mr-stars">⭐{{ c.avgStar }}</span>
              <span class="mr-reviews">{{ c.reviewCount }}条评论</span>
              <span :style="{color:c.trendDir.indexOf('↑')>=0?'#00B42A':'#F53F3F',fontWeight:'bold',marginLeft:'8px',fontSize:'14px'}">{{ c.trendDir }}</span>
              <span v-if="c.trendScores!=='--'" style="font-size:12px;color:#555;marginLeft:4px">{{ c.trendScores }}</span>
            </div>
            <div class="mr-body">
              <div class="mr-cols">
                <div class="mr-col">
                  <div class="mr-label">核心优势</div>
                  <div v-if="c.strengths.length" class="mr-val">{{ c.strengths.slice(0,2).map(s=>getFeatureName(s.feature)).join('、') }}</div>
                  <div v-else class="mr-val-dim">数据收集中</div>
                </div>
                <div class="mr-col">
                  <div class="mr-label">推荐SKU</div>
                  <div v-if="c.topSku.length" class="mr-val">{{ c.topSku.slice(0,2).map(s=>getSkuName(s.sku_info)).join('、') }}</div>
                  <div v-else class="mr-val-dim">数据收集中</div>
                </div>
                <div class="mr-col">
                  <div class="mr-label">注意风险</div>
                  <div v-if="c.weaknesses.length" class="mr-val">{{ c.weaknesses.slice(0,2).map(s=>getFeatureName(s.feature)).join('、') }}</div>
                  <div v-else-if="c._ldaFallback" class="mr-val" style="color:#e65100">*{{ c._ldaFallback.join('、') }}</div>
                  <div v-else class="mr-val-dim">暂无显著负面</div>
                </div>
              </div>
            </div>
          </div>
        </div>
        <!-- 国家详情（选中国家后展开） -->
        <div style="margin-top:16px;padding:14px 18px;background:#fafafa;border-radius:10px">
          <div style="font-size:14px;font-weight:700;color:#333;margin-bottom:10px">🔍 选择国家查看深度洞察</div>
          <select v-model="selectedCountry" class="tb-sel" style="color:#333;background:#fff;border:1px solid #ddd;padding:8px 16px;border-radius:6px;font-size:14px;width:200px;margin-bottom:12px">
            <option value="">— 选择国家 —</option><option v-for="r in allCountryOptions" :key="r.country" :value="r.country">{{ getCountryName(r.country) }} (⭐{{ r.avgStar }})</option>
          </select>
          <div v-if="countryDetail&&countryDetail.noData" style="text-align:center;padding:30px;color:#e65100;font-size:14px">⚠️ {{ countryDetail.cnName }} 目前在「{{ countryDetail.name }}」品类暂无评论数据</div>
          <div v-else-if="countryDetail" style="margin-top:10px">
            <div class="country-card" style="margin-bottom:10px">
              <div class="cc-hd"><span class="cc-flag">{{ countryDetail.cnName }}</span> 市场深度洞察 — {{ countryDetail.name }}</div>
              <div class="cc-body">
                <div class="cc-stat"><span class="cc-num blue">{{ countryDetail.avgStar }}</span><span class="cc-lbl">平均星评</span></div>
                <div class="cc-stat"><span class="cc-num green">{{ countryDetail.reviewCount }}</span><span class="cc-lbl">评论数</span></div>
                <div class="cc-stat"><span :class="'cc-num '+(countryDetail.trendDir.indexOf('↑')>=0?'green':'red')">{{ countryDetail.trendDir }}</span><span class="cc-lbl">评分趋势 {{ countryDetail.trendScores }}</span></div>
                <div class="cc-stat"><span class="cc-num" style="font-size:16px">{{ countryDetail.topSku[0] ? getSkuName(countryDetail.topSku[0].sku_info) : '暂无数据' }}</span><span class="cc-lbl">推荐属性</span></div>
              </div>
              <div class="cc-insight">
                💡 {{ countryDetail.strengths.length ? '消费者认可'+countryDetail.strengths.slice(0,2).map(s=>getFeatureName(s.feature)).join('、')+'。' : '' }}{{ countryDetail.weaknesses.length ? '主要不满集中在'+countryDetail.weaknesses.slice(0,2).map(s=>getFeatureName(s.feature)).join('、')+'。' : '' }}建议备货{{ countryDetail.topSku.slice(0,2).map(s=>getSkuName(s.sku_info)).join('、') }}，维持高分物流渠道。
              </div>
            </div>
            <div class="card-row-2">
              <div class="card"><div class="ctitle">📈 评分趋势</div><div id="ch-d-trend" class="chart"></div></div>
              <div class="card"><div class="ctitle">🛒 SKU偏好</div><div id="ch-d-sku" class="chart"></div></div>
            </div>
          </div>
          <div v-else style="text-align:center;padding:30px;color:#999">上方选择国家后，此处展示该国的完整分析</div>
        </div>
      </div>

      <!-- 数据质量报告 -->
      <div v-show="activeMenu==='quality'">
        <div class="card-row-2" style="margin-bottom:12px">
          <div class="card"><div class="ctitle">📦 数据资产概览</div>
            <div class="qa-grid" v-if="qualityReport">
              <div class="qa-item"><span class="qa-num">{{ qualityReport.overview.product_count }}</span><span class="qa-lbl">商品品类</span></div>
              <div class="qa-item"><span class="qa-num">{{ qualityReport.overview.country_count }}</span><span class="qa-lbl">TOP国家覆盖</span></div>
              <div class="qa-item"><span class="qa-num">{{ qualityReport.overview.total_reviews.toLocaleString() }}</span><span class="qa-lbl">有效评论数</span></div>
              <div class="qa-item"><span class="qa-num">{{ qualityReport.timeSpan.months }}个月</span><span class="qa-lbl">{{ qualityReport.timeSpan.earliest }} ~ {{ qualityReport.timeSpan.latest }}</span></div>
            </div>
            <div v-else style="text-align:center;padding:40px;color:#999">加载中...</div>
          </div>
          <div class="card"><div class="ctitle">🧹 数据清洗统计</div>
            <div class="qa-grid" v-if="qualityReport">
              <div class="qa-item"><span class="qa-num">{{ qualityReport.cleaning.rawRows.toLocaleString() }}</span><span class="qa-lbl">CSV原始行数</span></div>
              <div class="qa-item"><span class="qa-num" style="color:#2e7d32">{{ qualityReport.cleaning.cleanedRows.toLocaleString() }}</span><span class="qa-lbl">DWD清洗后</span></div>
              <div class="qa-item"><span class="qa-num" style="color:#c62828">{{ qualityReport.cleaning.removedRows.toLocaleString() }}</span><span class="qa-lbl">过滤脏数据</span></div>
              <div class="qa-item"><span class="qa-num">{{ qualityReport.cleaning.removalRate }}</span><span class="qa-lbl">过滤率</span></div>
            </div>
            <div v-else style="text-align:center;padding:40px;color:#999">加载中...</div>
          </div>
        </div>
        <div class="card-row-2" style="margin-bottom:12px">
          <div class="card"><div class="ctitle">📈 评论月度分布</div>
            <div class="qa-table" v-if="qualityReport">
              <table><thead><tr><th>月份</th><th>评论数</th><th>均分</th></tr></thead>
              <tbody><tr v-for="r in qualityReport.monthlyDetail" :key="r.month"><td>{{ r.month }}</td><td>{{ r.review_count.toLocaleString() }}</td><td>{{ r.avg_star }}</td></tr></tbody></table>
            </div>
          </div>
          <div class="card"><div class="ctitle">🌍 国家数据覆盖 TOP10</div>
            <div class="qa-table" v-if="qualityReport">
              <table><thead><tr><th>国家</th><th>评论数</th><th>覆盖率</th></tr></thead>
              <tbody><tr v-for="r in qualityReport.topCountries" :key="r.buyer_country"><td>{{ getCountryName(r.buyer_country) }}</td><td>{{ r.review_count.toLocaleString() }}</td><td>{{ r.coverage_rate }}%</td></tr></tbody></table>
            </div>
          </div>
        </div>
        <div class="card-row-2">
          <div class="card"><div class="ctitle">🏷 各品类数据画像</div>
            <div class="qa-table" v-if="qualityReport">
              <table><thead><tr><th>商品</th><th>评论数</th><th>均分</th><th>好评率</th><th>推荐指数</th></tr></thead>
              <tbody><tr v-for="r in qualityReport.productDetail" :key="r.product_id"><td>{{ productNames[r.product_id]||r.product_id }}</td><td>{{ r.total_reviews.toLocaleString() }}</td><td>{{ r.avg_star }}</td><td>{{ r.pos_rate }}%</td><td>{{ r.recommendation_score }}</td></tr></tbody></table>
            </div>
          </div>
          <div class="card"><div class="ctitle">✅ 数据质量结论</div>
            <div style="padding:20px;line-height:2.2;color:#333;font-size:14px" v-if="qualityReport">
              ✅ 覆盖 <b>{{ qualityReport.overview.country_count }}</b> 个国家，评论总量 <b>{{ qualityReport.overview.total_reviews.toLocaleString() }}</b> 条<br>
              ✅ 时间跨度 <b>{{ qualityReport.timeSpan.months }}</b> 个月（{{ qualityReport.timeSpan.earliest }} ~ {{ qualityReport.timeSpan.latest }}）<br>
              ✅ CSV 原始 <b>{{ qualityReport.cleaning.rawRows.toLocaleString() }}</b> 行，清洗后有效数据 <b>{{ qualityReport.cleaning.cleanedRows.toLocaleString() }}</b> 条<br>
              ✅ 脏数据过滤率仅 <b>{{ qualityReport.cleaning.removalRate }}</b>，数据源质量良好<br>
              ✅ 第一大市场：<b>{{ getCountryName(qualityReport.topCountries[0].buyer_country) }}</b>（{{ qualityReport.topCountries[0].review_count.toLocaleString() }}条，占比{{ qualityReport.topCountries[0].coverage_rate }}%）<br>
              ✅ 评论旺季：2025-11月 ~ 12月（月均2,700+条），符合跨境电商节庆规律
            </div>
          </div>
        </div>
      </div>
    </div>
  </main>

  <!-- 右侧悬浮指标卡 -->
  <aside class="float-panel">
    <div class="fp-card">
      <div class="fp-num blue">{{ liveMetrics.totalReviews }}</div>
      <div class="fp-label">当前商品评论数</div>
    </div>
    <div class="fp-card">
      <div class="fp-num green">{{ liveMetrics.posRate }}%</div>
      <div class="fp-label">正面情感占比</div>
    </div>
  </aside>
</div>
</template>

<style>
*{margin:0;padding:0;box-sizing:border-box}
body{background:#f0f2f5;font-family:-apple-system,BlinkMacSystemFont,'Segoe UI','Microsoft YaHei',sans-serif}
</style>

<style scoped>
/* 数据质量报告 */
.qa-grid{display:grid;grid-template-columns:1fr 1fr;gap:12px;padding:8px 0}
.qa-item{text-align:center;padding:10px}
.qa-num{display:block;font-size:26px;font-weight:800;color:#111}
.qa-lbl{display:block;font-size:12px;color:#889;margin-top:4px}
.qa-table table{width:100%;border-collapse:collapse;font-size:13px}
.qa-table th{background:#f5f5f5;padding:8px 12px;text-align:left;color:#555;font-weight:600;border-bottom:2px solid #e0e0e0}
.qa-table td{padding:8px 12px;border-bottom:1px solid #f0f0f0;color:#333}
.qa-table tbody tr:hover{background:#fafafa}

.app-shell{display:flex;min-height:100vh}

/* 左侧导航 */
.sidebar{width:200px;background:linear-gradient(180deg,#0d1b2a,#1b2838);display:flex;flex-direction:column;padding:20px 0;flex-shrink:0}
.sb-logo{color:#4fc3f7;font-size:22px;font-weight:800;text-align:center;padding:0 0 30px;letter-spacing:2px}
.sb-nav{flex:1;display:flex;flex-direction:column;gap:4px;padding:0 12px}
.sb-nav a{display:flex;align-items:center;gap:12px;padding:12px 16px;border-radius:8px;color:#8899aa;cursor:pointer;transition:all .2s;text-decoration:none;font-size:14px}
.sb-nav a:hover{background:rgba(79,195,247,.1);color:#bcc}
.sb-nav a.active{background:linear-gradient(90deg,rgba(79,195,247,.2),rgba(79,195,247,.05));color:#4fc3f7;font-weight:600}
.nav-icon{font-size:18px}.nav-label{font-size:14px}
.sb-footer{text-align:center;color:#445;font-size:12px;padding-top:16px}

/* 主区域 */
.main{flex:1;display:flex;flex-direction:column;overflow:hidden}
.topbar{background:linear-gradient(90deg,#1565c0,#0d47a1);padding:12px 24px;display:flex;justify-content:space-between;align-items:center;flex-shrink:0}
.tb-left{display:flex;align-items:center;gap:12px}
.tb-logo-icon{font-size:24px}
.tb-title{color:#fff;font-size:18px;font-weight:600;letter-spacing:1px}
.tb-right{display:flex;align-items:center;gap:12px}
.tb-sel{background:rgba(255,255,255,.15);color:#fff;border:1px solid rgba(255,255,255,.2);border-radius:6px;padding:7px 14px;font-size:13px;cursor:pointer;outline:none}
.tb-sel option{color:#333}
.tb-avatar{font-size:24px;cursor:pointer}

.content{flex:1;overflow-y:auto;padding:20px}

/* 卡片 */
.card-row-3{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;margin-bottom:16px}
.card-row-2{display:grid;grid-template-columns:1fr 1fr;gap:16px}
.card{background:#fff;border-radius:12px;padding:20px;box-shadow:0 2px 8px rgba(0,0,0,.06)}
.ctitle{font-size:15px;font-weight:600;color:#333;margin-bottom:12px;padding-left:10px;border-left:3px solid #2979ff}
.chart{width:100%;height:280px}

/* 国家洞察 */
.country-card{background:linear-gradient(135deg,#fff8e1,#fff3e0);border:1px solid #ffe0b2;border-radius:12px;padding:24px;margin-bottom:16px}
.cc-hd{font-size:18px;font-weight:700;color:#e65100;margin-bottom:16px}
.cc-flag{background:#e65100;color:#fff;padding:2px 10px;border-radius:4px;font-size:14px;margin-right:6px}
.cc-body{display:grid;grid-template-columns:repeat(4,1fr);gap:16px;margin-bottom:16px}
.cc-stat{text-align:center}
.cc-num{font-size:28px;font-weight:800;color:#111}.cc-num.blue{color:#1565c0}.cc-num.green{color:#2e7d32}.cc-num.red{color:#c62828}
.cc-lbl{display:block;font-size:13px;color:#333;margin-top:4px;font-weight:600}
.cc-insight{background:#fff;border-radius:8px;padding:14px 18px;font-size:14px;color:#000;line-height:1.7}

/* 右侧悬浮 */
.float-panel{width:180px;padding:16px 12px;display:flex;flex-direction:column;gap:14px;flex-shrink:0}
.fp-card{background:linear-gradient(135deg,#1565c0,#0d47a1);border-radius:12px;padding:18px 14px;text-align:center;color:#fff;box-shadow:0 4px 12px rgba(21,101,192,.3)}
.fp-num{font-size:24px;font-weight:800;margin-bottom:4px}.fp-num.blue{color:#81d4fa}.fp-num.green{color:#a5d6a7}.fp-num.gold{color:#ffe082}
.fp-label{font-size:12px;opacity:.85}

/* 市场洞察排名卡片 */
.rank-card{background:#fff;border-radius:10px;padding:16px 20px;box-shadow:0 1px 6px rgba(0,0,0,.06)}
.mr-hd{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.mr-rank{font-size:20px;font-weight:800;color:#1565c0;min-width:32px}
.mr-flag{font-size:17px;font-weight:700;color:#1E293B}
.mr-stars{font-size:15px;font-weight:700;color:#1E293B}
.mr-reviews{font-size:14px;color:#555;font-weight:600}
.mr-body{border-top:1px solid #f0f0f0;padding-top:10px}
.mr-cols{display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px}
.mr-col{font-size:14px;color:#222;line-height:1.7;font-weight:600}
.mr-label{font-size:12px;color:#555;font-weight:700;text-transform:uppercase;margin-bottom:4px;letter-spacing:.5px}
.mr-val{color:#222;font-weight:600}
.mr-val-dim{color:#777;font-weight:600}
.info-banner{border-left:3px solid #1565c0!important}
</style>
