import sys, time
sys.path.insert(0,'/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/wt2318/tower')
sys.dont_write_bytecode=True
import l3ctext
t=time.time()
img=l3ctext.tool_image()
open('/tmp/claude-1000/-home-user-work-copymachine/1c004ad6-28ff-45b4-8554-7c327219b055/scratchpad/w2318/tool.img','wb').write(img)
print(len(img), time.time()-t)
