# Simple OAuth

一个轻量的本地 OAuth 工具，用来让用户自助完成授权，并直接复制 token。

目前支持：

- Facebook 广告授权
- TikTok Business API 授权
- Amazon Ads API 的 Login with Amazon 授权
- Amazon SP-API 的 Seller Central 授权

## Amazon 说明

这个项目里现在同时支持两种 Amazon 授权：

1. **Amazon Ads API**

用途：

- 拉取广告数据
- 管理广告活动
- 调用广告相关接口

2. **Amazon SP-API**

用途：

- 店铺
- 订单
- 商品
- 库存

两者虽然都基于 Login with Amazon，但授权入口、回调参数、调用域名和后续使用方式都不一样。

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

Amazon SP-API 需要重点确认这几个值：

- `AMAZON_SP_CLIENT_ID`
- `AMAZON_SP_CLIENT_SECRET`
- `AMAZON_SP_APP_ID`
- `AMAZON_SP_REDIRECT_URI`

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

6. Amazon SP-API 授权流程

- 先选地区
- 再选国家
- 然后跳转到对应 Seller Central 授权页

SP-API 这条链路会按 `superset-copilot` 的参数方式发起授权：

- `application_id`
- `client_id`
- `state`
- `redirect_uri`

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

## Amazon SP-API 授权结果

Amazon SP-API 授权成功后，页面会直接展示：

- `access_token`
- `refresh_token`
- `selling_partner_id`
- 站点对应的 SP-API endpoint
- 一份可直接复制给后端使用的 JSON 包

SP-API 更常见的用法是把 `refresh_token` 交给后端保存，再由后端换取短期 `access_token`。

注意：真正调用 SP-API 时，通常除了 `x-amz-access-token`，还需要 AWS SigV4 签名。这一点和 Amazon Ads API 不一样。

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
