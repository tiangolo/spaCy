from .conf import settings, bot_comment
import typer
import httpx
from enum import Enum


app = typer.Typer()


class TriggerTypes(str, Enum):
    trigger_train_transformers = "trigger-train-transformers"


@app.command()
def trigger(test_type: TriggerTypes):
    # Send one single comment while waiting for the result
    bot_comment(message="Triggering test in CI... ⏳")
    response = httpx.post(
        f"https://api.buildkite.com/v2/organizations/explosion-ai/pipelines/{test_type.value}/builds",
        headers={
            "Authorization": f"Bearer {settings.input_ci_token.get_secret_value()}"
        },
        json={
            "commit": "HEAD",
            "branch": "spacy-3",
            "message": f"Trigger {test_type.value}",
            "author": {"name": "Explosion", "email": "contact@explosion.ai"},
            "env": {"SPACY_COMMIT": "$COMMIT"},
            "meta_data": {},
        },
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
