from Service import Service
from Environment import Environment
from typing import Dict, List
import requests
import os
import json
import re
from semantic_version import Version as v
from datetime import datetime

NO_CHANGES = "No change since last release\n"
GITHUB_API = "https://api.github.com/repos/dissco/"


def github_auth() -> Dict[str, str]:
    return {
        "Authorization": f'Bearer {os.environ["GITHUB_TOKEN"]}',
        "X-GitHub-Api-Version": "2022-11-28",
    }


def fetch_release_notes(service: Service) -> str:
    """
    Fetches release notes from GitHub, using previous and latest tags in the Image object
    :param service: Image we want release notes for
    :return: Unformatted release notes
    """
    body = {"tag_name": service.latest_tag, "previous_tag_name": service.prev_tag}
    result = requests.post(
        f"https://api.github.com/repos/dissco/{service.image_name}/releases/generate-notes",
        headers=github_auth(),
        data=json.dumps(body),
    )
    return format_release_notes(service, result.json().get("body"))


def format_release_notes(service: Service, raw_notes: str) -> str:
    no_changes = f"## {service.image_name}\n{NO_CHANGES}"
    if not raw_notes:
        service.add_release_notes(no_changes)
        return no_changes
    notes = raw_notes
    notes = re.sub(r"by @.+", "", notes)
    notes = re.sub(r"\*\*Full Changelog\*\*:.+", "", notes)
    notes = re.sub(r"## What's Changed\n.+", "", notes)
    notes = notes.replace(r"## New Contributors", "")
    notes = re.sub(r"\* @\w+ made.+", "", notes)
    notes = f"{notes.strip()}\n"
    if not notes or notes == "\n":
        service.add_release_notes(no_changes)
        return no_changes
    service.add_release_notes(notes)
    return f"## {service.image_name}\n{notes}\n"


def get_release_notes(service_list: List[Service], env: Environment) -> str:
    """
    Generates release notes for a given list of images
    :param service_list: list of images to generate release notes for
    :param env: production or acceptance environment
    :return: None
    """
    release_name = get_release_name(env)
    with open(f"release/release-notes/{release_name}.md", "w+") as f:
        print("Compiling release notes")
        f.write(f"# Release {release_name}\n")
        f.write(f'{env.value} release - {datetime.now().strftime("%b-%d-%Y")}\n')
        for image in service_list:
            f.write(fetch_release_notes(image))
    print(f"Compiled release notes for release {release_name}")
    return release_name


def publish_releases(
    service_list: List[Service], env: Environment, release_name: str
) -> None:
    """
    Creates a new release for every image we're looking at
    :param service_list: List of images to generate releases for
    :param env: acceptance or production environment
    :param release_name: calculated name of new release
    :return: None
    """
    for service in service_list:
        publish_release(service, env, release_name)


def publish_release(service: Service, env: Environment, release_name: str) -> None:
    """
    Given an image, create a new release on github
    :param service: service we're creating the release for
    :param release_name: release name
    :return: None
    """
    if NO_CHANGES in service.release_notes:
        print(f"No changes in service {service.image_name}. Not publishing release")
        return
    repository_name = service.image_name if service.image_name != 'disscover-production' else 'disscover'
    is_prerelease = env == Environment.ACCEPTANCE
    body = {
        "tag_name": service.latest_tag,
        "name": release_name,
        "generate_release_notes": True,
        "prerelease": is_prerelease
        ## "draft" : True
    }
    result = requests.post(
        f"{GITHUB_API}{repository_name}/releases",
        headers=github_auth(),
        data=json.dumps(body),
    )
    result.raise_for_status()
    print(f"Created new release for {service.image_name}")


def get_release_name(env: Environment) -> str:
    """
    Given local records, calculates next release name
    :param env: Environment
    :return: Semantically incremented release name
    """
    with open("release/release-notes/latest_release.json", "r") as readFile:
        latest_releases = json.load(readFile)
        if env == Environment.PRODUCTION:
            return get_production_release_name(latest_releases)
        else:
            return get_acceptance_release_name(latest_releases)


def get_production_release_name(latest_releases: Dict[str, str]) -> str:
    """
    Increments minor version of production release and updates local file
    :param latest_releases: record of current releases
    :return: new release name
    """
    current_production_release = v(
        latest_releases.get(Environment.PRODUCTION.value).replace("v", "")
    )
    new_production_release = v.next_minor(current_production_release)
    release_name = f"v{new_production_release}"
    latest_releases[Environment.PRODUCTION.value] = release_name
    update_release_file(latest_releases)
    return release_name


def get_acceptance_release_name(latest_releases: Dict[str, str]) -> str:
    """
    Increments patch of acceptance release and updates local file. If production env is ahead, increments minor version as well
    :param latest_releases: record of current releases
    :return: new release name
    """
    current_production_release = v(
        latest_releases.get(Environment.PRODUCTION.value).replace("v", "")
    )
    current_acceptance_release = v(
        latest_releases.get(Environment.ACCEPTANCE.value).replace("v", "")
    )
    if current_acceptance_release > current_production_release:
        release_name = f"v{v.next_patch(current_acceptance_release).next_patch()}-alpha"
    else:
        release_name = f"v{current_production_release.next_patch()}-alpha"
    latest_releases[Environment.ACCEPTANCE.value] = f"{release_name}"
    return release_name


def update_release_file(latest_releases: Dict[str, str]) -> None:
    """
    Updates local file with updated releases
    :param latest_releases: release dict
    :return: None
    """
    with open("release/release-notes/latest_release.json", "w") as writeFile:
        json.dump(latest_releases, writeFile, indent=4)
