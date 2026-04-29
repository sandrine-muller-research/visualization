clear;
close all;

%% load data:
pp = 'C:\Users\Sandr\Documents\code\GitHub\visualization\translator\results_5014cf36-fc74-40ad-a811-c26c6a747ee0_KG.csv';
[input_file_path,input_file_name,input_file_ext] = fileparts(pp);
fixed_node_normalized = 'MONDO:0005148';
result = readtable(pp, 'Delimiter', ',');

%% create graph
node_all = [result.subject;result.object];
node_names_all = [result.subjectName;result.objectName];
node_catgories_all = [result.subject_category;result.object_category];
[nodes,i_nodes_unique] = unique(node_all);

[ii,i1] = ismember(result.subject,nodes);
[ii,i2] = ismember(result.object,nodes);

S = full(sparse(i1,i2,ones(length(i1),1)));
S = double((S + S')>=1);

nodes_attributes = [node_all(i_nodes_unique) node_names_all(i_nodes_unique) node_catgories_all(i_nodes_unique)];

T_attributes = table(nodes_attributes);
writetable(T_attributes,[input_file_name '_node_attributes.txt'],'delimiter','\t');

%filter only direct predicates:
predicates_to_keep ={'biolink:affects','biolink:colocalizes_with','biolink:derives_from','biolink:directly_physically_interacts_with','biolink:disrupts','biolink:exacerbates','biolink:has_part','biolink:physically_interacts_with','biolink:subclass_of','biolink:same_as'};
% faire un filtre basé sur les categories : ici sélectionner molecular

ii = ismember(result.predicate,predicates_to_keep);
ii1 = ~ismember(result.subject,fixed_node_normalized);
ii2 = ~ismember(result.object,fixed_node_normalized);
i_to_keep = logical(ii.* ii1 .* ii2);

S_to_keep = full(sparse(i1(i_to_keep),i2(i_to_keep),ones(sum(i_to_keep),1)));
S_to_keep = double((S_to_keep + S_to_keep')>=1);
i_nodes_filtered = sum(S_to_keep)~=0;
S_to_keep = S_to_keep(i_nodes_filtered,i_nodes_filtered);
nodes_attributes_filtered = nodes_attributes(i_nodes_filtered,:);

figure;spy(S);

restoredefaultpath; 
rehash toolboxcache;
g = graph(sparse(S_to_keep));
% compute distances from laplacian:
distances = get_distances_from_laplacian(g);

% 
addpath(genpath("C:\Users\Sandr\Documents\code\MATLAB\from_others\umapFileExchange1-5-1"));


[reduction, umap, clusterIdentifiers, extras]=run_umap(real(distances));

figure;
gscatter(reduction(:,1),reduction(:,2),clusterIdentifiers);

clusterIdentifiers = clusterIdentifiers';
T = table(nodes_attributes_filtered,clusterIdentifiers);

writetable(T,[input_file_name '_node_clusters.txt'],'delimiter','\t');
save('umap.mat','reduction','clusterIdentifiers','umap');

% function l = laplacian(g)
%     deg = degree(g);
%     l = deg-G;
% end

function distances = get_distances_from_laplacian(G)
    % Compute the Laplacian matrix
    L = full(laplacian(G));
    
    % Calculate the Moore-Penrose pseudoinverse
    L_pinv = pinv(L);
    
    % Get the number of nodes
    n = size(G.Nodes,1);
    
    % Compute distances
    distances = zeros(n);
    L_pinv_ii = repmat(diag(L_pinv),1,size(L_pinv,2));
    L_pinv_jj = repmat(diag(L_pinv)',size(L_pinv,2),1);
    
    distances = L_pinv_ii + L_pinv_jj - 2*L_pinv;
%     for i = 1:n
%         for j = i+1:n
%             distances(i,j) = L_pinv(i,i) + L_pinv(j,j) - 2*L_pinv(i,j);
%             distances(j,i) = distances(i,j);  % Symmetric
%         end
%     end
    
    % Take the square root
    distances = sqrt(distances);
end
