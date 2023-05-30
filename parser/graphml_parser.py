import xml.etree.ElementTree as ET



def graphml_parse(self, context, graphml_file):
    scene = context.scene
    tree = ET.parse(graphml_file) # provide the path

    allnodes = tree.findall('.//{http://graphml.graphdrawing.org/xmlns}node')

    for node_element in allnodes:
        if EM_check_node_type(node_element) == 'node_simple': # The node is not a group or a swimlane
            if EM_check_node_us(node_element): # Check if the node is an US, SU, USV, USM or USR node
                my_nodename, my_node_description, my_node_url, my_node_shape, my_node_y_pos, my_node_fill_color = EM_extract_node_name(node_element)
                scene.em_list.add()
                scene.em_list[em_list_index_ema].name = my_nodename
                scene.em_list[em_list_index_ema].y_pos = float(my_node_y_pos)
                scene.em_list[em_list_index_ema].description = my_node_description
                    #print(my_node_shape)
                if my_node_fill_color == '#FFFFFF':
                    if my_node_shape == "ellipse" or my_node_shape == "octagon":
                        scene.em_list[em_list_index_ema].shape = my_node_shape+"_white"
                    else:
                        scene.em_list[em_list_index_ema].shape = my_node_shape
                else:
                    scene.em_list[em_list_index_ema].shape = my_node_shape
                scene.em_list[em_list_index_ema].id_node = getnode_id(node_element)
                em_list_index_ema += 1
            elif EM_check_node_document(node_element):
                source_already_in_list = False
                source_number = 2
                src_nodename, src_node_id, src_node_description, src_nodeurl, subnode_is_document = EM_extract_document_node(node_element)
                src_nodename_safe = src_nodename
                if em_sources_index_ema > 0: 
                    for source_item in scene.em_sources_list:
                        if source_item.name == src_nodename:
                            source_already_in_list = True
                if source_already_in_list:
                    src_nodename = src_nodename+"_"+str(source_number)
                    source_number +=1
                scene.em_sources_list.add()
                scene.em_sources_list[em_sources_index_ema].name = src_nodename
                #scene.em_sources_list[em_sources_index_ema].icon = check_objs_in_scene_and_provide_icon_for_list_element(src_nodename_safe)
                scene.em_sources_list[em_sources_index_ema].id_node = src_node_id
                scene.em_sources_list[em_sources_index_ema].url = src_nodeurl
                if src_nodeurl == "--None--":
                    scene.em_sources_list[em_sources_index_ema].icon_url = "CHECKBOX_DEHLT"
                else:
                    scene.em_sources_list[em_sources_index_ema].icon_url = "CHECKBOX_HLT"
                scene.em_sources_list[em_sources_index_ema].description = src_node_description
                em_sources_index_ema += 1
            elif EM_check_node_property(node_element):
                pro_nodename, pro_node_id, pro_node_description, pro_nodeurl, subnode_is_property = EM_extract_property_node(node_element)
                scene.em_properties_list.add()
                scene.em_properties_list[em_properties_index_ema].name = pro_nodename
                #scene.em_properties_list[em_properties_index_ema].icon = check_objs_in_scene_and_provide_icon_for_list_element(pro_nodename)
                scene.em_properties_list[em_properties_index_ema].id_node = pro_node_id
                scene.em_properties_list[em_properties_index_ema].url = pro_nodeurl
                if pro_nodeurl == "--None--":
                    scene.em_properties_list[em_properties_index_ema].icon_url = "CHECKBOX_DEHLT"
                else:
                    scene.em_properties_list[em_properties_index_ema].icon_url = "CHECKBOX_HLT"
                scene.em_properties_list[em_properties_index_ema].description = pro_node_description
                em_properties_index_ema += 1
            elif EM_check_node_extractor(node_element):
                ext_nodename, ext_node_id, ext_node_description, ext_nodeurl, subnode_is_extractor = EM_extract_extractor_node(node_element)
                scene.em_extractors_list.add()
                scene.em_extractors_list[em_extractors_index_ema].name = ext_nodename
                scene.em_extractors_list[em_extractors_index_ema].id_node = ext_node_id                   
                #scene.em_extractors_list[em_extractors_index_ema].icon = check_objs_in_scene_and_provide_icon_for_list_element(ext_nodename)
                scene.em_extractors_list[em_extractors_index_ema].url = ext_nodeurl
                #print(ext_nodeurl)
                if ext_nodeurl == "--None--":
                    scene.em_extractors_list[em_extractors_index_ema].icon_url = "CHECKBOX_DEHLT"
                else:
                    scene.em_extractors_list[em_extractors_index_ema].icon_url = "CHECKBOX_HLT"
                scene.em_extractors_list[em_extractors_index_ema].description = ext_node_description
                em_extractors_index_ema += 1
            elif EM_check_node_combiner(node_element):
                ext_nodename, ext_node_id, ext_node_description, ext_nodeurl, subnode_is_combiner = EM_extract_combiner_node(node_element)
                scene.em_combiners_list.add()
                scene.em_combiners_list[em_combiners_index_ema].name = ext_nodename
                scene.em_combiners_list[em_combiners_index_ema].id_node = ext_node_id                   
                #scene.em_combiners_list[em_combiners_index_ema].icon = check_objs_in_scene_and_provide_icon_for_list_element(ext_nodename)
                scene.em_combiners_list[em_combiners_index_ema].url = ext_nodeurl
                #print(ext_nodeurl)
                if ext_nodeurl == "--None--":
                    scene.em_combiners_list[em_combiners_index_ema].icon_url = "CHECKBOX_DEHLT"
                else:
                    scene.em_combiners_list[em_combiners_index_ema].icon_url = "CHECKBOX_HLT"
                scene.em_combiners_list[em_combiners_index_ema].description = ext_node_description
                em_combiners_index_ema += 1
            else:
                pass

        if EM_check_node_type(node_element) == 'node_swimlane':
            extract_epochs(node_element)

    for em_i in range(len(scene.em_list)):
        for epoch_in in range(len(scene.epoch_list)):
            if scene.epoch_list[epoch_in].min_y < scene.em_list[em_i].y_pos < scene.epoch_list[epoch_in].max_y:
                scene.em_list[em_i].epoch = scene.epoch_list[epoch_in].name

    #porzione di codice per estrarre le continuità
    for node_element in allnodes:
        if EM_check_node_type(node_element) == 'node_simple': # The node is not a group or a swimlane
            if EM_check_node_continuity(node_element):
                #print("found continuity node")
                EM_us_target, continuity_y = get_edge_target(tree, node_element)
                #print(EM_us_target+" has y value: "+str(continuity_y))
                for EM_item in bpy.context.scene.em_list:
                    if EM_item.icon == "RESTRICT_INSTANCED_OFF":
                        if EM_item.name == EM_us_target:
                            for ep_i in range(len(scene.epoch_list)):
                                #print("epoca "+epoch.name+" : min"+str(epoch.min_y)+" max: "+str(epoch.max_y)+" minore di "+str(continuity_y)+" e "+ str(epoch.min_y) +" minore di "+str(EM_item.y_pos))
                                if scene.epoch_list[ep_i].max_y > continuity_y and scene.epoch_list[ep_i].max_y < EM_item.y_pos:
                                    #print("found")
                                    scene.em_reused.add()
                                    scene.em_reused[em_reused_index].epoch = scene.epoch_list[ep_i].name
                                    scene.em_reused[em_reused_index].em_element = EM_item.name
                                    #print("All'epoca "+scene.em_reused[em_reused_index].epoch+ " appartiene : "+ scene.em_reused[em_reused_index].em_element)
                                    em_reused_index += 1
    read_edge_db(context,tree)
    try:
        node_send = scene.em_list[scene.em_list_index]
    except IndexError as error:
        scene.em_list_index = 0
        node_send = scene.em_list[scene.em_list_index]
    create_derived_lists(node_send)
    if context.scene.proxy_display_mode == "EM":
        bpy.ops.emset.emmaterial()
    else:
        bpy.ops.emset.epochmaterial()
    return {'FINISHED'}


def EM_check_node_type(node_element):
    id_node = str(node_element.attrib)
    if "yfiles.foldertype" in id_node:
        tablenode = node_element.find('.//{http://www.yworks.com/xml/graphml}TableNode')
        if tablenode is not None:
            #print(' un nodo swimlane: ' + id_node)
            node_type = 'node_swimlane'
        else:
            #print(' un nodo group: ' + id_node)
            node_type = 'node_group'
    else:
        #print(' un semplice nodo: ' + id_node)
        node_type = 'node_simple'
    return node_type

def EM_check_node_us(node_element):
    US_nodes_list = ['rectangle', 'parallelogram',
                     'ellipse', 'hexagon', 'octagon', 'roundrectangle']
    my_nodename, my_node_description, my_node_url, my_node_shape, my_node_y_pos, my_node_fill_color = EM_extract_node_name(node_element)
    #print(my_node_shape)
    if my_node_shape in US_nodes_list:
        id_node_us = True
    else:
        id_node_us = False
    return id_node_us

def EM_check_node_document(node_element):
    try:
        src_nodename, src_node_id, src_node_description, src_nodeurl, subnode_is_document = EM_extract_document_node(node_element)
    except TypeError as e:
        subnode_is_document = False
        #print(f"Huston abbiamo un problema {e} al nodo {node_element}")
    return subnode_is_document

def EM_check_node_property(node_element):
    try:
        pro_nodename, pro_node_id, pro_node_description, pro_nodeurl, subnode_is_property = EM_extract_property_node(node_element)
    except UnboundLocalError as e:
        subnode_is_property = False
    return subnode_is_property

def EM_check_node_extractor(node_element):
    try:
        ext_nodename, ext_node_id, ext_node_description, ext_nodeurl, subnode_is_extractor = EM_extract_extractor_node(node_element)
    except TypeError as e:
        subnode_is_extractor = False
    return subnode_is_extractor

def EM_check_node_combiner(node_element):
    try:
        com_nodename, com_node_id, com_node_description, com_nodeurl, subnode_is_combiner = EM_extract_combiner_node(node_element)
    except TypeError as e:
        subnode_is_combiner = False
    return subnode_is_combiner

def EM_check_node_continuity(node_element):
    id_node_continuity = False
    my_node_description, my_node_y_pos = EM_extract_continuity(node_element)
    if my_node_description == "_continuity":
        id_node_continuity = True
        #print("found node continuity")
    else:
        id_node_continuity = False
    return id_node_continuity

def getnode_id(node_element):
    id_node = str(node_element.attrib['id'])
    return id_node

def EM_extract_document_node(node_element):

    is_d4 = False
    is_d5 = False
    node_id = node_element.attrib['id']
    if len(node_id) > 2:
        subnode_is_document = False
        nodeurl = " "
        nodename = " "
        node_description = " "
        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib
            #print(subnode.tag)
            if attrib1 == {'key': 'd6'}:
                for USname in subnode.findall('.//{http://www.yworks.com/xml/graphml}NodeLabel'):
                    nodename = USname.text
                for nodetype in subnode.findall('.//{http://www.yworks.com/xml/graphml}Property'):
                    attrib2 = nodetype.attrib
                    if attrib2 == {'class': 'com.yworks.yfiles.bpmn.view.DataObjectTypeEnum', 'name': 'com.yworks.bpmn.dataObjectType', 'value': 'DATA_OBJECT_TYPE_PLAIN'}:
                        subnode_is_document = True

        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib                        
            if subnode_is_document is True:

                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd4'}:
                    if subnode.text is not None:
                        is_d4 = True
                        nodeurl = subnode.text
                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd5'}:
                    is_d5 = True
                    node_description = clean_comments(subnode.text)
        if not is_d4:
            nodeurl = '--None--'
        if not is_d5:
            nodedescription = '--None--'
        return nodename, node_id, node_description, nodeurl, subnode_is_document

def check_if_empty(name):
    if name == None:
        name = "--None--"
    return name

def EM_extract_property_node(node_element):
    is_d4 = False
    is_d5 = False
    node_id = node_element.attrib['id']
    if len(node_id) > 2:
        subnode_is_property = False
        nodeurl = " "
        nodename = " "
        node_description = " "
        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib
            if attrib1 == {'key': 'd6'}:
                for USname in subnode.findall('.//{http://www.yworks.com/xml/graphml}NodeLabel'):
                    nodename = check_if_empty(USname.text)
                for nodetype in subnode.findall('.//{http://www.yworks.com/xml/graphml}Property'):
                    attrib2 = nodetype.attrib
                    if attrib2 == {'class': 'com.yworks.yfiles.bpmn.view.BPMNTypeEnum', 'name': 'com.yworks.bpmn.type', 'value': 'ARTIFACT_TYPE_ANNOTATION'}:
                        subnode_is_property = True

        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib                        
            if subnode_is_property is True:

                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd4'}:
                    if subnode.text is not None:
                        is_d4 = True
                        nodeurl = subnode.text
                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd5'}:
                    is_d5 = True
                    node_description = clean_comments(subnode.text)

        if not is_d4:
            nodeurl = '--None--'
        if not is_d5:
            nodedescription = '--None--'        


    return nodename, node_id, node_description, nodeurl, subnode_is_property

def remove_comments(text_to_clean):
    clean_text = text_to_clean.split("##")[0].replace("\n","")
    return clean_text

def clean_comments(multiline_str):
    newstring = ""
    for line in multiline_str.splitlines():
        #print(line)
        if line.startswith("«") or line.startswith("#"):
            pass
        else:
            newstring = newstring+line+" "
    return newstring

def EM_extract_node_name(node_element):
    is_d4 = False
    is_d5 = False
    node_y_pos = None
    nodeshape = None
    nodeurl = None
    nodedescription = None
    nodename = None
    fillcolor = None
    for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
        attrib = subnode.attrib
        if attrib == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd4'}:
            is_d4 = True
            nodeurl = subnode.text
        if attrib == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd5'}:
            is_d5 = True
            nodedescription = clean_comments(subnode.text)
        if attrib == {'key': 'd6'}:
            for USname in subnode.findall('.//{http://www.yworks.com/xml/graphml}NodeLabel'):
                nodename = check_if_empty(USname.text)
            for fill_color in subnode.findall('.//{http://www.yworks.com/xml/graphml}Fill'):
                fillcolor = fill_color.attrib['color']
            for USshape in subnode.findall('.//{http://www.yworks.com/xml/graphml}Shape'):
                nodeshape = USshape.attrib['type']
            for geometry in subnode.findall('./{http://www.yworks.com/xml/graphml}ShapeNode/{http://www.yworks.com/xml/graphml}Geometry'):
            #for geometry in subnode.findall('./{http://www.yworks.com/xml/graphml}Geometry'):
                node_y_pos = geometry.attrib['y']
    if not is_d4:
        nodeurl = '--None--'
    if not is_d5:
        nodedescription = '--None--'
    return nodename, nodedescription, nodeurl, nodeshape, node_y_pos, fillcolor 

def EM_extract_continuity(node_element):
    is_d5 = False
    node_y_pos = 0.0
    nodedescription = None
    for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
        attrib = subnode.attrib
        #print(attrib)
        if attrib == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd5'}:
            is_d5 = True
            nodedescription = subnode.text
            #print(nodedescription)
        if attrib == {'key': 'd6'}:
            for geometry in subnode.findall('./{http://www.yworks.com/xml/graphml}SVGNode/{http://www.yworks.com/xml/graphml}Geometry'):
                node_y_pos = float(geometry.attrib['y'])
                #print("il valore y di nodo "+ str(nodedescription) +" = "+str(node_y_pos))
    if not is_d5:
        nodedescription = '--None--'
    return nodedescription, node_y_pos 

def EM_extract_extractor_node(node_element):

    is_d4 = False
    is_d5 = False
    node_id = node_element.attrib['id']
    if len(node_id) > 2:
        subnode_is_extractor = False
        nodeurl = " "
        nodename = " "
        node_description = " "
        is_document = False
        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib
            #print(subnode.tag)
            if attrib1 == {'key': 'd6'}:
                for USname in subnode.findall('.//{http://www.yworks.com/xml/graphml}NodeLabel'):
                    nodename = check_if_empty(USname.text)
                if nodename.startswith("D."):
                    for elem in bpy.context.scene.em_sources_list:
                        if nodename == elem.name:
                            is_document = True
                    if not is_document:
                        #print(f"il nodo non è un documento e si chiama: {nodename}")
                        subnode_is_extractor = True
                # for nodetype in subnode.findall('.//{http://www.yworks.com/xml/graphml}SVGContent'):
                #     attrib2 = nodetype.attrib
                #     if attrib2 == {'refid': '1'}:
                #         subnode_is_extractor = True
                        
        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib                        
            if subnode_is_extractor is True:

                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd4'}:
                    if subnode.text is not None:
                        is_d4 = True
                        nodeurl = check_if_empty(subnode.text)
                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd5'}:
                    is_d5 = True
                    node_description = clean_comments(check_if_empty(subnode.text))

        if not is_d4:
            nodeurl = '--None--'
        if not is_d5:
            nodedescription = '--None--'
        return nodename, node_id, node_description, nodeurl, subnode_is_extractor
    

def EM_extract_combiner_node(node_element):

    is_d4 = False
    is_d5 = False
    node_id = node_element.attrib['id']
    if len(node_id) > 2:
        subnode_is_combiner = False
        nodeurl = " "
        nodename = " "
        node_description = " "
        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib
            #print(subnode.tag)
            if attrib1 == {'key': 'd6'}:
                for USname in subnode.findall('.//{http://www.yworks.com/xml/graphml}NodeLabel'):
                    nodename = check_if_empty(USname.text)
                if nodename.startswith("C."):
                    subnode_is_combiner = True
                    #print(nodename)
                # for nodetype in subnode.findall('.//{http://www.yworks.com/xml/graphml}SVGContent'):
                #     attrib2 = nodetype.attrib
                #     if attrib2 == {'refid': '3'}:
                #         subnode_is_combiner = True
                        
        for subnode in node_element.findall('.//{http://graphml.graphdrawing.org/xmlns}data'):
            attrib1 = subnode.attrib                        
            if subnode_is_combiner is True:

                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd4'}:
                    if subnode.text is not None:
                        is_d4 = True
                        nodeurl = check_if_empty(subnode.text)
                if attrib1 == {'{http://www.w3.org/XML/1998/namespace}space': 'preserve', 'key': 'd5'}:
                    is_d5 = True
                    node_description = clean_comments(check_if_empty(subnode.text))

        if not is_d4:
            nodeurl = '--None--'
        if not is_d5:
            nodedescription = '--None--'
        return nodename, node_id, node_description, nodeurl, subnode_is_combiner
    
def extract_epochs(node_element):
    geometry = node_element.find('.//{http://www.yworks.com/xml/graphml}Geometry')
    y_start = float(geometry.attrib['y'])
    context = bpy.context
    scene = context.scene    
    EM_list_clear(context, "epoch_list")  
    epoch_list_index_ema = 0
    y_min = y_start
    y_max = y_start

    for row in node_element.findall('./{http://graphml.graphdrawing.org/xmlns}data/{http://www.yworks.com/xml/graphml}TableNode/{http://www.yworks.com/xml/graphml}Table/{http://www.yworks.com/xml/graphml}Rows/{http://www.yworks.com/xml/graphml}Row'):
        id_row = row.attrib['id']
        h_row = float(row.attrib['height'])
        
        scene.epoch_list.add()
        scene.epoch_list[epoch_list_index_ema].id = str(id_row)
        scene.epoch_list[epoch_list_index_ema].height = h_row
        
        y_min = y_max
        y_max += h_row
        scene.epoch_list[epoch_list_index_ema].min_y = y_min
        scene.epoch_list[epoch_list_index_ema].max_y = y_max
        #print(str(id_row))
        epoch_list_index_ema += 1        

    for nodelabel in node_element.findall('./{http://graphml.graphdrawing.org/xmlns}data/{http://www.yworks.com/xml/graphml}TableNode/{http://www.yworks.com/xml/graphml}NodeLabel'):
        RowNodeLabelModelParameter = nodelabel.find('.//{http://www.yworks.com/xml/graphml}RowNodeLabelModelParameter')
        if RowNodeLabelModelParameter is not None:
            label_node = nodelabel.text
            id_node = str(RowNodeLabelModelParameter.attrib['id'])
            # read the color of the epoch from the title of the row, if no color is provided, a default color is used
            if 'backgroundColor' in nodelabel.attrib:
                e_color = str(nodelabel.attrib['backgroundColor'])
                #print(e_color)
            else:
                e_color = "#BCBCBC"
            #print(e_color)
        else:
            id_node = "null"
            
        for i in range(len(scene.epoch_list)):
            id_key = scene.epoch_list[i].id
            if id_node == id_key:
                scene.epoch_list[i].name = str(label_node)
                scene.epoch_list[i].epoch_color = e_color
                scene.epoch_list[i].epoch_RGB_color = hex_to_rgb(e_color)

def get_edge_target(tree, node_element):
    alledges = tree.findall('.//{http://graphml.graphdrawing.org/xmlns}edge')
    id_node = getnode_id(node_element)
    EM_us_target = "" 
    node_y_pos = 0.0
    
    for edge in alledges:
        id_node_edge_source = getnode_edge_source(edge) 
        if id_node_edge_source == id_node:
            my_continuity_node_description, node_y_pos = EM_extract_continuity(node_element)
            id_node_edge_target = getnode_edge_target(edge)
            EM_us_target = find_node_us_by_id(id_node_edge_target)
            #print("edge with id: "+ getnode_id(edge)+" with target US_node "+ id_node_edge_target+" which is the US "+ EM_us_target)
    #print("edge with id: "+ getnode_id(edge)+" with target US_node "+ id_node_edge_target+" which is the US "+ EM_us_target)
    return EM_us_target, node_y_pos

def read_edge_db(context, tree):
    alledges = tree.findall('.//{http://graphml.graphdrawing.org/xmlns}edge')
    scene = context.scene
    EM_list_clear(context, "edges_list")
    em_list_index_ema = 0

    for edge in alledges:
        #print(str(edge.attrib['id']))
        scene.edges_list.add()
        scene.edges_list[em_list_index_ema].id_node = str(edge.attrib['id'])
        scene.edges_list[em_list_index_ema].source = str(edge.attrib['source'])#getnode_edge_source(edge)
        scene.edges_list[em_list_index_ema].target = str(edge.attrib['target'])#getnode_edge_target(edge)
        #print(scene.edges_list[em_list_index_ema].id_node)
        #print(scene.edges_list[em_list_index_ema].target)
        em_list_index_ema += 1
    return

def create_derived_lists(node):
    context = bpy.context
    scene = context.scene
    prop_index = 0
    EM_list_clear(context, "em_v_properties_list")

    is_property = False

    # pass degli edges
    for edge_item in scene.edges_list:
        #print("arco id: "+edge_item.id_node)
        #controlliamo se troviamo edge che parte da lui
        if edge_item.source == node.id_node:
            # pass delle properties
            for property_item in scene.em_properties_list:
                #controlliamo se troviamo una proprietà di arrivo compatibile con l'edge
                if edge_item.target == property_item.id_node:
                   # print("trovato nodo: "+ node.name+" con proprieta: "+ property_item.name)
                    scene.em_v_properties_list.add()
                    scene.em_v_properties_list[prop_index].name = property_item.name
                    scene.em_v_properties_list[prop_index].description = property_item.description
                    scene.em_v_properties_list[prop_index].url = property_item.url
                    scene.em_v_properties_list[prop_index].id_node = property_item.id_node
                    prop_index += 1
                    is_property = True
                    #if not scene.prop_paradata_streaming_mode:
                        
    if is_property:
        if scene.prop_paradata_streaming_mode:
            #print("qui ci arrivo")
            selected_property_node = scene.em_v_properties_list[scene.em_v_properties_list_index]
            #print("il nodo che voglio inseguire: "+selected_property_node.name)
            is_combiner = create_derived_combiners_list(selected_property_node)
            if not is_combiner:
                create_derived_extractors_list(selected_property_node)
        else:
            for v_list_property in scene.em_v_properties_list:
                is_combiner = create_derived_combiners_list(v_list_property)
                if not is_combiner:
                    create_derived_extractors_list(v_list_property)                

    else:
        EM_list_clear(context, "em_v_extractors_list")
        EM_list_clear(context, "em_v_sources_list")
        EM_list_clear(context, "em_v_combiners_list")

    #print("property: "+ str(prop_index))     
    return