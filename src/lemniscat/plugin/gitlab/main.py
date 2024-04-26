
import argparse
import ast
import logging
import os
from logging import Logger
import re
from lemniscat.core.contract.engine_contract import PluginCore
from lemniscat.core.model.models import Meta, TaskResult, VariableValue
from lemniscat.core.util.helpers import FileSystem, LogUtil
from gitLab import GitLab

_REGEX_CAPTURE_VARIABLE = r"(?:\${{(?P<var>[^}]+)}})"

class Action(PluginCore):
    
    def __init__(self, logger: Logger) -> None:
        super().__init__(logger)
        plugin_def_path = os.path.abspath(os.path.dirname(__file__)) + '/plugin.yaml'
        manifest_data = FileSystem.load_configuration_path(plugin_def_path)
        self.meta = Meta(
            name=manifest_data['name'],
            description=manifest_data['description'],
            version=manifest_data['version']
        )
        
    def invoke(self, parameters: dict = {}, variables: dict = {}) -> TaskResult:
        super().invoke(parameters, variables)
        self._logger.debug(f'Command: {self.parameters["action"]} -> {self.meta}')
        task = self.__run_gitlab()
        return task

    def __run_gitlab(self) -> TaskResult:

        result = {}

        # set gitlab command    
        command = self.parameters['action']

        gitlab_url   = self.parameters['gitlabUrl']
        private_token = self.parameters['token']
        project_name = self.parameters['projectname']
        group_name = self.parameters["groupname"]
        parent_path = self.parameters["parentgroupname"]
        organization = self.parameters['organization']
        members_Withaccesslevel = self.parameters['memberswithaccesslevel']

        git = GitLab(gitlab_url, private_token)
        if(command == 'createProject'):
            self._logger.debug(f'gitLab {command} run')
            result = git.create_project(project_name, organization, parent_path)
        elif(command == 'createPipeline'):
            self._logger.debug(f'gitLab {command} run')
            result = git.create_pipeline(project_name, user_id=organization)
        elif(command == 'addMembers'):
            self._logger.debug(f'gitLab {command} run')
            result = git.add_member_to_project(project_name, parent_path, members_Withaccesslevel)
        elif(command == 'createGroup'):
            self._logger.debug(f'gitLab {command} run')
            result = git.create_group(group_name, parent_path)

        if(result[0] != 0):
            self._logger.error(f'gitLab {command}, Status: Failed, Errors: {result[1]} {result[2]}')
            return TaskResult(
                name=f'gitLab {command}',
                status='Failed',
                errors=result[2])
        else:
            return TaskResult(
                name=f'gitLab {command}',
                status='Completed',
                errors=[])

def __init_cli() -> argparse:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        '-p', '--parameters', required=True, 
        help="""(Required) Supply a dictionary of parameters which should be used. The default is {}
        """
    )
    parser.add_argument(
        '-v', '--variables', required=True, help="""(Optional) Supply a dictionary of variables which should be used. The default is {}
        """
    )                
    return parser

if __name__ == "__main__":
    logger = LogUtil.create()
    action = Action(logger)
    __cli_args = __init_cli().parse_args()   
    variables = {}   
    vars = ast.literal_eval(__cli_args.variables)
    for key in vars:
        variables[key] = VariableValue(vars[key])
    
    action.invoke(ast.literal_eval(__cli_args.parameters), variables)