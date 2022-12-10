import argparse
import getpass
import json
import logging
import os
import sys

from revChatGPT.revChatGPT import Chatbot


def common_config(parser):
    parser.add_argument(
        "--debug", action="store_true", help="Include debug output (to stderr)"
    )


def main_parser():
    parser = argparse.ArgumentParser(
        description="Run large language models from the command-line"
    )
    parsers = parser.add_subparsers(dest="command")
    chatgpt_parser = parsers.add_parser(
        "chatgpt", help="Set a prompt to a large language model"
    )

    chatgpt_config(chatgpt_parser)
    common_config(parser)
    return parser


def chatgpt_config(parser):
    parser.add_argument("--new", action="store_true", help="Start a new conversation")
    parser.add_argument("--login", action="store_true", help="Login to the API")
    parser.add_argument("--stdin", action="store_true", help="Read request from stdin")
    parser.add_argument(
        "--read-credentials-stdin",
        action="store_true",
        help="Read credentials from standard in in JSON",
    )
    parser.add_argument("prompt", help="Prompt to the model", nargs="*")
    parser.add_argument("--conversation", "-c")


def main():
    parser = main_parser()
    args = main_parser().parse_args()
    setup_debug(args)

    if args.command is None:
        parser.print_help()
    elif args.command == "chatgpt":
        chatgpt(args)
    else:
        raise ValueError(args.command)


def chatgpt_main():
    parser = argparse.ArgumentParser(description="chatgpt interface")
    common_config(parser)
    chatgpt_config(parser)
    args = parser.parse_args()
    setup_debug(args)
    chatgpt(args)


def setup_debug(args):
    if args.debug:
        logging.basicConfig(level=logging.DEBUG)


CONFIG_DIR = os.path.join(os.path.expanduser("~"), ".config", "llmcli")
SESSION_FILE = os.path.join(CONFIG_DIR, "chatgpt-session.json")
CONVERSATION_FILE = os.path.join(CONFIG_DIR, "chatgpt-conversations.json")


class ConversationTracker:
    """Track conversations.

    Default to use parent pid which will tend to be the terminal
    """

    def __init__(self):
        self.conversation_ids = {}
        self.read_data()

    def write_data(self):
        # sync data to file
        with open(CONVERSATION_FILE, "w") as f:
            json.dump(self.conversation_ids, f)

    def read_data(self):
        # read data from file
        if os.path.exists(CONVERSATION_FILE):
            with open(CONVERSATION_FILE) as f:
                self.conversation_ids = json.load(f)
        else:
            self.conversation_ids = {}

    def _guess_conversation(self):
        # get parent pid
        return "guessed-pid-{os.getppid()}"

    def get(self, conversation=None):
        # get conversation id for parent pid
        self.read_data()
        conversation = conversation or self._guess_conversation()
        return self.conversation_ids.get(conversation, None)

    def set(self, *, details, conversation=None):
        # set conversation id for parent pid
        conversation = conversation or self._guess_conversation()
        self.conversation_ids[conversation] = details
        self.write_data()


def chatgpt(args):
    # make sure the .config/llmcli directory exists
    if not os.path.isdir(CONFIG_DIR):
        os.makedirs(CONFIG_DIR, exist_ok=True)

    if args.login:
        if os.path.isfile(SESSION_FILE):
            os.remove(SESSION_FILE)

    chat = chatgpt_login(SESSION_FILE, args.read_credentials_stdin)

    # get conversation id
    conversation_tracker = ConversationTracker()

    if not args.new:
        conversation_details = parent_id, conversation_id = conversation_tracker.get(
            args.conversation
        )
        logging.debug(f"loading conversation details: {conversation_details}")
        chat.conversation_id = conversation_id
        chat.parent_id = parent_id
    else:
        logging.debug("starting new conversation")

    if args.stdin and args.prompt:
        raise ValueError("Cannot have prompt and stdin")

    if args.stdin:
        prompt = sys.stdin.read()
    else:
        prompt = " ".join(args.prompt)

    response = chat.get_chat_response(prompt)

    logging.debug("Response: %s", response)

    conversation_details = (response["parent_id"], response["conversation_id"])
    conversation_tracker.set(
        details=conversation_details, conversation=args.conversation
    )
    logging.debug("storing conversation_id: %s", conversation_details)

    print(response["message"])


def prompt_credentials():
    email = input("Email:")
    password = getpass.getpass()
    return dict(email=email, password=password)


def read_credentials_from_stdin():
    d = json.loads(sys.stdin.read())
    assert set(d.keys()) == {"email", "password"}
    assert set(map(type, d.values())) == {str}
    return d


def chatgpt_login(session_file, read_credentials=False):
    # Get the session
    if os.path.isfile(session_file):
        chat = Chatbot(config={})
        with open(session_file, "r") as f:
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
        with open(session_file, "w") as f:
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
