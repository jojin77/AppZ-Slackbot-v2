import os
import re
import logging, sys, traceback
import json
from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    handlers=[logging.FileHandler('/appz/log/slackbot.log', mode='a', encoding='utf-8')]
)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
logging.getLogger().addHandler(console_handler)

# Get the environment variables
app_token = os.environ.get("APP_TOKEN")
bot_token = os.environ.get("BOT_TOKEN")
target_channel_id = os.environ.get("TARGET_CHANNEL_ID")
channel_ids = os.environ.get("CHANNEL_IDS").split(",")
python_encoding = os.environ.get("PYTHONIOENCODING")
if not app_token:
    logging.warning('APP_TOKEN not found in the vault.')
if not bot_token:
    logging.warning('BOT_TOKEN not found in the vault.')
if not target_channel_id:
    logging.warning('TARGET_CHANNEL_ID not found in env.')
if not channel_ids:
    logging.warning('CHANNEL_IDS not found in env.')
#if not python_encoding:
#    logging.warning('PYTHONIOENCODING not found in env.')

if not all([app_token, bot_token, target_channel_id, channel_ids]):
    logging.warning('Missing required environment variables. Aborting...')
    sys.exit(1)
# Initializes your app with your bot token and socket mode handler
app = App(token=bot_token)
def load_filter_patterns():
    patterns_file = "/appz/scripts/webapps/patterns.json"
    try:
        with open(patterns_file, 'r') as file:
            data = json.load(file)
            return data.get('patterns', [])
    except Exception:
        logging.error("Failed to load filter patterns")
        logging.error(traceback.format_exc())
        sys.exit(1)
#def load_filter_patterns():
#    patterns_file = "/appz/scripts/patterns.json"
#    with open(patterns_filee, 'r') as file:
#        data = json.load(file)
#        return data.get('patterns', [])

# Listens to incoming messages from the specified channels and filters based on patterns
@app.message(re.compile("|".join(load_filter_patterns())))
def filter_messages(message, say):
    if message['channel'] in channel_ids:
        handle_filtered_message(message, say)

def handle_filtered_message(message, say):
    # Get the original message text
    original_message = message['text']

    # Send the message to the target channel
    try:
        app.client.chat_postMessage(
            channel=target_channel_id,
            text=original_message,
            blocks=[
                {
                    "type": "section",
                    "text": {"type": "mrkdwn", "text": original_message},
                    "accessory": {
                        "type": "button",
                        "text": {
                            "type": "plain_text",
                            "text": "Have you fixed it?"
                        },
                        "action_id": "button_click"
                    }
                }
            ]
        )
    except Exception as e:
        app.logger.error(f"Failed to send message: {e}")

@app.action("button_click")
def action_button_click(body, ack, say, client):
    # Acknowledge the action
    ack()

    # Get the original message's timestamp
    original_timestamp = body["message"]["ts"]

    # Add a white check mark reaction to the original message
    client.reactions_add(
        channel=body["channel"]["id"],
        name="white_check_mark",
        timestamp=original_timestamp
    )

@app.event("message")
def handle_message_events(body, logger):
    logger.info(body)
for channel_id in channel_ids:
    try:
        app.client.conversations_info(channel=channel_id)
    except Exception as e:
        logging.error(f"Invalid channel ID: {channel_id}")
        sys.exit(1)

# Start your app
if __name__ == "__main__":
    logging.getLogger().setLevel(logging.ERROR)  # Set the root logger level to ERROR
    logging.getLogger("slack_bolt").setLevel(logging.ERROR)  # Set the Bolt logger level to ERROR
    logging.getLogger("slack_sdk").setLevel(logging.ERROR)  # Set the Slack SDK logger level to ERROR
    os.environ["PYTHONIOENCODING"] = "UTF-8"
    SocketModeHandler(app, app_token).start()
