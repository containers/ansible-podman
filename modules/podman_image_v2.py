from __future__ import absolute_import, division, print_function
__metaclass__ = type

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
        
        if self.state in ['absent']:
            self.absent()

    def present(self):
        if self.force:
            # Pull the image
            self.results['actions'].append('Pulled image {image_name}'.format(image_name=self.image_name))
            self.results['changed'] = True
            if not self.module.check_mode:
                self.results['image'] = self.pull_image()
                # self.results = self.pull_image()

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
