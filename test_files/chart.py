from typing import List
import os
from svg.charts import bar


class Bar:

    def __init__(self, fields: List, values: List[int], titles: List[str], graph_title: str):
        self.graph = bar.VerticalBar(fields)
        self.graph.stack = 'side'
        self.graph.scale_integers = True
        self.graph.width, g.height = 1024, 768
        self.graph.graph_title = graph_title
        self.graph.show_graph_title = True

        for i in range(len(values)):
            self.graph.add_data({'data': values[i], 'title': titles[i]})

    def save(self, filename):
        root = os.path.dirname(__file__)
        res = self.graph.burn()
        with open(f'{os.path.join(root, "svg", filename)}.py.svg', 'w') as f:
            f.write(res)
