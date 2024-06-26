from django.conf import settings
from django.core import mail
from django.template import Context
from django.template.loader import get_template

import logging
logger = logging.getLogger(__name__)


def tree_to_list(items, sort_by=None, omit=[], reverse=False):

    items_flat = []
    roots = []
    items_sorted = []
    items_keyed_by_id = {}

    for item in items:
        items_flat.append({
            'obj': item,
            'children': [],
            'depth': 0,
        })

    for item in items_flat:
        items_keyed_by_id[item['obj'].id] = item

    for item in items_flat:
        if item['obj'].parent and item['obj'].parent.id in items_keyed_by_id:
            parent = items_keyed_by_id[item['obj'].parent.id]
            parent['children'].append(item)
        else:
            roots.append(item)

    if sort_by:
        roots = sorted(roots, key=lambda k: getattr(k['obj'], sort_by), reverse=reverse)

    while len(roots):
        root = roots[0]
        del roots[0]

        if not omit or not root.obj.id in omit:
            items_sorted.append(root)
            children = sorted(root['children'], key=lambda k: getattr(k['obj'], sort_by), reverse=True)
            for child in children:
                child['depth'] = root['depth'] + 1
                child['indent_rendered'] = '&nbsp;&nbsp;&nbsp;&nbsp;'.join(['' for i in range(child['depth'] + 1)])
                roots.insert(0, child)

    return items_sorted


def list_at_node(items, root):
    new_list = []
    found_root = False
    for node in items:
        if node['obj'] == root:
            found_root = True
            root_depth = node['depth']
        if found_root:
            if node['depth'] <= root_depth and node['obj'] != root:
                found_root = False
            else:
                new_list.append(node)
    return new_list
