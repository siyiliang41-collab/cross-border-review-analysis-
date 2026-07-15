# 项目运行操作手册

> 跨境电商评论情感挖掘与选品决策支持系统 — 昌平champion盛世  
> v5.0 | 最后更新：2026-07-14

---

## 目录

1. [环境概况](#一环境概况)
2. [集群冷启动（VM 重启后完整启动流程）](#八集群冷启动vm-重启--一切从零开始)
3. [前置检查：MySQL 是否正常](#二前置检查mysql-是否正常)
4. [前置检查：后端 SpringBoot 是否运行](#三前置检查后端-springboot-是否运行)
5. [访问前端大屏](#四访问前端大屏)
6. [验证全链路](#五验证全链路)
7. [常见问题排查](#六常见问题排查)
8. [HA 故障切换演示（答辩必演示）](#七ha-故障切换演示答辩必演示)
9. [快速启动速查卡](#九快速启动速查卡)

---

## 一、环境概况

| 组件 | 所在机器 | 地址 | 端口 |
|------|------|------|:--:|
| MySQL 8.0 | hadoop01 | 192.168.229.101 | 3306 |
| SpringBoot 后端（含前端） | hadoop01 | 192.168.229.101 | 8080 |
| HDFS | hadoop01/02/03 | — | 9000 |
| YARN | hadoop03 | 192.168.229.103 | 8088 |
| ngrok 公网穿透 | hadoop01 | squint-owl-worshiper.ngrok-free.dev | 443 |

**数据库名：** `bipt_project`  
**用户/密码：** `root / Root@123456`

---

## 二、前置检查：MySQL 是否正常

### 2.1 登录 hadoop01

在本机 Windows 上打开终端（Git Bash 或 CMD），SSH 到 hadoop01：

```bash
ssh root@192.168.229.101
# 密码：123456
```

### 2.2 检查 MySQL 是否运行

```bash
systemctl status mysqld
```

看到 `active (running)` 表示 MySQL 在运行。

如果没运行，启动它：

```bash
systemctl start mysqld
```

### 2.3 检查数据是否在

```bash
mysql -u root -p'Root@123456' -e "USE bipt_project; SHOW TABLES;"
```

应该看到 15 张表（13 张 `ads_*` + `bipt_review` + `users`）：

```
ads_country_monthly_trend
ads_country_product_matrix
ads_country_top15
ads_feature_country_product
ads_feature_time_analysis
ads_image_followup
ads_logistics
ads_monthly_trend
ads_product_rating
ads_product_scorecard
ads_sentiment_product
ads_sku_analysis
ads_sku_country_pref
bipt_review
users
```

### 2.4 验证表里有数据

```bash
mysql -u root -p'Root@123456' -e "USE bipt_project; SELECT COUNT(*) AS cnt FROM ads_product_rating;"
```

应返回 `5`（5个商品）。

---

## 三、前置检查：后端 SpringBoot 是否运行

### 3.1 检查后端进程

在 hadoop01 上：

```bash
ps aux | grep bipt-api
```

或者检查端口：

```bash
ss -tlnp | grep 8080
```

看到 `LISTEN` 表示后端在监听 8080 端口。

### 3.2 后端不在跑？——打包并启动

**第一次部署或者代码有更新时，需要重新编译。**

#### Step 1：确认 JDK 版本

```bash
java -version
# 应显示 17 或以上
```

如果不是 JDK 17：

```bash
export JAVA_HOME=/opt/jdk-17
export PATH=$JAVA_HOME/bin:$PATH
```

#### Step 2：把后端源码传到 hadoop01

在本机 Windows 上：

```bash
# 打包整个 bipt-api 目录，scp 传到 hadoop01
cd "c:\Users\10730\Desktop\bipt project"
scp -r bipt-api root@192.168.229.101:/root/
```

#### Step 3：在 hadoop01 上编译

```bash
cd /root/bipt-api

# Maven 编译打包（跳过测试，加快速度）
mvn clean package -DskipTests
```

编译成功会看到 `BUILD SUCCESS`，生成的 jar 包在 `target/` 目录下：

```bash
ls target/*.jar
# 输出类似：target/bipt-api-1.0.0.jar
```

#### Step 4：启动后端

```bash
# 后台启动，日志输出到 app.log
nohup java -jar target/bipt-api-1.0.0.jar > /root/app.log 2>&1 &

# 等 5 秒让 SpringBoot 启动
sleep 5

# 检查是否启动成功
tail -20 /root/app.log
```

看到 `Started BiptApplication in X.XXX seconds` 表示启动成功。

### 3.3 验证后端接口

在 hadoop01 上：

```bash
curl http://localhost:8080/api/overview
```

返回类似这样的 JSON 表示后端正常：

```json
{"totalReviews":16989,"avgStar":4.21}
```

如果 `curl` 报 `Connection refused`，说明后端没起来，看日志：

```bash
cat /root/app.log
```

---

## 四、访问前端大屏

> **v3.0 起前端已打包嵌入后端 JAR 包，无需 `npm run dev`。**  
> 后端启动时会自动托管前端静态文件，浏览器直接访问即可。

### 4.1 浏览器打开

**局域网（推荐）：** `http://192.168.229.101:8080`  
**公网备用：** `https://squint-owl-worshiper.ngrok-free.dev`（首次需点 Visit Site）

同一个端口同时提供 API 和前端页面（相对路径 `/api`），无跨域问题。

### 4.2 前端需要修改时怎么调试

如果后续要改前端代码，先用开发模式调试：

```bash
cd "c:\Users\10730\Desktop\bipt project\frontend"
npm run dev
# → http://localhost:5173（热更新，改代码即刷新）
```

调试完毕确认无误后，重新打包嵌入后端：

```bash
cd "c:\Users\10730\Desktop\bipt project\frontend"
npm run build

# 把 dist 和 kmeans_data.json 拷入后端 static 目录
rm -rf "../backend/src/main/resources/static/"*
cp -r dist/* "../backend/src/main/resources/static/"
cp public/kmeans_data.json "../backend/src/main/resources/static/"

# 上传到 hadoop01 重新编译后端（使用 paramiko 或手动 SCP）
# 或直接在 hadoop01 上 mvn clean package -DskipTests
# 然后重启: pkill -f java; nohup java -jar target/bipt-api-1.0.0.jar > /root/app.log 2>&1 &
```

### 4.3 公网穿透（ngrok）

```bash
# 在 hadoop01 上
nohup ngrok http 8080 > /dev/null 2>&1 &
# 公网地址: https://squint-owl-worshiper.ngrok-free.dev
```

---

## 五、验证全链路

打开前端后，按以下顺序检查，确认端到端数据流通：

### 5.1 数据概览 Tab（默认进入）

| 检查项 | 怎么看 | 预期 |
|------|------|------|
| 是否加载 | 图表区域没有转圈或空白 | 6张图+文字全部显示 |
| 情感趋势折线 | 第一行左图 | 有13个月的数据点 |
| 选品雷达 | 第一行右图 | 5条线对应5个商品 |
| 热力图 | 第二行全宽 | 格子有颜色和数字 |
| KMeans散点图 | 第三行全宽 | 102国气泡+4色聚类 |
| 选品排名 | 第四行左图 | 5商品排序柱状 |
| 情感堆叠 | 第四行右图 | 正/中/负三色堆叠 |

### 5.2 产品洞察 Tab

| 检查项 | 怎么看 | 预期 |
|------|------|------|
| ABSA特征 | 左图 | 好评绿/差评红柱子 |
| 月度趋势 | 右图 | 随顶栏选品变化 |
| 情感环形图 | 左下 | 正/中/负占比 |

### 5.3 市场洞察 Tab

| 检查项 | 怎么看 | 预期 |
|------|------|------|
| TOP5排名卡片 | 切换不同商品 | 国家排名自动变化 |
| 国家详情 | 下拉选国家 | 橙色洞察卡片+趋势+SKU图 |
| 预测线 | 趋势图中 | 红色虚线回归+菱形预测点 |
| LDA风险兜底 | 注意风险列 | 缺数据的国家标注（全品类推测风险） |

### 5.4 控制台检查

按 **F12** → **Console**：

- ❌ CORS 报错 → 检查是否在用 `http://192.168.229.101:8080` 访问
- ❌ 红色报错 → API 挂了，检查后端进程
- ✅ 无报错 → 一切正常

---

## 六、常见问题排查

### 问题1：前端加载后所有图表空白

**可能性1：后端没启动**

在 hadoop01 上：

```bash
curl http://localhost:8080/api/overview
```

如果没有返回 JSON → 按第三章重新启动后端。

**可能性2：后端启动了但前端连不上**

- 检查 `.env` 中 IP 是否正确
- 检查 hadoop01 的防火墙是否关闭：

```bash
# 在 hadoop01 上
systemctl stop firewalld
# 或者
iptables -F
```

**可能性3：MySQL 没启动**

```bash
# 在 hadoop01 上
systemctl start mysqld
```

然后重启后端：

```bash
# 先杀掉旧进程
pkill -f bipt-api
# 再启动
cd /root/bipt-api
nohup java -jar target/bipt-api-1.0.0.jar > /root/app.log 2>&1 &
```

### 问题2：ABSA 特征图空白

按 F12 → Console，看 `d.feats` 的返回数据是什么样的：

```javascript
// 在 Console 里输入这个看原始数据
// 这会告诉你 feature 字段是否有值、sentiment_flag 是否为空
```

如果是空数组 `[]`，说明数据库里 `ads_feature_country_product` 表没数据——需要用 Spark 重新跑 `build_deep_ads.py`。

### 问题3：`npm run dev` 报错

```bash
# 删除 node_modules 和 lock 文件重新安装
cd "c:\Users\10730\Desktop\bipt project\bipt-dashboard"
rm -rf node_modules package-lock.json
npm install
npm run dev
```

### 问题4：前端端口 5173 被占用

```bash
# 查看谁占用了 5173
netstat -ano | findstr 5173
# 杀掉对应进程（用任务管理器或）
taskkill /PID <进程ID> /F
```

### 问题5：跨域 CORS 报错（Console 里看到 CORS 相关红色报错）

两种解决方式（任选其一）：

**方式A（推荐·临时）：** 用 Chrome 无安全模式启动
```bash
"C:\Program Files\Google\Chrome\Application\chrome.exe" --disable-web-security --user-data-dir="C:\chrome-temp"
```

**方式B：** 在 Vite 配置代理（让 Vite 转发请求，绕过浏览器跨域检查）。编辑 `vite.config.js`：

```js
export default {
  server: {
    proxy: {
      '/api': 'http://192.168.229.101:8080'
    }
  }
}
```

然后把 `.env` 中的 `VITE_API_BASE_URL` 改为空（让前端走 Vite 代理）。

---

## 七、HA 故障切换演示（答辩必演示）

> **演示目的：** 证明 HDFS NameNode 高可用——Active NN 挂了，Standby 自动接管，HDFS 继续正常读写。  
> **口播话术：** "生产环境中 NameNode 单点故障会导致整个 HDFS 不可用。我们部署了 HA 架构，接下来演示故障自动切换。"

### 7.1 演示前检查

```bash
# ① 确认 ZooKeeper 三节点都在运行
ssh hadoop01 "zkServer.sh status"
ssh hadoop02 "zkServer.sh status"
ssh hadoop03 "zkServer.sh status"
# 预期：三台分别显示 leader / follower / follower

# ② 确认 HDFS HA 状态
hdfs haadmin -getAllServiceState
# 预期：
#   hadoop01:8020  active
#   hadoop02:8020  standby

# ③ 先展示 HDFS 正常工作
hdfs dfs -ls /
# 预期：看到 /user 等目录

# ④ 往 HDFS 写一个测试文件（演示用）
echo "HA测试-故障切换前写入" > /tmp/ha_test.txt
hdfs dfs -put -f /tmp/ha_test.txt /ha_test.txt
hdfs dfs -cat /ha_test.txt
# 预期：输出 "HA测试-故障切换前写入"
```

### 7.2 演示步骤（按顺序操作）

**Step 1 — 找到 Active NameNode 并告知观众**

口播："目前 Active NameNode 运行在 hadoop01 上，Standby 在 hadoop02 上。"

```bash
hdfs haadmin -getAllServiceState
```

**Step 2 — 展示 Active NameNode 的进程 ID**

口播："hadoop01 上的 NameNode 进程 PID 是多少，我们记录下来。"

```bash
ssh hadoop01 "jps | grep NameNode"
# 输出类似：12345 NameNode
```

**Step 3 — 模拟故障**

口播："现在我们模拟 hadoop01 宕机——直接 kill 掉 Active NameNode 进程。"

```bash
ssh hadoop01 "jps | grep NameNode | awk '{print \$1}' | xargs kill -9"
```

**Step 4 — 立即查看切换结果**

口播："观察——hadoop02 上的 Standby NameNode 正在自动接管。"

```bash
sleep 3 && hdfs haadmin -getAllServiceState
```

预期输出：

```
hadoop01:8020                                      Failed to connect ...
hadoop02:8020                                      active
```

口播："hadoop02 已经从 Standby 切换为 Active，整个过程约 3~5 秒。"

**Step 5 — 验证 HDFS 仍然正常工作**

口播："关键来了——HDFS 服务有没有中断？我们读一下刚才写的文件。"

```bash
hdfs dfs -cat /ha_test.txt
```

预期输出：`HA测试-故障切换前写入`

口播："文件正常读取，数据零丢失。"

**Step 6 — 恢复 hadoop01（演示完整性）**

口播："生产环境中我们会把 hadoop01 重新加入集群作为 Standby。"

```bash
ssh hadoop01 "hdfs --daemon start namenode"
sleep 3
hdfs haadmin -getAllServiceState
```

预期：

```
hadoop01:8020                                      standby
hadoop02:8020                                      active
```

口播："hadoop01 恢复后自动成为 Standby，不会抢占 Active——因为 ZooKeeper 做了选主协调，避免了脑裂。"

### 7.3 演示脚本（一条命令版）

如果你不想逐条敲，可以把这个脚本保存为 `/root/ha_demo.sh`，演示时一键跑：

```bash
#!/bin/bash
# HA 故障切换演示脚本
# 用法：bash /root/ha_demo.sh

echo "========== HA 故障切换演示 =========="

echo -e "\n[1/5] 初始状态"
hdfs haadmin -getAllServiceState

echo -e "\n[2/5] 写入测试文件"
echo "HA测试-$(date +%H:%M:%S)" > /tmp/ha_test.txt
hdfs dfs -put -f /tmp/ha_test.txt /ha_test.txt
echo "写入成功：$(hdfs dfs -cat /ha_test.txt)"

echo -e "\n[3/5] kill Active NameNode"
ACTIVE_PID=$(ssh hadoop01 "jps | grep NameNode | awk '{print \$1}'")
echo "hadoop01 NameNode PID = $ACTIVE_PID"
ssh hadoop01 "kill -9 $ACTIVE_PID"
echo "已发送 kill -9 信号"

echo -e "\n[4/5] 切换结果（等待 3 秒）"
sleep 3
hdfs haadmin -getAllServiceState

echo -e "\n[5/5] 验证 HDFS 可用性"
echo "hdfs dfs -cat /ha_test.txt →"
hdfs dfs -cat /ha_test.txt

echo -e "\n========== 演示完成 =========="
```

### 7.4 常见问题

| 现象 | 原因 | 解决 |
|------|------|------|
| `getAllServiceState` 全都 `Connection Refused` | HDFS 没启动 | `start-dfs.sh` |
| 两个都显示 `standby` | ZK 或 ZKFC 没启 | `zkServer.sh start` + `hdfs --daemon start zkfc` |
| `hdfs haadmin` 报 `operation not permitted` | 自动故障切换开启中 | 用 `--forcemanual` 或等 ZKFC 自动切 |
| `jps` 命令不存在 | JDK 没装或没加 PATH | `export PATH=$JAVA_HOME/bin:$PATH` |

---

## 八、集群冷启动（VM 重启 / 一切从零开始）

> **适用场景：** VM 关机后重启、长期未使用、或者 `jps` 发现进程全没了。  
> **核心原则：** ZooKeeper → JournalNode → NameNode（HDFS）→ DataNode → ZKFC，顺序不能乱。

### 8.1 启动 ZooKeeper（三台都要）

ZooKeeper 是 HA 的协调中心——HDFS 的选主和故障切换都依赖它，必须最先启。

```bash
# 在 hadoop01 上执行（本机 + 远程另两台）
zkServer.sh start
ssh hadoop02 "zkServer.sh start"
ssh hadoop03 "zkServer.sh start"

# 等 3 秒让选举完成，然后验证
sleep 3
zkServer.sh status
ssh hadoop02 "zkServer.sh status"
ssh hadoop03 "zkServer.sh status"
```

**预期输出：**
```
hadoop01: Mode: follower
hadoop02: Mode: leader
hadoop03: Mode: follower
```

> 三台中任意一台为 Leader、其余为 Follower 即正常。具体哪台当 Leader 不重要。

**常见问题：**
- `Error contacting service` → 还没启起来，等几秒再查
- 三台全是 follower → 再等一下，选举正在进行
- 三台全是 leader → 不可能，检查网络

### 8.2 启动 JournalNode（三台都要）

JournalNode 负责存储 NameNode 的编辑日志（HA 数据同步的基础）。

```bash
ssh hadoop01 "hdfs --daemon start journalnode"
ssh hadoop02 "hdfs --daemon start journalnode"
ssh hadoop03 "hdfs --daemon start journalnode"
```

验证（每台上都应该看到 JournalNode 进程）：

```bash
ssh hadoop01 "jps | grep JournalNode"
ssh hadoop02 "jps | grep JournalNode"
ssh hadoop03 "jps | grep JournalNode"
```

### 8.3 启动 HDFS

在 **hadoop01** 上直接执行：

```bash
start-dfs.sh
```

这条命令会自动启动：
- hadoop01 上的 NameNode + ZKFC
- hadoop02 上的 NameNode + ZKFC
- 三台上的 DataNode

等 5 秒让 HA 初始化，然后验证：

```bash
sleep 5

# 检查所有进程
jps
ssh hadoop02 "jps"
ssh hadoop03 "jps"

# 检查 HA 状态
hdfs haadmin -getAllServiceState
```

**预期输出：**
```
hadoop01:8020                                      active
hadoop02:8020                                      standby
```

### 8.4 验证 HDFS 可读写

```bash
# 读
hdfs dfs -ls /

# 写一个测试文件确认正常
echo "冷启动验证-$(date +%H:%M:%S)" > /tmp/startup_test.txt
hdfs dfs -put -f /tmp/startup_test.txt /startup_test.txt
hdfs dfs -cat /startup_test.txt
```

### 8.5 启动 YARN（如需要跑 MR/Spark）

```bash
# 在 hadoop03（ResourceManager 所在节点）上
ssh hadoop03 "start-yarn.sh"
```

验证：

```bash
ssh hadoop03 "jps | grep ResourceManager"
# 浏览器访问 http://192.168.229.103:8088 确认 Web UI 可打开
```

> YARN 只在需要跑 MR Job（性能对比）或 Spark on YARN 时才需要启。平时 HDFS + MySQL + 后端就够了。

### 8.6 启动 MySQL

```bash
systemctl start mysqld
systemctl status mysqld
# 看到 active (running) 即可
```

验证数据在：

```bash
mysql -u root -p'Root@123456' -e "USE bipt_project; SELECT COUNT(*) AS table_count FROM information_schema.tables WHERE table_schema='bipt_project';"
```

### 8.7 启动后端 SpringBoot

```bash
# 先杀掉可能残留的旧进程
pkill -f bipt-api 2>/dev/null

# 启动
cd /root/bipt-api
nohup java -jar target/bipt-api-1.0.0.jar > /root/app.log 2>&1 &

# 等 5 秒
sleep 5

# 验证
curl http://localhost:8080/api/overview
```

---

## 九、快速启动速查卡

> **完整冷启动流程见第八章。** 以下是演示/答辩前逐条确认的速查清单。

```bash
# ===== 1. ZooKeeper（三台） =====
ssh hadoop01 "zkServer.sh start"
ssh hadoop02 "zkServer.sh start"
ssh hadoop03 "zkServer.sh start"
sleep 3

# ===== 2. JournalNode（三台） =====
ssh hadoop01 "hdfs --daemon start journalnode"
ssh hadoop02 "hdfs --daemon start journalnode"
ssh hadoop03 "hdfs --daemon start journalnode"

# ===== 3. HDFS =====
ssh hadoop01 "start-dfs.sh"
sleep 5

# ===== 4. 验证 HA 状态 =====
ssh hadoop01 "hdfs haadmin -getAllServiceState"
# 预期：active / standby 各一个

# ===== 5. MySQL =====
ssh hadoop01 "systemctl start mysqld"
ssh hadoop01 "systemctl status mysqld"

# ===== 6. 后端 SpringBoot =====
ssh hadoop01 "pkill -f bipt-api 2>/dev/null; cd /root/bipt-api && nohup java -jar target/bipt-api-1.0.0.jar > /root/app.log 2>&1 &"
sleep 5
ssh hadoop01 "curl http://localhost:8080/api/overview"

# ===== 7. 公网穿透（可选，ngrok 固定域名） =====
# 需要提前在 hadoop01 上配置 ngrok authtoken（一次性的）
ssh hadoop01 "nohup ngrok http 8080 > /dev/null 2>&1 &"
# 公网访问: https://squint-owl-worshiper.ngrok-free.dev（首次需点 Visit Site）

# ===== 8. 前端访问 =====
# 局域网（推荐，答辩当天用）：
#   浏览器打开 http://192.168.229.101:8080
# 公网（备用）：
#   浏览器打开 https://squint-owl-worshiper.ngrok-free.dev（首次需点 Visit Site）
# F12 → Console → 无红色报错 ✅
```
