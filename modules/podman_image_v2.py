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

"image": {
            "annotations": {},
            "architecture": "amd64",
            "author": "",
            "comment": "",
            "config": {
                "cmd": [
                    "/bin/sh"
                ],
                "env": [
                    "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin"
                ]
            },
            "created": "2019-07-11T22:20:52.375286404Z",
            "digest": "sha256:57334c50959f26ce1ee025d08f136c2292c128f84e7b229d1b0da5dac89e9866",
            "graphdriver": {
                "data": {
                    "mergeddir": "/var/lib/containers/storage/overlay/1bfeebd65323b8ddf5bd6a51cc7097b72788bc982e9ab3280d53d3c613adffa7/merged",
                    "upperdir": "/var/lib/containers/storage/overlay/1bfeebd65323b8ddf5bd6a51cc7097b72788bc982e9ab3280d53d3c613adffa7/diff",
                    "workdir": "/var/lib/containers/storage/overlay/1bfeebd65323b8ddf5bd6a51cc7097b72788bc982e9ab3280d53d3c613adffa7/work"
                },
                "name": "overlay"
            },
            "history": [
                {
                    "created": "2019-07-11T22:20:52.139709355Z",
                    "created_by": "/bin/sh -c #(nop) ADD file:0eb5ea35741d23fe39cbac245b3a5d84856ed6384f4ff07d496369ee6d960bad in / "
                },
                {
                    "created": "2019-07-11T22:20:52.375286404Z",
                    "created_by": "/bin/sh -c #(nop)  CMD [\"/bin/sh\"]",
                    "empty_layer": true
                }
            ],
            "id": "b7b28af77ffec6054d13378df4fdf02725830086c7444d9c278af25312aa39b9",
            "labels": null,
            "manifesttype": "application/vnd.docker.distribution.manifest.v2+json",
            "os": "linux",
            "parent": "",
            "repodigests": [
                "docker.io/library/alpine@sha256:57334c50959f26ce1ee025d08f136c2292c128f84e7b229d1b0da5dac89e9866"
            ],
            "repotags": [
                "docker.io/library/alpine:latest"
            ],
            "rootfs": {
                "layers": [
                    "sha256:1bfeebd65323b8ddf5bd6a51cc7097b72788bc982e9ab3280d53d3c613adffa7"
                ],
                "type": "layers"
            },
            "size": 5846536,
            "user": "",
            "version": "18.06.1-ce",
            "virtualsize": 5846536
        }

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
        id=self._client.images.pull(image_name)
        img=self._client.images.get(id)
        res=img.inspect()
        return res._asdict()
    
    def absent(self):
        image = self.find_image()

        if image:
            self.results['actions'].append('Removed image {name}'.format(name=self.name))
            self.results['changed'] = True
            self.results['image']['state'] = 'Deleted'
            if not self.module.check_mode:
                self.remove_image()

    def remove_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name

        img = client.images.get(image_name)
        if self.force:
            _id=img.remove(self.force)
        else:
            _id=img.remove()
        
        return _id


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
