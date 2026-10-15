#!/usr/bin/env python3
"""Compare two chezmoi source trees by *target* path (attribute prefixes stripped).

Usage: python3 -I compare-trees.py <boco-source-dir> <personal-source-dir> <out.json>
  e.g. python3 -I docs/boco-merge/compare-trees.py ~/Source/chezmoi-boco/home . /tmp/cmp.json
Prints counts; the JSON has only_b / both / only_p lists plus name maps.
"""
import os,re,sys,collections
PFX=['private_','executable_','readonly_','empty_','exact_','create_','modify_','symlink_','remove_','encrypted_','once_','onchange_','before_','after_','literal_']
def norm(rel):
    out=[]
    for part in rel.split('/'):
        orig=part
        # run scripts keep their name (attrs stripped)
        if part.startswith('run_'):
            part=re.sub(r'^run_((once|onchange)_)?((before|after)_)?','run:',part)
        else:
            changed=True
            while changed:
                changed=False
                for p in PFX:
                    if part.startswith(p): part=part[len(p):]; changed=True
            if part.startswith('dot_'): part='.'+part[4:]
        if part.endswith('.tmpl'): part=part[:-5]
        out.append(part)
    return '/'.join(out)
def walk(root):
    d={}
    for dp,dn,fn in os.walk(root):
        dn[:]=[x for x in dn if x!='.git']
        for f in fn:
            full=os.path.join(dp,f); rel=os.path.relpath(full,root)
            d[norm(rel)]=rel
    return d
b=walk(sys.argv[1]); p=walk(sys.argv[2])
only_b=sorted(set(b)-set(p)); both=sorted(set(b)&set(p)); only_p=sorted(set(p)-set(b))
print('boco files',len(b),'| personal',len(p),'| only-boco',len(only_b),'| both',len(both),'| only-personal',len(only_p))
def top(paths,depth=2):
    c=collections.Counter('/'.join(x.split('/')[:depth]) for x in paths); return c
import json
json.dump({'only_b':only_b,'both':both,'only_p':only_p,'b':b,'p':p},open(sys.argv[3],'w'))
