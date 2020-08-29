import logging
import sys

from typer.testing import CliRunner
from .conf import settings, command_keyword, issue, bot_comment
from .app import app


def main():
    logging.basicConfig(level=logging.INFO)

    logging.info(f"Using config: {settings.json()}")
    if not issue.pull_request:
        logging.info("GitHub issue event is not a PR")
        sys.exit()
    if settings.github_event.comment.user.login in settings.users:
        if settings.github_event.comment.body.startswith(f"{command_keyword} "):
            # To get body of command after @explosion-bot and a space, so a comment:
            # "@explosion-bot run something"
            # Would get: "run something"
            index = len(command_keyword) + 1
            body = settings.github_event.comment.body[index:]
            runner = CliRunner(mix_stderr=False)
            result = runner.invoke(app, body)
            bot_comment(output=result.stdout, error_output=result.stderr)
    logging.info("Finished")


main()
