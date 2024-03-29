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
        
            if user_id:
                # Créer le projet sous un utilisateur spécifique
                project = self.gl.projects.create(project_data, user_id=user_id)
            else:
                # Créer le projet sous l'utilisateur authentifié
                project = self.gl.projects.create(project_data)
        except:
            e = sys.exc_info()[0]
            return 1, '', '{e}'
        
        return 0, '',''