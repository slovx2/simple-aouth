import os
import secrets
from typing import Optional

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
REDIRECT_URI = os.getenv("REDIRECT_URI", f"http://localhost:{PORT}/callback")

# Facebook OAuth URLs
FACEBOOK_API_VERSION = "v21.0"
FACEBOOK_OAUTH_URL = f"https://www.facebook.com/{FACEBOOK_API_VERSION}/dialog/oauth"
FACEBOOK_TOKEN_URL = f"https://graph.facebook.com/{FACEBOOK_API_VERSION}/oauth/access_token"


@app.route("/")
def index() -> str:
    """首页，显示登录链接"""
    if not FACEBOOK_APP_ID:
        return "请先配置 FACEBOOK_APP_ID 环境变量", 500

    auth_url = (
        f"{FACEBOOK_OAUTH_URL}?"
        f"client_id={FACEBOOK_APP_ID}&"
        f"redirect_uri={REDIRECT_URI}&"
        f"scope=email,public_profile&"
        f"response_type=code"
    )

    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Facebook 授权</title>
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
            a {{
                display: inline-block;
                padding: 16px 32px;
                background-color: #1877f2;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-size: 18px;
                font-weight: bold;
                box-shadow: 0 2px 8px rgba(24, 119, 242, 0.3);
                transition: all 0.3s ease;
            }}
            a:hover {{
                background-color: #166fe5;
                box-shadow: 0 4px 12px rgba(24, 119, 242, 0.4);
                transform: translateY(-2px);
            }}
        </style>
    </head>
    <body>
        <a href="{auth_url}">Facebook 授权</a>
    </body>
    </html>
    """


@app.route("/callback")
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
            </style>
        </head>
        <body>
            <div class="container">
                <div class="success-icon">✓</div>
                <h1>Access Token</h1>
                <div class="token-box" id="token">{access_token}</div>
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


def main() -> None:
    """启动 Flask 应用"""
    if not FACEBOOK_APP_ID or not FACEBOOK_APP_SECRET:
        print("错误: 请先配置 FACEBOOK_APP_ID 和 FACEBOOK_APP_SECRET 环境变量")
        print("请复制 .env.example 为 .env 并填入你的 Facebook 应用凭据")
        return

    print(f"Facebook OAuth 应用启动中...")
    print(f"请在浏览器中访问: http://localhost:{PORT}")
    print(f"回调地址: {REDIRECT_URI}")
    app.run(debug=True, host="0.0.0.0", port=PORT)
