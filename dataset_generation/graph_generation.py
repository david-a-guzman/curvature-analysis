import pandas as pd
import networkx as nx
import sys
import os
sys.path.append('../')
from OllivierRicci import ricciCurvature
from dataset_generation.write_anchormeshes import generating_latency_matrix
from dataset_generation.write_geography_matrix import generating_gcd_matrix
from util import project_dir, start_date
import json

def graph_inference(df_residual, list_of_ids, output, edge_thresholds = range(2, 60, 2), cloud = None):
    """
    Generate a graph from the residual latency dataframe, add attributes and perform Ricci curvature calculations.

    Parameters:
    df_residual (DataFrame): DataFrame containing the latency data.
    list_of_ids (list): List of dictionaries containing node attributes like city, country, continent.
    outcome (str): Path to save the output graph files.
    inference_type (str): Type of inference to be performed ('all', 'intercontinent', 'cloud', 'cloud_inter').

    Returns:
    None
    """

    # Create output directory if it does not exist
    os.makedirs(output, exist_ok=True)

    G = nx.Graph()
    df_residual.index = df_residual.index.map(str)
    G.add_nodes_from(list(df_residual.index))
    # Setting node attributes
    nx.set_node_attributes(G, list_of_ids[0], 'city')
    nx.set_node_attributes(G, list_of_ids[1], 'country')
    nx.set_node_attributes(G, list_of_ids[2], 'continent')
    nx.set_node_attributes(G, list_of_ids[3], 'latitude')
    nx.set_node_attributes(G, list_of_ids[4], 'longitude')
    google_anchors = json.load(open(f'{project_dir}/Datasets/ProbeFiles/google_anchors.json'))
    aws_anchors = json.load(open(f'{project_dir}/Datasets/ProbeFiles/aws_anchors.json'))
    is_google = {k: 1 for k in google_anchors.keys()}
    is_aws = {k: 1 for k in aws_anchors.keys()}
    nx.set_node_attributes(G, is_aws, 'is_aws')
    nx.set_node_attributes(G, is_google, 'is_google')
    if cloud == 'aws':
        G = nx.Graph(G.subgraph(aws_anchors.keys()))
    elif cloud == 'google':
        G = nx.Graph(G.subgraph(google_anchors.keys()))
    for threshold in edge_thresholds:
        # Adding edges based on the threshold
        for t in G.nodes():
            for s in G.nodes():
                if t != s and (df_residual.at[s, t] < threshold or df_residual.at[t, s] < threshold):
                    G.add_edge(s, t)
        # Removing specific nodes that we had identified as being incorrectly labeled
        for node in ['6201', '6231']:
            if node in G.nodes():
                G.remove_node(node)
        compute_RicciCurv(G, output, threshold, cloud=cloud)

def compute_RicciCurv(G, output, threshold, cloud= None):
    """ Process all connections and save the graph. """
    print(nx.info(G))
    # print([len(c) for c in sorted(nx.connected_components(G), key=len, reverse=True)])
    G = ricciCurvature(G, alpha=0, method='OTD', verbose=False)
    if cloud:
        nx.write_graphml(G, f'{output}/{cloud}_graph_ricci_{threshold}.graphml')
    else:
        nx.write_graphml(G, f'{output}/graph_ricci_{threshold}.graphml')


