"""
"""

import graphviz
import os
import datajoint as dj
from datajoint.schema import lookup_class_name
from flask import render_template, request, flash, url_for, redirect

from . import config
from .virtual_schema import schemata


def draw_helper(obj=None, type='table'):
    """helper for drawing erds
    """
    # rankdir TB?

    # setup of graphviz
    graph_attr = {'size': '12, 12', 'rankdir': 'LR', 'splines': 'ortho'}
    node_attr = {
        'style': 'filled', 'shape': 'note', 'align': 'left',
        'ranksep': '0.1', 'fontsize': '10', 'fontfamily': 'opensans',
        'height': '0.2', 'fontname': 'Sans-Serif'
    }

    dot = graphviz.Digraph(
        graph_attr=graph_attr, node_attr=node_attr,
        engine='dot', format='svg')

    def add_node(name, node_attr={}):
        """
        Add a node/table to the current graph (adding subgraphs if needed).
        """

        table_names = dict(
            zip(['schema', 'table', 'subtable'], name.split('.'))
        )
        graph_attr = {
            'color': 'grey80', 'style': 'filled',
            'label': table_names['schema']
        }

        with dot.subgraph(
            name='cluster_{}'.format(table_names['schema']),
            node_attr=node_attr,
            graph_attr=graph_attr
        ) as subgraph:
            subgraph.node(
                name, label=name,
                URL=url_for('table', **table_names),
                target='_top', **node_attr
            )
        return name

    def name_lookup(full_name):
        """ Look for a table's class name given its full name. """
        return lookup_class_name(full_name, schemata) or full_name

    node_attrs = {
        dj.Manual: {'fillcolor': 'green3'},
        dj.Computed: {'fillcolor': 'coral1'},
        dj.Lookup: {'fillcolor': 'azure3'},
        dj.Imported: {'fillcolor': 'cornflowerblue'},
        dj.Part: {'fillcolor': 'azure3', 'fontsize': '8'},
        dj.Settingstable: {'fillcolor': 'orange'},
        dj.AutoComputed: {'fillcolor': 'coral1'},
        dj.AutoImported: {'fillcolor': 'cornflowerblue'},
    }

    if type == 'table':
        root_table = obj
        root_dependencies = root_table.connection.dependencies
        root_dependencies.load()
        root_name = root_table.full_table_name
        root_id = add_node(
            name_lookup(root_name), node_attrs[dj.diagram._get_tier(root_name)]
        )

        # in edges
        for node_name, _ in root_dependencies.in_edges(root_name):
            if dj.diagram._get_tier(node_name) is dj.diagram._AliasNode:
                # renamed attribute
                node_name = list(root_dependencies.in_edges(node_name))[0][0]

            node_id = add_node(
                name_lookup(node_name),
                node_attrs[dj.diagram._get_tier(node_name)]
            )
            dot.edge(node_id, root_id)

        # out edges
        for _, node_name in root_dependencies.out_edges(root_name):
            if dj.diagram._get_tier(node_name) is dj.diagram._AliasNode:
                # renamed attribute
                node_name = list(root_dependencies.out_edges(node_name))[0][1]

            node_id = add_node(
                name_lookup(node_name),
                node_attrs[dj.diagram._get_tier(node_name)]
            )
            dot.edge(root_id, node_id)

        filename = root_name

    else:
        conn = dj.conn()
        dependencies = conn.dependencies
        dependencies.load()
        for root_name in dependencies.nodes.keys():
            try:
                int(root_name)
                continue
            except Exception:
                pass
            schema = root_name.replace('`', '').split('.')[0]
            if obj is None and schema in ('mysql', 'sys', 'performance_schema'):
                continue
            if obj is not None and (obj != schema):
                continue

            root_id = add_node(
                name_lookup(root_name),
                node_attrs[dj.diagram._get_tier(root_name)]
            )

            for _, node_name in dependencies.out_edges(root_name):
                if dj.diagram._get_tier(node_name) is dj.diagram._AliasNode:
                    # renamed attribute
                    node_name = list(dependencies.out_edges(node_name))[0][1]

                node_id = add_node(
                    name_lookup(node_name),
                    node_attrs[dj.diagram._get_tier(node_name)]
                )
                dot.edge(root_id, node_id)
        if obj is None:
            filename = '<erd>'
        else:
            filename = obj
    filepath = os.path.join(config['tmp_folder'], filename)
    if os.path.exists(filepath):
        os.remove(filepath)
    dot.render(filepath)

    return f'{filename}.svg'
