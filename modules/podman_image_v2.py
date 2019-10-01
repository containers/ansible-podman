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
  short_description: Pull, Push and remove images for use by podman
  notes: []
  description:
      - pull, Push, remove images using Podman.
  options:
    name:
      description:
        - Name of the image to pull, push or delete. It may contain a tag using the format C(image:tag).
      required: True
    tag:
      description:
        - Tag of the image to pull, push or delete.
      default: "latest"
    pull:
      description: Whether or not to pull the image.
      default: True
    push:
      description: Whether or not to push an image.
      default: False
    force:
      description:
        - Whether or not to force pull an image. force the pull even if the image already exists.
    state:
      description:
        - Whether an image should be present or absent.
      default: "present"
      choices:
        - present
        - absent
        - build
    push_args:
      description: Arguments that control pushing images.
      suboptions:
        dest:
          description: Path or URL where image will be pushed.
        transport:
          description:
            - Transport to use when pushing in image. If no transport is set, will attempt to push to a remote registry.
          choices:
            - dir
            - docker-archive
            - docker-daemon
            - oci-archive
            - ostree
 """

EXAMPLES = """
   - name: Pull an image
     podman_image_v2:
       name: fedora

    - name: Remove an image 
      podman_image_v2:
         name: alpine
         state: absent 

    - name: Pull an image with specific tag
     podman_image_v2:
        name: alpine
        tag: "3.10.1"

    - name: push an image
        podman_image_v2:
            name: alpine
            push: yes
            push_args:
            dest: docker.io/dhanisha
    
    - name: push an image to 
        podman_image_v2:
            name: alpine
            push: yes
            push_args:
            dest: docker.io/dhanisha
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
        self.push = self.module.params.get('push')
        self.force = self.module.params.get('force')
        self.state = self.module.params.get('state')
        self.push_args = self.module.params.get('push_args')
        self._client= podman.Client()

        repo, repo_tag = parse_repository_tag(self.name)
        if repo_tag:
            self.name = repo
            self.tag = repo_tag

        self.image_name = '{name}:{tag}'.format(name=self.name, tag=self.tag)

        if self.state in ['present', 'build']:
            self.present()
        
        if self.state in ['absent']:
            self.absent()

    def present(self):

        if not self.force:
            # Pull the image
            self.results['actions'].append('Pulled image {image_name}'.format(image_name=self.image_name))
            self.results['changed'] = True
            if not self.module.check_mode:
                self.results['image'] = self.pull_image()
        
        if self.push:
            # Push the image
            if '/' in self.image_name:
                push_format_string = 'Pushed image {image_name}'
            else:
                push_format_string = 'Pushed image {image_name} to {dest}'

            if not self.module.check_mode:
                self.results['actions'].append(push_format_string.format(image_name=self.image_name, dest=self.push_args['dest']))
                self.results['changed'] = True
                self.results['image']= self.push_image()

    #TODO implement this function once https://github.com/containers/python-podman/issues/51 resolved
    def build_image(self):
        pass
                

    def find_image(self, image_name=None):
        pass

    def pull_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name
        id=self._client.images.pull(image_name)
        img=self._client.images.get(id)
        res=img.inspect()
        return res._asdict()

    #FIXME The result will return error until https://github.com/containers/python-podman/issues/52 is resolved
    #TODO Implement the push args
    def push_image(self, image_name=None):

        # Build the destination argument
        #  dest - docker.io/dhanisha {image_name} : self.name
        if image_name is None:
            image_name = self.image_name
        dest = self.push_args.get('dest')
        dest_format_string = '{dest}/{image_name}'
        regexp = re.compile(r'/{name}(:{tag})?'.format(name=self.name, tag=self.tag))
        if not dest:
            if '/' not in self.name:
                self.module.fail_json(msg="'push_args['dest']' is required when pushing images that do not have the remote registry in the image name")

        # If the push destinaton contains the image name and/or the tag
        # remove it and warn since it's not needed.
        elif regexp.search(dest):
            dest = regexp.sub('', dest)
            self.module.warn("Image name and tag are automatically added to push_args['dest']. Destination changed to {dest}".format(dest=dest))

        if dest and dest.endswith('/'):
            dest = dest[:-1]

        transport = self.push_args.get('transport')

        if transport:
            if not dest:
                self.module.fail_json("'push_args['transport'] requires 'push_args['dest'] but it was not provided.")
            if transport == 'docker':
                dest_format_string = '{transport}://{dest}'
            elif transport == 'ostree':
                dest_format_string = '{transport}:{name}@{dest}'
            else:
                dest_format_string = '{transport}:{dest}'

        dest_string = dest_format_string.format(transport=transport, name=self.name, dest=dest, image_name=self.image_name,)

        # Only append the destination argument if the image name is not a URL
        if '/' not in self.name:
            try:
                img = self._client.images.get(image_name)
                result= img.push(dest_string)
            except KeyError as err:
                result= "Failed to push image {image_name}: KeyError {err}".format(image_name=self.image_name, err=err)
                self.module.fail_json(msg="Failed to push image {image_name}: KeyError {err}".format(image_name=self.image_name, err=err))
        else:
            #result= "Failed to push image {image_name}:Image name is an url".format(image_name=self.image_name)
            self.module.fail_json(msg="Failed to push image {image_name}:Image name is an url".format(image_name=self.image_name))

        return result


    def absent(self):
        image = self.image_name

         #TODO find_image function to check if the image is present before removal
        if image:
            if not self.module.check_mode and self.remove_image() == 'Deleted':
                self.results['actions'].append('Removed image {name}'.format(name=self.name))
                self.results['changed'] = True
                self.results['image']['state'] = 'Deleted'
            else:
                self.results['image']['state'] = 'ImageNotFound'


    def remove_image(self, image_name=None):
        if image_name is None:
            image_name = self.image_name
        try:
            img = self._client.images.get(image_name)
            if self.force:
                _id=img.remove(self.force)
            else:
                _id=img.remove()
            
            if _id:
                out= "Deleted"

        except:
            out= "ImageNotFound"

        return out

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
            push=dict(type='bool', default=False),
            force=dict(type='bool', default=False),
            state=dict(type='str', default='present', choices=['absent', 'present', 'build']),
            username=dict(type='str'),
            password=dict(type='str', no_log=True),
            push_args=dict(
                type='dict',
                default={},
                options=dict(
                    dest=dict(type='str', aliases=['destination'],),
                    transport=dict(
                        type='str',
                        choices=[
                            'dir',
                            'docker-archive',
                            'docker-daemon',
                            'oci-archive',
                            'ostree',
                        ]
                    ),
                ),
            ),
        )
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
