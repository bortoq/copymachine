import sys
sys.path.insert(0,'/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower')
sys.dont_write_bytecode=True
import l3ctext, l1text, text, l3, common
from common import run
def chain_image(src):
    l1, err = l3ctext.language1(src.encode('latin-1'))
    assert err is None, err
    img, err = l1text.encode(l1)
    assert err is None, err
    return img
def py_image(src):
    p, errs = text.compile_text(src)
    assert not errs, errs
    return p
if __name__=='__main__':
    src=open(sys.argv[1]).read()
    img=chain_image(src)
    r=run(img,20,2,checked=True,limit=10**7)
    print('chain', r.out, r.rc, r.ticks, r.err[:200])
    p=py_image(src)
    st=p
    print(type(p))
