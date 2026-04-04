# Simple OAuth

一个轻量的本地 OAuth 工具，用来让用户自助完成授权，并直接复制 token。

目前支持：

- Facebook 广告授权
- TikTok Business API 授权
- Amazon Ads API 的 Login with Amazon 授权

## Amazon 说明

这个项目里新增的 Amazon 授权，针对的是 **Amazon Ads API**。

它的用途是：

- 拉取广告数据
- 管理广告活动
- 调用广告相关接口

它不是 SP-API。

SP-API 更偏卖家侧数据，比如：

- 店铺
- 订单
- 商品
- 库存

两者虽然都可能基于 Login with Amazon，但实际调用接口、请求头和后续使用方式不一样。

## 本地运行

1. 安装依赖

```bash
uv sync
```

2. 配置环境变量

```bash
cp .env.example .env
```

按需填写你要启用的平台配置。

Amazon Ads 需要重点确认这几个值：

- `AMAZON_AD_CLIENT_ID`
- `AMAZON_AD_CLIENT_SECRET`
- `AMAZON_AD_REDIRECT_URI`

3. 启动服务

```bash
uv run fb-oauth
```

4. 打开浏览器

访问 [http://localhost:5001](http://localhost:5001)

5. Amazon Ads 授权流程

- 先选地区
- 再选国家
- 然后跳转到对应 Amazon 授权页

`scope` 已固定为后端同款的 `advertising::campaign_management`，不需要你手动配置。

## Amazon Ads 授权结果

Amazon Ads 授权成功后，页面会直接展示：

- `access_token`
- `refresh_token`
- 按 `NA / EU / FE` 聚合的 profile 列表
- 调广告 API 需要的 header 模板
- 一份可直接复制给后端使用的 JSON 包

调用 Amazon Ads API 时，除了 `Authorization: Bearer <access_token>`，还需要：

- `Amazon-Advertising-API-ClientId`
- `Amazon-Advertising-API-Scope: <profile_id>`

其中 `profile_id` 需要从授权成功页里返回的 profiles 中选择。

## Docker

### Docker Compose

```bash
docker compose up -d --build
docker compose down
```

### Docker CLI

```bash
docker build -t simple-oauth .
docker run -p 5001:5001 --env-file .env simple-oauth
```
