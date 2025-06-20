# Automatic Releases

This service automates some of the more tedious parts of updating the acceptance and production environments.

## Setup

* In order to run the script, you need set `env` in `update-images.py`.
* If you want to exclude certain services, you can add directory names to `exclude_directories`
* If you want to only update specific services, you can add the directory names to `include_directories`. This
  overwrites
  `exclude_directories` and will only update the specified services.
* You will need to
  add [GitHub Personal Access Token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens)
  as an environment variable to authenticate with the GitHub API
* Configure the application using the `config` variable in `main.py`.
    * `env`: Selects the environment, `Environment.ACCEPTANCE` or `Environment.PRODUCTION`
    * `do_update`: Will update deployment files and create releases on GitHub if set to `True`. Otherwise, just compiles
      release notes.
    * `exclude_directories`: Consists of default list of directories not to update. The user may add more directories to
      exclude from the given release
    * `include_directories`: Overwrites `exclude_directories` to only update services in the given directories.
    * `release_name`: Allows user to manually set release name. If not set, follows rules according
      to [Determining Release Names](#determining-release-name)
* Run the `update_images.py` script, followed by the `kubernetes_update.sh` script.

## 1. Updating Image Tags in Deployment Files

The script runs through all directories specified in the configuration (either through `exclude_directories` or
`include_directories`).
For each image, it pulls the latest image tag using the AWS ECR API.

The script writes the names of the files that were updated for **Step 4 - Deploying to Kubernetes**

The deployment files are updated only if `config.do_update` is set to `True`

## 2. Release Notes

Using the GitHub API, the script generates a changelog for each service. The changelog consists of the commits between
the **previous tag and the latest tag**.

These changes for all the services are compiled under a file named after the current release. The generated file should
be added to git.

The release notes are always compiled, regardless of what `config.do_update` is set to.

### Determining Release Name

The following section gives an outline for automatic increments of release names. If `release-names` is set in the
configuration, the user's input overrides these rules. The user's input is implemented **verbatim**, meaning any
additional tags (e.g. `-alpha` for acceptance releases) must be included in the release name. 

The file `latest_release.json` captures the current release numbers for each environment. This file will determine the
release names for each service if no release name has been set according to the following rules:

* **Production Environment** increments in minor versions (v1.1.0, v1.2.0, etc.)
* **Acceptance Environment** increments in patches (v1.1.1-alpha, v1.1.2-alpha, etc.). However, if there has been a
  production release since the last
  acceptance release, it will increment a patch from the latest production release.
    * i.e., if the latest acceptance release is 1.1.1-alpha, and the latest production release is v1.2.0, the next
      acceptance release will be v1.2.1-alpha
    * The keyword "-alpha" is appended to acceptance releases to indicate these are pre-releases.

In each new release, all updated services will have the same release number. If a service hasn't been updated in a
previous release, it will not have a release with the new name (that would cause a
conflict with GitHub). It is thus possible for a specific service to "skip" a release name if no changes have been made.

The `latest_release.json` file is updated only when `config.do_update` is set to `True`

## 3. GitHub Release

Using the calculated release name, the script calls the GitHub API and creates a new release for each service we're
updating.

A release may already exist as a pre-release. This happens if the same tag was used to create a pre-release. In this
case, we update the existing pre-release to become a full release.

Releases are only created if `config.do_update` is set to `True`

### DiSSCover Release

For nearly all services, the image tag is the same tag as the commit tag on GitHub. We can use these image tags (
obtained from the AWS image store) to identify which commits we're comparing in the release notes, and to generate
GitHub releases.

The exception to this is DiSSCover, which pushes a slightly longer tag to GitHub. To identify the correct commits in
GitHub, we call the GitHub `/tags` endpoint and match the DiSSCover image tag to the correct GitHub commit tag.

## 4. Deploying to Kubernetes

Manually running the script `kubernetes_update.sh` will update the desired environment based on the updated deployment
files. These file names were compiled when we updated the image tags (feature 1).

### Important

**Be sure you are updating the correct environment before proceeding. You will need to set the environment in the script
**

## Managing Interdependent Change

These kinds of changes depend on a change from outside the codebase -- database changes, data model
changes, deployment changes, etc. **This release script does not automatically manage any breaking changes**.

You can identify where breaking changes have occurred by looking at the release notes. Any breaking change should be
identified with a "!" in the note. You can use this notification to refer back to the relevant Pull Request and update
the
environment accordingly before proceeding. 
