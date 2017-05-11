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
                roots.insert(0, child)

    return items_sorted
