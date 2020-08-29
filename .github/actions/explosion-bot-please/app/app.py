import logging
from enum import Enum

import httpx
import typer
from github.Commit import Commit

from .conf import bot_comment, issue, settings

app = typer.Typer()


class TriggerTypes(str, Enum):
    trigger_train_transformers = "trigger-train-transformers"


@app.command()
def trigger(test_type: TriggerTypes):
    # Send one single comment while waiting for the result
    bot_comment(message="Triggering test in CI... ⏳")
    pr = issue.as_pull_request()
    commits = pr.get_commits()
    last_commit: Commit = commits.reversed[0]
    send_json = {
        "commit": "HEAD",
        "branch": "spacy-3",
        "message": f"Trigger {test_type.value}",
        "author": {"name": "Explosion", "email": "contact@explosion.ai"},
        "env": {"SPACY_COMMIT": f"{last_commit.sha}"},
        "meta_data": {},
    }
    logging.info(f"JSON to send: {send_json}")
    raise typer.Abort()
    response = httpx.post(
        f"https://api.buildkite.com/v2/organizations/explosion-ai/pipelines/{test_type.value}/builds",
        headers={
            "Authorization": f"Bearer {settings.input_ci_token.get_secret_value()}"
        },
        json=send_json,
    )
    if response.status_code != 200:
        typer.echo(
            "😿 Error triggering CI:\n\n" "```\n" f"{response.text}" "\n```", err=True
        )
    else:
        data = response.json()
        if "web_url" in data:
            web_url = data["web_url"]
            typer.echo(f"🚀 Successfully triggered: {web_url}")


@app.command()
def info():
    typer.echo(
        "About Explosion: https://explosion.ai\n\n"
        "About spaCy: https://https://spacy.io\n\n"
    )
