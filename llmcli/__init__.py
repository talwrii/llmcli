import argparse
import getpass
import json
import os

from revChatGPT.revChatGPT import Chatbot

PARSER = argparse.ArgumentParser(
    description="Run large language models from the command-line"
)
parsers = PARSER.add_subparsers(dest="command")
chatgpt = parsers.add_parser("chatgpt", help="Set a prompt to a large language model")
chatgpt.add_argument("--login", action="store_true", help="Login to the API")
chatgpt.add_argument("prompt", help="Prompt to the model")


def main():
    args = PARSER.parse_args()

    if args.command is None:
        PARSER.print_help()
    elif args.command == "chatgpt":
        chatgpt(args)
    else:
        raise ValueError(args.command)


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "llmcli")
SESSION_FILE = os.path.join(CONFIG_DIR, "chatgpt-session.json")


def chatgpt(args):
    # make sure the .config/llmcli directory exists
    if not os.path.isdir(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    if args.login:
        if os.path.isfile(SESSION_FILE):
            os.remove(SESSION_FILE)

    chat = chatgpt_login()
    print(chat.get_chat_response(args.prompt))


def chatgpt_login():
    # Get the session
    if os.path.isfile(SESSION_FILE):
        chat = Chatbot(config={})
        with open(SESSION_FILE, "r") as f:
            session = json.load(f)
        chatgpt_set_session(chat, session)
    else:
        email = input("Email:")
        password = getpass.getpass()
        d = dict(email=email, password=password)
        chat = Chatbot(config=d)
        chat.refresh_session()
        session = chatgpt_extract_session(chat)
        with open(SESSION_FILE, "w") as f:
            json.dump(session, f)

    return chat


def chatgpt_extract_session(chat):
    """Extract session token from chatbot object"""
    return dict(
        Authorization=chat.config["Authorization"],
        session_token=chat.config["session_token"],
    )


def chatgpt_set_session(chat, session):
    """Set session token from chatbot object"""
    chat.config["Authorization"] = session["Authorization"]
    chat.config["session_token"] = session["session_token"]
    chat.refresh_headers()
