import json
import os
import secrets
from typing import Optional
from urllib.parse import urlparse, parse_qs, urlunparse

from flask import Flask, redirect, request, session, jsonify
from dotenv import load_dotenv
import requests

load_dotenv()

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

# Facebook OAuth 配置
FACEBOOK_APP_ID = os.getenv("FACEBOOK_APP_ID")
FACEBOOK_APP_SECRET = os.getenv("FACEBOOK_APP_SECRET")
PORT = int(os.getenv("PORT", "5001"))
REDIRECT_URI = os.getenv("REDIRECT_URI", f"http://localhost:{PORT}/fb/callback")
FACEBOOK_SCOPE = os.getenv("FACEBOOK_SCOPE", "ads_read,ads_management")

# Facebook OAuth URLs
FACEBOOK_API_VERSION = "v21.0"
FACEBOOK_OAUTH_URL = f"https://www.facebook.com/{FACEBOOK_API_VERSION}/dialog/oauth"
FACEBOOK_TOKEN_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/oauth/access_token"
FACEBOOK_GRAPH_API_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/me"

# TikTok OAuth 配置
TIKTOK_APP_ID = os.getenv("TIKTOK_APP_ID")
TIKTOK_APP_SECRET = os.getenv("TIKTOK_APP_SECRET")
TIKTOK_REDIRECT_URI = os.getenv("TIKTOK_REDIRECT_URI", f"http://localhost:{PORT}/tiktok/callback")
TIKTOK_SCOPE = os.getenv("TIKTOK_SCOPE", "user.info.basic")

# TikTok Business API OAuth URLs
TIKTOK_OAUTH_URL = "https://business-api.tiktok.com/portal/auth"
TIKTOK_TOKEN_URL = "https://business-api.tiktok.com/open_api/v1.3/oauth2/access_token/"
TIKTOK_ADVERTISER_URL = "https://business-api.tiktok.com/open_api/v1.3/oauth2/advertiser/get/"


def exchange_tiktok_token(code: str, redirect_uri: str) -> dict:
    """用授权码换取 TikTok Business API access_token"""
    # Business API 使用 JSON 格式
    token_data = {
        "app_id": TIKTOK_APP_ID,
        "secret": TIKTOK_APP_SECRET,
        "auth_code": code,
        "grant_type": "authorization_code",
    }
    headers = {"Content-Type": "application/json"}

    # 调试日志
    print("\n" + "=" * 50)
    print("TikTok Business API Token 请求")
    print("=" * 50)
    print(f"URL: {TIKTOK_TOKEN_URL}")
    print(f"auth_code: {code}")
    print(f"app_id: {TIKTOK_APP_ID}")
    print(f"grant_type: authorization_code")
    print("=" * 50)

    response = requests.post(TIKTOK_TOKEN_URL, json=token_data, headers=headers)

    # 打印响应
    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("=" * 50 + "\n")

    response.raise_for_status()
    return response.json()


def get_tiktok_advertiser_ids(access_token: str) -> list[str]:
    """获取授权的广告主 ID 列表"""
    headers = {
        "Access-Token": access_token,
        "Content-Type": "application/json",
    }
    params = {
        "app_id": TIKTOK_APP_ID,
        "secret": TIKTOK_APP_SECRET,
    }

    print("\n" + "=" * 50)
    print("获取 Advertiser IDs")
    print("=" * 50)

    response = requests.get(TIKTOK_ADVERTISER_URL, headers=headers, params=params)

    print(f"Status: {response.status_code}")
    print(f"Response: {response.text}")
    print("=" * 50 + "\n")

    if response.status_code == 200:
        result = response.json()
        if result.get("code") == 0:
            data = result.get("data", {})
            # 返回广告主 ID 列表
            advertiser_list = data.get("list", [])
            return [str(adv.get("advertiser_id", "")) for adv in advertiser_list]
    return []


def render_tiktok_success_page(
    access_token: str,
    refresh_token: str,
    advertiser_ids: list[str],
    expires_in: int,
    refresh_expires_in: int,
) -> str:
    """渲染 TikTok Business API 授权成功页面"""
    advertiser_ids_str = ", ".join(advertiser_ids) if advertiser_ids else "无"

    # 在控制台打印信息
    print("\n" + "="*50)
    print("TikTok Business API 授权成功")
    print("="*50)
    print(f"Access Token: {access_token}")
    print(f"Refresh Token: {refresh_token}")
    print(f"Advertiser IDs: {advertiser_ids_str}")
    print(f"Access Token 有效期: {expires_in} 秒")
    print(f"Refresh Token 有效期: {refresh_expires_in} 秒")
    print("="*50 + "\n")

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TikTok 授权成功</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background-color: #f0f2f5;
                padding: 20px;
            }}
            .container {{
                max-width: 900px;
                width: 100%;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.1);
                text-align: center;
            }}
            h1 {{
                color: #000000;
                margin-bottom: 30px;
                font-size: 28px;
            }}
            .token-box {{
                background: #f8f9fa;
                padding: 20px;
                border-radius: 6px;
                word-break: break-all;
                margin: 10px 0 20px 0;
                font-family: 'Courier New', monospace;
                font-size: 14px;
                line-height: 1.6;
                color: #333;
                border: 1px solid #e0e0e0;
                text-align: left;
            }}
            .token-label {{
                font-weight: bold;
                color: #333;
                margin-top: 20px;
                margin-bottom: 5px;
            }}
            button {{
                padding: 12px 24px;
                background-color: #000000;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
                margin: 5px;
            }}
            button:hover {{
                background-color: #333333;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                transform: translateY(-2px);
            }}
            .success-icon {{
                color: #28a745;
                font-size: 48px;
                margin-bottom: 10px;
            }}
            .open-id {{
                font-size: 14px;
                color: #666;
                margin-bottom: 20px;
            }}
            .warning-box {{
                background-color: #fff3cd;
                border: 1px solid #ffc107;
                border-radius: 6px;
                padding: 15px;
                margin: 20px 0;
                color: #856404;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 8px;
            }}
            .warning-icon {{
                font-size: 20px;
            }}
            .expires-info {{
                font-size: 12px;
                color: #888;
                margin-top: 5px;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="success-icon">✓</div>
            <h1>TikTok Business API 授权成功</h1>

            <div class="token-label">Advertiser IDs</div>
            <div class="token-box" id="advertiser-ids">{advertiser_ids_str}</div>
            <button onclick="copyToken('advertiser-ids')">复制 Advertiser IDs</button>

            <div class="token-label">Access Token</div>
            <div class="token-box" id="access-token">{access_token}</div>
            <div class="expires-info">有效期: {expires_in // 3600} 小时</div>
            <button onclick="copyToken('access-token')">复制 Access Token</button>

            <div class="token-label">Refresh Token</div>
            <div class="token-box" id="refresh-token">{refresh_token}</div>
            <div class="expires-info">有效期: {refresh_expires_in // 86400} 天</div>
            <button onclick="copyToken('refresh-token')">复制 Refresh Token</button>

            <div class="warning-box">
                <span class="warning-icon">⚠️</span>
                <span>请自行保管 token，本应用不保存</span>
            </div>
        </div>

        <script>
            function copyToken(elementId) {{
                const token = document.getElementById(elementId).textContent;
                navigator.clipboard.writeText(token).then(() => {{
                    alert('已复制到剪贴板！');
                }});
            }}
        </script>
    </body>
    </html>
    """


@app.route("/")
def index() -> str:
    """首页，显示 Facebook 和 TikTok 授权链接"""
    fb_auth_url = ""
    tiktok_auth_url = ""

    if FACEBOOK_APP_ID:
        fb_auth_url = (
            f"{FACEBOOK_OAUTH_URL}?"
            f"client_id={FACEBOOK_APP_ID}&"
            f"redirect_uri={REDIRECT_URI}&"
            f"scope={FACEBOOK_SCOPE}&"
            f"response_type=code"
        )

    if TIKTOK_APP_ID:
        state = secrets.token_hex(16)
        session["tiktok_state"] = state
        # Business API 使用 app_id 而非 client_key
        tiktok_auth_url = (
            f"{TIKTOK_OAUTH_URL}?"
            f"app_id={TIKTOK_APP_ID}&"
            f"redirect_uri={TIKTOK_REDIRECT_URI}&"
            f"state={state}"
        )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>OAuth 授权</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                height: 100vh;
                margin: 0;
                background-color: #f0f2f5;
            }}
            .container {{
                display: flex;
                flex-direction: column;
                gap: 20px;
                align-items: center;
            }}
            h1 {{
                color: #333;
                margin-bottom: 20px;
            }}
            .btn {{
                display: inline-block;
                padding: 16px 32px;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                transition: all 0.3s ease;
                min-width: 200px;
                text-align: center;
            }}
            .btn-facebook {{
                background-color: #1877f2;
                box-shadow: 0 2px 8px rgba(24, 119, 242, 0.3);
            }}
            .btn-facebook:hover {{
                background-color: #166fe5;
                box-shadow: 0 4px 12px rgba(24, 119, 242, 0.4);
                transform: translateY(-2px);
            }}
            .btn-tiktok {{
                background-color: #000000;
                box-shadow: 0 2px 8px rgba(0, 0, 0, 0.3);
            }}
            .btn-tiktok:hover {{
                background-color: #333333;
                box-shadow: 0 4px 12px rgba(0, 0, 0, 0.4);
                transform: translateY(-2px);
            }}
            .btn-disabled {{
                background-color: #cccccc;
                cursor: not-allowed;
                pointer-events: none;
            }}
            .btn-outline {{
                background-color: transparent;
                border: 2px solid #000;
                color: #000;
                box-shadow: none;
            }}
            .btn-outline:hover {{
                background-color: #000;
                color: white;
            }}
            .divider {{
                width: 100%;
                height: 1px;
                background-color: #ddd;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>OAuth 授权</h1>
            <a href="{fb_auth_url}" class="btn btn-facebook {'btn-disabled' if not fb_auth_url else ''}">
                Facebook 授权
            </a>
            <a href="{tiktok_auth_url}" class="btn btn-tiktok {'btn-disabled' if not tiktok_auth_url else ''}">
                TikTok 授权
            </a>
            <div class="divider"></div>
            <a href="/tiktok/manual" class="btn btn-outline {'btn-disabled' if not TIKTOK_APP_ID else ''}">
                TikTok 手动授权
            </a>
        </div>
    </body>
    </html>
    """


@app.route("/fb/callback")
def callback() -> tuple[str, int] | str:
    """处理 Facebook OAuth 回调"""
    code = request.args.get("code")
    error = request.args.get("error")

    if error:
        return f"授权失败: {error}", 400

    if not code:
        return "缺少授权码", 400

    try:
        # 1. 获取短期 access_token
        token_params = {
            "client_id": FACEBOOK_APP_ID,
            "client_secret": FACEBOOK_APP_SECRET,
            "redirect_uri": REDIRECT_URI,
            "code": code,
        }
        response = requests.get(FACEBOOK_TOKEN_URL, params=token_params)
        response.raise_for_status()
        token_data = response.json()

        short_lived_token = token_data.get("access_token")
        if not short_lived_token:
            return "获取短期 token 失败", 500

        # 2. 将短期 token 换成长期 token
        long_token_params = {
            "grant_type": "fb_exchange_token",
            "client_id": FACEBOOK_APP_ID,
            "client_secret": FACEBOOK_APP_SECRET,
            "fb_exchange_token": short_lived_token,
        }
        long_token_response = requests.get(FACEBOOK_TOKEN_URL, params=long_token_params)
        long_token_response.raise_for_status()
        long_token_data = long_token_response.json()

        access_token = long_token_data.get("access_token", short_lived_token)

        # 3. 获取用户信息
        user_id = "未获取"
        user_name = "未获取"
        try:
            user_info_params = {
                "fields": "id,name",
                "access_token": access_token,
            }
            user_info_response = requests.get(FACEBOOK_GRAPH_API_URL, params=user_info_params)
            user_info_response.raise_for_status()
            user_info = user_info_response.json()

            user_id = user_info.get("id", "未获取")
            user_name = user_info.get("name", "未获取")

            # 在控制台打印信息
            print("\n" + "="*50)
            print("Facebook OAuth 授权成功")
            print("="*50)
            print(f"Access Token: {access_token}")
            print(f"User ID: {user_id}")
            print(f"User Name: {user_name}")
            print("="*50 + "\n")
        except requests.RequestException as e:
            print(f"警告: 获取用户信息失败: {str(e)}")

        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Access Token</title>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    display: flex;
                    justify-content: center;
                    align-items: center;
                    min-height: 100vh;
                    margin: 0;
                    background-color: #f0f2f5;
                    padding: 20px;
                }}
                .container {{
                    max-width: 900px;
                    width: 100%;
                    background: white;
                    padding: 40px;
                    border-radius: 8px;
                    box-shadow: 0 2px 12px rgba(0,0,0,0.1);
                    text-align: center;
                }}
                h1 {{
                    color: #1877f2;
                    margin-bottom: 30px;
                    font-size: 28px;
                }}
                .token-box {{
                    background: #f8f9fa;
                    padding: 20px;
                    border-radius: 6px;
                    word-break: break-all;
                    margin: 20px 0;
                    font-family: 'Courier New', monospace;
                    font-size: 14px;
                    line-height: 1.6;
                    color: #333;
                    border: 1px solid #e0e0e0;
                }}
                button {{
                    padding: 12px 24px;
                    background-color: #1877f2;
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 16px;
                    font-weight: bold;
                    cursor: pointer;
                    transition: all 0.3s ease;
                    box-shadow: 0 2px 8px rgba(24, 119, 242, 0.3);
                }}
                button:hover {{
                    background-color: #166fe5;
                    box-shadow: 0 4px 12px rgba(24, 119, 242, 0.4);
                    transform: translateY(-2px);
                }}
                .success-icon {{
                    color: #28a745;
                    font-size: 48px;
                    margin-bottom: 10px;
                }}
                .user-info {{
                    margin: 20px 0;
                }}
                .user-name {{
                    font-size: 24px;
                    font-weight: bold;
                    color: #333;
                    margin-bottom: 5px;
                }}
                .user-id {{
                    font-size: 14px;
                    color: #666;
                    margin-bottom: 20px;
                }}
                .warning-box {{
                    background-color: #fff3cd;
                    border: 1px solid #ffc107;
                    border-radius: 6px;
                    padding: 15px;
                    margin: 20px 0;
                    color: #856404;
                    display: flex;
                    align-items: center;
                    justify-content: center;
                    gap: 8px;
                }}
                .warning-icon {{
                    font-size: 20px;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>授权成功</h1>
                <div class="user-info">
                    <div class="user-name">{user_name}</div>
                    <div class="user-id">用户 ID: {user_id}</div>
                </div>
                <h2 style="color: #333; margin-top: 30px; margin-bottom: 10px;">Access Token</h2>
                <div class="token-box" id="token">{access_token}</div>
                <div class="warning-box">
                    <span class="warning-icon">⚠️</span>
                    <span>请自行保管 access token，本应用不保存</span>
                </div>
                <button onclick="copyToken()">复制 Token</button>
            </div>

            <script>
                function copyToken() {{
                    const token = document.getElementById('token').textContent;
                    navigator.clipboard.writeText(token).then(() => {{
                        alert('Token 已复制到剪贴板！');
                    }});
                }}
            </script>
        </body>
        </html>
        """

    except requests.RequestException as e:
        return f"请求失败: {str(e)}", 500


@app.route("/tiktok/callback")
def tiktok_callback() -> tuple[str, int] | str:
    """处理 TikTok OAuth 回调"""
    code = request.args.get("code")
    state = request.args.get("state")
    error = request.args.get("error")

    if error:
        error_description = request.args.get("error_description", "未知错误")
        return f"授权失败: {error} - {error_description}", 400

    if not code:
        return "缺少授权码", 400

    # 验证 state（防止 CSRF 攻击）
    saved_state = session.get("tiktok_state")
    if saved_state and state != saved_state:
        return "State 验证失败", 400

    try:
        result = exchange_tiktok_token(code, TIKTOK_REDIRECT_URI)

        # Business API 响应格式: {"code": 0, "message": "OK", "data": {...}}
        if result.get("code") != 0:
            error_msg = result.get("message", result.get("error", "未知错误"))
            return f"获取 token 失败: {error_msg}", 500

        data = result.get("data", result)
        access_token = data.get("access_token", "未获取")

        # 获取广告主 ID 列表
        advertiser_ids = get_tiktok_advertiser_ids(access_token)

        return render_tiktok_success_page(
            access_token=access_token,
            refresh_token=data.get("refresh_token", "未获取"),
            advertiser_ids=advertiser_ids,
            expires_in=data.get("expires_in", 0),
            refresh_expires_in=data.get("refresh_expires_in", 0),
        )

    except requests.RequestException as e:
        return f"请求失败: {str(e)}", 500


@app.route("/tiktok/manual", methods=["GET", "POST"])
def tiktok_manual() -> tuple[str, int] | str:
    """TikTok 手动授权：输入回调 URL 提取 code 换取 token"""
    if not TIKTOK_APP_ID or not TIKTOK_APP_SECRET:
        return "请先配置 TIKTOK_APP_ID 和 TIKTOK_APP_SECRET", 500

    if request.method == "POST":
        callback_url = request.form.get("callback_url", "").strip()

        if not callback_url:
            return "请输入回调 URL", 400

        # 从 URL 中提取 code 和 redirect_uri
        # TikTok 可能返回 auth_code 或 code
        try:
            parsed = urlparse(callback_url)
            params = parse_qs(parsed.query)
            code = params.get("auth_code", [None])[0] or params.get("code", [None])[0]

            if not code:
                return "URL 中未找到 code 或 auth_code 参数", 400

            # 自动提取 redirect_uri（去掉 query 和 fragment）
            redirect_uri = urlunparse((parsed.scheme, parsed.netloc, parsed.path, "", "", ""))

            result = exchange_tiktok_token(code, redirect_uri)

            # Business API 响应格式: {"code": 0, "message": "OK", "data": {...}}
            if result.get("code") != 0:
                error_msg = result.get("message", result.get("error", "未知错误"))
                return f"获取 token 失败: {error_msg}", 500

            data = result.get("data", result)
            access_token = data.get("access_token", "未获取")

            # 获取广告主 ID 列表
            advertiser_ids = get_tiktok_advertiser_ids(access_token)

            return render_tiktok_success_page(
                access_token=access_token,
                refresh_token=data.get("refresh_token", "未获取"),
                advertiser_ids=advertiser_ids,
                expires_in=data.get("expires_in", 0),
                refresh_expires_in=data.get("refresh_expires_in", 0),
            )

        except requests.RequestException as e:
            return f"请求失败: {str(e)}", 500

    # GET 请求：显示表单
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>TikTok 手动授权</title>
        <meta charset="utf-8">
        <style>
            body {{
                font-family: Arial, sans-serif;
                display: flex;
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                background-color: #f0f2f5;
                padding: 20px;
            }}
            .container {{
                max-width: 800px;
                width: 100%;
                background: white;
                padding: 40px;
                border-radius: 8px;
                box-shadow: 0 2px 12px rgba(0,0,0,0.1);
            }}
            h1 {{
                color: #000;
                margin-bottom: 10px;
                font-size: 24px;
                text-align: center;
            }}
            .description {{
                color: #666;
                margin-bottom: 30px;
                text-align: center;
                font-size: 14px;
            }}
            .form-group {{
                margin-bottom: 20px;
            }}
            label {{
                display: block;
                margin-bottom: 8px;
                font-weight: bold;
                color: #333;
            }}
            .hint {{
                font-size: 12px;
                color: #888;
                margin-top: 5px;
            }}
            input[type="text"], textarea {{
                width: 100%;
                padding: 12px;
                border: 1px solid #ddd;
                border-radius: 6px;
                font-size: 14px;
                font-family: 'Courier New', monospace;
                box-sizing: border-box;
            }}
            textarea {{
                height: 80px;
                resize: vertical;
            }}
            input[type="text"]:focus, textarea:focus {{
                outline: none;
                border-color: #000;
            }}
            button {{
                width: 100%;
                padding: 14px;
                background-color: #000;
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 16px;
                font-weight: bold;
                cursor: pointer;
                transition: all 0.3s ease;
            }}
            button:hover {{
                background-color: #333;
            }}
            .back-link {{
                display: block;
                text-align: center;
                margin-top: 20px;
                color: #666;
                text-decoration: none;
            }}
            .back-link:hover {{
                color: #000;
            }}
            .example {{
                background: #f8f9fa;
                padding: 10px;
                border-radius: 4px;
                font-size: 12px;
                color: #666;
                margin-top: 5px;
                word-break: break-all;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>TikTok 手动授权</h1>
            <p class="description">粘贴授权后的回调 URL，自动提取 code 和 redirect_uri 换取 token</p>

            <form method="POST">
                <div class="form-group">
                    <label>授权后的回调 URL（包含 code 参数）</label>
                    <textarea name="callback_url" placeholder="https://your-domain.com/callback?code=xxx&state=xxx" required></textarea>
                    <p class="hint">完成 TikTok 授权后，浏览器地址栏中的完整 URL</p>
                    <div class="example">
                        示例: https://example.com/callback?code=abc123&state=xyz
                    </div>
                </div>

                <button type="submit">换取 Token</button>
            </form>

            <a href="/" class="back-link">← 返回首页</a>
        </div>
    </body>
    </html>
    """


def main() -> None:
    """启动 Flask 应用"""
    has_facebook = FACEBOOK_APP_ID and FACEBOOK_APP_SECRET
    has_tiktok = TIKTOK_APP_ID and TIKTOK_APP_SECRET

    if not has_facebook and not has_tiktok:
        print("错误: 请至少配置一个平台的 OAuth 凭据")
        print("请复制 .env.example 为 .env 并填入应用凭据")
        return

    print("OAuth 应用启动中...")
    print(f"请在浏览器中访问: http://localhost:{PORT}")
    if has_facebook:
        print(f"Facebook 回调地址: {REDIRECT_URI}")
    if has_tiktok:
        print(f"TikTok 回调地址: {TIKTOK_REDIRECT_URI}")
    app.run(debug=True, host="0.0.0.0", port=PORT)
