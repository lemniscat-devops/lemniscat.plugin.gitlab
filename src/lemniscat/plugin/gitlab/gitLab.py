# -*- coding: utf-8 -*-
# above is for compatibility of python2.7.11

import logging
import os
import subprocess, sys
from queue import Queue
import threading
import re
import gitlab as git
from lemniscat.core.util.helpers import LogUtil
from lemniscat.core.model.models import VariableValue
import json

try:  # Python 2.7+
    from logging import NullHandler
except ImportError:
    class NullHandler(logging.Handler):
        def emit(self, record):
            pass

logging.setLoggerClass(LogUtil)
log = logging.getLogger(__name__.replace('lemniscat.', ''))

class GitLab:
    def __init__(self, gitlab_url, private_token):
        self.gl = git.Gitlab(None, private_token=private_token)
    
    def create_project(self, project_name, user_id=None, group_name=None, **kwargs):
        """
        Crée un nouveau projet (dépôt) dans GitLab.

        :param project_name: Le nom du nouveau projet.
        :param user_id: L'ID de l'utilisateur sous lequel le projet sera créé (optionnel).
        :param group_name: Le nom du groupe parent si le projet doit être créé dans un groupe (optionnel).
        :param kwargs: Arguments supplémentaires passés à la création du projet.
        :return: Le projet créé.
        """
        try:
            project_data = {'name': project_name}
            project_data.update(kwargs)

            if group_name:
                try:
                    # Rechercher le groupe parent par son nom
                    group = self.gl.groups.get(group_name)
                    project_data['namespace_id'] = group.id
                    project = self.gl.projects.create(project_data, user_id=user_id)
                    log.info(f"Project {project_name} created under parent group {group.name}")
                except git.exceptions.GitlabGetError:
                    log.error(f"Parent group not found: {group_name}")
                    return 1, '', f"Parent group not found: {group_name}"
            else:
                # Rechercher si le projet existe déjà
                projects = self.gl.projects.list(search=project_name, user_id=user_id)
                project_found = next((p for p in projects if p.path == project_name), None)
                if project_found:
                    log.info(f"Project {project_name} already exists")
                    return 0, project_found.id, ''
                else:
                    # Créer le projet sans groupe parent
                    project = self.gl.projects.create(project_data, user_id=user_id)
                    log.info(f"Project {project_name} created")

        except Exception as ex:
            e = sys.exc_info()[0]
            return 1, ex.error_message, sys.exc_info()[-1].tb_frame

        return 0, project.id, ''

    def create_group(self, group_name, parent_path=None, **kwargs):
        """
        Crée un nouveau groupe ou sous-groupe dans GitLab.
        sur GitLab.com, il n'est pas autorisé de créer un groupe top-level avec l'api actuellement

        :param group_name: Le nom du nouveau groupe.
        :param parent_path: Le chemin du groupe parent si le nouveau groupe est un sous-groupe (optionnel).
        :param kwargs: Arguments supplémentaires passés à la création du groupe.
        :return: Le groupe créé.
        """
        try:
            group_data = {'name': group_name, 'path': group_name}
            group_data.update(kwargs)

            if parent_path:
                try:
                    # Rechercher le groupe parent par son chemin
                    parent_group = self.gl.groups.get(parent_path)
                    group_data['parent_id'] = parent_group.id
                    group = self.gl.groups.create(group_data)
                    log.info(f"Subgroup {group_name} created under parent group {parent_group.name}")
                except git.exceptions.GitlabGetError:
                    log.error(f"Parent group not found: {parent_path}")
                    return 1, '', f"Parent group not found: {parent_path}"
            else:
                # Créer un groupe de niveau supérieur
                group = self.gl.groups.create(group_data)
                log.info(f"Group {group_name} created")

        except Exception as ex:
            e = sys.exc_info()[0]
            return 1, ex.error_message, sys.exc_info()[-1].tb_frame

        return 0, group.id, ''

    def create_pipeline(self, project_name, user_id, ref='main') -> None:
        """
        Crée un pipeline pour le projet GitLab spécifié.

        :param project_name: Le nom du nouveau projet.
        :param user_id: L'ID de l'utilisateur sous lequel le projet sera créé.
        :param ref: La référence pour laquelle le pipeline doit être créé (nom de branche ou tag).
        """
        try:
            projects = self.gl.projects.list(search=project_name, user_id=user_id)
            project_found = next((project for project in projects if project.path_with_namespace == f"{user_id}/{project_name}"), None)
            if( project_found ):
                if( project_found.pipelines.len > 0):
                    # Création du pipeline
                    pipeline = project_found.pipelines.create({'ref': ref})
                else:
                    log.info(f"Pipeline does not exist in Project {user_id}/{project_name}")
            else:
                log.info(f"Project {user_id}/{project_name} does not exist")

        except Exception as ex:
            e = sys.exc_info()[0]
            return 1, ex.error_message, sys.exc_info()[-1].tb_frame
        
        return 0, '', ''
    
    def add_member_to_project(self, project_name, group_path=None, members_withaccesslevel=None):
        """
        Ajoute un membre (utilisateur ou groupe) à un projet GitLab.

        :param project_name: Le nom du projet.
        :param group_path: Le chemin du groupe contenant le projet (optionnel).
        :param members_withaccesslevel: Une liste de dictionnaires contenant les informations des membres à ajouter avec leurs niveaux d'accès sous la forme [{'member': 'xxx@xxx.com', 'accesslevel': 20},{'member': 'xxx@xxx.com', 'accesslevel': 30}].
            avec 20 gitlab.REPORTER_ACCES, 30 gitlab.DEVELOPER_ACCESS, 40 gitlab.MAINTAINER_ACCESS
        """
        try:
            if group_path:
                # Rechercher le projet dans le groupe spécifié
                group = self.gl.groups.get(group_path)
                projects = group.projects.list(search=project_name)
                groupproject = next((p for p in projects if p.name == project_name), None)
                if groupproject:
                    project = self.gl.projects.get(groupproject.id)
                else:
                    project = None
            else:
                # Rechercher le projet sans groupe spécifié
                projects = self.gl.projects.list(search=project_name)
                project = next((p for p in projects if p.name == project_name), None)
            
            if project:
                if members_withaccesslevel:
                    for memberaccesslevel in members_withaccesslevel:
                        project.invitations.create({"email": memberaccesslevel['member'], "access_level": memberaccesslevel['accesslevel']})
                        log.info(f"Member {memberaccesslevel['member']} invite to project {project.name} with access level {memberaccesslevel['accesslevel']}")  
                else:
                    log.info(f"No members to add to project {project.name}")
            else:
                log.warning(f"Project {project_name} not found")

        except Exception as ex:
            log.error(f"An error occurred while adding members to project: {ex}")
            return 1, ex.error_message, sys.exc_info()[-1].tb_frame

        return 0, '', ''