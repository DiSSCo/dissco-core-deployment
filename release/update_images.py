import boto3
import os
import re
from typing import Dict, List
from Environment import Environment
from Service import Service
from github_service import get_release_notes, publish_releases


US_REGION = "us-east-1"  # We use this region because us-east-1 is what is used for all public ECRs
ECR_PUBLIC = "ecr-public"

# Pattern that identifies image name (May contain 'latest' or a specific sha image tag)
# Group 1 = image name (e.g. "annotation-processing-service")
# Group 2 = image tag (e.g. sha-17c02bb)
IMG_PATTERN = r".+public\.ecr\.aws\/dissco\/([\w-]+):(sha-\w{7}).+"
pattern = re.compile(IMG_PATTERN)

# Add other directories to exclude if you don't want to update everything
EXCLUDE_SERVICES = [
    "kafka",
    "elastic",
    "karpenter",
    "secret-manager",
    "traefik",
    "data-export-job",
    "release",
    "translator-services",
]

# Mutually exclusive - if you only want to update specific services, include here
# Otherwise, leave blank
INCLUDE_SERVICES = []


def get_image_names(environment: Environment) -> Dict[str, Service]:
    """
    Given an environment, return a dict of image names and the services associated with them.
    :param environment: The environment to update. Either 'production' or 'acceptance'
    :return: List of image names and the data associated with them associated with these images
    """
    service_dict = {}
    for curr_dir in os.scandir(environment.value):
        if curr_dir.is_dir() and is_dir_of_interest(curr_dir.name):
            for entry in os.scandir(curr_dir):
                with open(entry) as file:
                    for line in file:
                        if match := pattern.match(line):
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


def is_dir_of_interest(dir_name: str) -> bool:
    """
    Given user parameters, checks whether or not the directory should be included
    :param dir_name: name of directory
    :return: if the dir should be included in our update
    """
    if INCLUDE_SERVICES:
        return dir_name in INCLUDE_SERVICES
    else:
        return dir_name not in EXCLUDE_SERVICES


def get_latest_tags(service_dict: Dict[str, Service]) -> List[Service]:
    """
    Calls AWS API to retrieve the latest image tags from AWS ECR.
    :param service_dict: Dict containing image names and the service data
    :return: List of Serivces
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
                    if pattern.match(line) and service.image_name in line:
                        match = pattern.match(line)
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


def export_updated_files(service_list: List[Service]) -> None:
    """
    Identifies what files have been changed and writes to a file for our k8s script to read from
    :param service_list: List of service objects we collected
    :return: None
    """
    file_names = {file for service in service_list for file in service.related_files}
    with open("release/file_names.txt", "w+") as file:
        for file_name in file_names:
            file.write(file_name + "\n")


if __name__ == "__main__":
    env = None  # Match to desired environment
    if (env == None):
        raise ValueError("Environment variable not set")
    service_dict = get_image_names(env)
    service_list = get_latest_tags(service_dict)
    release_name = get_release_notes(service_list, env)
    print("Release notes updated.")
    update = input("Do you wish to update deployment files? (y)")
    if update == "y":
        update_deployment_files(service_list)
        print("Successfully updated and exported deployment files")
    else:
        print("Deployment files not updated")
    export_updated_files(service_list)
    publish_releases(service_list, env, release_name)
