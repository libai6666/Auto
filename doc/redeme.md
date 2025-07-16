# 接口测试自动化框架

## 项目介绍
本项目是一个基于Python + Pytest + Requests的接口测试自动化框架，用于进行高效、稳定的API接口自动化测试。框架采用模块化设计，支持数据驱动测试，提供丰富的断言方式和报告生成功能。

## 技术栈
- Python 3.8+
- Pytest：测试框架
- Requests：HTTP请求库
- PyYAML：处理YAML格式的测试数据
- Allure：测试报告生成
- Loguru：日志管理
- PyMySQL/SQLAlchemy：数据库操作（可选）

## 框架结构
```
DuooInterfaceAuto/
├── config/                 # 配置文件目录
│   ├── config.yaml         # 主配置文件（环境、URL、请求配置、测试控制）
│   ├── db_config.yaml      # 数据库配置（连接信息、查询超时等）
│   ├── email_config.yaml   # 邮件配置（SMTP服务器、账号等）
│   └── users.yaml          # 测试用户配置（登录凭证、权限等）
├── data/                   # 测试数据目录
│   └── api_data/           # API测试数据（YAML格式，包含请求和预期结果）
│       └── user.yaml       # 用户相关接口测试数据
├── logs/                   # 日志目录（存储测试运行日志）
├── reports/                # 测试报告目录（存储HTML报告和Allure报告）
├── testcases/              # 测试用例目录
│   ├── conftest.py         # Pytest配置文件（夹具和钩子函数）
│   ├── __init__.py         # 包初始化文件
│   ├── module1/            # 按模块组织测试用例
│   │   ├── __init__.py     # 模块初始化文件
│   │   └── test_user_nick.py # 用户昵称功能测试
│   └── module2/            # 其他模块测试用例  
├── utils/                  # 工具类目录
│   ├── __init__.py         # 工具包初始化文件
│   ├── api_client.py       # 请求封装（HTTP客户端基类，处理重试、日志等）
│   ├── assert_utils.py     # 断言工具（提供多种断言方式和规则）
│   ├── client_factory.py   # 客户端工厂（创建和管理用户客户端）
│   ├── data_handler.py     # 数据处理工具（加载配置、测试数据、变量替换）
│   ├── db_utils.py         # 数据库工具（数据库连接和操作封装）
│   ├── logger.py           # 日志工具（统一日志记录和配置）
│   └── user_client.py      # 用户客户端（继承API客户端，封装用户操作）
├── requirements.txt        # 项目依赖
├── pytest.ini              # Pytest配置（测试发现规则、插件配置等）
├── run.py                  # 启动测试的入口（命令行参数解析、测试执行）
└── README.md               # 项目说明文档
```

## 核心组件说明

### 1. 配置文件 (config/)

#### 1.1 config.yaml
主配置文件，包含以下内容：
- 环境配置：当前环境和各环境基础URL
- 请求配置：默认请求头、超时设置、重试策略
- 测试控制：失败重试、截图设置、报告生成

#### 1.2 db_config.yaml
数据库配置文件，包含各环境的数据库连接信息：
- 数据库类型
- 主机和端口
- 用户名和密码
- 连接池设置

#### 1.3 users.yaml
测试用户配置文件，包含各测试账号信息：
- 手机号和国家代码
- 用户描述信息
- 可选的密码或固定验证码

### 2. 工具类 (utils/)

#### 2.1 api_client.py
HTTP请求封装，核心功能：
- 自动管理会话和请求头
- 请求重试机制
- 详细请求和响应日志
- 支持常见HTTP方法和文件上传/下载

#### 2.2 user_client.py
用户客户端，继承自api_client.py，提供：
- 自动登录功能
- 用户信息管理
- 用户相关API的封装（如修改昵称）

#### 2.3 client_factory.py
客户端工厂，用于创建和管理用户客户端：
- 根据配置创建不同用户的客户端
- 缓存已创建的客户端实例
- 支持创建自定义客户端

#### 2.4 data_handler.py
数据处理工具，提供：
- 配置文件加载
- 测试数据读写
- 变量替换和随机数据生成
- 响应数据提取

#### 2.5 assert_utils.py
断言工具，支持多种断言方式：
- 状态码断言
- 响应内容包含断言
- JSON路径值断言
- 正则表达式断言
- 复合断言规则

#### 2.6 db_utils.py
数据库工具，提供：
- 数据库连接管理
- SQL查询和执行
- 查询结果处理
- 事务管理

#### 2.7 logger.py
日志工具，基于loguru实现：
- 统一日志格式
- 日志轮转和保留
- 多级别日志输出
- 控制台和文件双输出

### 3. 测试用例 (testcases/)

#### 3.1 conftest.py
Pytest配置和全局夹具：
- API客户端夹具
- 数据库处理器夹具
- 客户端工厂夹具
- 会话变量夹具
- 测试前后钩子函数

#### 3.2 模块化测试用例
按功能模块组织的测试用例：
- module1/test_user_nick.py：用户昵称功能测试
- 其他模块化测试文件

### 4. 测试数据 (data/)

#### 4.1 api_data/
YAML格式的测试数据文件：
- 请求信息（URL、方法、参数）
- 预期结果（状态码、内容、JSON结构）
- 支持变量和引用

### 5. 执行入口 (run.py)

测试执行的主入口：
- 命令行参数解析
- 环境和测试范围选择
- 测试执行和报告生成
- 测试结果处理

## 安装与配置

### 环境要求
- Python 3.8 或更高版本
- pip 包管理工具

### 安装Python环境（使用pyenv-win）

1. **安装pyenv-win**：
   - 使用PowerShell（以管理员身份运行）执行以下命令：
   ```powershell
   Invoke-WebRequest -UseBasicParsing -Uri "https://raw.githubusercontent.com/pyenv-win/pyenv-win/master/pyenv-win/install-pyenv-win.ps1" -OutFile "./install-pyenv-win.ps1"; &"./install-pyenv-win.ps1"
   ```
   - 或者使用Git:
   ```
   git clone https://github.com/pyenv-win/pyenv-win.git "%USERPROFILE%\.pyenv"
   ```

2. **设置环境变量**：
   - 安装脚本通常会自动设置环境变量，但如果需要手动设置，添加以下变量：
   ```
   PYENV: %USERPROFILE%\.pyenv\pyenv-win
   PATH: %PYENV%\bin;%PYENV%\shims
   ```
   - 重启PowerShell或命令提示符使环境变量生效

3. **验证安装**：
   ```
   pyenv --version
   ```

4. **查看可安装的Python版本**：
   ```
   pyenv install -l
   ```

5. **安装Python版本**：
   ```
   pyenv install 3.8.10
   ```
   - 此过程可能需要几分钟，取决于网络速度和计算机性能

6. **设置全局Python版本**：
   ```
   pyenv global 3.8.10
   ```

7. **验证Python版本**：
   ```
   python --version
   ```

### 管理多个Python版本

1. **安装多个版本**：
   ```
   pyenv install 3.9.9
   pyenv install 3.10.4
   ```

2. **在特定目录使用指定版本**：
   - 进入项目目录，设置本地Python版本：
   ```
   cd D:\tools\Pycharm\PycharmWork\DuooInterfaceAuto
   pyenv local 3.8.10
   ```
   - 这会在项目目录创建一个`.python-version`文件来标记使用的Python版本

3. **切换版本**：
   ```
   # 切换全局版本
   pyenv global 3.9.9
   
   # 切换当前会话版本
   pyenv shell 3.10.4
   
   # 恢复为系统Python
   pyenv global system
   ```

4. **查看已安装的版本**：
   ```
   pyenv versions
   ```

### 创建虚拟环境

pyenv-win与venv结合使用可以为不同Python版本创建虚拟环境：

1. **创建虚拟环境**：
   ```
   # 确保使用正确的Python版本
   pyenv local 3.8.10
   
   # 创建虚拟环境
   python -m venv venv
   ```

2. **激活虚拟环境**：
   ```
   # PowerShell
   .\venv\Scripts\activate
   
   # 如果PowerShell执行策略限制，先运行
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process
   
   # CMD
   venv\Scripts\activate.bat
   ```

3. **安装依赖**：
   ```
   pip install -r requirements.txt
   ```

4. **退出虚拟环境**：
   ```
   deactivate
   ```

## 运行测试框架

### 基本运行
```bash
# 运行所有测试
python run.py

# 运行特定模块测试
python run.py --module module1

# 生成HTML报告
python run.py --report --open

# 生成Allure报告
python run.py --allure --open

# 指定环境
python run.py --env test

# 运行标记的测试用例
python run.py --marker smoke
```

### 命令行参数
run.py支持以下命令行参数：
- `--env`：指定测试环境（dev, test, prod）
- `--case`：指定要运行的测试用例
- `--module`：指定要运行的测试模块
- `--marker`：指定要运行的测试标记
- `--report`：生成HTML报告
- `--allure`：生成Allure报告
- `--open`：在浏览器中打开报告
- `--xdist`：并行执行测试的进程数
- `--reruns`：失败重试次数
- `--debug`：启用调试模式

## 测试用例编写

### 数据驱动测试
在data/api_data/目录下创建YAML文件定义测试数据：
```yaml
# 测试用例标题
test_login:
  # 请求信息
  request:
    method: POST
    url: /api/v1/login
    headers:
      Content-Type: application/json
    json:
      username: test_user
      password: test_pass
  # 预期结果
  expected:
    status_code: 200
    contains: "login success"
    json:
      code: 0
      message: "登录成功"
```

### 测试类编写
在testcases/目录下创建测试文件：
```python
import pytest
import allure
from utils.data_handler import load_test_data

@allure.feature("用户管理")
class TestUserAPI:
    
    @allure.story("用户登录")
    @allure.title("测试成功登录")
    @pytest.mark.smoke
    def test_login_success(self, client_factory):
        """测试用户成功登录"""
        # 获取客户端
        client = client_factory.get_client("user1")
        
        # 执行登录
        success = client.login()
        
        # 断言
        assert success, "用户登录失败"
        assert client.get_user_id() is not None, "登录成功但未获取到用户ID"
```

## 框架特性和最佳实践

### 1. 分层架构
- 测试数据、测试逻辑和工具类严格分离
- 便于维护和扩展

### 2. 数据驱动
- 使用YAML配置测试数据
- 实现数据与代码分离
- 支持变量替换和随机数据

### 3. 多环境支持
- 配置文件支持多环境
- 简单切换测试环境
- 环境特定配置管理

### 4. 灵活断言
- 支持多种断言方式
- 自定义断言规则
- 清晰的断言失败信息

### 5. 详细日志和报告
- 请求和响应详细日志
- 支持HTML和Allure报告
- 失败用例屏幕截图

## 执行流程详解

run.py执行流程：
1. 解析命令行参数
2. 设置工作目录和日志
3. 构建pytest命令参数
4. 执行测试用例
5. 生成测试报告
6. 处理测试结果

具体测试执行过程：
1. pytest加载测试模块和用例
2. 执行conftest.py中的夹具和钩子
3. 运行测试前准备（如登录）
4. 执行测试步骤和断言
5. 记录测试结果和日志
6. 运行测试后清理

---

© 2023 DuooInterfaceAuto 团队