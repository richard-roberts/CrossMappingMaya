import sys
import json

import numpy
import matplotlib.colors
import matplotlib.pyplot

import mapper



snapshot_filepath = sys.argv[1]
baked_filepath = snapshot_filepath.replace(".json", "-baked.json")

cm = mapper.CrossMapping()
cm.configure_from_json(snapshot_filepath, 0)
cm.solve()
cm.

with open(baked_filepath, "r") as f:
	data = json.loads(f.read())
	anim = data["anim"]



frames = list(range(1, len(anim) + 1))
names = list(cm.snapshots.keys())

for name in names:
	snapshot = cm.snapshots[name]["target"]
	s = numpy.array(snapshot)

	dists = []
	for f in frames:
		ix = f - 1
		c = numpy.array(anim[ix])	
		d = numpy.linalg.norm(c - s)
		dists.append(d)
	
	matplotlib.pyplot.plot(frames, dists, label=name)

matplotlib.pyplot.legend()
matplotlib.pyplot.show()

# dists = numpy.array(dists)
# ax.set_title(snapshot_key)
# ax.plt(dists.T, aspect='auto', cmap=cmap, norm=norm)
# ax.set_yticks(numpy.arange(len(names) + 1))
# ax.set_xticks([f for f in frames if f % tick_spacing == 0])
# ax.set_yticklabels(names + ["sum"])
# ax.set_xticklabels([str(f) for f in frames if f % tick_spacing == 0])
