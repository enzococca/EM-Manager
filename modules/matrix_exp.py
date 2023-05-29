import os,sys
import subprocess
from graphviz import Digraph, Source
from .config import config

class HarrisMatrix:


    def __init__(self, sequence,conteporene,property,periodi):
        self.sequence = sequence
        self.periodi=periodi
        self.property = property
        self.conteporene=conteporene
        self.path=config.path




    @property
    def export_matrix_2(self):
        G = Digraph(engine='dot',strict=False)
        G.attr(rankdir='TB')
        G.attr(compound='true')
        G.graph_attr['pad']="0.5"
        G.graph_attr['nodesep']="1"
        G.graph_attr['ranksep']="1.5"
        G.graph_attr['splines'] = 'ortho'
        G.graph_attr['dpi'] = '300'
        elist1 = []
        elist2 =[]
        elist3 = []
        #print(self.sequence)
        for aa in self.periodi:
            with G.subgraph(name=aa[1]) as c:
                for n in aa[0]:
                    c.attr('node',shape='record', label =str(n))
                    c.node(str(n))
                c.attr(color='blue')
                c.attr('node', shape='record', fillcolor='white', style='filled', gradientangle='90',label=aa[2])
                c.node(aa[2])
        for bb in self.sequence:
            a = (bb[0],bb[1])
            elist1.append(a)
        with G.subgraph(name='main') as e:
            e.attr(rankdir='TB')
            e.edges(elist1)
            e.node_attr['shape'] = 'box'
            e.node_attr['style'] = 'solid'
            e.node_attr.update(style='filled', fillcolor='white')
            e.node_attr['color'] = 'black'
            e.node_attr['penwidth'] = '.5'
            e.edge_attr['penwidth'] = '.5'
            e.edge_attr['style'] = 'solid'
            e.edge_attr.update(arrowhead='normal', arrowsize='.8')
            for pp in self.property:
                a = (pp[0],pp[1])
                elist2.append(a)
            with G.subgraph(name='main2') as b:
                b.edges(elist2)
                b.node_attr['shape'] = 'box'
                b.node_attr['style'] = 'solid'
                b.node_attr.update(style='filled', fillcolor='white')
                b.node_attr['color'] = 'black'
                b.node_attr['penwidth'] = '.5'
                b.edge_attr['penwidth'] = '.5'
                b.edge_attr['style'] = 'dashed'
                b.edge_attr.update(arrowhead='normal', arrowsize='.8')

            for cc in self.conteporene:
                a = (cc[0],cc[1])
                elist3.append(a)
            with G.subgraph(name='main1') as b:
                b.edges(elist3)
                b.node_attr['shape'] = 'box'
                b.node_attr['style'] = 'solid'
                b.node_attr.update(style='filled', fillcolor='white')
                b.node_attr['color'] = 'black'
                b.node_attr['penwidth'] = '.5'
                b.edge_attr['penwidth'] = '.5'
                b.edge_attr['style'] = 'solid'
                b.edge_attr.update(arrowhead='none', arrowsize='.8')

        #matrix_path = '{}{}{}'.format(self.HOME, os.sep, "pyarchinit_Matrix_folder")
        if self.path:
            filename = os.path.join(self.path, "Harris_matrix2ED")  # Percorso completo al file dot

            print(f"self.path: {filename}")
            G.format = 'dot'
            #dot_file = G.render(directory=self.path, filename=filename)
            dot_file = G.render(filename=filename, format='dot')
            with open(os.path.join(filename + '_graphml.dot'), "w") as out:
                if sys.platform == 'Windows':
                    si = subprocess.STARTUPINFO()
                    si.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                    si.wShowWindow = subprocess.SW_HIDE
                    subprocess.Popen(['tred',dot_file], stdout=out, startupinfo=si)
                else:
                    subprocess.Popen(['tred',dot_file], stdout=out)


            tred_file = dot_file
            print(f"path da tred file: {tred_file}")
            f = Source.from_file(tred_file, format='png')
            f.render()
            g = Source.from_file(tred_file, format='jpg')
            g.render()
            return g, f
        else:
            print('la path dove deve essere salvato il file dot non è valido')