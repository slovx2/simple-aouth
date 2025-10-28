# Simple OAuth

Simple Facebook OAuth application to quickly get long-lived access_token.

## Features

- Facebook OAuth authorization
- Auto exchange short-lived token to long-lived token (60 days validity)
- Simple UI interface
- One-click token copy

## Local Usage

1. Install dependencies:
```bash
uv sync
```

2. Configure environment:
```bash
cp .env.example .env
# Edit .env file with your Facebook app credentials
```

3. Run:
```bash
uv run fb-oauth
```

## Docker Usage

### Using Docker Compose (Recommended)

One command to build and deploy:

```bash
# Build and start
docker compose up -d --build

# Stop
docker compose down
```

### Using Docker CLI

1. Build image:
```bash
docker build -t simple-oauth .
```

2. Run container:
```bash
docker run -p 5001:5001 --env-file .env simple-oauth
```

### Image Details

- Base image: `python:3.12-alpine`
- Final image size: **57.1MB**
- Multi-stage build for minimal size
- No uv in final image (only used during build)
- Runs as non-root user for security

## Facebook App Configuration

1. Create app at https://developers.facebook.com/apps/
2. Add Facebook Login product
3. Add OAuth redirect URI: http://localhost:5001/callback
4. Get App ID and App Secret

## Environment Variables

- FACEBOOK_APP_ID: Facebook application ID
- FACEBOOK_APP_SECRET: Facebook application secret
- PORT: Server port (default: 5001)
- REDIRECT_URI: OAuth callback URL (default: http://localhost:5001/callback)
