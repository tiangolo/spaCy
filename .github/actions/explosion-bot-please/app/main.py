import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Optional

import typer
from github import Github
from github.NamedUser import NamedUser
from pydantic import AnyHttpUrl, BaseModel, BaseSettings, SecretStr, validator
from typer.testing import CliRunner

command_keyword = "@explosion-bot please"


class PartialGitHubEventIssue(BaseModel):
    number: int


class PartialGitHubEventCommentUser(BaseModel):
    id: int
    login: str
    node_id: str


class PartialGitHubEventComment(BaseModel):
    author_association: str
    body: str
    created_at: datetime
    html_url: AnyHttpUrl
    id: int
    issue_url: AnyHttpUrl
    node_id: str
    updated_at: datetime
    url: AnyHttpUrl
    user: PartialGitHubEventCommentUser


class PartialGitHubEvent(BaseModel):
    issue: Optional[PartialGitHubEventIssue] = None
    comment: Optional[PartialGitHubEventComment] = None


class Settings(BaseSettings):
    github_repository: str
    input_token: SecretStr
    github_event_path: Path
    github_event_name: Optional[str] = None
    input_users: str = ""
    users: List[str] = []

    @validator("users")
    def split_commas(cls, v: str, values):
        if "input_users" in values:
            input_users = values["input_users"]
            if isinstance(input_users, str):
                return [u.strip() for u in input_users.split(",")]
        return v

    github_event: Optional[PartialGitHubEvent] = None

    @validator("github_event")
    def parse_event(cls, v, values):
        if "github_event_path" in values:
            github_event_path: Path = values["github_event_path"]
            assert github_event_path.is_file()
            contents = github_event_path.read_text()
            github_event = PartialGitHubEvent.parse_raw(contents)
            return github_event


app = typer.Typer()


@app.command()
def test(test_type: str):
    typer.echo(f"Running test {test_type}")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    settings = Settings()
    logging.info(f"Using config: {settings.json()}")
    g = Github(settings.input_token.get_secret_value())
    repo = g.get_repo(settings.github_repository)
    owner: NamedUser = repo.owner
    github_event: Optional[PartialGitHubEvent] = None
    if not settings.github_event_path.is_file():
        raise RuntimeError("No GitHub event path")
    contents = settings.github_event_path.read_text()
    github_event = PartialGitHubEvent.parse_raw(contents)
    if not github_event:
        logging.info("No GitHub event available")
        sys.exit()
    if not github_event.issue:
        logging.info("GitHub event is not an issue")
        sys.exit()
    issue = repo.get_issue(github_event.issue.number)
    if not issue.pull_request:
        logging.info("GitHub issue event is not a PR")
        sys.exit()
    if github_event.comment:
        if github_event.comment.user.login in settings.users:
            if github_event.comment.body.startswith(f"{command_keyword} "):
                # To get body of command after @explosion-bot and a space, so a comment:
                # "@explosion-bot run something"
                # Would get: "run something"
                index = len(command_keyword) + 1
                body = github_event.comment.body[index:]
                runner = CliRunner(mix_stderr=False)
                result = runner.invoke(app, body)
                message = "💥🤖\n\n"
                if result.stdout:
                    message += f"## Output:\n\n{result.stdout}"
                if result.stderr:
                    message += f"## Errors:\n\n{result.stderr}"
                issue.create_comment(message)
    logging.info("Finished")
