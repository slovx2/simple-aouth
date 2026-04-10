from __future__ import annotations

import html
import json
import os
import secrets
from dataclasses import dataclass
from typing import Any
from urllib.parse import parse_qs, urlencode, urlparse, urlunparse

import requests
from dotenv import load_dotenv
from flask import Flask, redirect, request, session

load_dotenv()


@dataclass(frozen=True)
class ProviderCard:
    key: str
    title: str
    description: str
    accent_color: str
    action_text: str
    auth_url: str
    enabled: bool
    disabled_reason: str
    extra_actions: tuple[tuple[str, str], ...] = ()


@dataclass(frozen=True)
class AmazonAdsRegion:
    key: str
    label: str
    host: str


@dataclass(frozen=True)
class AmazonAdsCountry:
    code: str
    label: str
    region_key: str
    auth_url: str


@dataclass(frozen=True)
class AmazonSpRegion:
    key: str
    label: str
    endpoint: str


@dataclass(frozen=True)
class AmazonSpCountry:
    code: str
    label: str
    region_key: str
    seller_central_url: str


app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", secrets.token_hex(32))

PORT = int(os.getenv("PORT", "5001"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "30"))
OAUTH_DEBUG = os.getenv("OAUTH_DEBUG", "").strip().lower() in {"1", "true", "yes", "on"}

# Facebook OAuth 配置
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
FACEBOOK_REDIRECT_URI = os.getenv("REDIRECT_URI", f"http://localhost:{PORT}/fb/callback")
FACEBOOK_SCOPE = os.getenv("FACEBOOK_SCOPE", "ads_read,ads_management")
FACEBOOK_API_VERSION = "v21.0"
FACEBOOK_OAUTH_URL = f"https://www.facebook.com/{FACEBOOK_API_VERSION}/dialog/oauth"
FACEBOOK_TOKEN_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/oauth/access_token"
FACEBOOK_GRAPH_API_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/me"

# TikTok Business OAuth 配置
TIKTOK_APP_ID = os.getenv("TIKTOK_APP_ID")
TIKTOK_APP_SECRET = os.getenv("TIKTOK_APP_SECRET")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", f"http://localhost:{PORT}/tiktok/callback")
TIKTOK_SCOPE = os.getenv("TIKTOK_SCOPE", "user.info.basic")
TIKTOK_OAUTH_URL = "https://business-api.tiktok.com/portal/auth"
TIKTOK_TOKEN_URL = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
TIKTOK_ADVERTISER_URL = "https://business-api.tiktok.com/open_api/v1.3/oauth2/advertiser/get/"

# Amazon Ads OAuth 配置
AMAZON_AD_CLIENT_ID = os.getenv("AMAZON_AD_CLIENT_ID")
AMAZON_AD_CLIENT_SECRET = os.getenv("AMAZON_AD_CLIENT_SECRET")
AMAZON_AD_REDIRECT_URI = os.getenv(
    "AMAZON_AD_REDIRECT_URI",
    f"http://localhost:{PORT}/amazon-ads/callback",
)
AMAZON_AD_TOKEN_URL = os.getenv("AMAZON_AD_TOKEN_URL", "https://api.amazon.com/auth/o2/token")
AMAZON_AD_PROFILE_PATH = "/v2/profiles"
AMAZON_AD_SCOPE = "advertising::campaign_management"
AMAZON_AD_REGIONS: tuple[AmazonAdsRegion, ...] = (
    AmazonAdsRegion("NA", "北美", "https://advertising-api.amazon.com"),
    AmazonAdsRegion("EU", "欧洲", "https://advertising-api-eu.amazon.com"),
    AmazonAdsRegion("FE", "远东", "https://advertising-api-fe.amazon.com"),
)
AMAZON_AD_COUNTRIES: tuple[AmazonAdsCountry, ...] = (
    AmazonAdsCountry("US", "美国", "NA", "https://www.amazon.com/ap/oa"),
    AmazonAdsCountry("CA", "加拿大", "NA", "https://www.amazon.com/ap/oa"),
    AmazonAdsCountry("MX", "墨西哥", "NA", "https://www.amazon.com/ap/oa"),
    AmazonAdsCountry("BR", "巴西", "NA", "https://www.amazon.com/ap/oa"),
    AmazonAdsCountry("GB", "英国", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("DE", "德国", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("ES", "西班牙", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("FR", "法国", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("IT", "意大利", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("NL", "荷兰", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("TR", "土耳其", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("AE", "阿联酋", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("SA", "沙特阿拉伯", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("IN", "印度", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("PL", "波兰", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("SE", "瑞典", "EU", "https://eu.account.amazon.com/ap/oa"),
    AmazonAdsCountry("SG", "新加坡", "FE", "https://apac.account.amazon.com/ap/oa"),
    AmazonAdsCountry("JP", "日本", "FE", "https://apac.account.amazon.com/ap/oa"),
    AmazonAdsCountry("AU", "澳大利亚", "FE", "https://apac.account.amazon.com/ap/oa"),
)

# Amazon SP-API OAuth 配置
AMAZON_SP_CLIENT_ID = os.getenv("AMAZON_SP_CLIENT_ID")
AMAZON_SP_CLIENT_SECRET = os.getenv("AMAZON_SP_CLIENT_SECRET")
AMAZON_SP_APP_ID = os.getenv("AMAZON_SP_APP_ID")
AMAZON_SP_REDIRECT_URI = os.getenv(
    "AMAZON_SP_REDIRECT_URI",
    f"http://localhost:{PORT}/amazon-sp/callback",
)
AMAZON_SP_TOKEN_URL = os.getenv("AMAZON_SP_TOKEN_URL", "https://api.amazon.com/auth/o2/token")
AMAZON_SP_AUTH_PATH = "/apps/authorize/consent"
AMAZON_SP_REGIONS: tuple[AmazonSpRegion, ...] = (
    AmazonSpRegion("NA", "北美", "https://sellingpartnerapi-na.amazon.com"),
    AmazonSpRegion("EU", "欧洲", "https://sellingpartnerapi-eu.amazon.com"),
    AmazonSpRegion("SG", "新加坡", "https://sellingpartnerapi-fe.amazon.com"),
    AmazonSpRegion("JP", "日本", "https://sellingpartnerapi-fe.amazon.com"),
    AmazonSpRegion("AU", "澳大利亚", "https://sellingpartnerapi-fe.amazon.com"),
)
AMAZON_SP_COUNTRIES: tuple[AmazonSpCountry, ...] = (
    AmazonSpCountry("US", "美国", "NA", "https://sellercentral.amazon.com"),
    AmazonSpCountry("CA", "加拿大", "NA", "https://sellercentral.amazon.ca"),
    AmazonSpCountry("MX", "墨西哥", "NA", "https://sellercentral.amazon.com.mx"),
    AmazonSpCountry("BR", "巴西", "NA", "https://sellercentral.amazon.com.br"),
    AmazonSpCountry("GB", "英国", "EU", "https://sellercentral-europe.amazon.com"),
    AmazonSpCountry("DE", "德国", "EU", "https://sellercentral-europe.amazon.com"),
    AmazonSpCountry("ES", "西班牙", "EU", "https://sellercentral-europe.amazon.com"),
    AmazonSpCountry("FR", "法国", "EU", "https://sellercentral-europe.amazon.com"),
    AmazonSpCountry("IT", "意大利", "EU", "https://sellercentral-europe.amazon.com"),
    AmazonSpCountry("NL", "荷兰", "EU", "https://sellercentral.amazon.nl"),
    AmazonSpCountry("TR", "土耳其", "EU", "https://sellercentral.amazon.com.tr"),
    AmazonSpCountry("AE", "阿联酋", "EU", "https://sellercentral.amazon.ae"),
    AmazonSpCountry("SA", "沙特阿拉伯", "EU", "https://sellercentral.amazon.sa"),
    AmazonSpCountry("IN", "印度", "EU", "https://sellercentral.amazon.in"),
    AmazonSpCountry("PL", "波兰", "EU", "https://sellercentral.amazon.pl"),
    AmazonSpCountry("SE", "瑞典", "EU", "https://sellercentral.amazon.se"),
    AmazonSpCountry("SG", "新加坡", "SG", "https://sellercentral.amazon.sg"),
    AmazonSpCountry("JP", "日本", "JP", "https://sellercentral.amazon.co.jp"),
    AmazonSpCountry("AU", "澳大利亚", "AU", "https://sellercentral.amazon.com.au"),
)

STATE_SESSION_PREFIX = "oauth_state:"
STATE_CONTEXT_SESSION_PREFIX = "oauth_state_context:"


def html_escape(value: Any) -> str:
    return html.escape("" if value is None else str(value))


def pretty_json(data: Any) -> str:
    return json.dumps(data, ensure_ascii=False, indent=2)


def build_url(base_url: str, params: dict[str, Any]) -> str:
    filtered_params = {
        key: value
        for key, value in params.items()
        if value not in (None, "")
    }
    return f"{base_url}?{urlencode(filtered_params)}"


def get_amazon_region(region_key: str) -> AmazonAdsRegion | None:
    for region in AMAZON_AD_REGIONS:
        if region.key == region_key:
            return region
    return None


def get_amazon_country(country_code: str) -> AmazonAdsCountry | None:
    upper_code = country_code.upper()
    for country in AMAZON_AD_COUNTRIES:
        if country.code == upper_code:
            return country
    return None


def get_amazon_countries_by_region(region_key: str) -> list[AmazonAdsCountry]:
    return [country for country in AMAZON_AD_COUNTRIES if country.region_key == region_key]


def get_amazon_sp_region(region_key: str) -> AmazonSpRegion | None:
    for region in AMAZON_SP_REGIONS:
        if region.key == region_key:
            return region
    return None


def get_amazon_sp_country(country_code: str) -> AmazonSpCountry | None:
    upper_code = country_code.upper()
    for country in AMAZON_SP_COUNTRIES:
        if country.code == upper_code:
            return country
    return None


def get_amazon_sp_countries_by_region(region_key: str) -> list[AmazonSpCountry]:
    return [country for country in AMAZON_SP_COUNTRIES if country.region_key == region_key]


def create_state(provider_key: str, context: dict[str, Any] | None = None) -> str:
    state = secrets.token_urlsafe(24)
    session[f"{STATE_SESSION_PREFIX}{provider_key}"] = state
    if context:
        session[f"{STATE_CONTEXT_SESSION_PREFIX}{provider_key}:{state}"] = context
    return state


def consume_state(provider_key: str, state: str | None) -> tuple[bool, dict[str, Any]]:
    saved_state = session.pop(f"{STATE_SESSION_PREFIX}{provider_key}", None)
    if saved_state:
        saved_context = session.pop(f"{STATE_CONTEXT_SESSION_PREFIX}{provider_key}:{saved_state}", {})
    else:
        saved_context = {}
    if not saved_state or not state:
        return False, {}
    return saved_state == state, saved_context if saved_state == state else {}


def request_json(
    method: str,
    url: str,
    *,
    params: dict[str, Any] | None = None,
    data: dict[str, Any] | None = None,
    json_body: dict[str, Any] | None = None,
    headers: dict[str, str] | None = None,
) -> Any:
    response = requests.request(
        method=method,
        url=url,
        params=params,
        data=data,
        json=json_body,
        headers=headers,
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


def render_page(page_title: str, body_html: str) -> str:
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{html_escape(page_title)}</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            :root {{
                --bg: #f3f5f8;
                --panel: #ffffff;
                --text: #1f2328;
                --subtle: #5f6b7a;
                --border: #d9dee5;
                --shadow: 0 12px 36px rgba(15, 23, 42, 0.08);
                --warning-bg: #fff5db;
                --warning-border: #f2c76e;
                --warning-text: #7a5800;
                --success: #1a7f37;
                --code-bg: #f7f9fb;
            }}
            * {{
                box-sizing: border-box;
            }}
            body {{
                margin: 0;
                padding: 24px;
                min-height: 100vh;
                background: radial-gradient(circle at top, #ffffff 0%, var(--bg) 45%, #e8edf5 100%);
                color: var(--text);
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            }}
            a {{
                color: inherit;
            }}
            .page {{
                width: min(1120px, 100%);
                margin: 0 auto;
            }}
            .panel {{
                background: var(--panel);
                border: 1px solid var(--border);
                border-radius: 20px;
                box-shadow: var(--shadow);
                padding: 28px;
            }}
            .hero {{
                text-align: center;
                margin-bottom: 24px;
            }}
            .hero h1 {{
                margin: 0 0 12px 0;
                font-size: clamp(28px, 4vw, 42px);
            }}
            .hero p {{
                margin: 0;
                color: var(--subtle);
                line-height: 1.6;
            }}
            .cards {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
                gap: 18px;
            }}
            .card {{
                border: 1px solid var(--border);
                border-radius: 18px;
                padding: 20px;
                display: flex;
                flex-direction: column;
                gap: 14px;
                background: #fff;
            }}
            .card-top {{
                display: flex;
                flex-direction: column;
                gap: 8px;
            }}
            .card-accent {{
                width: 56px;
                height: 6px;
                border-radius: 999px;
            }}
            .card h2 {{
                margin: 0;
                font-size: 22px;
            }}
            .card p {{
                margin: 0;
                color: var(--subtle);
                line-height: 1.6;
            }}
            .button-row {{
                display: flex;
                flex-wrap: wrap;
                gap: 10px;
                margin-top: auto;
            }}
            .btn {{
                border: none;
                border-radius: 12px;
                padding: 12px 18px;
                font-size: 15px;
                font-weight: 700;
                text-decoration: none;
                cursor: pointer;
                display: inline-flex;
                align-items: center;
                justify-content: center;
                transition: transform 0.15s ease, box-shadow 0.15s ease, opacity 0.15s ease;
            }}
            .btn:hover {{
                transform: translateY(-1px);
            }}
            .btn-primary {{
                color: #fff;
                box-shadow: 0 10px 20px rgba(15, 23, 42, 0.12);
            }}
            .btn-secondary {{
                color: var(--text);
                background: #eef3f8;
            }}
            .btn-disabled {{
                opacity: 0.55;
                pointer-events: none;
                cursor: not-allowed;
            }}
            .note {{
                margin-top: 22px;
                padding: 16px 18px;
                border-radius: 14px;
                border: 1px solid var(--warning-border);
                background: var(--warning-bg);
                color: var(--warning-text);
                line-height: 1.7;
            }}
            .success-mark {{
                width: 64px;
                height: 64px;
                margin: 0 auto 16px auto;
                border-radius: 999px;
                background: rgba(26, 127, 55, 0.12);
                color: var(--success);
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 34px;
                font-weight: 800;
            }}
            .section {{
                margin-top: 24px;
                padding-top: 24px;
                border-top: 1px solid var(--border);
            }}
            .section h2 {{
                margin: 0 0 12px 0;
                font-size: 20px;
            }}
            .muted {{
                color: var(--subtle);
                line-height: 1.6;
            }}
            .copy-block {{
                margin-top: 14px;
            }}
            .copy-label {{
                margin-bottom: 8px;
                font-weight: 700;
            }}
            .code-box {{
                margin: 0;
                padding: 16px;
                border: 1px solid var(--border);
                border-radius: 14px;
                background: var(--code-bg);
                overflow-x: auto;
                white-space: pre-wrap;
                word-break: break-word;
                font-size: 13px;
                line-height: 1.7;
                font-family: "SFMono-Regular", "Consolas", monospace;
            }}
            .kv-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
                gap: 12px;
                margin-top: 16px;
            }}
            .kv-item {{
                border: 1px solid var(--border);
                border-radius: 14px;
                padding: 14px;
                background: #fafbfd;
            }}
            .kv-item .key {{
                color: var(--subtle);
                font-size: 13px;
                margin-bottom: 6px;
            }}
            .kv-item .value {{
                font-weight: 700;
                word-break: break-word;
            }}
            .profile-grid {{
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 14px;
                margin-top: 16px;
            }}
            .profile-card {{
                border: 1px solid var(--border);
                border-radius: 16px;
                padding: 18px;
                background: #fff;
            }}
            .profile-card h3 {{
                margin: 0 0 12px 0;
                font-size: 18px;
            }}
            .profile-meta {{
                margin: 6px 0;
                color: var(--subtle);
                line-height: 1.6;
                word-break: break-word;
            }}
            .profile-meta strong {{
                color: var(--text);
            }}
            .empty {{
                padding: 18px;
                border: 1px dashed var(--border);
                border-radius: 16px;
                color: var(--subtle);
                background: #fbfcfe;
            }}
            textarea {{
                width: 100%;
                min-height: 120px;
                padding: 14px;
                border-radius: 14px;
                border: 1px solid var(--border);
                font-size: 14px;
                font-family: "SFMono-Regular", "Consolas", monospace;
                resize: vertical;
            }}
            .form-actions {{
                display: flex;
                gap: 12px;
                margin-top: 18px;
                flex-wrap: wrap;
            }}
            .back-link {{
                display: inline-flex;
                margin-top: 18px;
                color: var(--subtle);
                text-decoration: none;
                font-weight: 600;
            }}
            @media (max-width: 640px) {{
                body {{
                    padding: 16px;
                }}
                .panel {{
                    padding: 20px;
                    border-radius: 16px;
                }}
            }}
        </style>
    </head>
    <body>
        <div class="page">
            {body_html}
        </div>
        <script>
            async function copyText(elementId) {{
                const element = document.getElementById(elementId);
                if (!element) {{
                    return;
                }}
                const text = element.textContent || "";
                await navigator.clipboard.writeText(text);
                alert("已复制到剪贴板");
            }}
        </script>
    </body>
    </html>
    """


def render_copy_block(
    label: str,
    element_id: str,
    value: str,
    *,
    hint: str | None = None,
    button_text: str = "复制",
) -> str:
    hint_html = f'<div class="muted">{html_escape(hint)}</div>' if hint else ""
    return f"""
    <div class="copy-block">
        <div class="copy-label">{html_escape(label)}</div>
        <pre class="code-box" id="{html_escape(element_id)}">{html_escape(value)}</pre>
        <div class="form-actions">
            <button class="btn btn-secondary" onclick="copyText('{html_escape(element_id)}')">{html_escape(button_text)}</button>
        </div>
        {hint_html}
    </div>
    """


def render_key_value_grid(items: list[tuple[str, str]]) -> str:
    blocks = []
    for key, value in items:
        blocks.append(
            f"""
            <div class="kv-item">
                <div class="key">{html_escape(key)}</div>
                <div class="value">{html_escape(value)}</div>
            </div>
            """
        )
    return f'<div class="kv-grid">{"".join(blocks)}</div>'


def render_provider_cards(cards: list[ProviderCard]) -> str:
    rendered_cards: list[str] = []
    for card in cards:
        primary_class = "btn btn-primary"
        if not card.enabled:
            primary_class += " btn-disabled"

        secondary_buttons = "".join(
            f'<a href="{html_escape(url)}" class="btn btn-secondary">{html_escape(label)}</a>'
            for label, url in card.extra_actions
        )
        disabled_hint = (
            f'<div class="muted">{html_escape(card.disabled_reason)}</div>'
            if not card.enabled
            else ""
        )
        rendered_cards.append(
            f"""
            <div class="card">
                <div class="card-top">
                    <div class="card-accent" style="background:{html_escape(card.accent_color)};"></div>
                    <h2>{html_escape(card.title)}</h2>
                    <p>{html_escape(card.description)}</p>
                </div>
                {disabled_hint}
                <div class="button-row">
                    <a href="{html_escape(card.auth_url)}" class="{primary_class}" style="background:{html_escape(card.accent_color)};">
                        {html_escape(card.action_text)}
                    </a>
                    {secondary_buttons}
                </div>
            </div>
            """
        )
    return "".join(rendered_cards)


def render_home_page(cards: list[ProviderCard]) -> str:
    cards_html = render_provider_cards(cards)
    body_html = f"""
    <div class="panel">
        <div class="hero">
            <h1>OAuth 授权中心</h1>
            <p>选择一个平台完成授权，页面会直接展示可复制的 token 信息。本应用不落库存储 token。</p>
        </div>
        <div class="cards">{cards_html}</div>
        <div class="note">
            Amazon 这里同时接入了 <strong>Amazon Ads API</strong> 和 <strong>SP-API</strong> 两条授权链路。
            <br>
            Ads API 用来拉广告数据、管理广告。SP-API 用于店铺、订单、商品等卖家数据。
            <br>
            两者虽然都基于 Login with Amazon，但授权入口、回调参数和后续调用方式都不一样。
        </div>
    </div>
    """
    return render_page("OAuth 授权中心", body_html)


def render_amazon_region_page() -> str:
    region_cards: list[str] = []
    for region in AMAZON_AD_REGIONS:
        countries = get_amazon_countries_by_region(region.key)
        country_labels = "、".join(country.label for country in countries)
        region_cards.append(
            f"""
            <div class="card">
                <div class="card-top">
                    <div class="card-accent" style="background:#ff9900;"></div>
                    <h2>{html_escape(region.label)}</h2>
                    <p>{html_escape(country_labels)}</p>
                </div>
                <div class="button-row">
                    <a href="/amazon-ads/select-country/{html_escape(region.key)}" class="btn btn-primary" style="background:#ff9900;">选择国家</a>
                </div>
            </div>
            """
        )

    body_html = f"""
    <div class="panel">
        <div class="hero">
            <h1>Amazon Ads 选择地区</h1>
            <p>先选地区，再选国家发起授权。授权完成后，页面会返回 token 和 profile 列表。</p>
        </div>
        <div class="cards">{"".join(region_cards)}</div>
        <a class="back-link" href="/">返回首页</a>
    </div>
    """
    return render_page("Amazon Ads 选择地区", body_html)


def render_amazon_country_page(region: AmazonAdsRegion, countries: list[AmazonAdsCountry]) -> str:
    country_cards: list[str] = []
    for country in countries:
        country_cards.append(
            f"""
            <div class="card">
                <div class="card-top">
                    <div class="card-accent" style="background:#ff9900;"></div>
                    <h2>{html_escape(country.label)}</h2>
                    <p>{html_escape(country.code)} / {html_escape(region.label)}</p>
                </div>
                <div class="button-row">
                    <a href="/amazon-ads/start/{html_escape(country.code)}" class="btn btn-primary" style="background:#ff9900;">开始授权</a>
                </div>
            </div>
            """
        )

    body_html = f"""
    <div class="panel">
        <div class="hero">
            <h1>Amazon Ads 选择国家</h1>
            <p>当前地区：{html_escape(region.label)}。请选择要授权的站点国家。</p>
        </div>
        <div class="cards">{"".join(country_cards)}</div>
        <a class="back-link" href="/amazon-ads/select-region">返回地区选择</a>
    </div>
    """
    return render_page("Amazon Ads 选择国家", body_html)


def render_amazon_sp_region_page() -> str:
    region_cards: list[str] = []
    for region in AMAZON_SP_REGIONS:
        countries = get_amazon_sp_countries_by_region(region.key)
        country_labels = "、".join(country.label for country in countries)
        region_cards.append(
            f"""
            <div class="card">
                <div class="card-top">
                    <div class="card-accent" style="background:#232f3e;"></div>
                    <h2>{html_escape(region.label)}</h2>
                    <p>{html_escape(country_labels)}</p>
                </div>
                <div class="button-row">
                    <a href="/amazon-sp/select-country/{html_escape(region.key)}" class="btn btn-primary" style="background:#232f3e;">选择国家</a>
                </div>
            </div>
            """
        )

    body_html = f"""
    <div class="panel">
        <div class="hero">
            <h1>Amazon SP-API 选择地区</h1>
            <p>先选地区和国家，再跳到对应 Seller Central 授权页。授权完成后，页面会展示 token 和 selling_partner_id。</p>
        </div>
        <div class="cards">{"".join(region_cards)}</div>
        <a class="back-link" href="/">返回首页</a>
    </div>
    """
    return render_page("Amazon SP-API 选择地区", body_html)


def render_amazon_sp_country_page(region: AmazonSpRegion, countries: list[AmazonSpCountry]) -> str:
    country_cards: list[str] = []
    for country in countries:
        country_cards.append(
            f"""
            <div class="card">
                <div class="card-top">
                    <div class="card-accent" style="background:#232f3e;"></div>
                    <h2>{html_escape(country.label)}</h2>
                    <p>{html_escape(country.code)} / {html_escape(region.label)}</p>
                </div>
                <div class="button-row">
                    <a href="/amazon-sp/start/{html_escape(country.code)}" class="btn btn-primary" style="background:#232f3e;">开始授权</a>
                </div>
            </div>
            """
        )

    body_html = f"""
    <div class="panel">
        <div class="hero">
            <h1>Amazon SP-API 选择国家</h1>
            <p>当前地区：{html_escape(region.label)}。请选择要授权的 Seller Central 站点。</p>
        </div>
        <div class="cards">{"".join(country_cards)}</div>
        <a class="back-link" href="/amazon-sp/select-region">返回地区选择</a>
    </div>
    """
    return render_page("Amazon SP-API 选择国家", body_html)


def render_message_page(title: str, message: str, *, back_url: str = "/") -> str:
    body_html = f"""
    <div class="panel">
        <div class="hero">
            <h1>{html_escape(title)}</h1>
            <p>{html_escape(message)}</p>
        </div>
        <a class="back-link" href="{html_escape(back_url)}">返回上一页</a>
    </div>
    """
    return render_page(title, body_html)


def render_facebook_success_page(access_token: str, user_id: str, user_name: str) -> str:
    body_html = f"""
    <div class="panel">
        <div class="success-mark">✓</div>
        <div class="hero">
            <h1>Facebook 授权成功</h1>
            <p>可以直接复制下面的长期 access token。页面不会保存你的 token。</p>
        </div>
        {render_key_value_grid([("用户名称", user_name), ("用户 ID", user_id)])}
        <div class="section">
            <h2>Access Token</h2>
            {render_copy_block("长期 Access Token", "facebook-access-token", access_token)}
        </div>
    </div>
    """
    return render_page("Facebook 授权成功", body_html)


def render_tiktok_success_page(
    access_token: str,
    refresh_token: str,
    advertiser_ids: list[str],
    expires_in: int,
    refresh_expires_in: int,
) -> str:
    advertiser_ids_text = ", ".join(advertiser_ids) if advertiser_ids else "未获取到 advertiser_id"
    summary_items = [
        ("Access Token 有效期", f"{expires_in} 秒"),
        ("Refresh Token 有效期", f"{refresh_expires_in} 秒"),
        ("Advertiser 数量", str(len(advertiser_ids))),
    ]
    body_html = f"""
    <div class="panel">
        <div class="success-mark">✓</div>
        <div class="hero">
            <h1>TikTok Business API 授权成功</h1>
            <p>你可以直接复制 token，或先复制 advertiser_id 作为后续广告接口调用参数。</p>
        </div>
        {render_key_value_grid(summary_items)}
        <div class="section">
            <h2>Advertiser 信息</h2>
            {render_copy_block("Advertiser IDs", "tiktok-advertiser-ids", advertiser_ids_text)}
        </div>
        <div class="section">
            <h2>Token</h2>
            {render_copy_block("Access Token", "tiktok-access-token", access_token, hint=f"有效期: {expires_in} 秒")}
            {render_copy_block("Refresh Token", "tiktok-refresh-token", refresh_token, hint=f"有效期: {refresh_expires_in} 秒")}
        </div>
    </div>
    """
    return render_page("TikTok 授权成功", body_html)


def render_amazon_profile_cards(
    profiles_by_region: dict[str, list[dict[str, Any]]],
    errors_by_region: dict[str, str],
) -> str:
    cards: list[str] = []
    for region in AMAZON_AD_REGIONS:
        region_profiles = profiles_by_region.get(region.key, [])
        region_error = errors_by_region.get(region.key)
        if region_error:
            cards.append(
                f"""
                <div class="profile-card">
                    <h3>{html_escape(region.label)} / {html_escape(region.key)}</h3>
                    <div class="profile-meta"><strong>广告 Host:</strong> {html_escape(region.host)}</div>
                    <div class="profile-meta"><strong>拉取结果:</strong> {html_escape(region_error)}</div>
                </div>
                """
            )
            continue
        if not region_profiles:
            cards.append(
                f"""
                <div class="profile-card">
                    <h3>{html_escape(region.label)} / {html_escape(region.key)}</h3>
                    <div class="profile-meta"><strong>广告 Host:</strong> {html_escape(region.host)}</div>
                    <div class="profile-meta">当前 region 没有拿到 profile。可能是此区域没有广告账户，或应用未获批对应账号权限。</div>
                </div>
                """
            )
            continue

        for profile in region_profiles:
            account_info = profile.get("accountInfo") or {}
            cards.append(
                f"""
                <div class="profile-card">
                    <h3>{html_escape(region.label)} / {html_escape(region.key)}</h3>
                    <div class="profile-meta"><strong>广告 Host:</strong> {html_escape(region.host)}</div>
                    <div class="profile-meta"><strong>Profile ID:</strong> {html_escape(profile.get("profileId"))}</div>
                    <div class="profile-meta"><strong>Country Code:</strong> {html_escape(profile.get("countryCode"))}</div>
                    <div class="profile-meta"><strong>Currency Code:</strong> {html_escape(profile.get("currencyCode"))}</div>
                    <div class="profile-meta"><strong>Timezone:</strong> {html_escape(profile.get("timezone"))}</div>
                    <div class="profile-meta"><strong>Account Name:</strong> {html_escape(account_info.get("name", "未返回"))}</div>
                    <div class="profile-meta"><strong>Account ID:</strong> {html_escape(account_info.get("id", "未返回"))}</div>
                    <div class="profile-meta"><strong>Account Type:</strong> {html_escape(account_info.get("type", "未返回"))}</div>
                </div>
                """
            )
    return f'<div class="profile-grid">{"".join(cards)}</div>'


def build_amazon_bundle(
    token_data: dict[str, Any],
    profiles_by_region: dict[str, list[dict[str, Any]]],
    errors_by_region: dict[str, str],
) -> dict[str, Any]:
    flattened_profiles: list[dict[str, Any]] = []
    host_map = {region.key: region.host for region in AMAZON_AD_REGIONS}
    for region_key, profiles in profiles_by_region.items():
        region_host = host_map[region_key]
        for profile in profiles:
            account_info = profile.get("accountInfo") or {}
            flattened_profiles.append(
                {
                    "region": region_key,
                    "host": region_host,
                    "profile_id": str(profile.get("profileId", "")),
                    "country_code": profile.get("countryCode"),
                    "currency_code": profile.get("currencyCode"),
                    "timezone": profile.get("timezone"),
                    "account_name": account_info.get("name"),
                    "account_id": account_info.get("id"),
                    "account_type": account_info.get("type"),
                }
            )

    return {
        "provider": "amazon_ads",
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type"),
        "expires_in": token_data.get("expires_in"),
        "scope": token_data.get("scope", AMAZON_AD_SCOPE),
        "profiles": flattened_profiles,
        "profile_errors": errors_by_region,
        "call_headers_template": {
            "Authorization": "Bearer <access_token>",
            "Amazon-Advertising-API-ClientId": AMAZON_AD_CLIENT_ID,
            "Amazon-Advertising-API-Scope": "<profile_id>",
        },
    }


def render_amazon_success_page(
    token_data: dict[str, Any],
    profiles_by_region: dict[str, list[dict[str, Any]]],
    errors_by_region: dict[str, str],
    selected_country: AmazonAdsCountry | None = None,
) -> str:
    bundle = build_amazon_bundle(token_data, profiles_by_region, errors_by_region)
    summary_items = [
        ("Token 类型", str(token_data.get("token_type", "未返回"))),
        ("Access Token 有效期", f'{token_data.get("expires_in", "未返回")} 秒'),
        ("Profile 数量", str(len(bundle["profiles"]))),
        ("默认 Scope", str(token_data.get("scope", AMAZON_AD_SCOPE))),
    ]
    if selected_country:
        summary_items.insert(0, ("授权国家", f"{selected_country.label} ({selected_country.code})"))
        summary_items.insert(1, ("授权地区", selected_country.region_key))
    headers_example = pretty_json(
        {
            "Authorization": "Bearer <access_token>",
            "Amazon-Advertising-API-ClientId": AMAZON_AD_CLIENT_ID,
            "Amazon-Advertising-API-Scope": "<profile_id>",
        }
    )

    body_html = f"""
    <div class="panel">
        <div class="success-mark">✓</div>
        <div class="hero">
            <h1>Amazon Ads 授权成功</h1>
            <p>这里返回的是 Amazon Ads API 能直接使用的 Login with Amazon token 信息，不是 SP-API 凭据。</p>
        </div>
        {render_key_value_grid(summary_items)}
        <div class="note">
            调 Amazon Ads API 时，除了 <code>Authorization: Bearer &lt;access_token&gt;</code>，
            还需要带上 <code>Amazon-Advertising-API-ClientId</code>，以及具体广告账户对应的
            <code>Amazon-Advertising-API-Scope: &lt;profile_id&gt;</code>。
        </div>
        <div class="section">
            <h2>Token</h2>
            {render_copy_block("Access Token", "amazon-access-token", str(token_data.get("access_token", "")))}
            {render_copy_block("Refresh Token", "amazon-refresh-token", str(token_data.get("refresh_token", "")))}
        </div>
        <div class="section">
            <h2>调用头模板</h2>
            {render_copy_block("Headers JSON", "amazon-headers-json", headers_example)}
        </div>
        <div class="section">
            <h2>Profiles</h2>
            <div class="muted">同一个 access token 会按 region 分别拉取 profile。实际调广告接口时，请使用对应 region 的 Host 和 profile_id。</div>
            {render_amazon_profile_cards(profiles_by_region, errors_by_region)}
        </div>
        <div class="section">
            <h2>可复制 JSON 包</h2>
            <div class="muted">如果你想把这次授权结果直接喂给后端服务，复制这一段通常最方便。</div>
            {render_copy_block("Amazon Ads JSON", "amazon-bundle-json", pretty_json(bundle))}
        </div>
    </div>
    """
    return render_page("Amazon Ads 授权成功", body_html)


def build_amazon_sp_bundle(
    token_data: dict[str, Any],
    selected_country: AmazonSpCountry | None,
    selling_partner_id: str,
) -> dict[str, Any]:
    region = get_amazon_sp_region(selected_country.region_key) if selected_country else None
    return {
        "provider": "amazon_sp",
        "access_token": token_data.get("access_token"),
        "refresh_token": token_data.get("refresh_token"),
        "token_type": token_data.get("token_type"),
        "expires_in": token_data.get("expires_in"),
        "selling_partner_id": selling_partner_id,
        "country_code": selected_country.code if selected_country else None,
        "country_label": selected_country.label if selected_country else None,
        "region": selected_country.region_key if selected_country else None,
        "sp_api_endpoint": region.endpoint if region else None,
        "call_headers_template": {
            "x-amz-access-token": "<access_token>",
        },
    }


def render_amazon_sp_success_page(
    token_data: dict[str, Any],
    selected_country: AmazonSpCountry | None,
    selling_partner_id: str,
) -> str:
    bundle = build_amazon_sp_bundle(token_data, selected_country, selling_partner_id)
    region = get_amazon_sp_region(selected_country.region_key) if selected_country else None
    summary_items = [
        ("Token 类型", str(token_data.get("token_type", "未返回"))),
        ("Access Token 有效期", f'{token_data.get("expires_in", "未返回")} 秒'),
        ("Selling Partner ID", selling_partner_id or "未返回"),
    ]
    if selected_country:
        summary_items.insert(0, ("授权国家", f"{selected_country.label} ({selected_country.code})"))
        summary_items.insert(1, ("授权地区", selected_country.region_key))
    if region:
        summary_items.append(("SP-API Endpoint", region.endpoint))

    body_html = f"""
    <div class="panel">
        <div class="success-mark">✓</div>
        <div class="hero">
            <h1>Amazon SP-API 授权成功</h1>
            <p>这里返回的是 SP-API 可继续换取 access token 的 Login with Amazon 凭据，主要给卖家、订单、商品、库存这类接口使用。</p>
        </div>
        {render_key_value_grid(summary_items)}
        <div class="note">
            SP-API 常见用法是把 <code>refresh_token</code> 交给后端，后端再去刷新短期 <code>access_token</code>。
            <br>
            真正调用 SP-API 时，除了 <code>x-amz-access-token</code>，通常还需要 AWS SigV4 签名，这一点和 Amazon Ads API 不一样。
        </div>
        <div class="section">
            <h2>Token</h2>
            {render_copy_block("Access Token", "amazon-sp-access-token", str(token_data.get("access_token", "")))}
            {render_copy_block("Refresh Token", "amazon-sp-refresh-token", str(token_data.get("refresh_token", "")))}
        </div>
        <div class="section">
            <h2>卖家标识</h2>
            {render_copy_block("Selling Partner ID", "amazon-sp-selling-partner-id", selling_partner_id)}
        </div>
        <div class="section">
            <h2>可复制 JSON 包</h2>
            <div class="muted">如果你想把这次授权结果直接交给后端服务，复制这一段通常最方便。</div>
            {render_copy_block("Amazon SP JSON", "amazon-sp-bundle-json", pretty_json(bundle))}
        </div>
    </div>
    """
    return render_page("Amazon SP-API 授权成功", body_html)


def get_provider_cards() -> list[ProviderCard]:
    facebook_enabled = bool(FACEBOOK_APP_ID and FACEBOOK_APP_SECRET)
    tiktok_enabled = bool(TIKTOK_APP_ID and TIKTOK_APP_SECRET)
    amazon_ads_enabled = bool(AMAZON_AD_CLIENT_ID and AMAZON_AD_CLIENT_SECRET)
    amazon_sp_enabled = bool(AMAZON_SP_CLIENT_ID and AMAZON_SP_CLIENT_SECRET and AMAZON_SP_APP_ID)

    facebook_auth_url = "#"
    if facebook_enabled:
        facebook_auth_url = build_url(
            FACEBOOK_OAUTH_URL,
            {
                "client_id": FACEBOOK_APP_ID,
                "redirect_uri": FACEBOOK_REDIRECT_URI,
                "scope": FACEBOOK_SCOPE,
                "response_type": "code",
                "state": create_state("facebook"),
            },
        )

    tiktok_auth_url = "#"
    if tiktok_enabled:
        tiktok_auth_url = build_url(
            TIKTOK_OAUTH_URL,
            {
                "app_id": TIKTOK_APP_ID,
                "redirect_uri": TIKTOK_REDIRECT_URI,
                "state": create_state("tiktok"),
            },
        )

    amazon_ads_auth_url = "#"
    if amazon_ads_enabled:
        amazon_ads_auth_url = "/amazon-ads/select-region"

    amazon_sp_auth_url = "#"
    if amazon_sp_enabled:
        amazon_sp_auth_url = "/amazon-sp/select-region"

    return [
        ProviderCard(
            key="facebook",
            title="Facebook",
            description="获取可直接用于广告接口的长期 access token。",
            accent_color="#1877f2",
            action_text="开始授权",
            auth_url=facebook_auth_url,
            enabled=facebook_enabled,
            disabled_reason="请先配置 FACEBOOK_APP_ID 和 FACEBOOK_APP_SECRET。",
        ),
        ProviderCard(
            key="tiktok",
            title="TikTok",
            description="获取 TikTok Business API token，并顺带拉 advertiser_id。",
            accent_color="#111111",
            action_text="开始授权",
            auth_url=tiktok_auth_url,
            enabled=tiktok_enabled,
            disabled_reason="请先配置 TIKTOK_APP_ID 和 TIKTOK_APP_SECRET。",
            extra_actions=(("手动换 Token", "/tiktok/manual"),),
        ),
        ProviderCard(
            key="amazon_ads",
            title="Amazon Ads",
            description="Login with Amazon 授权，用于 Amazon 广告 API，不是 SP-API。",
            accent_color="#ff9900",
            action_text="开始授权",
            auth_url=amazon_ads_auth_url,
            enabled=amazon_ads_enabled,
            disabled_reason="请先配置 AMAZON_AD_CLIENT_ID 和 AMAZON_AD_CLIENT_SECRET。",
        ),
        ProviderCard(
            key="amazon_sp",
            title="Amazon SP-API",
            description="Seller Central 授权，用于订单、商品、库存等卖家接口，不是广告 API。",
            accent_color="#232f3e",
            action_text="开始授权",
            auth_url=amazon_sp_auth_url,
            enabled=amazon_sp_enabled,
            disabled_reason="请先配置 AMAZON_SP_CLIENT_ID、AMAZON_SP_CLIENT_SECRET 和 AMAZON_SP_APP_ID。",
        ),
    ]


def get_enabled_provider_names() -> list[str]:
    enabled_names: list[str] = []
    if FACEBOOK_APP_ID and FACEBOOK_APP_SECRET:
        enabled_names.append("Facebook")
    if TIKTOK_APP_ID and TIKTOK_APP_SECRET:
        enabled_names.append("TikTok")
    if AMAZON_AD_CLIENT_ID and AMAZON_AD_CLIENT_SECRET:
        enabled_names.append("Amazon Ads")
    if AMAZON_SP_CLIENT_ID and AMAZON_SP_CLIENT_SECRET and AMAZON_SP_APP_ID:
        enabled_names.append("Amazon SP-API")
    return enabled_names


def exchange_tiktok_token(code: str) -> dict[str, Any]:
    token_data = {
        "app_id": TIKTOK_APP_ID,
        "secret": TIKTOK_APP_SECRET,
        "auth_code": code,
        "grant_type": "authorization_code",
    }
    headers = {"Content-Type": "application/json"}
    return request_json("POST", TIKTOK_TOKEN_URL, json_body=token_data, headers=headers)


def get_tiktok_advertiser_ids(access_token: str) -> list[str]:
    headers = {
        "Access-Token": access_token,
        "Content-Type": "application/json",
    }
    params = {
        "app_id": TIKTOK_APP_ID,
        "secret": TIKTOK_APP_SECRET,
    }
    result = request_json("GET", TIKTOK_ADVERTISER_URL, params=params, headers=headers)
    if result.get("code") != 0:
        return []
    advertisers = result.get("data", {}).get("list", [])
    return [str(item.get("advertiser_id", "")) for item in advertisers if item.get("advertiser_id")]


def exchange_amazon_ads_token(code: str) -> dict[str, Any]:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": AMAZON_AD_CLIENT_ID,
        "client_secret": AMAZON_AD_CLIENT_SECRET,
        "redirect_uri": AMAZON_AD_REDIRECT_URI,
    }
    return request_json("POST", AMAZON_AD_TOKEN_URL, data=payload)


def exchange_amazon_sp_token(code: str) -> dict[str, Any]:
    payload = {
        "grant_type": "authorization_code",
        "code": code,
        "client_id": AMAZON_SP_CLIENT_ID,
        "client_secret": AMAZON_SP_CLIENT_SECRET,
    }
    return request_json("POST", AMAZON_SP_TOKEN_URL, data=payload)


def get_amazon_ads_profiles(access_token: str, region: AmazonAdsRegion) -> list[dict[str, Any]]:
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Amazon-Advertising-API-ClientId": AMAZON_AD_CLIENT_ID or "",
        "Accept": "application/json",
        "Content-Type": "application/json",
    }
    response = request_json("GET", f"{region.host}{AMAZON_AD_PROFILE_PATH}", headers=headers)
    if isinstance(response, list):
        return response
    return []


@app.route("/")
def index() -> str:
    return render_home_page(get_provider_cards())


@app.route("/healthz")
def healthz() -> tuple[str, int]:
    return "ok", 200


@app.route("/amazon-ads/select-region")
def amazon_ads_select_region() -> str:
    if not AMAZON_AD_CLIENT_ID or not AMAZON_AD_CLIENT_SECRET:
        return render_message_page("Amazon Ads 未配置", "请先配置 AMAZON_AD_CLIENT_ID 和 AMAZON_AD_CLIENT_SECRET。")
    return render_amazon_region_page()


@app.route("/amazon-ads/select-country/<region_key>")
def amazon_ads_select_country(region_key: str) -> str:
    region = get_amazon_region(region_key.upper())
    if not region:
        return render_message_page("地区不存在", f"未找到地区: {region_key}")
    countries = get_amazon_countries_by_region(region.key)
    return render_amazon_country_page(region, countries)


@app.route("/amazon-ads/start/<country_code>")
def amazon_ads_start(country_code: str):
    if not AMAZON_AD_CLIENT_ID or not AMAZON_AD_CLIENT_SECRET:
        return render_message_page("Amazon Ads 未配置", "请先配置 AMAZON_AD_CLIENT_ID 和 AMAZON_AD_CLIENT_SECRET。")

    country = get_amazon_country(country_code)
    if not country:
        return render_message_page("国家不存在", f"未找到国家: {country_code}", back_url="/amazon-ads/select-region")

    state = create_state(
        "amazon_ads",
        context={"country_code": country.code, "region_key": country.region_key},
    )
    auth_url = build_url(
        country.auth_url,
        {
            "scope": AMAZON_AD_SCOPE,
            "response_type": "code",
            "state": state,
            "client_id": AMAZON_AD_CLIENT_ID,
            "redirect_uri": AMAZON_AD_REDIRECT_URI,
        },
    )
    return redirect(auth_url)


@app.route("/amazon-sp/select-region")
def amazon_sp_select_region() -> str:
    if not AMAZON_SP_CLIENT_ID or not AMAZON_SP_CLIENT_SECRET or not AMAZON_SP_APP_ID:
        return render_message_page(
            "Amazon SP-API 未配置",
            "请先配置 AMAZON_SP_CLIENT_ID、AMAZON_SP_CLIENT_SECRET 和 AMAZON_SP_APP_ID。",
        )
    return render_amazon_sp_region_page()


@app.route("/amazon-sp/select-country/<region_key>")
def amazon_sp_select_country(region_key: str) -> str:
    region = get_amazon_sp_region(region_key.upper())
    if not region:
        return render_message_page("地区不存在", f"未找到地区: {region_key}")
    countries = get_amazon_sp_countries_by_region(region.key)
    return render_amazon_sp_country_page(region, countries)


@app.route("/amazon-sp/start/<country_code>")
def amazon_sp_start(country_code: str):
    if not AMAZON_SP_CLIENT_ID or not AMAZON_SP_CLIENT_SECRET or not AMAZON_SP_APP_ID:
        return render_message_page(
            "Amazon SP-API 未配置",
            "请先配置 AMAZON_SP_CLIENT_ID、AMAZON_SP_CLIENT_SECRET 和 AMAZON_SP_APP_ID。",
        )

    country = get_amazon_sp_country(country_code)
    if not country:
        return render_message_page("国家不存在", f"未找到国家: {country_code}", back_url="/amazon-sp/select-region")

    state = create_state(
        "amazon_sp",
        context={"country_code": country.code, "region_key": country.region_key},
    )
    auth_url = build_url(
        f"{country.seller_central_url}{AMAZON_SP_AUTH_PATH}",
        {
            "application_id": AMAZON_SP_APP_ID,
            "state": state,
            "client_id": AMAZON_SP_CLIENT_ID,
            "redirect_uri": AMAZON_SP_REDIRECT_URI,
        },
    )
    return redirect(auth_url)


@app.route("/fb/callback")
def facebook_callback() -> tuple[str, int] | str:
    error = request.args.get("error")
    if error:
        return f"授权失败: {error}", 400

    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return "缺少授权码", 400
    is_valid_state, _ = consume_state("facebook", state)
    if not is_valid_state:
        return "State 验证失败", 400

    try:
        short_lived_token_data = request_json(
            "GET",
            FACEBOOK_TOKEN_URL,
            params={
                "client_id": FACEBOOK_APP_ID,
                "client_secret": FACEBOOK_APP_SECRET,
                "redirect_uri": FACEBOOK_REDIRECT_URI,
                "code": code,
            },
        )
        short_lived_token = short_lived_token_data.get("access_token")
        if not short_lived_token:
            return "获取短期 token 失败", 500

        long_lived_token_data = request_json(
            "GET",
            FACEBOOK_TOKEN_URL,
            params={
                "grant_type": "fb_exchange_token",
                "client_id": FACEBOOK_APP_ID,
                "client_secret": FACEBOOK_APP_SECRET,
                "fb_exchange_token": short_lived_token,
            },
        )
        access_token = long_lived_token_data.get("access_token", short_lived_token)

        user_info = request_json(
            "GET",
            FACEBOOK_GRAPH_API_URL,
            params={
                "fields": "id,name",
                "access_token": access_token,
            },
        )
        user_id = str(user_info.get("id", "未获取"))
        user_name = str(user_info.get("name", "未获取"))
        print(f"[Facebook] 授权成功 user_id={user_id}")
        return render_facebook_success_page(access_token, user_id, user_name)
    except requests.RequestException as exc:
        return f"请求失败: {exc}", 500


@app.route("/tiktok/callback")
def tiktok_callback() -> tuple[str, int] | str:
    error = request.args.get("error")
    if error:
        error_description = request.args.get("error_description", "未知错误")
        return f"授权失败: {error} - {error_description}", 400

    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return "缺少授权码", 400
    is_valid_state, _ = consume_state("tiktok", state)
    if not is_valid_state:
        return "State 验证失败", 400

    try:
        result = exchange_tiktok_token(code)
        if result.get("code") != 0:
            error_msg = result.get("message", result.get("error", "未知错误"))
            return f"获取 token 失败: {error_msg}", 500

        data = result.get("data", result)
        access_token = str(data.get("access_token", ""))
        advertiser_ids = get_tiktok_advertiser_ids(access_token)
        print(f"[TikTok] 授权成功 advertiser_count={len(advertiser_ids)}")
        return render_tiktok_success_page(
            access_token=access_token,
            refresh_token=str(data.get("refresh_token", "")),
            advertiser_ids=advertiser_ids,
            expires_in=int(data.get("expires_in", 0)),
            refresh_expires_in=int(data.get("refresh_expires_in", 0)),
        )
    except requests.RequestException as exc:
        return f"请求失败: {exc}", 500


@app.route("/amazon-ads/callback")
def amazon_ads_callback() -> tuple[str, int] | str:
    error = request.args.get("error")
    if error:
        error_description = request.args.get("error_description", "未知错误")
        return f"授权失败: {error} - {error_description}", 400

    code = request.args.get("code")
    state = request.args.get("state")
    if not code:
        return "缺少授权码", 400
    is_valid_state, state_context = consume_state("amazon_ads", state)
    if not is_valid_state:
        return "State 验证失败", 400

    try:
        token_data = exchange_amazon_ads_token(code)
        access_token = str(token_data.get("access_token", ""))
        if not access_token:
            return "获取 Amazon Ads access token 失败", 500

        profiles_by_region: dict[str, list[dict[str, Any]]] = {}
        errors_by_region: dict[str, str] = {}
        for region in AMAZON_AD_REGIONS:
            try:
                profiles_by_region[region.key] = get_amazon_ads_profiles(access_token, region)
            except requests.RequestException as exc:
                errors_by_region[region.key] = str(exc)
                profiles_by_region[region.key] = []

        total_profiles = sum(len(items) for items in profiles_by_region.values())
        print(f"[Amazon Ads] 授权成功 total_profiles={total_profiles}")
        selected_country = None
        country_code = str(state_context.get("country_code", "")).upper()
        if country_code:
            selected_country = get_amazon_country(country_code)
        return render_amazon_success_page(
            token_data,
            profiles_by_region,
            errors_by_region,
            selected_country=selected_country,
        )
    except requests.RequestException as exc:
        return f"请求失败: {exc}", 500


@app.route("/amazon-sp/callback")
def amazon_sp_callback() -> tuple[str, int] | str:
    error = request.args.get("error")
    if error:
        error_description = request.args.get("error_description", "未知错误")
        return f"授权失败: {error} - {error_description}", 400

    code = request.args.get("spapi_oauth_code")
    state = request.args.get("state")
    selling_partner_id = request.args.get("selling_partner_id", "").strip()
    if not code:
        return "缺少 spapi_oauth_code", 400
    is_valid_state, state_context = consume_state("amazon_sp", state)
    if not is_valid_state:
        return "State 验证失败", 400

    try:
        token_data = exchange_amazon_sp_token(code)
        access_token = str(token_data.get("access_token", ""))
        if not access_token:
            return "获取 Amazon SP-API access token 失败", 500

        print(f"[Amazon SP] 授权成功 selling_partner_id={selling_partner_id or 'unknown'}")
        selected_country = None
        country_code = str(state_context.get("country_code", "")).upper()
        if country_code:
            selected_country = get_amazon_sp_country(country_code)
        return render_amazon_sp_success_page(token_data, selected_country, selling_partner_id)
    except requests.RequestException as exc:
        return f"请求失败: {exc}", 500


@app.route("/tiktok/manual", methods=["GET", "POST"])
def tiktok_manual() -> tuple[str, int] | str:
    if not TIKTOK_APP_ID or not TIKTOK_APP_SECRET:
        return "请先配置 TIKTOK_APP_ID 和 TIKTOK_APP_SECRET", 500

    if request.method == "POST":
        callback_url = request.form.get("callback_url", "").strip()
        if not callback_url:
            return "请输入回调 URL", 400

        parsed_url = urlparse(callback_url)
        query_params = parse_qs(parsed_url.query)
        code = query_params.get("auth_code", [None])[0] or query_params.get("code", [None])[0]
        if not code:
            return "URL 中未找到 code 或 auth_code 参数", 400

        try:
            result = exchange_tiktok_token(code)
            if result.get("code") != 0:
                error_msg = result.get("message", result.get("error", "未知错误"))
                return f"获取 token 失败: {error_msg}", 500

            data = result.get("data", result)
            access_token = str(data.get("access_token", ""))
            advertiser_ids = get_tiktok_advertiser_ids(access_token)
            return render_tiktok_success_page(
                access_token=access_token,
                refresh_token=str(data.get("refresh_token", "")),
                advertiser_ids=advertiser_ids,
                expires_in=int(data.get("expires_in", 0)),
                refresh_expires_in=int(data.get("refresh_expires_in", 0)),
            )
        except requests.RequestException as exc:
            return f"请求失败: {exc}", 500

    example_url = urlunparse(("https", "example.com", "/callback", "", "code=abc123&state=xyz", ""))
    body_html = f"""
    <div class="panel">
        <div class="hero">
            <h1>TikTok 手动换 Token</h1>
            <p>如果你已经在别的地址完成授权，可以把回调 URL 粘贴到这里，页面会自动提取 code 并换取 token。</p>
        </div>
        <form method="POST">
            <div class="copy-label">授权后的回调 URL</div>
            <textarea name="callback_url" placeholder="{html_escape(example_url)}" required></textarea>
            <div class="form-actions">
                <button class="btn btn-primary" style="background:#111111;" type="submit">换取 Token</button>
                <a href="/" class="btn btn-secondary">返回首页</a>
            </div>
        </form>
    </div>
    """
    return render_page("TikTok 手动换 Token", body_html)


def main() -> None:
    enabled_providers = get_enabled_provider_names()
    if not enabled_providers:
        print("错误: 请至少配置一个平台的 OAuth 凭据")
        print("请复制 .env.example 为 .env 后再填写应用配置")
        return

    print("OAuth 应用启动中...")
    print(f"访问地址: http://localhost:{PORT}")
    print(f"已启用平台: {', '.join(enabled_providers)}")
    if FACEBOOK_APP_ID and FACEBOOK_APP_SECRET:
        print(f"Facebook 回调地址: {FACEBOOK_REDIRECT_URI}")
    if TIKTOK_APP_ID and TIKTOK_APP_SECRET:
        print(f"TikTok 回调地址: {TIKTOK_REDIRECT_URI}")
    if AMAZON_AD_CLIENT_ID and AMAZON_AD_CLIENT_SECRET:
        print(f"Amazon Ads 回调地址: {AMAZON_AD_REDIRECT_URI}")
    if AMAZON_SP_CLIENT_ID and AMAZON_SP_CLIENT_SECRET and AMAZON_SP_APP_ID:
        print(f"Amazon SP-API 回调地址: {AMAZON_SP_REDIRECT_URI}")
    print(f"Debug 模式: {'开启' if OAUTH_DEBUG else '关闭'}")
    app.run(
        debug=OAUTH_DEBUG,
        use_reloader=OAUTH_DEBUG,
        host="0.0.0.0",
        port=PORT,
    )
