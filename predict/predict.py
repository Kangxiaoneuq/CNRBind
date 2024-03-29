import os
import sys
import copy
import pickle
import warnings 
import pandas as pd
import numpy as np
import networkx as nx
from sklearn import metrics
from scipy.spatial.distance import pdist
from sklearn.metrics import matthews_corrcoef
from sklearn.ensemble import RandomForestClassifier
warnings.filterwarnings('ignore')

in_file = sys.argv[1]           
name = []#########A list for all RNA name
sequence = []#########A list for all RNA sequence
label_ = []#########A list for each RNA's label
with open('..\\data_cashe\\'+in_file+'.txt', 'r') as f:
    lines = f.readlines()
for i in range(len(lines)):
    if i % 3 == 0:
        name.append(lines[i][1:-1])
    if i % 3 == 1:
        sequence.append(lines[i][:-1])
    if i % 3 == 2:
        label_.append(lines[i][:-1])
label = [int(i) for i in ''.join(label_)]######### All RNA's label

def Kmers_funct(seq, size): 
    return [seq[x:x+size] for x in range(len(seq) - size + 1)]

seq_len = [len(seq) for seq in sequence]#A list for all RNA length

one_mers = [Kmers_funct(seq, size=1) for seq in sequence]
all_residues = [residue for sublist in one_mers for residue in sublist]#A long list for all residues
        
Name = [name[i] for i in range(len(sequence)) for _ in range(len(sequence[i]))]
########################Start building nucleotide information-based feature vector

########################site location coefficient (SL)
sl = []
for i in range(len(sequence)):
    one = Kmers_funct(sequence[i],1)
    for j in range(len(one)):
        sl.append((j+1)/len(one))
        
########################nucleotide position-specific coefficient (NPS)     
nps = []
for i in range(len(sequence)):
    if len(sequence[i])%2 == 1:
        for j in range(int((len(sequence[i])+1)/2),0,-1):
            nps.append(j/((len(sequence[i])+1)/2))
        for j in range(2,int((len(sequence[i])+3)/2)):
            nps.append(j/((len(sequence[i])+1)/2))
    else:
        for j in range(int(len(sequence[i])/2),0,-1):
            nps.append(j/(len(sequence[i])/2))
        for j in range(1,int((len(sequence[i])+2)/2)):
            nps.append(j/(len(sequence[i])/2))
            
########################density (DST)
dst=[]
for i in range(len(sequence)):
    for j in range(len(sequence[i])):
        a=sequence[i][:j+1]
        dst.append(a.count(a[j])/(j+1))

########################frequency of occurrence (Fre)
fre = []
for i in range(len(sequence)):
    one = Kmers_funct(sequence[i],1)
    for j in range(len(one)):
        fre.append(one.count(one[j])/len(one))

#accessible surface area (ASA)
ASA_path = "..\\ASA\\"###### location of ASA files
ASA = []
for n in range(len(name)):    
    for line in open(ASA_path + name[n] +'.txt'):
        list = line.split()
        ASA.append(float(list[2]))

################EIIP+CB+MM+pKa+RFHC+CS+BE+BER (See the RNA.xlsx file for details.)
ori1 = pd.read_excel(r'RNA.xlsx')
nuc = ori1.iloc[:, 0]
info = ori1.set_index('nuc').T.to_dict('list')
iii = [info.get(residue) for residue in all_residues]
df1 = pd.DataFrame(iii)

############################NDC and NDS
path = "..\\pdb\\"###### location of PDB files
df_empty = pd.DataFrame()
NDS, NDC, COSS, COSC, CHEBS, CHEBC = [], [], [], [], [], []

for n in range(len(name)):
    x1, y1, z1 = [], [], []
    with open(os.path.join(path, name[n] + '.pdb')) as file:
        lines = file.readlines()
        for line in lines:
            parts = line.split()
            if parts[0] == 'ATOM' and parts[2] == "C1'":
                x1.append(float(parts[6]))
                y1.append(float(parts[7]))
                z1.append(float(parts[8]))
    center = np.array([np.mean(x1), np.mean(y1), np.mean(z1)])
    for i in range(len(x1)):
        nds = [np.linalg.norm(np.array([x1[i], y1[i], z1[i]]) - np.array([x1[j], y1[j], z1[j]])) for j in range(len(x1)) if i != j]
        coss = [np.dot(np.array([x1[i], y1[i], z1[i]]), np.array([x1[j], y1[j], z1[j]])) / (np.linalg.norm(np.array([x1[i], y1[i], z1[i]])) * np.linalg.norm(np.array([x1[j], y1[j], z1[j]]))) for j in range(len(x1)) if i != j]
        chebs = [np.abs(np.array([x1[i], y1[i], z1[i]]) - np.array([x1[j], y1[j], z1[j]])).max() for j in range(len(x1)) if i != j]
        NDS.append(sum(nds) / len(x1))
        COSS.append(sum(coss) / len(x1))
        CHEBS.append(sum(chebs) / len(x1))
        point = np.array([x1[i], y1[i], z1[i]])
        NDC.append(np.linalg.norm(point - center))
        COSC.append(np.dot(point, center) / (np.linalg.norm(point) * np.linalg.norm(center)))
        CHEBC.append(np.abs(point - center).max())

########################################Summarize
nuc_inf_vec = {'ASA':ASA,'sl':sl,'dst':dst,'fre':fre,'nps':nps,'BE1':df1.iloc[:,11],'BE2':df1.iloc[:,12],
               'BE3':df1.iloc[:,13],'BE4':df1.iloc[:,14],'BER1':df1.iloc[:,15],'BER2':df1.iloc[:,16],
               'BER3':df1.iloc[:,17],'BER4':df1.iloc[:,18],'RFHC1':df1.iloc[:,4],'RFHC2':df1.iloc[:,5],
               'RFHC3':df1.iloc[:,6],'CS1':df1.iloc[:,7],'CS2':df1.iloc[:,8],'CS3':df1.iloc[:,9],
               'CS4':df1.iloc[:,10],'CB':df1.iloc[:,1],'EIIP':df1.iloc[:,0],'pKa':df1.iloc[:,3],
               'MM':df1.iloc[:,2],'NDS':NDS,'NDC':NDC,'COSS':COSS,'COSC':COSC,'CHEBS':CHEBS,'CHEBC':CHEBC,
               }
df_nuc_inf = pd.DataFrame(nuc_inf_vec)

######################################Construct complex networks
df_empty = pd.DataFrame()

for n in range(len(name)):    
    x = []
    y = []
    z = []
    NO_aminoacid = []
    for line in open(path + name[n] +'.pdb'):
        list = line.split()
        if list[0] == 'ATOM':
            NO_aminoacid.append(list[5])
            x.append(float(list[6]))
            y.append(float(list[7]))
            z.append(float(list[8]))
    number_of_atom = len(x)
    number_of_aminoacid = 1
    Rev_NO_aminoacid = [1]*number_of_atom
    for i in range(2,len(x)):
        if NO_aminoacid[i]!=NO_aminoacid[i-1]:
            number_of_aminoacid = number_of_aminoacid +1
            for j in range(i,len(x)):
                Rev_NO_aminoacid[j] = number_of_aminoacid
            
    contact = np.zeros((number_of_aminoacid, number_of_aminoacid)).astype('int64')
    for i in range(len(x)):
        for j in range(len(x)):
            if abs(Rev_NO_aminoacid[i]-Rev_NO_aminoacid[j]) > 1:
                a=[x[i],y[i],z[i]]
                b=[x[j],y[j],z[j]]
                X=np.vstack([a,b]) 
                d_ij = pdist(X)
                if d_ij <= 8 :
                    contact[Rev_NO_aminoacid[i]-1][Rev_NO_aminoacid[j]-1] = 1
    G=nx.Graph(contact)
#degree
    degree = []
    degree.extend(nx.degree_centrality(G).values())
#closeness
    closeness = []
    closeness.extend(nx.closeness_centrality(G).values())
#betweenness
    betweenness = []
    betweenness.extend(nx.betweenness_centrality(G).values())

    son_of_site = [[j + 1 for j in range(len(contact)) if contact[i][j] == 1] for i in range(len(contact))]
    
#degree & closeness & betweenness of adjacent node
    a1 = [[degree[site - 1] for site in sublist] for sublist in son_of_site]
    a2 = [[closeness[site - 1] for site in sublist] for sublist in son_of_site]
    a3 = [[betweenness[site - 1] for site in sublist] for sublist in son_of_site]

    info_ = []
    for j in range(len(Name)):
        if Name[j] == name[n]: 
            info_.append(df_nuc_inf.iloc[j,:])
    info = pd.DataFrame(info_)
    info.reset_index(drop = True,inplace = True)
    
    info2 = []
    for i in range(len(son_of_site)):
        info1 = [info.loc[son_of_site[i][j]-1] for j in range(len(son_of_site[i]))]
        info2.append(info1)
    
    info41 = []
    info42 = []
    info43 = []
    for i in range(len(info2)):
        info31 = []
        info32 = []
        info33 = []
        for j in range(len(info2[i])):
            for k in range(len(info2[i][j])):
                info31.append(info2[i][j][k] * a1[i][j])
                info32.append(info2[i][j][k] * a2[i][j])
                info33.append(info2[i][j][k] * a3[i][j])
        info41.append(info31)
        info42.append(info32)
        info43.append(info33)
    
    info_DG = []
    info_CL = []
    info_BC = []
    for i in range(len(info41)):
        x1 = np.array(info41[i])
        x2 = np.array(info42[i])
        x3 = np.array(info43[i])
        x = int(len(x1)/info.columns.size)
        info_DG.append(np.sum(np.reshape(x1, (x,info.columns.size)), axis=0))
        info_CL.append(np.sum(np.reshape(x2, (x,info.columns.size)), axis=0))
        info_BC.append(np.sum(np.reshape(x3, (x,info.columns.size)), axis=0))
   
    e=np.hstack((info_DG,info_CL,info_BC))
    df_e = pd.DataFrame(e)
    df_empty = pd.concat([df_empty,df_e],ignore_index=True)

########################################normalized to the range of [0,1]
seq_len_sum = [sum(seq_len[:i+1]) if i > 0 else seq_len[i] for i in range(len(seq_len))]
seq_len_sum.insert(0, 0)

for i in range(len(seq_len)):
    df = df_empty.iloc[seq_len_sum[i]:seq_len_sum[i+1], :]
    df = (df - df.min()) / (df.max() - df.min())
    df_empty.iloc[seq_len_sum[i]:seq_len_sum[i+1], :] = df

#######################################sliding window
def stack(ww):
    def window(data, w):
        def yilie(array):
            return [element for sublist in array for element in sublist]
        data_up = data
        for i in range(1, 11):
            data_up = np.row_stack((data[i], data_up))
        data_down = data_up
        for i in range(len(data) - 2, len(data) - 12, -1):
             data_down = np.row_stack((data_down, data[i]))
        win = []
        for i in range(len(data)):
            win.append(yilie(data_down[10 + i - w: 11 + i + w, :]))
        return pd.DataFrame(win)
    empty = pd.DataFrame(data=None,columns=range((2*ww+1)*len(df_empty.iloc[0])),index=range(len(df_empty)))
    for i in range(len(seq_len)):
        df = np.array(df_empty.iloc[seq_len_sum[i]:seq_len_sum[i+1],:])
        empty.iloc[seq_len_sum[i]:seq_len_sum[i+1],:] = window(df,ww)
    empty.fillna(0, inplace=True)
    return empty

########################################predict
with open('CNRBind.pkl', 'rb') as f:
    model = pickle.load(f)
    
test_X = stack(5)
resample_pred = model.predict(np.array(test_X))
y_score = model.predict_proba(np.array(test_X))[:,1]
print('Pre:', round(metrics.precision_score(label, resample_pred), 4))
print('Sn:', round(metrics.recall_score(label, resample_pred), 4))
print('AUC:', round(metrics.roc_auc_score(label, y_score), 4))
print('MCC:', round(matthews_corrcoef(label, resample_pred), 4))