# lemniscat.plugin.gitlab

A gitlab plugin for lemniscat


## Usage

### Pre-requisites

To use this plugin, you need to add plugin into the required section of your manifest file.

```yaml
requirements:
  - name: lemniscat.plugin.github
    version: 0.2.0
```

### Create a new project in gitlab

```yaml
- task: gitlab
  displayName: 'Gitlab create project'
  steps:
    - pre
  parameters:
    action: createProject
    gitlabUrl: https://gitlab.com
    token: ${{ gitlab_token}}
    projectname: The name of the project
    groupName: Name of the parent group if the project needs to be created within a group (optional)

```


### Create a new group in gitlab

```yaml
- task: gitlab
  displayName: 'Gitlab create group'
  steps:
    - pre
  parameters:
    action: createGroup
    gitlabUrl: https://gitlab.com
    token: ${{ gitlab_token}}
    groupName: Name of the group
    parentgroupname: The path of the parent group if the new group is a subgroup (optional) ex: 'peskedlabs/lemniscat'

```


### Add a member to a project in gitlab

```yaml
- task: gitlab
  displayName: 'Adds a member to a project'
  steps:
    - pre
  parameters:
    action: addMembers
    gitlabUrl: https://gitlab.com
    token: ${{ gitlab_token}}
    projectName: The name of the project for which to add the member
    parentgroupname: The path of the group containing the project (optional) ex: 'peskedlabs/lemniscat'
    memberswithaccesslevel: A list containing the information of members to be added with their access levels in the form [{'member': 'xxx@xxx.com', 'accesslevel': 20}, {'member': 'xxx@xxx.com', 'accesslevel': 30}]. With 20 for gitlab.REPORTER_ACCESS, 30 for gitlab.DEVELOPER_ACCESS, 40 for gitlab.MAINTAINER_ACCESS.

```


### Create a directory tree in gitlab

```yaml

- task: gitlab
  displayName: 'Recursively creates directories in a GitLab project by creating and deleting temporary files'
  steps:
    - pre
  parameters:
    action: createDirectories
    gitlabUrl: https://gitlab.com
    token: ${{ gitlab_token}}
    projectName: The name of the project for which to add directories
    parentgroupname: ex: The path of the group ex: 'peskedlabs/lemniscat'
    directoryStructure: An array representing the directory tree to be created ex: ['terraform','terraform/params','terraform/terragrunt','terraform/modules']

```


## Inputs

### Parameters

* `action` : The action to be performed. It can be `createProject`, `createGroup`, `addMembers` or `createDirectories`.
* `gitLabUrl` : Gitlab url.
* `token` : Gitlab token.
* `projectName` : The name of the project.
* `groupName` : The name of the group.
* `parentgroupname` : The path of the parent group
* `memberswithaccesslevel` : A list containing the information of members to be added with their access levels in the form [{'member': 'xxx@xxx.com', 'accesslevel': 20}, {'member': 'xxx@xxx.com', 'accesslevel': 30}]. With 20 for gitlab.REPORTER_ACCESS, 30 for gitlab.DEVELOPER_ACCESS, 40 for gitlab.MAINTAINER_ACCESS.
* `directoryStructure` : An array representing the directory tree to be created ex: ['terraform','terraform/params','terraform/terragrunt','terraform/modules'].
