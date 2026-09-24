# Jenkins CI/CD 部署指南 - DuooInterfaceAuto 接口自动化项目

> 本文档为小白用户详细介绍如何将 GitHub 上的接口自动化测试项目集成到 Jenkins，实现自动化构建和测试。

---

## 📋 目录

1. [前置准备](#1-前置准备)
2. [Jenkins 安装](#2-jenkins-安装)
3. [Jenkins 初始配置](#3-jenkins-初始配置)
4. [安装必要插件](#4-安装必要插件)
5. [配置全局工具](#5-配置全局工具)
6. [创建 Jenkins 任务](#6-创建-jenkins-任务)
7. [配置 Jenkinsfile](#7-配置-jenkinsfile)
8. [配置 Webhook（可选）](#8-配置-webhook可选)
9. [常见问题排查](#9-常见问题排查)

---

## 1. 前置准备

### 1.1 服务器要求

| 资源 | 最低要求 | 推荐配置 |
|------|----------|----------|
| CPU | 2核 | 4核+ |
| 内存 | 4GB | 8GB+ |
| 磁盘 | 50GB | 100GB+ |
| 操作系统 | Windows/Linux/macOS | Linux (Ubuntu/CentOS) |

### 1.2 需要安装的软件

在 Jenkins 服务器上需要预装以下软件：

```
✅ Java JDK 11 或 17（Jenkins 运行需要）
✅ Python 3.9+（运行测试需要）
✅ Git（拉取代码需要）
✅ Allure Commandline（生成报告需要）
```

### 1.3 确认 GitHub 仓库信息

记录以下信息，后续配置需要用到：

- **仓库地址**: `https://github.com/你的用户名/DuooInterfaceAuto.git`
- **分支名称**: 通常是 `main` 或 `master`

---

## 2. Jenkins 安装

### 2.1 Windows 安装方式

#### 步骤 1：下载 Jenkins

1. 访问 Jenkins 官网：https://www.jenkins.io/download/
2. 选择 **Windows** 版本，下载 `.msi` 安装包

#### 步骤 2：安装 Jenkins

1. 双击运行下载的 `.msi` 文件
2. 按照安装向导完成安装
3. 默认安装路径：`C:\Program Files\Jenkins`
4. 默认端口：**8080**

#### 步骤 3：启动 Jenkins

安装完成后，Jenkins 会自动作为 Windows 服务启动。

打开浏览器访问：`http://localhost:8080`

---

### 2.2 Linux (Ubuntu) 安装方式

```bash
# 步骤 1：添加 Jenkins 仓库密钥
curl -fsSL https://pkg.jenkins.io/debian-stable/jenkins.io-2023.key | sudo tee \
  /usr/share/keyrings/jenkins-keyring.asc > /dev/null

# 步骤 2：添加 Jenkins 仓库
echo deb [signed-by=/usr/share/keyrings/jenkins-keyring.asc] \
  https://pkg.jenkins.io/debian-stable binary/ | sudo tee \
  /etc/apt/sources.list.d/jenkins.list > /dev/null

# 步骤 3：更新并安装
sudo apt update
sudo apt install jenkins -y

# 步骤 4：启动 Jenkins
sudo systemctl start jenkins
sudo systemctl enable jenkins

# 步骤 5：检查状态
sudo systemctl status jenkins
```

### 2.3 Docker 安装方式（推荐）

```bash
# 创建 Jenkins 数据目录
mkdir -p ~/jenkins_home

# 启动 Jenkins 容器
docker run -d \
  --name jenkins \
  -p 8080:8080 \
  -p 50000:50000 \
  -v ~/jenkins_home:/var/jenkins_home \
  -v /var/run/docker.sock:/var/run/docker.sock \
  jenkins/jenkins:lts
```

---

## 3. Jenkins 初始配置

### 3.1 获取初始管理员密码

#### Windows：
```
打开文件：C:\Program Files\Jenkins\secrets\initialAdminPassword
复制里面的密码
```

#### Linux：
```bash
sudo cat /var/lib/jenkins/secrets/initialAdminPassword
```

#### Docker：
```bash
docker exec jenkins cat /var/jenkins_home/secrets/initialAdminPassword
```

### 3.2 完成初始化向导

1. **浏览器访问** `http://你的服务器IP:8080`
2. **输入初始密码**（上一步获取的密码）
3. **选择插件安装**：选择 "安装推荐的插件"
4. **创建管理员账户**：
   - 用户名：admin（或自定义）
   - 密码：设置一个强密码
   - 邮箱：你的邮箱
5. **配置 Jenkins URL**：保持默认或修改为你的域名

---

## 4. 安装必要插件

### 4.1 进入插件管理

路径：`Dashboard` → `Manage Jenkins` → `Plugins` → `Available plugins`

### 4.2 搜索并安装以下插件

| 插件名称 | 用途 |
|----------|------|
| **Git** | Git 代码管理（通常已安装） |
| **Pipeline** | Pipeline 流水线支持（通常已安装） |
| **Allure Jenkins Plugin** | Allure 报告集成 |
| **HTML Publisher** | HTML 报告发布 |
| **DingTalk** | 钉钉通知（可选） |
| **Email Extension** | 邮件通知（可选） |
| **Credentials Binding** | 凭证管理 |
| **Timestamper** | 构建日志时间戳 |

### 4.3 安装步骤

1. 在搜索框输入插件名称
2. 勾选要安装的插件
3. 点击 **Install without restart** 或 **Install**
4. 等待安装完成
5. 如提示需要重启，点击重启 Jenkins

---

## 5. 配置全局工具

路径：`Dashboard` → `Manage Jenkins` → `Tools`

### 5.1 配置 JDK

> 如果服务器已安装 JDK，可以跳过自动安装

1. 找到 **JDK installations**
2. 点击 **Add JDK**
3. 配置：
   - Name: `JDK17`
   - 取消勾选 "Install automatically"
   - JAVA_HOME: 填写你的 JDK 安装路径
     - Windows 示例：`C:\Program Files\Java\jdk-17`
     - Linux 示例：`/usr/lib/jvm/java-17-openjdk-amd64`

### 5.2 配置 Git

1. 找到 **Git installations**
2. 点击 **Add Git**
3. 配置：
   - Name: `Default`
   - Path to Git executable:
     - Windows: `C:\Program Files\Git\bin\git.exe`
     - Linux: `git`（系统会自动查找）

### 5.3 配置 Allure Commandline

1. 找到 **Allure Commandline installations**
2. 点击 **Add Allure Commandline**
3. 配置：
   - Name: `allure`
   - 方式一（自动安装）：勾选 "Install automatically"，选择版本
   - 方式二（手动指定）：
     - 取消勾选自动安装
     - 填写 Allure 安装路径（如：`D:\tools\allure-2.34.0`）

4. 点击 **Save** 保存配置

---

## 6. 创建 Jenkins 任务

### 6.1 创建 Pipeline 任务

1. 点击 **Dashboard** → **New Item**（新建任务）
2. 输入任务名称：`DuooInterfaceAuto`
3. 选择 **Pipeline**（流水线）
4. 点击 **OK**

### 6.2 配置任务 - General

1. **Description**（描述）：
   ```
   多多接口自动化测试项目 - 每日定时执行接口测试
   ```

2. **Discard old builds**（丢弃旧构建）：
   - 勾选此选项
   - Days to keep builds: `30`
   - Max # of builds to keep: `50`

### 6.3 配置任务 - Build Triggers（构建触发器）

根据你的需求选择：

#### 选项 A：定时构建（推荐）
勾选 **Build periodically**，填写 cron 表达式：

```
# 每天早上8点执行
H 8 * * *

# 每天早上8点和晚上8点执行
H 8,20 * * *

# 每周一到周五，早上9点执行
H 9 * * 1-5

# 每2小时执行一次
H */2 * * *
```

#### 选项 B：代码推送时构建
勾选 **GitHub hook trigger for GITScm polling**
（需要配置 GitHub Webhook，见第8节）

### 6.4 配置任务 - Pipeline（流水线脚本）

1. **Definition** 选择 **Pipeline script from SCM**
2. **SCM** 选择 **Git**
3. **Repositories**:
   - Repository URL: `https://github.com/你的用户名/DuooInterfaceAuto.git`
   - Credentials: 点击 **Add** 添加 GitHub 凭证（见下方说明）
4. **Branches to build**: `*/main`（或你的默认分支）
5. **Script Path**: `Jenkinsfile`

### 6.5 添加 GitHub 凭证

1. 点击 **Credentials** 旁的 **Add** → **Jenkins**
2. **Kind**: Username with password
3. **Username**: 你的 GitHub 用户名
4. **Password**: GitHub Personal Access Token（不是密码！）
5. **ID**: `github-credentials`
6. **Description**: GitHub 访问凭证
7. 点击 **Add**

> ⚠️ **获取 GitHub Token**：
> 1. 登录 GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
> 2. Generate new token
> 3. 勾选 `repo` 权限
> 4. 生成并复制 token

### 6.6 保存任务

点击页面底部的 **Save** 按钮

---

## 7. 配置 Jenkinsfile

在你的项目根目录创建 `Jenkinsfile` 文件，这是 Jenkins Pipeline 的核心配置。

### 7.1 基础版 Jenkinsfile

```groovy
pipeline {
    agent any
    
    // 环境变量
    environment {
        PYTHON_PATH = 'python'  // 或者指定完整路径，如 'C:\\Python39\\python.exe'
        TEST_ENV = 'test'       // 测试环境：dev, test, prod
    }
    
    // 构建参数（可在构建时选择）
    parameters {
        choice(
            name: 'ENV',
            choices: ['test', 'dev', 'prod'],
            description: '选择测试环境'
        )
        choice(
            name: 'MARKER',
            choices: ['', 'smoke', 'regression', 'api'],
            description: '选择测试标记（留空表示执行全部）'
        )
        string(
            name: 'PARALLEL',
            defaultValue: '0',
            description: '并行执行进程数（0表示不并行）'
        )
        booleanParam(
            name: 'SEND_DINGTALK',
            defaultValue: true,
            description: '是否发送钉钉通知'
        )
    }
    
    stages {
        // 阶段1：拉取代码
        stage('Checkout') {
            steps {
                echo '>>> 拉取代码...'
                checkout scm
            }
        }
        
        // 阶段2：环境准备
        stage('Setup Environment') {
            steps {
                echo '>>> 安装 Python 依赖...'
                bat '''
                    python -m pip install --upgrade pip
                    pip install -r requirements.txt
                '''
                // Linux 使用 sh 替代 bat：
                // sh '''
                //     python3 -m pip install --upgrade pip
                //     pip3 install -r requirements.txt
                // '''
            }
        }
        
        // 阶段3：执行测试
        stage('Run Tests') {
            steps {
                echo ">>> 执行测试 [环境: ${params.ENV}]..."
                script {
                    def markerArg = params.MARKER ? "--marker ${params.MARKER}" : ""
                    def parallelArg = params.PARALLEL != '0' ? "--xdist ${params.PARALLEL}" : ""
                    def dingtalkArg = params.SEND_DINGTALK ? "--dingtalk" : ""
                    
                    // Windows 命令
                    bat """
                        python run.py --env ${params.ENV} --allure ${markerArg} ${parallelArg} ${dingtalkArg} --reruns 2
                    """
                    
                    // Linux 命令（取消注释使用）：
                    // sh """
                    //     python3 run.py --env ${params.ENV} --allure ${markerArg} ${parallelArg} ${dingtalkArg} --reruns 2
                    // """
                }
            }
        }
        
        // 阶段4：生成 Allure 报告
        stage('Generate Allure Report') {
            steps {
                echo '>>> 生成 Allure 报告...'
                script {
                    // 查找最新的 allure_results 目录
                    def allureResultsDir = bat(
                        script: '@FOR /F "delims=" %%i IN (\'dir /b /ad /o-d reports\\allure_results_*\') DO @echo reports\\%%i & exit /b',
                        returnStdout: true
                    ).trim()
                    
                    echo "Allure 结果目录: ${allureResultsDir}"
                    
                    allure([
                        includeProperties: false,
                        jdk: '',
                        properties: [],
                        reportBuildPolicy: 'ALWAYS',
                        results: [[path: allureResultsDir]]
                    ])
                }
            }
        }
    }
    
    // 构建后操作
    post {
        always {
            echo '>>> 清理工作空间...'
            // 可选：清理临时文件
            // cleanWs()
        }
        success {
            echo '✅ 构建成功！'
        }
        failure {
            echo '❌ 构建失败！'
        }
    }
}
```

### 7.2 进阶版 Jenkinsfile（带更多功能）

```groovy
pipeline {
    agent any
    
    options {
        // 构建超时时间
        timeout(time: 1, unit: 'HOURS')
        // 显示时间戳
        timestamps()
        // 禁止并发构建
        disableConcurrentBuilds()
        // 保留最近10次构建
        buildDiscarder(logRotator(numToKeepStr: '10'))
    }
    
    environment {
        PYTHON_PATH = 'python'
        ALLURE_RESULTS = 'reports/allure_results'
    }
    
    parameters {
        choice(
            name: 'ENV',
            choices: ['test', 'dev', 'prod'],
            description: '选择测试环境'
        )
        choice(
            name: 'MARKER',
            choices: ['', 'smoke', 'regression', 'api', 'high', 'medium'],
            description: '选择测试标记'
        )
        string(
            name: 'PARALLEL',
            defaultValue: '4',
            description: '并行进程数'
        )
        booleanParam(
            name: 'SEND_DINGTALK',
            defaultValue: true,
            description: '发送钉钉通知'
        )
        string(
            name: 'RERUNS',
            defaultValue: '2',
            description: '失败重试次数'
        )
    }
    
    stages {
        stage('Checkout') {
            steps {
                echo '========== 阶段1: 拉取代码 =========='
                checkout scm
                
                // 显示 Git 信息
                script {
                    env.GIT_COMMIT_SHORT = bat(
                        script: '@git rev-parse --short HEAD',
                        returnStdout: true
                    ).trim()
                    env.GIT_BRANCH_NAME = bat(
                        script: '@git rev-parse --abbrev-ref HEAD',
                        returnStdout: true
                    ).trim()
                }
                echo "分支: ${env.GIT_BRANCH_NAME}, 提交: ${env.GIT_COMMIT_SHORT}"
            }
        }
        
        stage('Setup') {
            steps {
                echo '========== 阶段2: 环境准备 =========='
                bat '''
                    python --version
                    pip --version
                    pip install -r requirements.txt -q
                '''
            }
        }
        
        stage('Test') {
            steps {
                echo '========== 阶段3: 执行测试 =========='
                script {
                    def timestamp = new Date().format('yyyyMMdd_HHmmss')
                    env.ALLURE_RESULTS = "reports/allure_results_${timestamp}"
                    
                    def cmd = "python run.py --env ${params.ENV} --allure"
                    
                    if (params.MARKER) {
                        cmd += " --marker ${params.MARKER}"
                    }
                    if (params.PARALLEL != '0') {
                        cmd += " --xdist ${params.PARALLEL}"
                    }
                    if (params.RERUNS != '0') {
                        cmd += " --reruns ${params.RERUNS}"
                    }
                    if (params.SEND_DINGTALK) {
                        cmd += " --dingtalk"
                    }
                    
                    echo "执行命令: ${cmd}"
                    
                    // 捕获退出码但不中断流程
                    def exitCode = bat(script: cmd, returnStatus: true)
                    
                    if (exitCode != 0) {
                        echo "测试执行完成，存在失败用例（退出码: ${exitCode}）"
                        currentBuild.result = 'UNSTABLE'
                    }
                }
            }
        }
        
        stage('Report') {
            steps {
                echo '========== 阶段4: 生成报告 =========='
                script {
                    // 查找最新的 allure_results 目录
                    def findCmd = '''
                        @FOR /F "delims=" %%i IN ('dir /b /ad /o-d reports\\allure_results_* 2^>nul') DO @echo reports\\%%i& exit /b
                    '''
                    def resultsDir = bat(script: findCmd, returnStdout: true).trim()
                    
                    if (resultsDir) {
                        echo "使用结果目录: ${resultsDir}"
                        allure([
                            includeProperties: false,
                            jdk: '',
                            reportBuildPolicy: 'ALWAYS',
                            results: [[path: resultsDir]]
                        ])
                    } else {
                        echo "未找到 Allure 结果目录"
                    }
                }
            }
        }
        
        stage('Archive') {
            steps {
                echo '========== 阶段5: 归档产物 =========='
                // 归档日志文件
                archiveArtifacts(
                    artifacts: 'logs/*.log',
                    allowEmptyArchive: true,
                    fingerprint: true
                )
            }
        }
    }
    
    post {
        always {
            echo '========== 构建结束 =========='
            echo "构建结果: ${currentBuild.result ?: 'SUCCESS'}"
            echo "构建耗时: ${currentBuild.durationString}"
        }
        success {
            echo '🎉 测试全部通过！'
        }
        unstable {
            echo '⚠️ 测试存在失败用例'
        }
        failure {
            echo '❌ 构建失败'
        }
        cleanup {
            // 清理旧的测试结果目录（保留最近5个）
            bat '''
                @echo off
                setlocal enabledelayedexpansion
                set count=0
                for /f "delims=" %%i in ('dir /b /ad /o-d reports\\allure_results_* 2^>nul') do (
                    set /a count+=1
                    if !count! gtr 5 (
                        echo 删除旧目录: reports\\%%i
                        rd /s /q "reports\\%%i"
                    )
                )
            '''
        }
    }
}
```

### 7.3 将 Jenkinsfile 提交到 GitHub

```bash
# 在项目根目录执行
git add Jenkinsfile
git commit -m "feat: 添加 Jenkins CI/CD 配置"
git push origin main
```

---

## 8. 配置 Webhook（可选）

配置 Webhook 后，每次向 GitHub 推送代码时会自动触发 Jenkins 构建。

### 8.1 在 Jenkins 中配置

1. 进入任务配置页面
2. **Build Triggers** 勾选 **GitHub hook trigger for GITScm polling**
3. 保存

### 8.2 在 GitHub 中配置

1. 进入 GitHub 仓库 → **Settings** → **Webhooks** → **Add webhook**
2. 配置：
   - **Payload URL**: `http://你的Jenkins服务器IP:8080/github-webhook/`
   - **Content type**: `application/json`
   - **Secret**: 可留空或设置密钥
   - **Which events**: 选择 `Just the push event`
3. 点击 **Add webhook**

### 8.3 验证 Webhook

1. 在 GitHub Webhook 页面查看 **Recent Deliveries**
2. 应该看到绿色的 ✓ 表示配置成功
3. 尝试推送代码，观察 Jenkins 是否自动触发构建

---

## 9. 常见问题排查

### 问题 1：Python 找不到

**错误信息**：`'python' is not recognized as an internal or external command`

**解决方案**：
1. 在 Jenkins 服务器上确认 Python 已安装
2. 将 Python 添加到系统 PATH 环境变量
3. 或在 Jenkinsfile 中使用完整路径：
   ```groovy
   environment {
       PYTHON_PATH = 'C:\\Python39\\python.exe'
   }
   ```

### 问题 2：Git 凭证错误

**错误信息**：`Authentication failed` 或 `Permission denied`

**解决方案**：
1. 确认使用的是 GitHub Token 而不是密码
2. Token 需要有 `repo` 权限
3. 重新创建凭证

### 问题 3：Allure 报告不显示

**错误信息**：报告页面空白或显示 `404 Not Found`

**解决方案**：
1. 确认 Allure 插件已正确安装
2. 确认 Allure Commandline 已配置
3. 检查 `allure_results` 目录路径是否正确
4. 查看 Jenkins 控制台日志获取详细错误

### 问题 4：构建超时

**错误信息**：`Build timed out`

**解决方案**：
1. 增加超时时间：
   ```groovy
   options {
       timeout(time: 2, unit: 'HOURS')
   }
   ```
2. 减少并行数或测试用例数量

### 问题 5：依赖安装失败

**错误信息**：`pip install` 相关错误

**解决方案**：
1. 检查网络连接
2. 使用国内镜像源：
   ```groovy
   bat 'pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple'
   ```

### 问题 6：工作空间权限问题

**错误信息**：`Permission denied` 或 `Access is denied`

**解决方案**：
1. 确保 Jenkins 服务账户有读写权限
2. Windows：以管理员身份运行 Jenkins 服务
3. Linux：`sudo chown -R jenkins:jenkins /var/lib/jenkins`

---

## 📎 附录

### A. 常用 Jenkins 命令

```bash
# Linux 重启 Jenkins
sudo systemctl restart jenkins

# 查看 Jenkins 日志
sudo tail -f /var/log/jenkins/jenkins.log

# Docker 查看日志
docker logs -f jenkins
```

### B. 推荐的目录结构

```
DuooInterfaceAuto/
├── Jenkinsfile          # Jenkins Pipeline 配置（新增）
├── run.py               # 测试入口
├── pytest.ini           # pytest 配置
├── requirements.txt     # Python 依赖
├── config/              # 配置文件
├── testcases/           # 测试用例
├── utils/               # 工具类
├── reports/             # 测试报告（自动生成）
└── logs/                # 日志文件
```

### C. 参考资源

- Jenkins 官方文档：https://www.jenkins.io/doc/
- Allure 官方文档：https://docs.qameta.io/allure/
- Pipeline 语法参考：https://www.jenkins.io/doc/book/pipeline/syntax/

---

## ✅ 快速检查清单

在开始之前，确保完成以下准备工作：

- [ ] Jenkins 服务器已安装并能访问
- [ ] Python 3.9+ 已安装在 Jenkins 服务器
- [ ] Git 已安装在 Jenkins 服务器
- [ ] Allure Commandline 已安装或配置自动安装
- [ ] GitHub 仓库已创建并上传代码
- [ ] GitHub Personal Access Token 已生成
- [ ] Jenkins 必要插件已安装
- [ ] Jenkinsfile 已创建并提交到仓库
- [ ] Jenkins 任务已创建并配置

---

**文档版本**: v1.0  
**更新日期**: 2025年1月  
**适用项目**: DuooInterfaceAuto 接口自动化测试框架
