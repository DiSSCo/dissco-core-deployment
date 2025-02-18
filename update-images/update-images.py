import boto3
import os
import re
from typing import Dict, List
from enum import Enum

class Image:
    image_name: str
    related_files = List[os.DirEntry]
    latest_tag = str
    pushed_date = str

    def __init__(self, image_name, related_files, latest_tag, pushed_date):
        self.image_name = image_name
        self.related_files = related_files
        self.latest_tag = latest_tag
        self.pushed_date = pushed_date

    def __get_files__(self) -> List[str]:
        return [self.related_files]


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

# Pattern that identifies image name (May contain "latest" or a specific sha image tag)
IMG_PATTERN = 'public\\.ecr\\.aws/dissco/[\\w-]+:.+'
# Pattern that identifies image tag
TAG_PATTERN = ':sha-\\w{7}'

Environment = Enum('Environment', [('ACC', 'acceptance'), ('PROD', 'production')])


def get_image_names(environment: Environment) -> Dict[str, List[str]]:
    """
    Given an environment, return a dict of image names and the files associated with them.
    :param environment: The environment to update. Either 'production' or 'acceptance'
    :return: List of image names and the files that are associated with these images
    """
    image_dict = {}
    for curr_dir in os.scandir(environment.value):
        if curr_dir.is_dir() and curr_dir.name.__str__() not in EXCLUDE_SERVICES:
            for entry in os.scandir(curr_dir):
                with (open(entry) as file):
                    for line in file:
                        if re.search(IMG_PATTERN, line):
                            image = line.split(':', 2)[1]  # Removes everything after image tag ('latest' or SHA)
                            image = image.replace('public.ecr.aws/dissco/', '') # Removes image repo name
                            image = re.sub('#.+', '', image) # Removes "latest" or sha tag from image name
                            image = image.strip()  # Clean up trailing spaces
                            if image not in image_dict:
                                image_dict[image] = [entry.path]
                            else:
                                image_dict[image].append(entry.path)
    return image_dict


def get_latest_tags(image_dict: Dict[str, List[str]]) -> List[Image]:
    """
    Calls AWS API to retrieve the latest image tags from AWS ECR.
    :param image_dict: Dict containing image names and the files that are associated with these images
    :return:
    """
    ecr_client = boto3.client('ecr-public', region_name='us-east-1')
    image_list = []
    for image_name, files in image_dict.items():
        response = ecr_client.describe_images(
            repositoryName=image_name,
            imageIds=[
                {
                    'imageTag': 'latest'
                }
            ])
        image_tag = response['imageDetails'][0]['imageTags']
        pushed_date = response['imageDetails'][0]['imagePushedAt'].strftime('%b-%d-%Y')
        if len(image_tag) == 2:
            image_tag.remove('latest')
        else:
            print('Warning: image ' + image_name + ' has no SHA tag. Using latest tag instead')
        image_tag = image_tag[0]
        print("Image: " + image_name + ", tag: " + image_tag, ", pushed at: " + pushed_date)
        image_list.append(Image(image_name, files, image_tag, pushed_date))
    return image_list


def update_images(image_list: List[Image]) -> None:
    for image in image_list:
        for related_file in image.related_files:
            with open(related_file, 'r+') as file:
                old = file.readlines()
                file.seek(0)
                for line in old:
                    if re.search(IMG_PATTERN, line):
                        new_line = ':'.join(line.split(':', 2)[:-1])
                        new_line = new_line + ':' + image.latest_tag + "   # " + image.pushed_date + '\n'
                        file.write(new_line)
                    else:
                        file.write(line)


if __name__ == '__main__':
    env = Environment.ACC  ## Set this to PROD if you want to update production environment
    image_dict = get_image_names(env)
    image_list = get_latest_tags(image_dict)
    update_images(image_list)
