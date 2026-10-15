"""Scene generator: Waldo in different poses and occlusions inside a crowd, with exact ground truth.

Ground truth `gt` = bounding box of Waldo's *visible* pixels; `full` = his full-body box (incl. hidden parts).
"""
import pathlib, random
from PIL import Image, ImageDraw
from .draw import person, decoy, TARGET, COLS

RED, WHITE = (200,20,30), (255,255,255)

def sprite(pose, s=8):
    """Draw target on transparent canvas in a pose. Returns RGBA cropped."""
    im = Image.new("RGBA", (40*s, 70*s), (0,0,0,0)); d = ImageDraw.Draw(im)
    x, y = 8*s, 10*s; cx = x+10*s; skin = TARGET["skin"]; pants = TARGET["pants"]
    if pose in ("standard","arms_up","wave","stride","back","sitting"):
        kw = dict(TARGET)
        if pose == "back": kw["glasses"] = False
        person(d, x, y, s, **kw)
        if pose == "back":  # cover face: hair instead of eyes
            d.chord([cx-6*s, y+3*s, cx+6*s, y+16*s], 0, 360, fill=(90,60,20)); d.rectangle([cx-6.5*s,y+6*s,cx+6.5*s,y+8*s], fill=WHITE)
            d.chord([cx-6.5*s, y+1*s, cx+6.5*s, y+13*s], 180, 360, fill=RED); d.rectangle([cx-6.5*s,y+6*s,cx+6.5*s,y+8*s], fill=WHITE); d.ellipse([cx-2*s,y-1.5*s,cx+2*s,y+2.5*s], fill=WHITE)
        if pose in ("arms_up","wave"):
            sides = [1] if pose == "wave" else [-1, 1]
            for sd in sides:
                ax = cx + sd*10.5*s
                d.rectangle([min(ax-1.5*s, ax+1.5*s), y+17*s, ax+1.5*s, y+30*s], fill=(0,0,0,0))
                d.rectangle([ax-1.5*s, y+2*s, ax+1.5*s, y+18*s], fill=skin)
        if pose == "stride":
            d.rectangle([cx-7*s, y+35*s, cx+7*s, y+53*s], fill=(0,0,0,0))
            d.polygon([(cx-6*s,y+34*s),(cx-1*s,y+34*s),(cx-8*s,y+52*s),(cx-13*s,y+52*s)], fill=pants)
            d.polygon([(cx+1*s,y+34*s),(cx+6*s,y+34*s),(cx+13*s,y+52*s),(cx+8*s,y+52*s)], fill=pants)
        if pose == "sitting":
            d.rectangle([cx-7*s, y+35*s, cx+7*s, y+53*s], fill=(0,0,0,0))
            d.rectangle([cx-6*s, y+33*s, cx+14*s, y+39*s], fill=pants)  # thighs forward
            d.rectangle([cx+9*s, y+38*s, cx+14*s, y+48*s], fill=pants)   # shins down
            d.rectangle([cx-9*s, y+39*s, cx+16*s, y+42*s], fill=(120,80,40)) # bench seat
            d.rectangle([cx-8*s, y+42*s, cx-6*s, y+50*s], fill=(90,60,30)); d.rectangle([cx+13*s, y+42*s, cx+15*s, y+50*s], fill=(90,60,30))
    else:
        person(d, x, y, s, **TARGET)
    return im.crop(im.getbbox())

def make_target(pose, scale):
    base = {"mirror_stride":"stride","mirror_wave":"wave","tilt_left":"standard","tilt_right":"standard","lying":"standard",
            "small":"standard","large":"standard","upside_down":"standard"}.get(pose, pose)
    sp = sprite(base)
    if pose.startswith("mirror"): sp = sp.transpose(Image.FLIP_LEFT_RIGHT)
    rot = {"tilt_left":25,"tilt_right":-30,"lying":90,"upside_down":180}.get(pose, 0)
    if rot: sp = sp.rotate(rot, expand=True, resample=Image.BICUBIC)
    k = scale/8; return sp.resize((max(4,round(sp.width*k)), max(4,round(sp.height*k))), Image.LANCZOS)

def scene(out_dir, name, pose="standard", occ=None, n=60, ndec=0, s=2.8, seed=0, tsc=None):
    random.seed(seed); Wd, Hd = 1400, 1000
    im = Image.new("RGB", (Wd, Hd), (120,170,90)); d = ImageDraw.Draw(im)
    mask = Image.new("L", (Wd, Hd), 0); md = ImageDraw.Draw(mask)
    for _ in range(15):
        x, y = random.randint(0,Wd), random.randint(0,Hd); d.ellipse([x,y,x+random.randint(60,200),y+random.randint(30,120)], fill=random.choice([(100,150,80),(190,170,120),(90,140,190)]))
    tscale = {"small":1.5*s/2.8*1.0, "large":5.5}.get(pose, s)
    if pose == "small": tscale = 1.5
    if tsc: tscale = tsc
    sp = make_target(pose, tscale)
    if occ == "edge_cut":
        side = random.choice(["left","right","bottom"])
        tx = -sp.width//2 if side=="left" else Wd-sp.width//2 if side=="right" else random.randint(100, Wd-200)
        ty = Hd-sp.height//2 if side=="bottom" else random.randint(100, Hd-sp.height-100)
    else:
        tx, ty = random.randint(80, Wd-sp.width-80), random.randint(80, Hd-sp.height-80)
    tb = (tx, ty, tx+sp.width, ty+sp.height)
    def overlaps(b): return not (b[2] < tb[0]-6 or b[0] > tb[2]+6 or b[3] < tb[1]-6 or b[1] > tb[3]+6)
    kinds = ["normal"]*n + ["decoy"]*ndec; items = []
    for kind in kinds:
        for _ in range(50):
            sc = s*random.uniform(0.85,1.15); x, y = random.uniform(0, Wd-24*sc), random.uniform(0, Hd-54*sc)
            if not overlaps((x-12*sc, y-2*sc, x+24*sc, y+53*sc)): break
        items.append((y, x, sc, kind))
    items.sort()
    for y, x, sc, kind in items:
        kw = decoy() if kind=="decoy" else dict(shirt="solid", shirt_c=random.choice(COLS), hat=random.choice([None,None,"cap"]), glasses=random.random()<.2)
        person(d, x, y, sc, **kw)
    im.paste(sp, (tx, ty), sp); mask.paste(255, (tx, ty), sp.split()[3])
    full = mask.getbbox(); fullpx = sum(1 for v in mask.getdata() if v) if occ else None
    w, h = sp.width, sp.height
    def cover(box, kind):
        if kind == "bush":
            d.rounded_rectangle(box, radius=12, fill=(40,110,40)); 
            for _ in range(10):
                px_, py_ = random.uniform(box[0],box[2]), random.uniform(box[1],box[3]); d.ellipse([px_-8,py_-8,px_+8,py_+8], fill=(30,90,30))
        elif kind == "tree":
            d.rectangle(box, fill=(110,70,35)); d.line([(box[0]+4,box[1]),(box[0]+4,box[3])], fill=(80,50,20), width=3)
        elif kind == "wall":
            d.rectangle(box, fill=(170,150,130)); 
            for yy in range(int(box[1]), int(box[3]), 14): d.line([(box[0],yy),(box[2],yy)], fill=(130,110,95), width=2)
        md.rectangle(box, fill=0)
    if occ in ("bottom25","bottom50","bottom75"):
        f = int(occ[6:])/100; cover([tx-15, ty+h*(1-f), tx+w+15, ty+h+12], random.choice(["bush","wall"]))
    elif occ == "side50":
        sd = random.choice([0,1]); cover([tx-6 if sd==0 else tx+w*0.5, ty-10, tx+w*0.5 if sd==0 else tx+w+6, ty+h+10] if True else None, "tree")
        # tree crown
        d.ellipse([tx+w*(0.25 if sd==0 else 0.75)-60, ty-110, tx+w*(0.25 if sd==0 else 0.75)+60, ty-5], fill=(40,120,50))
    elif occ == "head_only":
        cover([tx-20, ty+h*0.30, tx+w+20, ty+h+15], "wall")
    elif occ == "behind_person":
        sc = s*1.25; px_ = tx + w*0.15 - 12*sc + 10*sc; py_ = ty + h*0.22
        person(d, px_, py_, sc, shirt="solid", shirt_c=(30,150,60), hat="cap")
        # mask the occluding person's silhouette
        sil = Image.new("RGBA", (Wd,Hd), (0,0,0,0)); person(ImageDraw.Draw(sil), px_, py_, sc, shirt="solid", shirt_c=(1,1,1), hat="cap")
        mask.paste(0, (0,0), sil.split()[3])
    vis = mask.getbbox(); vispx = sum(1 for v in mask.getdata() if v)
    occfrac = round(1 - vispx/fullpx, 2) if occ and occ!="edge_cut" else None
    if occ == "edge_cut":
        inframe = sum(1 for v in mask.getdata() if v); occfrac = round(1 - inframe / (sp.split()[3].point(lambda v: 255 if v else 0).histogram()[255]), 2)
    im.save(pathlib.Path(out_dir)/f"{name}.png")
    return dict(gt=list(vis), full=list(tb), pose=pose, occ=occ or "none", occ_frac=occfrac, n=n, ndec=ndec, scale=tscale)

