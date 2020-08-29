from datetime import datetime
from pathlib import Path
from typing import List, Optional

from github import Github
from pydantic import AnyHttpUrl, BaseModel, BaseSettings, SecretStr, validator

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
    issue: PartialGitHubEventIssue
    comment: PartialGitHubEventComment


class Settings(BaseSettings):
    github_repository: str
    input_token: SecretStr
    input_ci_token: SecretStr
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


settings = Settings()

g = Github(settings.input_token.get_secret_value())
repo = g.get_repo(settings.github_repository)
issue = repo.get_issue(settings.github_event.issue.number)


def bot_comment(*, message: str = "", output: str = "", error_output: str = ""):
    comment = "💥 🤖\n\n"
    if message:
        comment += f"{message}\n\n"
    if output:
        comment += f"## Output:\n\n{output}"
    if error_output:
        comment += f"## Errors:\n\n{error_output}"
    issue.create_comment(comment)
