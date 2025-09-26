import boto3
import os
import re
from typing import Dict, List, Any
from environment import Environment
from service import Service
from github import Github


US_REGION = "us-east-1"  # We use this region because us-east-1 is what is used for all public ECRs
ECR_PUBLIC = "ecr-public"

# Pattern that identifies image name (May contain 'latest' or a specific sha image tag)
# Group 1 = image name (e.g. "annotation-processing-service")
# Group 2 = image tag (e.g. sha-17c02bb)
IMG_REGEX = r".+public\.ecr\.aws\/dissco\/([\w-]+):(sha-\w{7}).+"
IMG_PATTERN = re.compile(IMG_REGEX)

DATE_REGEX = r".+(\w{3}-\d{2}-\d{4})"
DATE_PATTERN = re.compile(DATE_REGEX)

# Default directories we wish to exclude
DEFAULT_EXCLUDE_DIRECTORIES = [
    "kafka",
    "rabbitmq",
    "elastic",
    "karpenter",
    "secret-manager",
    "traefik",
    "data-export-job",
    "release",
    "keda",
    "kube_green",
    "machine-annotation-service",
    "mas_inspector",
    "open-telemetry",
    "flyway"
]


def get_image_names(
    environment: Environment, config: Dict[str, Any]
) -> Dict[str, Service]:
    """
    Given an environment, return a dict of image names and the services associated with them.
    :param environment: The environment to update. Either 'production' or 'acceptance'
    :return: List of image names and the data associated with them associated with these services
    """
    service_dict = {}
    for curr_dir in os.scandir("../"+environment.value):
        if curr_dir.is_dir() and is_dir_of_interest(curr_dir.name, config):
            for entry in os.scandir(curr_dir):
                with open(entry) as file:
                    for line in file:
                        if match := IMG_PATTERN.match(line):
                            image_name = match.group(
                                1
                            )  # Gets the image name without the tag
                            if image_name not in service_dict:
                                service_dict[image_name] = Service(
                                    image_name, [entry.path], "", match.group(2), ""
                                )
                            else:
                                service_dict[image_name].add_file(entry.path)
    return service_dict


def is_dir_of_interest(dir_name: str, config: Dict[str, Any]) -> bool:
    """
    Given user parameters, checks whether or not the directory should be included
    :param dir_name: name of directory
    :return: if the dir should be included in our update
    """
    if config["include_directories"]:
        return dir_name in config["include_directories"]
    else:
        return dir_name not in config["exclude_directories"]


def get_latest_tags(
    env: Environment, service_dict: Dict[str, Service]
) -> List[Service]:
    if env == Environment.PRODUCTION:
        return get_latest_tags_prod(service_dict)
    else:
        return get_latest_tags_acc(service_dict)


def get_latest_tags_prod(service_dict: Dict[str, Service]) -> List[Service]:
    """
    Gets the latest tags for a service based on what is deployed in the acceptance environment
    :param service_dict:
    :return:
    """
    updated_services = set()
    # We look at the acc directory to find which tags to put in the production files
    for curr_dir in os.scandir(Environment.ACCEPTANCE.value):
        if curr_dir.is_dir() and is_dir_of_interest(curr_dir.name, config):
            for entry in os.scandir(curr_dir):
                with open(entry) as file:
                    for line in file:
                        if match := IMG_PATTERN.match(line):
                            image_name = match.group(
                                1
                            )  # Gets the image name without the tag
                            if image_name not in updated_services:
                                image_tag = match.group(2)
                                pushed_date = DATE_PATTERN.match(line).group(1)
                                prev_version = service_dict[image_name]
                                prev_version.set_latest_tag(image_tag)
                                prev_version.set_pushed_date(pushed_date)
                                updated_services.add(image_name)

    return [val for val in service_dict.values()]


def get_latest_tags_acc(service_dict: Dict[str, Service]) -> List[Service]:
    """
    Calls AWS API to retrieve the latest image tags from AWS ECR.
    :param service_dict: Dict containing service names and the service data
    :return: List of services
    """
    ecr_client = boto3.client(ECR_PUBLIC, region_name=US_REGION)
    updated_service_list = []
    for image_name, service in service_dict.items():
        response = ecr_client.describe_images(
            repositoryName=image_name,
            imageIds=[{"imageTag": "latest"}],  # Only return latest images
        )
        # Image_tags is a list of tags on a given image. We need to remove the 'latest' image tag and use what remains
        image_tags = response["imageDetails"][0]["imageTags"]
        assert len(image_tags) == 2
        pushed_date = response["imageDetails"][0]["imagePushedAt"].strftime("%b-%d-%Y")
        image_tags.remove("latest")
        latest_image_tag = image_tags[0]  # Get what image tag remains
        print(
            f"Image: {image_name} , tag: {latest_image_tag},  pushed at: {pushed_date}"
        )
        updated_service_list.append(
            Service(
                image_name,
                service.related_files,
                latest_image_tag,
                service.prev_tag,
                pushed_date,
            )
        )
    return updated_service_list


def update_deployment_files(service_list: List[Service]) -> None:
    """
    Replaces old image tags with latest version.
    :param service_list: List of Images (files and tags) to update
    :return: None
    """
    for service in service_list:
        for related_file in service.related_files:
            with open(related_file, "r+") as file:
                old = file.readlines()
                file.seek(0)
                for line in old:
                    if IMG_PATTERN.match(line) and service.image_name in line:
                        match = IMG_PATTERN.match(line)
                        old_tag = match.group(
                            2
                        )  # Gets the group which points to the tag
                        updated_line = line.replace(
                            old_tag, service.latest_tag
                        )  # Replace old tag with the new tag
                        updated_line = re.sub(
                            "#.+", f"# {service.pushed_date}", updated_line
                        )  # Updates the last updated comment
                        file.write(updated_line)
                    else:
                        file.write(line)


if __name__ == "__main__":
    """
    User to set desired configuration!
    """
    config = {
        "env": None,  # Match to desired environment
        "do_update": False,  # set to True to update files and create new Github release
        "exclude_directories": DEFAULT_EXCLUDE_DIRECTORIES,  # Add services you wish to exclude to this list -- all others will be included
        "include_directories": [],  # If this list is not empty, we will only update services from this list,
        "release_name": "",  # Set this to the desired release name; otherwise, will follow release rules in readme
    }
    env = config.get("env")
    if env is None:
        raise ValueError("Environment variable not set")
    service_dict = get_image_names(env, config)
    service_list = get_latest_tags(env, service_dict)
    github_service = Github(env, config["release_name"])
    github_service.generate_release_notes(service_list)
    print("Release notes updated")
    if config["do_update"]:
        print("Updating deployment files")
        update_deployment_files(service_list)
        print(f"Publishing GitHub release {github_service.release_name}")
        github_service.publish_releases(service_list)
        github_service.update_release_file()
