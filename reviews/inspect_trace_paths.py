#!/usr/bin/python3
"""Approximate trace centerline paths for independent layout inspection.

Uses overlapping track envelopes, via joins and pad contacts. Pad-interior
travel is treated as zero; filled planes are not modeled. This is a diagnostic
for non-plane nets, not a continuity, signal-integrity or DRC replacement.
Run with /usr/bin/python3 from the repository root (pcbnew + networkx).
"""
import pcbnew,networkx as nx,math,collections,hashlib
from pathlib import Path
print('Board SHA256:',hashlib.sha256(Path('hardware/airnote.kicad_pcb').read_bytes()).hexdigest())
b=pcbnew.LoadBoard('hardware/airnote.kicad_pcb')
fps={f.GetReference():f for f in b.GetFootprints()}
def xy(p):return (p.x/1e6,p.y/1e6)
def key(p,l):return (round(p[0],6),round(p[1],6),l)
for net in ['+3V3','+1V1','+5V','USB_DP','USB_DM','USB_DP_ESD','USB_DM_ESD','USB_DP_MCU','USB_DM_MCU','XIN','XOUT','XTAL_OUT']:
 ts=[t for t in b.GetTracks() if t.GetNetname()==net and not isinstance(t,pcbnew.PCB_VIA)]
 vs=[t for t in b.GetTracks() if t.GetNetname()==net and isinstance(t,pcbnew.PCB_VIA)]
 pads=[(f.GetReference(),p) for f in b.GetFootprints() for p in f.Pads() if p.GetNetname()==net]
 nodes={key(xy(p),t.GetLayer()) for t in ts for p in [t.GetStart(),t.GetEnd()]}
 radii=collections.defaultdict(float)
 for t in ts:
  for p in [t.GetStart(),t.GetEnd()]:radii[key(xy(p),t.GetLayer())]=max(radii[key(xy(p),t.GetLayer())],t.GetWidth()/2e6)
 for v in vs:
  for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
   n=key(xy(v.GetPosition()),l);nodes.add(n);radii[n]=v.GetWidth(l)/2e6
 g=nx.Graph();g.add_nodes_from(nodes)
 for t in ts:
  a,bp=xy(t.GetStart()),xy(t.GetEnd());d=(bp[0]-a[0],bp[1]-a[1]);length=math.hypot(*d)
  hit=[]
  for n in nodes:
   if n[2]!=t.GetLayer():continue
   rel=(n[0]-a[0],n[1]-a[1]);u=(rel[0]*d[0]+rel[1]*d[1])/(length*length)
   u=max(0,min(1,u));point=(a[0]+u*d[0],a[1]+u*d[1])
   distance=math.dist(n[:2],point)
   if distance<=t.GetWidth()/2e6+radii[n]+1e-5:
    projected=key(point,t.GetLayer());hit.append((u,projected))
    if n!=projected:g.add_edge(n,projected,weight=distance)
  hit.sort()
  for (_,n1),(_,n2) in zip(hit,hit[1:]):g.add_edge(n1,n2,weight=math.dist(n1[:2],n2[:2]))
 for v in vs:g.add_edge(key(xy(v.GetPosition()),pcbnew.F_Cu),key(xy(v.GetPosition()),pcbnew.B_Cu),weight=0)
 for ref,p in pads:
  pn=(ref,p.GetNumber())
  for n in nodes:
   if p.IsOnLayer(n[2]) and p.HitTest(pcbnew.VECTOR2I(round(n[0]*1e6),round(n[1]*1e6))):g.add_edge(pn,n,weight=0)
 if net in ['+3V3','+1V1','+5V']:
  for ref,p in pads:
   if ref not in ['U1','U2','U3','U4','U5']:continue
   pn=(ref,p.GetNumber())
   if pn not in g:print(net,pn,'NO GRAPH');continue
   distances=nx.single_source_dijkstra_path_length(g,pn,weight='weight')
   targets=sorted((round(distances[(r,pad.GetNumber())],2),r,fps[r].GetValue()) for r,pad in pads if r.startswith('C') and (r,pad.GetNumber()) in distances)
   print(net,pn,targets[:4])
 else:
  allpads=[(ref,p.GetNumber()) for ref,p in pads]
  print(net,'tracks_total',round(sum(t.GetLength()/1e6 for t in ts),2),'vias',len(vs),'pad_endpoints',allpads)
  endpoints={
   'USB_DP':[(('J1','A6'),('D1','1')),(('J1','B6'),('D1','1'))],
   'USB_DM':[(('J1','A7'),('D1','3')),(('J1','B7'),('D1','3'))],
   'USB_DP_ESD':[(('D1','6'),('R8','1'))],
   'USB_DM_ESD':[(('D1','4'),('R9','1'))],
   'USB_DP_MCU':[(('R8','2'),('U1','47'))],
   'USB_DM_MCU':[(('R9','2'),('U1','46'))],
   'XIN':[(('U1','20'),('Y1','1')),(('C1','1'),('Y1','1'))],
   'XOUT':[(('U1','21'),('R1','1'))],
   'XTAL_OUT':[(('R1','2'),('Y1','3')),(('C2','1'),('Y1','3'))],
  }
  for a,z in endpoints[net]:
   if a in g and z in g and nx.has_path(g,a,z):
    print('  endpoint path',a,z,round(nx.shortest_path_length(g,a,z,weight='weight'),2),'mm')
   else:print('  endpoint path',a,z,'not represented by diagnostic graph')
