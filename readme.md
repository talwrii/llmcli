# llmcli

A command line interface for using some large language models.

Support models:

* [chatgpt](https://openai.com/blog/chatgpt/)
* Other models when I want to use this. I might end up hooking this up to huggingface and gpt

Install:

```
pip install large-language-model-cli
```

# chatgpt

```llmcli chatgpt "prompt"```

Prompts for password if necessarily. Saves a session tokken

Use `--login` to force a new login.


# Prior work

* There are libraries in python and node to talk to chatgpt
* For ChatGPT [revChatGPT](https://github.com/acheong08/ChatGPT) which has a [Text User Interface](https://en.wikipedia.org/wiki/Text-based_user_interface) but not command line interface.
