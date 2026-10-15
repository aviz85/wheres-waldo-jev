"""Procedural cartoon people: crowd members, striped look-alike decoys, and Waldo (the target)."""
import random
from PIL import Image, ImageDraw

SKIN = [(241,194,155),(224,172,105),(198,134,66),(141,85,36),(255,219,172)]
COLS = [(40,90,200),(30,150,60),(230,180,30),(120,60,160),(240,120,30),(60,60,60),(0,150,160),(200,40,40),(250,250,250),(150,100,60)]

def person(d, x, y, s, shirt="solid", shirt_c=(40,90,200), hat=None, glasses=False, stripe_c=((200,20,30),(255,255,255)), pants=(50,60,140), skin=None):
    """x,y = top-left; s = scale (person ~ 20s wide, 52s tall). returns bbox"""
    skin = skin or random.choice(SKIN)
    cx = x + 10*s
    # legs
    d.rectangle([cx-6*s, y+34*s, cx-1*s, y+52*s], fill=pants); d.rectangle([cx+1*s, y+34*s, cx+6*s, y+52*s], fill=pants)
    # torso
    tb = [cx-9*s, y+16*s, cx+9*s, y+35*s]
    if shirt == "hstripe":
        n = 0; yy = tb[1]
        while yy < tb[3]:
            d.rectangle([tb[0], yy, tb[2], min(tb[3], yy+2.5*s)], fill=stripe_c[n%2]); yy += 2.5*s; n += 1
    elif shirt == "vstripe":
        n = 0; xx = tb[0]
        while xx < tb[2]:
            d.rectangle([xx, tb[1], min(tb[2], xx+2.5*s), tb[3]], fill=stripe_c[n%2]); xx += 2.5*s; n += 1
    else: d.rectangle(tb, fill=shirt_c)
    d.rectangle([cx-12*s, y+17*s, cx-9*s, y+30*s], fill=skin); d.rectangle([cx+9*s, y+17*s, cx+12*s, y+30*s], fill=skin)
    # head
    d.ellipse([cx-6*s, y+3*s, cx+6*s, y+16*s], fill=skin)
    if hat == "striped_beanie":
        d.chord([cx-6.5*s, y+1*s, cx+6.5*s, y+13*s], 180, 360, fill=(200,20,30)); d.rectangle([cx-6.5*s, y+6*s, cx+6.5*s, y+8*s], fill=(255,255,255))
        d.ellipse([cx-2*s, y-1.5*s, cx+2*s, y+2.5*s], fill=(255,255,255))
    elif hat == "red_beanie":
        d.chord([cx-6.5*s, y+1*s, cx+6.5*s, y+13*s], 180, 360, fill=(200,20,30))
    elif hat == "cap":
        d.chord([cx-6.5*s, y+1*s, cx+6.5*s, y+13*s], 180, 360, fill=random.choice(COLS)); d.rectangle([cx, y+6*s, cx+9*s, y+7.5*s], fill=(40,40,40))
    else:
        d.chord([cx-6.2*s, y+2*s, cx+6.2*s, y+12*s], 180, 360, fill=random.choice([(40,25,10),(90,60,20),(200,170,90),(20,20,20)]))
    if glasses:
        r = 2.2*s; e1 = (cx-2.8*s, y+10*s); e2 = (cx+2.8*s, y+10*s)
        for ex, ey in (e1, e2): d.ellipse([ex-r, ey-r, ex+r, ey+r], outline=(0,0,0), width=max(1, int(0.6*s)))
    else:
        d.ellipse([cx-3.3*s, y+9.5*s, cx-2.3*s, y+10.5*s], fill=(0,0,0)); d.ellipse([cx+2.3*s, y+9.5*s, cx+3.3*s, y+10.5*s], fill=(0,0,0))
    return [cx-12*s, y-1.5*s, cx+12*s, y+52*s]

TARGET = dict(shirt="hstripe", hat="striped_beanie", glasses=True, pants=(40,70,170), skin=(241,194,155))
def decoy():
    k = random.choice(["stripe_noglass", "vstripe", "redblack", "beanie_only", "stripe_capglass", "pinkstripe"])
    if k == "stripe_noglass": return dict(shirt="hstripe", hat=random.choice([None,"cap"]))
    if k == "vstripe": return dict(shirt="vstripe", hat="striped_beanie", glasses=True)
    if k == "redblack": return dict(shirt="hstripe", stripe_c=((200,20,30),(20,20,20)), hat="red_beanie", glasses=True)
    if k == "beanie_only": return dict(shirt="solid", shirt_c=random.choice(COLS), hat="striped_beanie", glasses=random.random()<.5)
    if k == "stripe_capglass": return dict(shirt="hstripe", hat="cap", glasses=True)
    return dict(shirt="hstripe", stripe_c=((240,120,170),(255,255,255)), hat="striped_beanie", glasses=True)

def reference(out_path):
    """Render the single reference image of Waldo that Jev is given."""
    im = Image.new("RGB", (400, 400), (235,240,230)); d = ImageDraw.Draw(im)
    random.seed(0); person(d, 110, 40, 6.5, **TARGET); im.save(out_path)

