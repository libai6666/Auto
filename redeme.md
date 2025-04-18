# 接口测试自动化框架

## 项目介绍
本项目是一个基于Python + Pytest + Requests的接口测试自动化框架，用于进行高效、稳定的API接口自动化测试。

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
│   ├── config.yaml         # 主配置文件（环境、URL等）
│   ├── db_config.yaml      # 数据库配置
│   └── email_config.yaml   # 邮件配置（可选）
├── data/                   # 测试数据目录
│   └── api_data/           # API测试数据（YAML格式）
├── logs/                   # 日志目录
├── reports/                # 测试报告目录
├── testcases/              # 测试用例目录
│   ├── conftest.py         # Pytest配置文件
│   ├── module1/            # 按模块组织测试用例
│   └── module2/            
├── utils/                  # 工具类目录
│   ├── api_client.py       # 请求封装
│   ├── assert_utils.py     # 断言工具
│   ├── db_utils.py         # 数据库工具
│   ├── logger.py           # 日志工具
│   └── data_handler.py     # 数据处理工具
├── requirements.txt        # 项目依赖
├── pytest.ini              # Pytest配置
├── run.py                  # 启动测试的入口
└── README.md               # 项目说明文档
```

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

1. **基本运行**：
   - 确保虚拟环境已激活
   - 执行以下命令运行所有测试：
   ```
   python run.py
   ```

2. **运行特定测试**：
   - 运行冒烟测试：
   ```
   python run.py --marker smoke
   ```
   - 运行特定模块：
   ```
   python run.py --module module1
   ```
   - 生成HTML报告：
   ```
   python run.py --report --open
   ```
   - 生成Allure报告（需要先安装Allure）：
   ```
   python run.py --allure --open
   ```

3. **安装Allure**（可选）：
   - 要使用Allure报告，需要先安装Allure命令行工具：
   - 下载[Allure](https://github.com/allure-framework/allure2/releases)
   - 解压到一个目录，例如：`D:\allure`
   - 将allure的bin目录添加到系统PATH环境变量：`D:\allure\bin`
   - 重新打开命令提示符，验证安装：`allure --version`

## 使用指南

### 编写测试数据
在 `data/api_data/` 目录下创建YAML文件，按照以下格式定义测试数据：

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

### 编写测试用例
在 `testcases/` 目录下创建测试文件，例如：

```python
import pytest
import allure
from utils.api_client import APIClient
from utils.data_handler import load_test_data

@allure.feature("用户管理")
class TestUserAPI:
    
    @allure.story("用户登录")
    @allure.title("测试成功登录")
    def test_login_success(self, api_client):
        """测试用户成功登录"""
        # 加载测试数据
        test_data = load_test_data("user/login.yaml", "test_login")
        
        # 发送请求
        response = api_client.request(
            method=test_data["request"]["method"],
            url=test_data["request"]["url"],
            headers=test_data["request"]["headers"],
            json=test_data["request"]["json"]
        )
        
        # 断言
        assert response.status_code == test_data["expected"]["status_code"]
        assert test_data["expected"]["contains"] in response.text
        
        # JSON响应断言
        response_json = response.json()
        assert response_json["code"] == test_data["expected"]["json"]["code"]
        assert response_json["message"] == test_data["expected"]["json"]["message"]
```

### 运行测试
使用以下命令运行测试：

```bash
# 运行所有测试
pytest

# 运行特定模块测试
pytest testcases/module1/

# 生成Allure报告
pytest --alluredir=./reports/allure-results
allure serve ./reports/allure-results
```

或使用入口文件：

```bash
python run.py
```

## 核心功能

### API客户端封装
`utils/api_client.py` 封装了Requests库，提供统一的请求方法：

```python
# 简化示例
class APIClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()
    
    def request(self, method, url, **kwargs):
        full_url = self.base_url + url
        response = self.session.request(method, full_url, **kwargs)
        # 日志记录请求和响应
        return response
```

### 测试数据管理
`utils/data_handler.py` 提供测试数据的加载和处理：

```python
# 简化示例
def load_test_data(file_path, key=None):
    """从YAML文件加载测试数据"""
    with open(f"data/api_data/{file_path}", "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data[key] if key else data
```

### 日志管理
`utils/logger.py` 基于Loguru实现统一的日志管理：

```python
# 简化示例
from loguru import logger

def setup_logger():
    logger.add(
        "logs/api_test_{time}.log",
        rotation="1 day",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {message}"
    )
    return logger
```

### 数据库工具
`utils/db_utils.py` 提供数据库操作能力：

```python
# 简化示例
import pymysql
from pymysql.cursors import DictCursor

class DBHandler:
    def __init__(self, config):
        self.conn = pymysql.connect(**config)
    
    def query(self, sql):
        with self.conn.cursor(DictCursor) as cursor:
            cursor.execute(sql)
            return cursor.fetchall()
```

## 高级特性

### 钩子函数
在 `testcases/conftest.py` 中定义全局夹具和钩子：

```python
import pytest
from utils.api_client import APIClient
from utils.logger import setup_logger
from utils.data_handler import load_config

# 初始化日志
logger = setup_logger()

@pytest.fixture(scope="session")
def api_client():
    """创建并返回API客户端实例"""
    config = load_config()
    base_url = config["base_url"]
    client = APIClient(base_url=base_url)
    return client

@pytest.hookimpl(tryfirst=True)
def pytest_runtest_setup(item):
    """测试用例开始前执行"""
    logger.info(f"开始执行: {item.nodeid}")
```

### 参数化测试
利用Pytest的参数化功能：

```python
@pytest.mark.parametrize("user_id, expected_name", [
    ("1001", "张三"),
    ("1002", "李四"),
    ("1003", "王五")
])
def test_get_user_info(api_client, user_id, expected_name):
    """参数化测试获取用户信息"""
    response = api_client.request("GET", f"/api/users/{user_id}")
    assert response.status_code == 200
    user_data = response.json()
    assert user_data["name"] == expected_name
```

## 最佳实践

1. **分层设计**：将测试数据、测试用例和工具类分离
2. **数据驱动**：使用YAML文件管理测试数据
3. **良好的报告**：集成Allure生成详细的测试报告
4. **日志管理**：记录详细的请求、响应和断言信息
5. **环境隔离**：支持多环境配置切换
6. **持续集成**：易于集成Jenkins等CI工具

## 常见问题

### Q: 如何切换测试环境？
A: 修改 `config/config.yaml` 文件中的 `current_env` 配置项。

### Q: 如何添加自定义断言？
A: 在 `utils/assert_utils.py` 中添加新的断言方法，然后在测试用例中使用。

### Q: 如何处理接口依赖？
A: 使用Pytest夹具管理接口依赖，或在 `utils/data_handler.py` 中实现数据关联功能。

### Q: 如何使用不同Python版本运行测试？
A: 使用pyenv-win切换到所需Python版本，然后运行测试：
```
pyenv local 3.9.9
python -m venv venv_py39
.\venv_py39\Scripts\activate
pip install -r requirements.txt
python run.py
```

---

© 2023 DuooInterfaceAuto 团队