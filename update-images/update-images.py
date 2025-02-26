import boto3
import os
import re
from typing import Dict, List
from enum import Enum

US_REGION = 'us-east-1'  # We use this region because us-east-1 is what is used for all public ECRs
ECR_PUBLIC = 'ecr-public'

# Pattern that identifies image name (May contain 'latest' or a specific sha image tag)
# Group 1 = image name (e.g. "annotation-processing-service")
# Group 2 = image tag (e.g. sha-17c02bb)
IMG_PATTERN = r'.+public\.ecr\.aws\/dissco\/([\w-]+):(sha-\w{7}).+'
pattern = re.compile(IMG_PATTERN)

# Add other directories to exclude if you don't want to update everything
EXCLUDE_SERVICES = [
    'kafka',
    'elastic',
    'karpenter',
    'secret-manager',
    'traefik',
    'data-export-job',
    'update-images',
    'translator-services'
]


class Environment(Enum):
    ACC = 'acceptance'
    PROD = 'production'


class Image:
    def __init__(self, image_name: str, related_files: List[str], latest_tag: str, pushed_date: str):
        self.image_name = image_name
        self.related_files = related_files
        self.latest_tag = latest_tag
        self.pushed_date = pushed_date


def get_image_names(environment: Environment) -> Dict[str, List[str]]:
    """
    Given an environment, return a dict of image names and the files associated with them.
    :param environment: The environment to update. Either 'production' or 'acceptance'
    :return: List of image names and the files that are associated with these images
    """
    image_dict = {}
    for curr_dir in os.scandir(environment.value):
        if curr_dir.is_dir() and curr_dir.name not in EXCLUDE_SERVICES:
            for entry in os.scandir(curr_dir):
                with open(entry) as file:
                    for line in file:
                        if match := pattern.match(line):
                            image = match.group(1)  # Gets the image name without the tag
                            if image not in image_dict:
                                image_dict[image] = [entry.path]
                            else:
                                image_dict[image].append(entry.path)
    return image_dict


def get_latest_tags(image_dict: Dict[str, List[str]]) -> List[Image]:
    """
    Calls AWS API to retrieve the latest image tags from AWS ECR.
    :param image_dict: Dict containing image names and the files that are associated with these images
    :return: List of images
    """
    ecr_client = boto3.client(ECR_PUBLIC, region_name=US_REGION)
    image_list = []
    for image_name, files in image_dict.items():
        response = ecr_client.describe_images(
            repositoryName=image_name,
            imageIds=[
                {
                    'imageTag': 'latest'
                }
            ])
        # Image_tags is a list of tags on a given image. We need to remove the 'latest' image tag and use what remains
        image_tags = response['imageDetails'][0]['imageTags']
        assert len(image_tags) == 2
        pushed_date = response['imageDetails'][0]['imagePushedAt'].strftime('%b-%d-%Y')
        image_tags.remove('latest')
        image_tag = image_tags[0]
        print(f'Image: {image_name} , tag: {image_tag},  pushed at: {pushed_date}')
        image_list.append(Image(image_name, files, image_tag, pushed_date))
    return image_list


def update_images(image_list: List[Image]) -> None:
    """
    Replaces old image tags with latest version
    :param image_list: List of Images (files and tags) to update
    :return: None
    """
    for image in image_list:
        for related_file in image.related_files:
            with open(related_file, 'r+') as file:
                old = file.readlines()
                file.seek(0)
                for line in old:
                    if pattern.match(line) and image.image_name in line:
                        match = pattern.match(line)
                        old_tag = match.group(2)  # Gets the group which points to the tag
                        updated_line = line.replace(old_tag, image.latest_tag)  # Replace old tag with the new tag
                        updated_line = re.sub('#.+', f'# {image.pushed_date}', updated_line)  # Updates the last updated comment
                        file.write(updated_line)
                    else:
                        file.write(line)


def export_images(image_dict: Dict[str, List[str]]) -> None:
    file_names = set([file for file_list in image_dict.values() for file in file_list])
    with open('file_names.txt', 'w+') as file:
        for file_name in file_names:
            file.write(file_name + '\n')


if __name__ == '__main__':
    env = Environment.ACC  ## Set this to PROD if you want to update production environment
    image_dict = get_image_names(env)
    image_list = get_latest_tags(image_dict)
    update_images(image_list)
    export_images(image_dict)
