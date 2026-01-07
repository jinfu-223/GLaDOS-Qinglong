# GLaDOS 自动签到脚本

## 更新日志

### 2026-01-07
- ✨ **域名更换**: API 地址从 `glados.rocks` 更新为 `glados.space`
- ✨ **重试机制**: 新增请求超时（15秒）和自动重试（最多3次）功能
- ✨ **本地测试支持**: 支持 `.env` 文件配置环境变量（需安装 `python-dotenv`）
- ✨ **错误处理优化**: 改进 Cookie 无效时的错误提示信息

## 依赖安装

```bash
pip install requests pandas python-dotenv
```

## 青龙面板部署

1. **自动添加**：订阅管理中创建订阅，复制仓库链接 https://github.com/dff652/GLaDOS-Qinglong.git  
   **手动添加**：下载脚本文件 `glados_sign_in.py`，在青龙面板的脚本管理中添加脚本
2. **设置环境变量**：
   - `GLADOS_COOKIE`（必要）：多个账号使用 `&` 隔开，示例：`cookie1;&cookie2`，每个 cookie 结尾后要加上 `;`
   - `PUSHPLUS_TOKEN`（非必要）
   - `WEBHOOK_CODE`（参考 pushplus 设置教程）
3. 添加定时任务，设置命令和定时规则

## 本地测试

1. 复制 `.env.example` 为 `.env`
2. 填写你的真实 Cookie 值（**不要加引号**）
3. 运行脚本：`python glados_sign_in.py`

## pushplus 设置流程

1. 注册 pushplus 获取自己的 token
2. 配置 webhook 渠道，如钉钉机器人等，参考 https://www.pushplus.plus/doc/extend/webhook.html
3. 配置好钉钉机器人后设置 webhook 编码

## 效果展示

![image](https://github.com/user-attachments/assets/989166a8-9699-4841-ba53-a0935a98a747)




# 参考项目：
1. https://github.com/Devilstore/Gladoscheckin
2. https://github.com/domeniczz/GLaDOS_checkin_auto
