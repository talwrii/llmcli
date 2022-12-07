import setuptools
import distutils.core

setuptools.setup(
    name="large-language-model-cli",
    version=0.7,
    author="Talwrii",
    long_description_content_type="text/markdown",
    author_email="Talwrii@googlemail.com",
    description="Command-line for interacting with large language models. not TUI. chatgpt",
    license="mit",
    keywords="ChatGPT",
    url="https://github.com/talwrii/llmcli",
    packages=["llmcli"],
    long_description=open("readme.md").read(),
    entry_points={"console_scripts": ["llmcli=llmcli:main"]},
    install_requires=["revChatGPT"],
    classifiers=[],
)
