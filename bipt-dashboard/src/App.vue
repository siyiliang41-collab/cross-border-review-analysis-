<script setup>
import { ref, watch, onMounted, nextTick } from 'vue'
import axios from 'axios'
import * as echarts from 'echarts'

const API = import.meta.env.VITE_API_BASE_URL || 'http://192.168.229.101:8080/api'
const selectedPid = ref('3256805677493085')
const selectedCountry = ref('')
const activeMenu = ref('overview')
const decision = ref(null)
const countryInsight = ref(null)
const td = ref({})

const menus = [
  {key:'overview',label:'数据概览',icon:'📊'},
  {key:'sentiment',label:'情感分析',icon:'💬'},
  {key:'decision',label:'选品建议',icon:'🎯'},
  {key:'history',label:'历史记录',icon:'📋'},
]

const productNames = {'3256808363596774':'蓝牙耳机','3256807406290815':'手机壳','3256807087680846':'LED小夜灯','3256807145227935':'连衣裙','3256805677493085':'油壶'}
const productList = Object.entries(productNames).map(([id,name])=>({id,name}))
const countryNames = {'ES':'西班牙','UA':'乌克兰','FR':'法国','US':'美国','KR':'韩国','GB':'英国','IT':'意大利','BR':'巴西','MX':'墨西哥','PL':'波兰','DE':'德国','RU':'俄罗斯','NL':'荷兰','TR':'土耳其','JP':'日本','IL':'以色列','CL':'智利','CA':'加拿大','AU':'澳大利亚','PT':'葡萄牙','BE':'比利时','SE':'瑞典','AT':'奥地利'}
function cn(c){return countryNames[c]||c}
const featureNames = {'Quality of sound':'音质','Durability':'耐用','User Friendly':'易用性','User Friendly ':'易用性','Fit':'合身度','Value for money':'性价比','Quality':'质量'}
function cnF(f){if(!f)return'';const t=f.trim();return featureNames[t]||featureNames[f]||t}
const logisticsNames = {'Aliexpress Selection Standard':'速卖通标准','Aliexpress Selection Premium':'速卖通优先','AliExpress Standard':'速卖通标准','SF eParcel':'顺丰国际','Cainiao Super Economy':'菜鸟超级经济','AliExpress Super Economy':'速卖通经济','AliExpress Saver':'速卖通省钱','Seller\\\'s Shipping':'卖家自选','China Post Registered':'中国邮政航空','China Post Ordinary':'中国邮政小包','ePacket':'e邮宝','EMS':'EMS','DHL':'DHL','FedEx':'联邦快递','UPS':'UPS'}
function cnL(l){if(!l)return'';for(const[k,v]of Object.entries(logisticsNames)){if(l.toLowerCase().includes(k.toLowerCase()))return v}return l.length>18?l.substring(0,17)+'..':l}
const colorCN = {'black':'黑','white':'白','blue':'蓝','red':'红','pink':'粉','green':'绿','purple':'紫','grey':'灰','gray':'灰','brown':'棕','gold':'金','silver':'银','navy':'深蓝','Light Purple':'浅紫','Deep Blue':'深蓝','Burgundy':'酒红','Coffee':'咖啡','GRAY':'灰','Warm light':'暖光','White light':'白光','7 Color light':'七彩'}
function cnSku(s){
  if(!s)return'';let r=s.trim().replace(/"/g,'')
  // "Color:500ml-Blue" -> 蓝 500ml
  r=r.replace(/Color:\s*(\d+)\s*ml\s*-\s*(.+)/gi,(_,ml,c)=>{let cl=c;for(const[en,zh]of Object.entries(colorCN))cl=cl.replace(new RegExp('\\b'+en+'\\b','gi'),zh);return cl+' '+ml+'ml'})
  // "Deep Blue" -> "深蓝" (先处理复合词)
  r=r.replace(/(Deep|Dark)\s+(blue|green|red|purple|grey|gray|brown|pink)/gi,(_,d,c)=>{let cl=c;for(const[en,zh]of Object.entries(colorCN))cl=cl.replace(new RegExp('\\b'+en+'\\b','gi'),zh);return '深'+cl})
  r=r.replace(/Color:\s*/gi,'')
  for(const[en,zh]of Object.entries(colorCN))r=r.replace(new RegExp('\\b'+en+'\\b','gi'),zh)
  r=r.replace(/Size:\s*/gi,'尺码').replace(/Emitting Color:\s*/gi,'光色')
  // iPhone型号标准化
  r=r.replace(/for\s+iphone\s*(\d+)\s*pro\s*max\s*/gi,'iP$1PM').replace(/for\s+iphone\s*(\d+)\s*pro\s*/gi,'iP$1P').replace(/for\s+iphone\s*(\d+)\s*plu[s]?\s*/gi,'iP$1+').replace(/for\s+iphone\s*(\d+)\s*/gi,'iP$1')
  r=r.replace(/尺码\s*/g,'').replace(/\s+/g,' ').trim().replace(/^["\s]+|["\s]+$/g,'')
  if(r.includes('iP'))r=r.replace(/\([^)]*\)/g,'').replace(/\s+/g,' ').trim()
  return r.length>22?r.substring(0,21)+'..':r
}

// 提取：产品特征正/负面判断（统一逻辑，5处复用）
function isPositiveFeature(f) {
  return f.sentiment_flag === 'positive' || f.score === 'Fast' || f.score === 'Good' || f.score === 'Great' || f.score === 'Fits ok ' || f.score === 'Fits ok'
}
function isNegativeFeature(f) {
  return f.sentiment_flag === 'negative' || f.score === 'Poor' || f.score === 'Difficult'
}

// axios 统一错误处理：接口异常时至少打印日志，避免前端静默白屏
async function apiGet(url) {
  try {
    const r = await axios.get(url)
    return r
  } catch (e) {
    console.error('[API错误]', url, e.message)
    throw e
  }
}

let charts={}
function cc(id,opt){setTimeout(()=>{const d=document.getElementById(id);if(d&&d.clientWidth>0){if(charts[id])charts[id].dispose();const c=echarts.init(d);c.setOption(opt);charts[id]=c}},150)}
function clearAll(){Object.values(charts).forEach(c=>c.dispose());charts={}}

// 实时指标
const liveMetrics = ref({totalReviews:0,posRate:0,todayRec:''})

async function loadAll(){
  const pid=selectedPid.value;const cid=selectedCountry.value
  const r=await apiGet(`${API}/decision/${pid}`)
  decision.value=r.data;const d=r.data
  const topRec=d.scorecard?d.scorecard[0]:null
  liveMetrics.value={totalReviews:d.sentiment?.total||0,posRate:d.sentiment?.pos_rate||0,todayRec:topRec?productNames[topRec.product_id]:'--'}

  const [matrix,monthly,logistics,sentiment,scorecard,feats,trend,sku]=await Promise.all([
    apiGet(API+'/matrix'),apiGet(API+'/trend/monthly'),apiGet(API+'/logistics'),
    apiGet(API+'/sentiment/product'),apiGet(API+'/scorecard'),
    apiGet(`${API}/feature/${pid}`),apiGet(API+'/trend/monthly'),apiGet(API+'/sku/analysis'),
  ])

  let cf=[],ct=[],cs=[]
  if(cid){
    try{
      const [a,b,c]=await Promise.all([apiGet(`${API}/feature/${pid}/country/${cid}`),apiGet(`${API}/trend/${pid}/country/${cid}`),apiGet(`${API}/sku/${pid}/country/${cid}`)])
      cf=a.data;ct=b.data;cs=c.data
      const fPos=cf.filter(isPositiveFeature)
      const fNeg=cf.filter(isNegativeFeature)
      const lTrend=ct.slice(-3)
      const dir=lTrend.length>=2?(lTrend[lTrend.length-1].avg_star>=lTrend[0].avg_star?'上升':'下降'):'--'
      const cm=matrix.data.filter(r=>r.buyer_country===cid&&r.product_id===pid)[0]
      const allC=matrix.data.filter(r=>r.buyer_country===cid).sort((a,b)=>(b.review_count||0)-(a.review_count||0))
      countryInsight.value={
        reviewCount:cm?cm.review_count:0,totalProducts:allC.length,rank:allC.findIndex(r=>r.product_id===pid)+1,
        avgStar:cm?Math.round(cm.avg_star*100)/100:0,avgSentiment:cm?Math.round(cm.avg_sentiment*1000)/1000:0,
        trendDir:dir,trendScores:lTrend.map(t=>Math.round(t.avg_star*100)/100).join('→'),
        strengths:fPos.slice(0,4),weaknesses:fNeg.slice(0,4),topSku:cs.slice(0,2),
        name:productNames[pid],cnName:cn(cid),featData:cf,trendData:ct,skuData:cs,
      }
    }catch(e){console.error('[国家洞察加载失败]',cid,pid,e.message);countryInsight.value=null}
  }else{countryInsight.value=null}

  td.value={matrix:matrix.data,trend:trend.data,logistics:logistics.data,sentiment:sentiment.data,scorecard:scorecard.data,feats:feats.data,sku:sku.data,countryFeat:cf,countryTrend:ct,countrySku:cs}
  renderCharts()
}

function renderCharts(){
  clearAll();const d=td.value;const pid=selectedPid.value;const cid=selectedCountry.value;const m=activeMenu.value

  if(m==='overview'){
    // 情感趋势折线
    cc('ch1',{tooltip:{trigger:'axis'},grid:{left:55,right:20,top:20,bottom:35},xAxis:{type:'category',data:d.trend.map(t=>t.month||t.eval_month),axisLabel:{color:'#889',fontSize:11,rotate:45}},yAxis:{type:'value',name:'评分',axisLabel:{color:'#889',fontSize:11},min:3.5,max:5},series:[{type:'line',data:d.trend.map(t=>Math.round(t.avg_star*100)/100),smooth:true,symbol:'circle',symbolSize:6,lineStyle:{color:'#2979ff',width:2.5},itemStyle:{color:'#2979ff'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(41,121,255,0.25)'},{offset:1,color:'rgba(41,121,255,0.02)'}])}}]})

    // 选品评分雷达
    cc('ch2',{tooltip:{},legend:{data:productList.map(p=>p.name),textStyle:{color:'#889',fontSize:10},bottom:0},radar:{center:['50%','45%'],radius:'60%',indicator:[{name:'推荐指数',max:60},{name:'好评率(%)',max:30},{name:'情感均分',max:0.2},{name:'评论规模',max:4200},{name:'星评均分',max:5}],axisName:{color:'#889',fontSize:11}},series:d.scorecard.map((s,i)=>({type:'radar',data:[{value:[Math.round(s.recommendation_score*10)/10,s.sentiment_pos_rate,Math.round(s.avg_sentiment*1000)/1000,s.total_reviews,Math.round(s.star_score*100)/100],name:productNames[s.product_id]||''}],lineStyle:{color:['#2979ff','#ff6d00','#00c853','#d50000','#6200ea'][i],width:2},itemStyle:{color:['#2979ff','#ff6d00','#00c853','#d50000','#6200ea'][i]},areaStyle:{color:'transparent'}}))})

    // 热力图
    const topC=[...new Set(d.matrix.map(r=>r.buyer_country))].slice(0,10)
    const hd=[];topC.forEach((c,i)=>{productList.forEach((p,j)=>{const x=d.matrix.find(r=>r.buyer_country===c&&r.product_id===p.id);if(x)hd.push([j,i,Math.round(Number(x.avg_star||0)*100)/100])})})
    cc('ch3',{tooltip:{formatter:p=>`${productList[p.value[0]]?.name} / ${cn(topC[p.value[1]])}: ${Number(p.value[2]).toFixed(2)}分`},grid:{left:75,right:110,top:15,bottom:15},xAxis:{type:'category',data:productList.map(p=>p.name),axisLabel:{color:'#889',fontSize:11,rotate:20}},yAxis:{type:'category',data:topC.map(cn),axisLabel:{color:'#889',fontSize:11}},visualMap:{min:3.5,max:5,text:['高','低'],textStyle:{color:'#889'},inRange:{color:['#e3f2fd','#90caf9','#42a5f5','#1e88e5','#1565c0']},calculable:true,orient:'vertical',right:10,top:'center',itemWidth:12,itemHeight:100},series:[{type:'heatmap',data:hd,label:{show:true,color:'#222',fontSize:11,fontWeight:'bold'}}]})

    // 选品排名柱状
    cc('ch4',{tooltip:{trigger:'axis'},grid:{left:100,right:60,top:10,bottom:20},xAxis:{type:'value',name:'推荐指数',axisLabel:{color:'#889',fontSize:11}},yAxis:{type:'category',data:d.scorecard.map(s=>productNames[s.product_id]||''),axisLabel:{color:'#333',fontSize:13,fontWeight:'bold'}},series:[{type:'bar',data:d.scorecard.map(s=>Math.round(s.recommendation_score*10)/10),itemStyle:{color:new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#2979ff'},{offset:1,color:'#82b1ff'}]),borderRadius:[0,4,4,0]},label:{show:true,position:'right',color:'#333',fontSize:13,fontWeight:'bold',formatter:'{c}分'},markLine:{symbol:'none',data:[{type:'average',label:{show:true,color:'#999',fontSize:10,position:'start',formatter:'均线{c}'}}],lineStyle:{color:'#bbb',type:'dashed'}}}]})

    // 特征ABSA（数据概览Tab）
    const fp=d.feats.filter(isPositiveFeature)
    const fn=d.feats.filter(isNegativeFeature)
    const fk=[...new Set(d.feats.map(f=>cnF(f.feature)))]
    cc('ch5',{tooltip:{trigger:'axis'},legend:{data:['好评','差评'],textStyle:{color:'#889',fontSize:11},top:0},grid:{left:90,right:50,top:30,bottom:25},xAxis:{type:'value',axisLabel:{color:'#889',fontSize:11}},yAxis:{type:'category',data:fk.reverse(),axisLabel:{color:'#333',fontSize:12}},series:[{name:'好评',type:'bar',data:fk.map(f=>{const r=fp.find(x=>cnF(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#00c853'},barGap:'20%'},{name:'差评',type:'bar',data:fk.map(f=>{const r=fn.find(x=>cnF(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#ff1744'}}]})
  }

  if(m==='sentiment'){
    // 特征ABSA（情感分析Tab）
    const fp=d.feats.filter(isPositiveFeature)
    const fn=d.feats.filter(isNegativeFeature)
    const fk=[...new Set(d.feats.map(f=>cnF(f.feature)))]
    cc('ch-s2',{tooltip:{trigger:'axis'},legend:{data:['好评','差评'],textStyle:{color:'#889',fontSize:11},top:0},grid:{left:90,right:50,top:30,bottom:25},xAxis:{type:'value',axisLabel:{color:'#889',fontSize:11}},yAxis:{type:'category',data:fk.reverse(),axisLabel:{color:'#333',fontSize:12}},series:[{name:'好评',type:'bar',data:fk.map(f=>{const r=fp.find(x=>cnF(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#00c853'},barGap:'20%'},{name:'差评',type:'bar',data:fk.map(f=>{const r=fn.find(x=>cnF(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#ff1744'}}]})
    const sp=d.sentiment
    cc('ch-s1',{tooltip:{trigger:'axis'},legend:{data:['正面','中性','负面'],textStyle:{color:'#889',fontSize:11},top:0},grid:{left:55,right:30,top:30,bottom:30},xAxis:{type:'category',data:sp.map(s=>productNames[s.product_id]||''),axisLabel:{color:'#889',fontSize:11,rotate:15}},yAxis:{type:'value',name:'%',axisLabel:{color:'#889',fontSize:11}},series:[{name:'正面',type:'bar',stack:'t',data:sp.map(s=>s.pos_rate),itemStyle:{color:'#00c853'},label:{show:true,color:'#fff',fontSize:10}},{name:'中性',type:'bar',stack:'t',data:sp.map(s=>((s.total-s.pos_cnt-s.neg_cnt)*100/s.total).toFixed(1)),itemStyle:{color:'#ff9800'}},{name:'负面',type:'bar',stack:'t',data:sp.map(s=>(s.neg_cnt*100/s.total).toFixed(1)),itemStyle:{color:'#ff1744'}}]})
  }

  if(m==='decision'){
    if(cid && countryInsight.value){
      // 国家洞察卡片（选品建议Tab）
      const ci=countryInsight.value
      if(d.countryTrend&&d.countryTrend.length) cc('ch-d1',{tooltip:{trigger:'axis'},grid:{left:55,right:20,top:10,bottom:40},xAxis:{type:'category',data:d.countryTrend.map(t=>t.month||t.eval_month),axisLabel:{color:'#889',fontSize:11,rotate:45}},yAxis:{type:'value',name:'评分',axisLabel:{color:'#889',fontSize:11},min:3,max:5},series:[{type:'line',data:d.countryTrend.map(t=>Math.round(t.avg_star*100)/100),smooth:true,symbol:'circle',symbolSize:6,lineStyle:{color:'#ff6d00',width:2.5},itemStyle:{color:'#ff6d00'},areaStyle:{color:new echarts.graphic.LinearGradient(0,0,0,1,[{offset:0,color:'rgba(255,109,0,0.2)'},{offset:1,color:'rgba(255,109,0,0.02)'}])}}]})
      if(d.countrySku&&d.countrySku.length){const sd=d.countrySku.slice(0,8);cc('ch-d2',{tooltip:{trigger:'axis'},grid:{left:150,right:40,top:10,bottom:10},yAxis:{type:'category',data:sd.map(s=>cnSku(s.sku_info)).reverse(),axisLabel:{color:'#333',fontSize:11}},xAxis:{type:'value',name:'评论数',axisLabel:{color:'#889',fontSize:11}},series:[{type:'bar',data:sd.map(s=>s.review_count).reverse(),itemStyle:{color:new echarts.graphic.LinearGradient(0,0,1,0,[{offset:0,color:'#ff6d00'},{offset:1,color:'#ffab40'}]),borderRadius:[0,3,3,0]},label:{show:true,position:'right',color:'#333',fontSize:11}}]})}
      if(d.countryFeat&&d.countryFeat.length){
        // 特征ABSA（选品建议Tab — 国家×商品过滤）
        const cfp=d.countryFeat.filter(isPositiveFeature)
        const cfn=d.countryFeat.filter(isNegativeFeature)
        const cfk=[...new Set(d.countryFeat.map(f=>cnF(f.feature)))]
        cc('ch-d3',{tooltip:{trigger:'axis'},legend:{data:['好评','差评'],textStyle:{color:'#889',fontSize:11},top:0},grid:{left:90,right:50,top:30,bottom:25},xAxis:{type:'value',axisLabel:{color:'#889',fontSize:11}},yAxis:{type:'category',data:cfk.reverse(),axisLabel:{color:'#333',fontSize:12}},series:[{name:'好评',type:'bar',data:cfk.map(f=>{const r=cfp.find(x=>cnF(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#00c853'},barGap:'20%'},{name:'差评',type:'bar',data:cfk.map(f=>{const r=cfn.find(x=>cnF(x.feature)===f);return r?r.cnt:0}).reverse(),itemStyle:{color:'#ff1744'}}]})
      }
    }
  }
}

watch([selectedPid,selectedCountry],()=>loadAll())
watch(activeMenu,()=>nextTick(()=>renderCharts()))
onMounted(()=>loadAll())
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
        <select v-model="selectedCountry" class="tb-sel"><option value="">全部国家</option><option v-for="(n,c) in countryNames" :key="c" :value="c">{{ n }}</option></select>
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
          <div class="card"><div class="ctitle">🔍 全站产品特征分析</div><div id="ch5" class="chart"></div></div>
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

      <!-- 选品建议 -->
      <div v-show="activeMenu==='decision'">
        <div class="country-card" v-if="countryInsight">
          <div class="cc-hd"><span class="cc-flag">{{ countryInsight.cnName }}</span> 市场深度洞察 — {{ countryInsight.name }}</div>
          <div class="cc-body">
            <div class="cc-stat"><span class="cc-num blue">{{ countryInsight.avgStar }}</span><span class="cc-lbl">平均星评</span></div>
            <div class="cc-stat"><span class="cc-num green">{{ countryInsight.reviewCount }}</span><span class="cc-lbl">评论数(排第{{ countryInsight.rank }})</span></div>
            <div class="cc-stat"><span :class="'cc-num '+(countryInsight.trendDir==='上升'?'green':'red')">{{ countryInsight.trendDir }}</span><span class="cc-lbl">评分趋势 {{ countryInsight.trendScores }}</span></div>
            <div class="cc-stat"><span class="cc-num">{{ countryInsight.topSku[0] ? cnSku(countryInsight.topSku[0].sku_info) : '-' }}</span><span class="cc-lbl">推荐属性</span></div>
          </div>
          <div class="cc-insight">
            💡 {{ countryInsight.strengths.length ? '消费者认可'+countryInsight.strengths.slice(0,2).map(s=>cnF(s.feature)).join('、')+'。' : '' }}{{ countryInsight.weaknesses.length ? '主要不满集中在'+countryInsight.weaknesses.slice(0,2).map(s=>cnF(s.feature)).join('、')+'。' : '' }}建议备货{{ countryInsight.topSku.slice(0,2).map(s=>cnSku(s.sku_info)).join('、') }}，维持高分物流渠道。
          </div>
        </div>
        <div v-else style="text-align:center;padding:60px;color:#999">请在上方选择一个国家以查看该国的选品深度分析</div>
        <div class="card-row-2" v-if="countryInsight" style="margin-top:14px">
          <div class="card"><div class="ctitle">📈 该国评分趋势</div><div id="ch-d1" class="chart"></div></div>
          <div class="card"><div class="ctitle">🛒 该国SKU偏好 TOP8</div><div id="ch-d2" class="chart"></div></div>
        </div>
      </div>

      <!-- 历史记录 -->
      <div v-show="activeMenu==='history'">
        <div class="card" style="text-align:center;padding:60px;color:#999">
          📋 历史选品记录与趋势对比（数据积累中，将在持续运营后开放）
        </div>
      </div>
    </div>
  </main>

  <!-- 右侧悬浮指标卡 -->
  <aside class="float-panel">
    <div class="fp-card">
      <div class="fp-num blue">{{ liveMetrics.totalReviews }}</div>
      <div class="fp-label">实时评论数</div>
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
.cc-num{font-size:28px;font-weight:800}.cc-num.blue{color:#1565c0}.cc-num.green{color:#2e7d32}.cc-num.red{color:#c62828}
.cc-lbl{display:block;font-size:12px;color:#222;margin-top:4px}
.cc-insight{background:#fff;border-radius:8px;padding:14px 18px;font-size:14px;color:#000;line-height:1.7}

/* 右侧悬浮 */
.float-panel{width:180px;padding:16px 12px;display:flex;flex-direction:column;gap:14px;flex-shrink:0}
.fp-card{background:linear-gradient(135deg,#1565c0,#0d47a1);border-radius:12px;padding:18px 14px;text-align:center;color:#fff;box-shadow:0 4px 12px rgba(21,101,192,.3)}
.fp-num{font-size:24px;font-weight:800;margin-bottom:4px}.fp-num.blue{color:#81d4fa}.fp-num.green{color:#a5d6a7}.fp-num.gold{color:#ffe082}
.fp-label{font-size:12px;opacity:.85}
</style>
