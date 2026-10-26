#!/usr/bin/env python3
"""GEMSDOE36 lane (2026-10-25 session): supervised hide-and-recover fault model.

LANE (single method paragraph): A supervised gradient-boosted pixel model trained
ONLY to separate catalogue fault pixels from off-fault background, using label-free
multi-scale lineament transforms of the 19-band GeoDAWN stack + 1 m LiDAR scarp +
radiometric externals. NO catalogue-derived feature (no distance-to-catalogue, no
SGMC prior), NO prior submission raster enters the surface. Emission is priority
Poisson-disk thinning with a B=2 (200 m) catalogue-flank exclusion; budget/spacing
chosen on a hide-and-recover holdout (whole fault segments withheld in 5 spatial
strips, 500 m train buffer, visible faults masked pixel-exactly, pooled organizer
DTI alpha=0.2 beta=0.8 R=300 m via gemsdoe36.metric).

Stages: features | e1 (canary + baselines) | e2 (OOF model + emission sweep) | e3 (final build)
"""
from __future__ import annotations
import json, sys, time, hashlib
from pathlib import Path
import numpy as np
import rasterio
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from gemsdoe36.metric import distance_weighted_tversky
from gemsdoe36.hypotheses import poisson_disk_thin_priority

SEED = 36
rng = np.random.default_rng(SEED)
DATA = ROOT / "data" / "raw"
WORK = ROOT / ".cache" / "gems_work" / "lane36"; WORK.mkdir(parents=True, exist_ok=True)
H, W = 3730, 3292
BANDS = ["mag_anom","rtp","tmi_hg","geod_2ndinv","iso_grav_anom_slope","tc","geod_shearrate",
         "geod_dilaterate","tmi_vg","deq_n100a15","iso_grav_anom_vg","det_elev","iso_grav_anom",
         "tmi","depth_to_base_surf","ieq_n100a15","cond_surf","iso_grav_anom_hg","det_elev_slope"]
KEYFIELDS = ["rtp","tmi","iso_grav_anom","det_elev","depth_to_base_surf","cond_surf"]

def log(*a): print(f"[{time.strftime('%H:%M:%S')}]", *a, flush=True)

def foot_labels():
    with rasterio.open(DATA/"sample_submission.tif") as s: foot = np.isfinite(s.read(1))
    with rasterio.open(DATA/"labels.tif") as s: lab = (s.read(1)==1) & foot
    return foot, lab

def zclip(x, foot):
    v = x[foot]; med = np.median(v); q25,q75 = np.percentile(v,[25,75])
    iqr = max(float(q75-q25), 1e-9)
    return np.clip((x-med)/(iqr/1.349), -8, 8).astype(np.float32), float(med)

def fill_med(x, foot, med=None):
    ok = foot & np.isfinite(x) & (np.abs(x) < 1e30)
    if med is None: med = float(np.median(x[ok]))
    return np.where(ok, x, med).astype(np.float32)

def gmag(x, sigma):
    gy = ndi.gaussian_filter(x, sigma, order=(1,0)); gx = ndi.gaussian_filter(x, sigma, order=(0,1))
    return np.hypot(gy, gx).astype(np.float32)

def stage_features():
    import gc
    foot, _ = foot_labels()
    NFEAT = 66
    stack = np.lib.format.open_memmap(WORK/"stack.f16.npy", mode="w+", dtype=np.float16, shape=(H,W,NFEAT))
    names = []
    def put(nm, a):
        z,_ = zclip(a, foot); stack[:,:,len(names)] = z.astype(np.float16); names.append(nm); del z; gc.collect()
    raw = {}
    with rasterio.open(DATA/"training_features.tif") as ds:
        assert ds.count==19 and (ds.height,ds.width)==(H,W)
        for i,name in enumerate(BANDS,1):
            bf = fill_med(ds.read(i).astype(np.float32), foot)
            if name in KEYFIELDS: raw[name]=bf
            put(f"raw_{name}", bf); log("band",name,len(names))
    gm1 = {}
    for f in KEYFIELDS:
        g1 = gmag(raw[f],1.0); gm1[f]=g1
        put(f"gmag1_{f}", g1); put(f"gmag3_{f}", gmag(raw[f],3.0))
        put(f"lap2_{f}", np.abs(ndi.gaussian_laplace(raw[f],2.0)).astype(np.float32))
        log("derived",f,len(names))
    for f in ["rtp","iso_grav_anom","det_elev"]:
        put(f"ridge_{f}", gm1[f]-gmag(raw[f],3.0))
    E = (gm1["rtp"]+gm1["iso_grav_anom"]+gm1["det_elev"])/3.0; del gm1; gc.collect()
    gy,gx = np.gradient(ndi.gaussian_filter(E,1.5)); del E
    s=2.0; Jxx=ndi.gaussian_filter(gx*gx,s); Jyy=ndi.gaussian_filter(gy*gy,s); Jxy=ndi.gaussian_filter(gx*gy,s)
    del gy,gx; gc.collect()
    tr=Jxx+Jyy; diff=np.sqrt(np.maximum((Jxx-Jyy)**2/4+Jxy**2,0))
    l1=tr/2+diff; l2=np.maximum(tr/2-diff,0)
    put("tensor_coh", ((l1-l2)/(l1+l2+1e-12)).astype(np.float32)); del l1,l2,tr,diff
    strike=((np.degrees(0.5*np.arctan2(2*Jxy,Jxx-Jyy))+180)%180+90)%180; del Jxx,Jyy,Jxy; gc.collect()
    put("anderson_dev", np.minimum.reduce([np.abs((strike-t+90)%180-90) for t in (15.0,140.0)]).astype(np.float32)); del strike
    for f in ["det_elev","tmi"]:
        m=ndi.gaussian_filter(raw[f],2.0); var=np.maximum(ndi.gaussian_filter(raw[f]**2,2.0)-m*m,0)
        put(f"std2_{f}", np.sqrt(var).astype(np.float32)); del m,var
    del raw; gc.collect()
    ext_specs=[("external/lidar_scarp_features_u8.tif","lidar"),("external/geodawn_rad_u8.tif","rad"),
               ("external/geodawn_extensions_u8.tif","ext")]
    for path,prefix in ext_specs:
        with rasterio.open(DATA/path) as ds:
            for i in range(1,ds.count+1):
                desc=ds.descriptions[i-1] or f"b{i}"
                bf=fill_med(ds.read(i).astype(np.float32),foot)
                put(f"{prefix}_{desc}", bf)
                if (prefix=="lidar" and desc=="step_max") or (prefix=="ext" and desc=="TMI_up150"):
                    put(f"gmag1_{prefix}_{desc}", gmag(bf,1.0))
        log("external",prefix,len(names))
    assert len(names)==NFEAT, (len(names), names)
    stack.flush()
    (WORK/"feature_names.json").write_text(json.dumps(names,indent=1))
    log("STACK", stack.shape, len(names),"features")

def load_stack():
    names=json.loads((WORK/"feature_names.json").read_text())
    return np.load(WORK/"stack.f16.npy", mmap_mode="r"), names

def folds_setup():
    foot, lab = foot_labels()
    comp, n = ndi.label(lab, structure=np.ones((3,3)))
    # 5 vertical strips by footprint column quantiles
    cols = np.where(foot.any(axis=0))[0]
    edges = [0]+[int(np.quantile(np.repeat(cols, foot.sum(axis=0)[cols]), q)) for q in (0.2,0.4,0.6,0.8)]+[W]
    cent = ndi.center_of_mass(lab, comp, range(1,n+1))
    comp_fold = np.zeros(n+1, np.int8)
    for i,(cy,cx) in enumerate(cent,1):
        comp_fold[i]=int(np.searchsorted(edges, cx, side="right")-1)
    fold_of_px = comp_fold[comp]
    np.savez_compressed(WORK/"folds.npz", foot=foot, lab=lab, comp=comp, fold_of_px=fold_of_px, edges=np.array(edges))
    log("components",n,"strip edges",edges, "withheld per fold",[int((lab&(fold_of_px==f)).sum()) for f in range(5)])
    return foot, lab, comp, fold_of_px, edges

def dti_components(pred_bool, truth_bool, valid):
    r = distance_weighted_tversky(pred_bool.astype(np.float32), truth_bool.astype(np.float32),
                                  valid_mask=valid, return_components=True)
    return r  # .true_positive .false_positive .false_negative .score

def pooled(per_fold):
    tp=sum(r.true_positive for r in per_fold); fp=sum(r.false_positive for r in per_fold); fn=sum(r.false_negative for r in per_fold)
    return tp/(tp+0.2*fp+0.8*fn+1e-8), tp, fp, fn

def score_dots(dots, foot, lab, fold_of_px, edges, visible_b2=False):
    """Hide-and-recover pooled DTI of a fixed dot set. If visible_b2, re-apply B=2 vs visible only per fold."""
    per=[]
    for f in range(5):
        truth = lab & (fold_of_px==f); visible = lab & (fold_of_px!=f)
        c0,c1 = edges[f],edges[f+1]
        sl=(slice(0,H),slice(max(0,c0-6),min(W,c1+6)))
        valid = foot[sl].copy()
        valid[:, : (c0-sl[1].start)+4] = False; valid[:, (c1-sl[1].start)-4:] = False
        d = dots[sl].copy()
        if visible_b2:
            dvis = ndi.distance_transform_edt(~visible[sl]); d &= dvis>2.0
        d &= ~visible[sl]  # mask visible faults pixel-exactly
        per.append(dti_components(d, truth[sl], valid))
    s,tp,fp,fn = pooled(per)
    return {"pooled_dti":s,"tp":tp,"fp":fp,"fn":fn,"per_fold":[r.score for r in per]}

def read_dots(path):
    with rasterio.open(path) as ds: a=ds.read(1)
    return np.nan_to_num(a,nan=0.0)>0.5

def stage_e1():
    foot, lab, comp, fold_of_px, edges = folds_setup()
    stack, names = load_stack()
    out={}
    # --- leakage canary: single-feature AUC, withheld pos vs far negatives (pooled over folds' own strips)
    from sklearn.metrics import roc_auc_score
    dcat = ndi.distance_transform_edt(~lab)
    canary={}
    neg_pool = np.argwhere(foot & (dcat>10))
    neg_idx = neg_pool[rng.choice(len(neg_pool), 60000, replace=False)]
    pos_idx = np.argwhere(lab)
    pos_s = pos_idx[rng.choice(len(pos_idx), 60000, replace=False)]
    # distance-to-visible canary (deliberate leak demo): for each pos px use dist to catalogue of OTHER folds
    leak_vals=np.empty(len(pos_s)); 
    for f in range(5):
        vis = lab & (fold_of_px!=f); dv = ndi.distance_transform_edt(~vis)
        m = fold_of_px[pos_s[:,0],pos_s[:,1]]==f; leak_vals[m]=dv[pos_s[m,0],pos_s[m,1]]
    dv_all = ndi.distance_transform_edt(~lab)
    y=np.r_[np.ones(len(pos_s)),np.zeros(len(neg_idx))]
    canary["LEAK_dist_to_visible_catalogue(neg)"] = float(roc_auc_score(y, -np.r_[leak_vals, dv_all[neg_idx[:,0],neg_idx[:,1]]]))
    aucs=[]
    for j,nm in enumerate(names):
        v=np.r_[stack[pos_s[:,0],pos_s[:,1],j], stack[neg_idx[:,0],neg_idx[:,1],j]].astype(np.float32)
        a=float(roc_auc_score(y,v)); aucs.append((nm, a if a>=0.5 else 1-a))
    aucs.sort(key=lambda t:-t[1]); canary["top_features"]=aucs[:12]; canary["max_feature_auc"]=aucs[0]
    out["canary"]=canary; log("CANARY leak AUC",canary["LEAK_dist_to_visible_catalogue(neg)"],"max feat",aucs[0])
    # --- baselines under hide-and-recover
    champ = read_dots(DATA/"registry/champion_h33-2-b2_02778.tif")
    d28 = read_dots(DATA/"scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif")
    andp = read_dots(ROOT/"docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif")
    h6 = read_dots(ROOT/"docs/downloads/GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif")
    out["champion_as_submitted"]={**score_dots(champ,foot,lab,fold_of_px,edges),"dots":int(champ.sum())}
    out["champion_analog_d28_B2visible"]={**score_dots(d28,foot,lab,fold_of_px,edges,visible_b2=True),"dots_raw":int(d28.sum())}
    out["anderson_pinn_36"]={**score_dots(andp,foot,lab,fold_of_px,edges),"dots":int(andp.sum())}
    out["h6_sgmc_prior"]={**score_dots(h6,foot,lab,fold_of_px,edges),"dots":int(h6.sum())}
    (WORK/"e1.json").write_text(json.dumps(out,indent=1,default=float))
    for k,v in out.items():
        if isinstance(v,dict) and "pooled_dti" in v: log(k, round(v["pooled_dti"],4), v.get("dots",v.get("dots_raw")))

def train_model(X,y,w):
    from sklearn.ensemble import HistGradientBoostingClassifier
    m=HistGradientBoostingClassifier(max_iter=300, learning_rate=0.08, max_leaf_nodes=63,
        min_samples_leaf=100, l2_regularization=1.0, random_state=SEED)
    m.fit(X,y,sample_weight=w); return m

def predict_grid(model, stack, foot):
    pred=np.zeros((H,W),np.float32)
    for r0 in range(0,H,256):
        blk=np.asarray(stack[r0:r0+256],dtype=np.float32).reshape(-1,stack.shape[2])
        p=model.predict_proba(blk)[:,1].reshape(-1,W)[:min(256,H-r0)]
        pred[r0:r0+p.shape[0]]=p
    pred[~foot]=0; return pred

def sample_train(stack, foot, lab, fold_of_px, f_hold=None):
    dcat = ndi.distance_transform_edt(~lab)
    if f_hold is None:
        pos_mask = lab; buf=np.zeros_like(lab)
    else:
        withheld = lab & (fold_of_px==f_hold)
        buf = ndi.distance_transform_edt(~withheld)<=5.0
        pos_mask = lab & (fold_of_px!=f_hold) & ~buf
    neg_mask = foot & (dcat>3.0) & ~buf
    pos=np.argwhere(pos_mask); neg=np.argwhere(neg_mask)
    neg=neg[rng.choice(len(neg),400000,replace=False)]
    X=np.vstack([np.asarray(stack[pos[:,0],pos[:,1]],dtype=np.float32), np.asarray(stack[neg[:,0],neg[:,1]],dtype=np.float32)])
    y=np.r_[np.ones(len(pos)),np.zeros(len(neg))].astype(np.int8)
    w=np.r_[np.full(len(pos), min(len(neg)/max(len(pos),1),20.0)), np.ones(len(neg))].astype(np.float32)
    return X,y,w,len(pos)

def emit(surface, foot, lab_visible, spacing, budget, domain=None):
    dvis=ndi.distance_transform_edt(~lab_visible)
    cand = foot & (dvis>2.0)
    if domain is not None: cand &= domain
    vals=surface[cand]
    thr=np.quantile(vals, 1-min(3*budget,max(vals.size,1))/max(vals.size,1)) if vals.size else 1.0
    cand &= surface>=thr
    dots=poisson_disk_thin_priority(cand, surface, min_dist_px=spacing, max_add=budget)
    return dots

def stage_e2():
    z=np.load(WORK/"folds.npz"); foot,lab,comp,fold_of_px,edges=z["foot"],z["lab"],z["comp"],z["fold_of_px"],list(z["edges"])
    stack,names=load_stack()
    oof=np.zeros((H,W),np.float32)
    for f in range(5):
        X,y,w,npos=sample_train(stack,foot,lab,fold_of_px,f_hold=f); log(f"fold{f} train pos={npos} X={X.shape}")
        m=train_model(X,y,w)
        c0,c1=edges[f],edges[f+1]
        sub=np.zeros((H,W),bool); sub[:,c0:c1]=True
        p=predict_grid(m,stack,foot); oof[sub&foot]=p[sub&foot]
        if f==0:
            imp=getattr(m,"feature_importances_",None)
        log(f"fold{f} predicted")
    np.save(WORK/"oof_surface.npy",oof)
    # surface quality: rank corr vs h19-5 continuous on sample
    from scipy.stats import spearmanr
    with rasterio.open(DATA/"scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") as ds:
        h195=np.nan_to_num(ds.read(1),nan=0.0)
    idx=np.argwhere(foot); s=idx[rng.choice(len(idx),200000,replace=False)]
    rho=float(spearmanr(oof[s[:,0],s[:,1]],h195[s[:,0],s[:,1]]).statistic)
    log("Spearman OOF vs h19-5 surface:",round(rho,4))
    results={"spearman_vs_h195":rho,"configs":{}}
    foot_frac=float(foot.mean())
    for spacing in (2.0,2.8):
        for budget_full in (20000,38000,55000,80000):
            per=[]; ndots=0
            for f in range(5):
                visible=lab&(fold_of_px!=f); truth=lab&(fold_of_px==f)
                c0,c1=edges[f],edges[f+1]
                domain=np.zeros((H,W),bool); domain[:,c0+4:c1-4]=True; domain&=foot
                b=int(budget_full*domain.sum()/foot.sum())
                dots=emit(oof,foot,visible,spacing,b,domain=domain)
                ndots+=int(dots.sum())
                sl=(slice(0,H),slice(max(0,c0-6),min(W,c1+6)))
                valid=foot[sl].copy(); valid[:,: (c0-sl[1].start)+4]=False; valid[:,(c1-sl[1].start)-4:]=False
                d=dots[sl] & ~visible[sl]
                per.append(dti_components(d,truth[sl],valid))
            s,tp,fp,fn=pooled(per)
            key=f"s{spacing}_b{budget_full}"
            results["configs"][key]={"pooled_dti":s,"dots":ndots,"tp":tp,"fp":fp,"fn":fn,"per_fold":[r.score for r in per]}
            log(key,round(s,4),"dots",ndots)
    (WORK/"e2.json").write_text(json.dumps(results,indent=1,default=float))

def overlap_frac(my_dots, other_dots, rad=3):
    d=ndi.distance_transform_edt(~other_dots)
    return float((d[my_dots]<=rad).mean()) if my_dots.any() else 0.0

def stage_e3(spacing, budget):
    z=np.load(WORK/"folds.npz"); foot,lab=z["foot"],z["lab"]
    stack,names=load_stack()
    X,y,w,npos=sample_train(stack,foot,lab,None,None); log("final train pos",npos)
    m=train_model(X,y,w); surf=predict_grid(m,stack,foot); np.save(WORK/"final_surface.npy",surf)
    dots=emit(surf,foot,lab,spacing,budget)
    log("final dots",int(dots.sum()))
    np.save(WORK/"final_dots.npy",dots)
    # uniqueness vs registry
    from scipy.stats import spearmanr
    with rasterio.open(DATA/"scored/gems19-h19-5-powerlaw-budget-multiline-corroborated-20260930-e27054cf-nan.tif") as ds:
        h195=np.nan_to_num(ds.read(1),nan=0.0)
    idx=np.argwhere(foot); s=idx[rng.choice(len(idx),200000,replace=False)]
    uni={"spearman_vs_h195":float(spearmanr(surf[s[:,0],s[:,1]],h195[s[:,0],s[:,1]]).statistic), "dot_overlap_le3px":{}}
    regs={"champion_h33-2-b2":DATA/"registry/champion_h33-2-b2_02778.tif",
          "d28":DATA/"scored/gems24-h25-1-dotted-h19-5-d2-8-20261002-e56ea318af89-nan.tif",
          "anderson_pinn36":ROOT/"docs/downloads/gemsdoe36-anderson-geothermal-pinn-38854-20261004T230000Z-9b9ea4e6-zeros.tif",
          "h6":ROOT/"docs/downloads/GEMS36_h6_offcatalog_network_prior_20261004T193432.021282Z_3276c04090_3c064db2.tif",
          "gems27":DATA/"scored/gems27-topo-gap-closure-t-v2-on-d1-5-20261002-5512495c6bd1-nan.tif"}
    for k,p in regs.items(): uni["dot_overlap_le3px"][k]=overlap_frac(dots, read_dots(p))
    (WORK/"e3_uniqueness.json").write_text(json.dumps(uni,indent=1,default=float)); log("UNIQUENESS",uni)

if __name__=="__main__":
    st=sys.argv[1]
    if st=="features": stage_features()
    elif st=="e1": stage_e1()
    elif st=="e2": stage_e2()
    elif st=="e3": stage_e3(float(sys.argv[2]), int(sys.argv[3]))
    else: raise SystemExit(st)
