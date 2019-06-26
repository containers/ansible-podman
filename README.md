
Ansible Module for Podman
=========================
This module allows Ansible to use Podman to manage container images.

Requirements
============
* Python 3.6+
* Ansible 2.8

Installation
============
1. Install [Podman](https://github.com/containers/libpod/blob/master/install.md)
2. Install [Python-podman library](https://github.com/containers/python-podman) on the host you will be
   running ansible playbooks.
```
git clone git@github.com:containers/python-podman.git
cd ~/python-podman
python3 setup.py clean -a && python3 setup.py sdist bdist
python3 setup.py install --user
```
3. Copy `podman_images_v2.py` to your directory library 
```
../podman_test/
├── library
│   └── podman_image_v2.py
└── pull_image.yml
```

Usage Examples
==============
This module will pull the fedora latest image from docker hub.

```
hosts: localhost
  tasks:
   - name: Pull an image
     podman_image_v2:
       name: fedora
     register: result

   - debug: var=result
```

Parameters
==========

<table>
<tr>
<th class="head">parameter</th>
<th class="head">required</th>
<th class="head">default</th>
<th class="head">choices</th>
<th class="head">comments</th>
</tr>
<tr>
<td>name</td>
<td>yes</td>
<td></td>
<td><ul></ul></td>
<td>Set image name</td>
</tr>
<tr>
<td>tag</td>
<td>no</td>
<td>latest</td>
<td><ul></ul></td>
<td>Set the tag of the image</td>
</tr>
<tr>
<td>pull</td>
<td>no</td>
<td>true</td>
<td><ul></ul></td>
<td>Set the pull option</td>
</tr>
<tr>
<td>force</td>
<td>no</td>
<td>false</td>
<td><ul></ul></td>
<td>Set to pull an image forcefully</td>
</tr>
  <tr>
<td>state</td>
<td>no</td>
<td>present</td>
<td><ul><li>present</li><li>build</li><li>absent</li></ul></td>
<td>Set the state of the image</td>
</tr>
</table>
