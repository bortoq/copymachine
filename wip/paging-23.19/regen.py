import sys
sys.path.insert(0,'/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower')
import l3ctext
P='/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower/programs/l3c.tw'
src=open(P).read()
a=src.index('# --- begin generated\n')+len('# --- begin generated\n'); b=src.index('# --- end generated')
src=src[:a]+l3ctext.tables_text()+src[b:]
open(P,'w').write(src)
