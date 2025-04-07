import os
import ssl
import certifi
from dotenv import load_dotenv
from fastapi import FastAPI, Request
from slack_bolt import App
from slack_bolt.adapter.fastapi import SlackRequestHandler
from slack_bolt.oauth.oauth_settings import OAuthSettings
from slack_sdk.web import WebClient
from slack_sdk.oauth.installation_store import FileInstallationStore
from slack_sdk.oauth.state_store import FileOAuthStateStore
from slack_bolt.oauth.callback_options import CallbackOptions, SuccessArgs, FailureArgs
from slack_bolt.response import BoltResponse

# Load environment variables
load_dotenv()

# TEMP SSL workaround (safe for local dev only)
unverified_ssl_context = ssl.create_default_context(cafile=certifi.where())
unverified_ssl_context.check_hostname = False
unverified_ssl_context.verify_mode = ssl.CERT_NONE

# OAuth callbacks
def success(args: SuccessArgs) -> BoltResponse:
    return BoltResponse(status=200, body="✅ Slack app installed successfully!")

def failure(args: FailureArgs) -> BoltResponse:
    return BoltResponse(status=args.suggested_status_code, body=f"❌ Install failed: {args.reason}")

# OAuth settings
oauth_settings = OAuthSettings(
    client_id=os.environ["SLACK_CLIENT_ID"],
    client_secret=os.environ["SLACK_CLIENT_SECRET"],
    scopes=["commands", "chat:write"],
    installation_store=FileInstallationStore(base_dir="./data/installations"),
    state_store=FileOAuthStateStore(expiration_seconds=600, base_dir="./data/states"),
    install_path="/slack/install",
    redirect_uri_path="/slack/oauth_redirect",
    callback_options=CallbackOptions(success=success, failure=failure)
)

# Slack app with injected custom SSL context
slack_app = App(
    signing_secret=os.environ["SLACK_SIGNING_SECRET"],
    oauth_settings=oauth_settings,
    client=WebClient(ssl=unverified_ssl_context),
)

# Slash command handler
@slack_app.command("/test")
def handle_test(ack, respond):
    ack()
    respond("Hello World!")

# FastAPI setup
api = FastAPI()
handler = SlackRequestHandler(slack_app)

@api.post("/slack/events")
async def slack_events(req: Request):
    return await handler.handle(req)

@api.get("/slack/install")
async def slack_install(req: Request):
    return await handler.handle(req)

@api.get("/slack/oauth_redirect")
async def slack_oauth_redirect(req: Request):
    return await handler.handle(req)

@api.post("/slack/events")
async def slack_events(req: Request):
    print("📩 Received event from Slack")
    return await handler.handle(req)

