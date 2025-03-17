# Automatic Releases

This service automates some of the more tedious parts of updating the acceptance and production environments.

## Setup

* In order to run the script, you need set `env` in `update-images.py`.
* If you want to exclude certain services, you can add directory names to `EXCLUDE_SERVICES`
* If you want to only update specific services, you can add the directory names to `INCLUDE_SERVICES`. This overwrites
  `EXCLUDE_SERVICES` and will only update the specified services.
* You will need to
  add [GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
  as an environment variable to authenticate with the GitHub API
* Configure the application using the `config` variable in `main.py`.
  * `env`: Selects the environment, `Environment.ACCEPTANCE` or `Environment.PRODUCTION`
  * `do_update`: Will update deployment files and create releases on GitHub if set to `True`
  * `exclude_directories`: Consists of default list of directories not to update. The user may add more directories to exclude from the given release
  * `include_directories`: Overwrites `exclude_directories` to only update services in the given directories. 
* Run the `update_images.py` script, followed by the `kubernetes_update.sh` script.

## 1. Updating Image tags in Deployment files

The script runs through all directories specified (either through `EXCLUDE_` or `INCLUDE_SERVICES`).
For each image, it pulls the latest image tag using the AWS ECR API.

The scripts save the files that were updated for **Feature 4 - Deploying to Kubernetes**

The deployment files are updated if `config.do_update` is set to `True`

## 2. Changelogs

Using the GitHub API, the script generates a changelog for each service. The changelog consists of the commits between
the previous tag and the latest tag.

These changes for all the services are compiled under a file named after the current release.

### Determining release name

The file `latest_release.json` captures the current release numbers for each environment. This file will determine the
release names for each service.

* **Production Environment** increments in minor versions
* **Acceptance Environment** increments in patches. However, if there has been a production release since the last
  acceptance release, it will increment a patch from the latest production release.
    * The keyword "-alpha" is appended to acceptance releases to indicate these are pre=releases.

In each new release, all updated services will have the same release number. If a service hasn't been updated in a
previous release, it will not have a release with the new name (that would cause a
conflict with GitHub). It is thus possible for a specific service to "skip" a release name if no changes have been made.

## 3. GitHub Release

Using the calculated release name, the script calls the GitHub API and creates a new release for each service we're
updating.

A release may already exist as a pre-release. This happens if the same tag was used to create a pre-release. In this
case, we update the existing pre-release to become a full release.

## 4. Deploying to Kubernetes

Manually running the script `kubernetes_update.sh` will update the desired environment based on the updated deployment
files. These file names were compiled when we updated the image tags (feature 1).

**Be sure you are updating the correct environment before proceeding**
