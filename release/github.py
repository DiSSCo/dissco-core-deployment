import logging

from service import Service
from environment import Environment
from typing import Dict, List
import requests
import os
import json
import re
from semantic_version import Version
from datetime import datetime

NO_CHANGES = "No change since last release\n"
GITHUB_API = "https://api.github.com/repos/dissco/"
RELEASE_FILE = "release/release-notes/latest_release.json"


def github_auth() -> Dict[str, str]:
    return {
        "Authorization": f"Bearer {os.environ['GITHUB_TOKEN']}",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def format_release_notes(service: Service, raw_notes: str) -> str:
    no_changes = f"## {service.image_name}\n{NO_CHANGES}\n\n"
    if not raw_notes:
        service.add_release_notes(no_changes)
        return no_changes
    notes = raw_notes
    notes = re.sub(r"by @.+", "", notes)
    notes = re.sub(r"\*\*Full Changelog\*\*:.+", "", notes)
    notes = notes.replace("## What's Changed\n", "")
    notes = re.sub(r"## New Contributors\n.+", "", notes)
    notes = re.sub(r"\* @\w+ made.+", "", notes)
    notes = f"{notes.strip()}\n"
    if not notes or notes == "\n":
        service.add_release_notes(no_changes)
        return no_changes
    service.add_release_notes(notes)
    return f"## {service.image_name}\n{notes}\n"


def get_production_release_name(latest_releases: Dict[str, str]) -> str:
    """
    Increments minor version of production release and updates local file
    :param latest_releases: record of current releases
    :return: new release name
    """
    current_production_release = Version(
        latest_releases.get(Environment.PRODUCTION.value).replace("v", "")
    )
    new_production_release = Version.next_minor(current_production_release)
    release_name = f"v{new_production_release}"
    latest_releases[Environment.PRODUCTION.value] = release_name
    return release_name


def get_acceptance_release_name(latest_releases: Dict[str, str]) -> str:
    """
    Increments patch of acceptance release and updates local file.
    If production env is ahead, increments minor version as well
    :param latest_releases: record of current releases
    :return: new release name
    """
    current_production_release = Version(
        latest_releases.get(Environment.PRODUCTION.value).replace("v", "")
    )
    current_acceptance_release = Version(
        latest_releases.get(Environment.ACCEPTANCE.value).replace("v", "")
    )
    if current_acceptance_release > current_production_release:
        release_name = (
            f"v{Version.next_patch(current_acceptance_release).next_patch()}-alpha"
        )
    else:
        release_name = f"v{current_production_release.next_patch()}-alpha"
    latest_releases[Environment.ACCEPTANCE.value] = release_name
    return release_name


def fetch_release_notes(service: Service) -> str:
    """
    Fetches release notes from GitHub, using previous and latest tags in the Service object
    :param service: Service we want release notes for
    :return: Unformatted release notes
    """
    if service.prev_tag == service.latest_tag:
        service.add_release_notes(NO_CHANGES)
        return f"## {service.image_name}\n{NO_CHANGES}"
    body = {
        "tag_name": get_github_tag_name(service, False),
        "previous_tag_name": get_github_tag_name(service, True),
    }
    repository_name = get_github_repository_name(service)
    result = requests.post(
        f"{GITHUB_API}{repository_name}/releases/generate-notes",
        headers=github_auth(),
        data=json.dumps(body),
    )
    try:
        result.raise_for_status()
    except Exception:
        logging.error(f"Failed to fetch release notes for {service.image_name}")
        return f"## {service.image_name}\nUnable to automatically generate notes\n\n"
    if "application/json" in result.headers.get("content-type"):
        return format_release_notes(service, result.json().get("body"))
    else:
        raise ValueError(f"Unexpected response from GitHub endpoint: '{result.text}'.")


def get_github_repository_name(service: Service) -> str:
    """
    We need to clean our repository name for one edge case
    :param service: service we want the GitHub repository name for
    :return: Repository name
    """
    return (
        service.image_name
        if service.image_name != "disscover-production"
        else "disscover"
    )


def get_github_tag_name(service: Service, prev_tag: bool) -> str:
    """
    DiSSCover github tags have "-orchestration-service" appended to them
    :param service: service we want the GitHub tag name for
    :param: prev_tag: whether we're fetching a previous tag or latest tag
    :return: tag name
    """
    if prev_tag:
        return (
            service.prev_tag
            if service.image_name != "disscover"
            else get_github_tag_name_disscover(service.prev_tag)
        )
    return (
        service.latest_tag
        if service.image_name != "disscover"
        else get_github_tag_name_disscover(service.latest_tag)
    )


def get_github_tag_name_disscover(image_tag_name: str) -> str:
    """
    Searches the Github API for the appropriate tag for disscover
    This is because the disscover tag is longer on github than what is pushed to aws
    :param image_tag_name: image tag name to match
    :return: github tag name
    """
    has_next = True
    page_number = 1
    while has_next:
        tags_response = requests.get(
            f"{GITHUB_API}disscover/tags?page={page_number}",
            headers=github_auth(),
        )
        try:
            tags_response.raise_for_status()
        except Exception:
            logging.info("Unable to retrieve disscover tag name from GITHUB API")
            return ""
        for tag in tags_response.json():
            if image_tag_name in tag["name"]:
                return tag["name"]
        if 'rel="next"' in tags_response.headers["Link"]:
            page_number += 1
        else:
            has_next = False
    logging.info("Unable to match disscover tag")
    return ""


class Github:
    def __init__(self, env: Environment):
        self.env = env
        self.is_update = False
        self.release_name = self.get_release_name()

    def get_release_name(self) -> str:
        """
        Given local records, calculates next release name
        :return: Semantically incremented release name
        """
        with open(RELEASE_FILE, "r") as read_file:
            latest_releases = json.load(read_file)
            if self.env == Environment.PRODUCTION:
                return get_production_release_name(latest_releases)
            else:
                return get_acceptance_release_name(latest_releases)

    def generate_release_notes(self, service_list: List[Service]):
        """
        Generates release notes for a given list of services
        :param service_list: list of services to generate release notes for
        :return: release name
        """
        with open(f"release/release-notes/{self.release_name}.md", "w+") as f:
            print("Compiling release notes")
            f.write(f"# Release {self.release_name}\n")
            f.write(
                f"{self.env.value} release - {datetime.now().strftime('%b-%d-%Y')}\n\n"
            )
            for service in service_list:
                logging.info(f"Combiling release notes for {service.image_name}")
                f.write(fetch_release_notes(service))
        print(f"Compiled release notes for release {self.release_name}")

    def publish_releases(self, service_list: List[Service]) -> None:
        """
        Creates a new release for every service we're looking at
        :param service_list: List of service to generate releases for
        :return: None
        """
        for service in service_list:
            self.publish_release(service)

    def publish_release(self, service: Service) -> None:
        """
        Given a service, create a new release on github
        :param service: service we're creating the release for
        :return: None
        """
        if NO_CHANGES in service.release_notes:
            print(f"No changes in service {service.image_name}. Not publishing release")
            return
        release_id = self.get_existing_release_id(service)
        if release_id:
            self.update_release(service, release_id)
        else:
            self.publish_new_release(service)

    def get_existing_release_id(self, service: Service) -> str | None:
        """
        Get ID for release, if it exists
        :param service: Service we want to check
        :return: id of the release, if it exists
        """
        repository_name = get_github_repository_name(service)
        result = requests.get(
            f"{GITHUB_API}{repository_name}/releases/tags/{service.latest_tag}",
            headers=github_auth(),
        )
        if result.status_code == 200:
            return result.json()["id"]

    def update_release(self, service: Service, release_id: str) -> None:
        """
        Updates existing release name on GitHub. This is done when a pre-release for the same tag has already been released in the acc environment.
        :param service: Service whose release we're updating
        :param release_id: id of the release to update
        :return: None
        """
        if self.env == Environment.ACCEPTANCE:
            print(
                f"Release already exists for repository {service.image_name}-{service.latest_tag}"
            )
            return
        repository_name = get_github_repository_name(service)
        body = {
            "tag_name": service.latest_tag,
            "name": self.release_name,
            "prerelease": False,
        }
        result = requests.post(
            f"{GITHUB_API}{repository_name}/releases/{release_id}",
            headers=github_auth(),
            data=json.dumps(body),
        )
        result.raise_for_status()

    def publish_new_release(self, service: Service) -> None:
        """
        Publish new release on GitHub
        :param service: Service we're publishing on GitHub
        :return: None
        """
        is_prerelease = self.env == Environment.ACCEPTANCE
        repository_name = get_github_repository_name(service)
        body = {
            "tag_name": service.latest_tag,
            "name": self.release_name,
            "generate_release_notes": True,
            "prerelease": is_prerelease,
        }
        result = requests.post(
            f"{GITHUB_API}{repository_name}/releases",
            headers=github_auth(),
            data=json.dumps(body),
        )
        result.raise_for_status()
        print(f"Created new release for {service.image_name}")

    def update_release_file(self):
        with open(RELEASE_FILE, "r") as read_file:
            latest_releases = json.load(read_file)
        with open(RELEASE_FILE, "w+") as write_file:
            if self.env == Environment.ACCEPTANCE:
                latest_releases[Environment.ACCEPTANCE.value] = self.release_name
            else:
                latest_releases[Environment.PRODUCTION.value] = self.release_name
            json.dump(latest_releases, write_file)
