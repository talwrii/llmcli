import sys
import argparse
import getpass
import json
import os

from revChatGPT.revChatGPT import Chatbot


def main_parser():
    parser = argparse.ArgumentParser(
        description="Run large language models from the command-line"
    )
    parsers = parser.add_subparsers(dest="command")
    chatgpt_parser = parsers.add_parser(
        "chatgpt", help="Set a prompt to a large language model"
    )
    chatgpt_config(chatgpt_parser)
    return parser


def chatgpt_config(parser):
    parser.add_argument("--login", action="store_true", help="Login to the API")
    parser.add_argument(
        "--read-credentials-stdin",
        action="store_true",
        help="Read credentials from standard in in JSON",
    )
    parser.add_argument("prompt", help="Prompt to the model", nargs="*")


def main():
    parser = main_parser()
    args = main_parser().parse_args()

    if args.command is None:
        parser.print_help()
    elif args.command == "chatgpt":
        chatgpt(args)
    else:
        raise ValueError(args.command)


def chatgpt_main():
    parser = argparse.ArgumentParser(description="chatgpt interface")
    chatgpt_config(parser)
    args = parser.parse_args()
    chatgpt(args)


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "llmcli")
SESSION_FILE = os.path.join(CONFIG_DIR, "chatgpt-session.json")


def chatgpt(args):
    # make sure the .config/llmcli directory exists
    if not os.path.isdir(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    if args.login:
        if os.path.isfile(SESSION_FILE):
            os.remove(SESSION_FILE)

    chat = chatgpt_login(args.read_credentials_stdin)
    print(chat.get_chat_response(" ".join(args.prompt))["message"])


def prompt_credentials():
    email = input("Email:")
    password = getpass.getpass()
    return dict(email=email, password=password)


def read_credentials_from_stdin():
    d = json.loads(sys.stdin.read())
    assert set(d.keys()) == {"email", "password"}
    assert set(map(type, d.values())) == {str}
    return d


def chatgpt_login(read_credentials=False):
    # Get the session
    if os.path.isfile(SESSION_FILE):
        chat = Chatbot(config={})
        with open(SESSION_FILE, "r") as f:
            session = json.load(f)
        chatgpt_set_session(chat, session)
    else:
        if read_credentials:
            config = read_credentials_from_stdin()
        else:
            config = prompt_credentials()
        chat = Chatbot(config=config)
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
