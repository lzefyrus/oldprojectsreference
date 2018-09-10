import json
import os
import yaml


def yaml_to_json(yaml_dir, json_dir, directory="", urlBase=None, responseMessages=None):
    combined = {}
    yaml_path = os.path.join(yaml_dir, directory)
    json_path = os.path.join(json_dir, directory)
    dir_list = []
    for item in os.listdir(os.path.join(yaml_dir, directory)):
        if '.yml' in item:
            with open(os.path.join(yaml_path, item), 'r') as yamlfile:
                data = yaml.load(yamlfile)
                # Troca o endpoint da aplicacao
                if urlBase and item == 'root.yml' and 'basePath' in data.keys():
                    data['basePath'] = urlBase

                # Pega os retornos de erro do conf
                if responseMessages and item == 'apis.yml':
                    # Pega todos codigos/msgs do conf
                    statusCode = list()
                    for codes in responseMessages:
                        statusCode.append(responseMessages[codes])

                    for apis in data:
                        for ib, blocks in enumerate(data[apis]):
                            if 'operations' in blocks:
                                for ip, block in enumerate(blocks['operations']):
                                    if 'responseMessages' in block:
                                        data[apis][ib]['operations'][ip]['responseMessages'] = statusCode
				#
                combined.update(data)
        else:
            dir_list.append(item)
    if not os.path.isdir(json_path):
        os.mkdir(json_path)
    with open(os.path.join(json_path, 'swagger.json'), 'w') as json_file:
        json.dump(combined, json_file)
    for new_directory in dir_list:
        yaml_to_json(yaml_dir, json_dir, new_directory, urlBase, responseMessages)
