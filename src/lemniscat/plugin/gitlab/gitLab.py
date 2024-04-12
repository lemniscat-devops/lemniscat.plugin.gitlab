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
    
    def create_project(self, project_name, user_id=None, **kwargs) -> None:
        """
        Crée un nouveau projet (dépôt) dans GitLab.
        
        :param project_name: Le nom du nouveau projet.
        :param user_id: L'ID de l'utilisateur sous lequel le projet sera créé (optionnel).
        :param kwargs: Arguments supplémentaires passés à la création du projet.
        :return: Le projet créé.
        """

        try:
            project_data = {'name': project_name}
            project_data.update(kwargs)
            
            projects = self.gl.projects.list(search=project_name)
            project_found = next((project for project in projects if project.path_with_namespace == f"{user_id}/{project_name}"), None)
            if( project_found ):
                log.info(f"Project {user_id}/{project_name} already exist")
            else:
                if user_id:
                    # Créer le projet sous un utilisateur spécifique
                    project = self.gl.projects.create(project_data, user_id=user_id)
                else:
                    # Créer le projet sous l'utilisateur authentifié
                    project = self.gl.projects.create(project_data)
        except Exception as ex:
            e = sys.exc_info()[0]
            return 1, ex.error_message, sys.exc_info()[-1].tb_frame
        
        return 0, '',''
    
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
    
    def add_member_to_project(self, project_name, user_id, members_withaccesslevel):
        """
        Ajoute un membre (utilisateur ou groupe) à un projet GitLab.

        :param project_name: Le nom du projet.
        :param user_id: L'ID de l'utilisateur propriétaire du projet.
        :param member_id: L'ID du membre (utilisateur ou groupe) à ajouter au projet.
        :param access_level: Le niveau d'accès à accorder au membre (AccessLevel).
        """
        try:
            projects = self.gl.projects.list(search=project_name, user_id=user_id)
            project_found = next((project for project in projects if project.path_with_namespace == f"{user_id}/{project_name}"), None)
            if project_found:
                members_withaccesslevel = members_withaccesslevel.replace("'", '"')
                members_withaccesslevel = json.loads(members_withaccesslevel)

                for memberaccesslevel in members_withaccesslevel:
                    # Recherche du membre par adresse e-mail
                    members = project_found.members.list(query=memberaccesslevel['member'])
                    member = next((m for m in members if m.email == memberaccesslevel['member']), None)
                    
                    if member:
                        # Le membre existe déjà, mettre à jour son niveau d'accès si nécessaire
                        if member.access_level != memberaccesslevel['accesslevel']:
                            member.access_level = memberaccesslevel['accesslevel']
                            member.save()
                            log.info(f"Member {memberaccesslevel['member']} access level updated to {memberaccesslevel['accesslevel']} in project {user_id}/{project_name}")
                        else:
                            log.info(f"Member {memberaccesslevel['member']} already exists in project {user_id}/{project_name}")
                    else:
                        # Le membre n'existe pas, ajouter le membre directement
                        project_found.invitations.create({"email": memberaccesslevel['member'], "access_level": memberaccesslevel['accesslevel']})
                        log.info(f"Member {memberaccesslevel['member']} invite to project {user_id}/{project_name} with access level {memberaccesslevel['accesslevel']}")
            else:
                log.info(f"Project {user_id}/{project_name} does not exist")

        except Exception as ex:
            e = sys.exc_info()[0]
            return 1, ex.error_message, sys.exc_info()[-1].tb_frame
    
        return 0, '', ''