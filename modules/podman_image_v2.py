#!/usr/bin/python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, division, print_function
__metaclass__ = type

ANSIBLE_METADATA = {'metadata_version': '1.1',
                    'status': ['preview'],
                    'supported_by': 'community'}

DOCUMENTATION = """
  module: podman_image_v2
  author:
      - Dhanisha Phadate (@Phadated) 
      - Renu Hadke (@renuHadke)
      - Neha Jain (@nehajain1809)
      - Krish Jain (@krishjain4894)
      - Chinmay Keskar (@ckeskar)
  short_description: Pull images for use by podman
  notes: []
  description:
      - pull images using Podman.
  options:
    name:
      description:
        - Name of the image to pull. It may contain a tag using the format C(image:tag).
      required: True
    tag:
      description:
        - Tag of the image to pull.
      default: "latest"
    pull:
      description: Whether or not to pull the image.
      default: True
    force:
      description:
        - Whether or not to force pull an image. force the pull even if the image already exists.
    state:
      description:
        - Whether an image should be present or absent.
      default: "present"
      choices:
        - present
 """

EXAMPLES = """
   - name: Pull an image
     podman_image_v2:
       name: fedora
     register: result
  
   - debug: var=result

"""

RETURN = """

"image": "289289d1a15b92ace1a822f9920f5c1477691aa01ca567a8502eb7eb67eb4a80"

"""

import os
import json
import re
import podman
from ansible.module_utils.basic import *

class PodmanImageManager(object):

    def __init__(self, module, results):
        super(PodmanImageManager, self).__init__()
        self.module = module
        self.results = results
        self.name = self.module.params.get('name')
        self.tag = self.module.params.get('tag')
        self.pull = self.module.params.get('pull')
        self.force = self.module.params.get('force')
        self.state = self.module.params.get('state')
        self._client= podman.Client()

        repo, repo_tag = parse_repository_tag(self.name)
        if repo_tag:
            self.name = repo
            self.tag = repo_tag

        self.image_name = '{name}:{tag}'.format(name=self.name, tag=self.tag)

        if self.state in ['present', 'build']:
            self.present()

    def present(self):
        if not self.force:
            # Pull the image
            self.results['actions'].append('Pulled image {image_name}'.format(image_name=self.image_name))
            self.results['changed'] = True
            if not self.module.check_mode:
                self.results['image'] = self.pull_image()

    def find_image(self, image_name=None):
        pass

    def pull_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name

        return self._client.images.pull(image_name)

def parse_repository_tag(repo_name):
    parts = repo_name.rsplit('@', 1)
    if len(parts) == 2:
        return tuple(parts)
        parts = repo_name.rsplit(':', 1)
    if len(parts) == 2 and '/' not in parts[1]:
        return tuple(parts)
    return repo_name, None


def main():
    module = AnsibleModule(
        argument_spec=dict(
            name=dict(type='str', required=True),
            tag=dict(type='str', default='latest'),
            pull=dict(type='bool', default=True),
            force=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present', 'build']),
        ),
    )

    results = dict(
        changed=False,
        actions=[],
        image={},
    )

    PodmanImageManager(module, results)
    module.exit_json(**results)


if __name__ == '__main__':
    main()
