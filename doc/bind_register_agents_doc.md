# 批量代理注册脚本

## 功能介绍

本脚本用于批量注册代理账号，实现了完整的注册流程，包括：

1. 登录管理后台
2. 生成邀请码
3. 获取未使用的邀请码
4. 发送验证码
5. 获取验证码
6. 注册代理

## 使用方法

### 命令行参数

```bash
python scripts/batch_register_agents.py [options]
```

#### 选项说明：

- `--count`, `-c`: 要注册的代理数量，默认为1
- `--base-phone`: 基础手机号，会依次递增，默认为"13800000000"
- `--area-code`: 国别码，默认为"86"
- `--name-prefix`: 代理名称前缀，会加上手机号后四位，默认为"autoAgent"
- `--country`: 国家代码，可选值为"CN"或"IN"，不指定则随机选择
- `--env`: 执行环境，可选值为"dev"、"test"或"prod"，默认为"test"
- `--debug`: 是否开启调试模式，不需要值

### 示例

1. 注册单个代理（默认）：

```bash
python scripts/batch_register_agents.py
```

2. 注册多个代理：

```bash
python scripts/batch_register_agents.py --count 5
```

3. 指定手机号和国别码：

```bash
python scripts/batch_register_agents.py --base-phone 13900000000 --area-code 86
```

4. 指定代理名称前缀和国家：

```bash
python scripts/batch_register_agents.py --name-prefix myAgent --country CN
```

5. 在开发环境中执行并开启调试模式：

```bash
python scripts/batch_register_agents.py --env dev --debug
```

## 输出说明

脚本执行过程中会输出详细的日志信息，包括：

- 执行参数信息
- 注册过程中的每个步骤
- 注册成功或失败的原因
- 最终统计结果

## 注意事项

1. 脚本需要在项目根目录下执行，或者确保项目根目录在Python路径中
2. 确保网络环境可以正常访问API服务器
3. 默认使用固定的管理员账号密码登录管理后台
4. 每个注册成功的代理信息会保存在日志中，可以查看日志获取注册结果
5. 为避免请求过于频繁，每次注册成功后会有1秒的延迟 