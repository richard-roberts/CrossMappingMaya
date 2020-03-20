import json

import numpy
import matplotlib.colors
import matplotlib.pyplot
import matplotlib.widgets
import mpl_toolkits.mplot3d

import mapper

CMAP_SOURCE_KEY = "Reds_r"
CMAP_SOURCE_NORM = matplotlib.colors.Normalize(vmin=0.0,vmax=15.0)
CMAP_TARGET_KEY = "Blues_r"
CMAP_TARGET_NORM = matplotlib.colors.Normalize(vmin=0.0,vmax=3.0) 
class Vis:

	def __init__(self, filepath):
		self.current_frame = 1
		self.cm = mapper.CrossMapping()
		self.cm.configure_from_json(filepath, 0)
		with open(filepath.replace(".json", "-baking.json"), "r") as f:
			data = json.loads(f.read())
			self.source_anim = data["anim"]
		self.update_target_anim()
		self.snapshot_keys, self.source_dist_matrix, self.target_dist_matrix = self.cm.get_snapshot_distance_matrices()

	def update_target_anim(self):
		self.cm.solve(check_initialized=False)
		self.target_anim = [self.cm.apply(p) for p in self.source_anim]

	def change_sigma(self, sigma):
		self.cm.sigma = sigma

	def plot_lines_for_axis(self, ax):
		s = 1
		ax.plot([-s, s], [ 0, 0], [ 0, 0], color="#FF9999")
		ax.plot([ 0, 0], [-s, s], [ 0, 0], color="#99FF99")
		ax.plot([ 0, 0], [ 0, 0], [-s, s], color="#9999FF")

	def plot_snapshots(self, ax, snapshot_key):
		xs, ys, zs = [], [], []
		labels = []
		for key in self.cm.snapshots.keys():
			labels.append(key)
			x, y, z = self.cm.snapshots[key][snapshot_key]
			xs.append(x); ys.append(y); zs.append(z)

		ax.scatter(xs, ys, zs, marker="o", color="#FF0000")
		ax.set_xlabel('X'); ax.set_ylabel('Y'); ax.set_zlabel('Z')
		for (l, x, y, z) in zip(labels, xs, ys, zs):
			ax.text(x, y, z, l, (1, 0, 0))

	def plot_animation(self, ax, anim):
		xs, ys, zs = [], [], []
		for pose in anim:
			x, y, z = pose
			xs.append(x); ys.append(y); zs.append(z)
		ax.plot(xs, ys, zs, color="#333333")

		# minv = min([min(xs), min(ys), min(zs)])
		# maxv = max([max(xs), max(ys), max(zs)])
		# ax.set_xlim3d(minv, maxv)
		# ax.set_ylim3d(minv, maxv)
		# ax.set_zlim3d(minv, maxv)

	def plot_snapshot_distance_matrix(self, ax, names, matrix, cmap, norm):
		ax.matshow(matrix, cmap=cmap, norm=norm)
		ax.set_xticks(numpy.arange(len(names)))
		ax.set_yticks(numpy.arange(len(names)))
		ax.set_xticklabels(names)
		ax.set_yticklabels(names)
		for i in range(len(names)):
			for j in range(len(names)):
				text = ax.text(
					j, i, 
					"%2.2f" % matrix[i][j],
					ha="center", va="center"#, color="w"
				)

	def plot_current_dists(self, ax, names, anim, snapshot_key, cmap, norm):
		dists = []
		ix = int(self.current_frame) - 1
		c = numpy.array(anim[ix])
		for key in self.cm.snapshots.keys():
			s = numpy.array(self.cm.snapshots[key][snapshot_key])
			d = numpy.linalg.norm(c - s)
			dists.append(d)
		ax.matshow([dists], cmap=cmap, norm=norm)
		ax.set_xticks(numpy.arange(len(names)))
		ax.set_yticks(numpy.arange(1))
		ax.set_xticklabels(names)
		for i in range(len(names)):
			text = ax.text(
				i, 0, 
				"%2.2f" % dists[i],
				ha="center", va="center"#, c"olor="w
			)

	def setup_pose_marker(self, ax, anim):
		ix = int(self.current_frame) - 1
		x, y, z = anim[ix]
		marker, = ax.plot([x], [y], [z], marker="^", markersize=10, color="#3333FF")
		return marker

	def update_pose_marker(self, marker, anim):
		ix = int(self.current_frame) - 1
		x, y, z = anim[ix]
		marker.set_data_3d([x], [y], [z])

	def setup_frame_slider(self):
		ax = matplotlib.pyplot.axes([0.25, 0.05, 0.65, 0.03])
		self.frame_slider = matplotlib.widgets.Slider(ax, 'Frame', 1, len(self.source_anim), valinit=self.current_frame, valstep=1)
		self.frame_slider.on_changed(self.handle_frame_slider_change)

	def handle_frame_slider_change(self, frame):
		self.current_frame = frame
		self.update_pose_marker(self.source_pose_marker, self.source_anim)
		self.update_pose_marker(self.target_pose_marker, self.target_anim)
		self.ax_source_dists.cla()
		self.ax_target_dists.cla()
		self.plot_current_dists(self.ax_source_dists, self.snapshot_keys, self.source_anim, "source", CMAP_SOURCE_KEY, CMAP_SOURCE_NORM)
		self.plot_current_dists(self.ax_target_dists, self.snapshot_keys, self.target_anim, "target", CMAP_TARGET_KEY, CMAP_TARGET_NORM)

	def setup_sigma_slider(self, callback):
		ax = matplotlib.pyplot.axes([0.25, 0.0, 0.65, 0.03])
		self.sigma_slider = matplotlib.widgets.Slider(ax, 'Sigma', -1.0, 10.0, valinit=self.cm.sigma, valstep=0.1)
		self.sigma_slider.on_changed(self.make_handle_sigma_slider_change_fn(callback))

	def make_handle_sigma_slider_change_fn(self, callback):
		def fn(sigma):
			self.change_sigma(sigma)
			self.update_target_anim()
			callback()
		return fn

	def redraw(self):
		ax = self.ax_source_graph
		ax.cla()
		self.plot_lines_for_axis(ax)
		self.plot_snapshots(ax, "source")
		self.plot_animation(ax, self.source_anim)
		self.source_pose_marker = self.setup_pose_marker(ax, self.source_anim)
		
		ax=self.ax_source_dists
		ax.cla()
		self.plot_current_dists(ax, self.snapshot_keys, self.source_anim, "source", CMAP_SOURCE_KEY, CMAP_SOURCE_NORM)

		ax = self.ax_target_graph
		ax.cla()
		self.plot_lines_for_axis(ax)
		self.plot_snapshots(ax, "target")
		self.plot_animation(ax, self.target_anim)
		self.target_pose_marker = self.setup_pose_marker(ax, self.target_anim)
		
		ax=self.ax_target_dists
		ax.cla()
		self.plot_current_dists(ax, self.snapshot_keys, self.target_anim, "target", CMAP_TARGET_KEY, CMAP_TARGET_NORM)

		ax=self.ax_source_dist_anim
		ax.cla()
		self.plot_snapshot_distance_anim(ax, self.source_anim, "source", CMAP_SOURCE_KEY, CMAP_SOURCE_NORM)

		ax=self.ax_target_dist_anim
		ax.cla()
		self.plot_snapshot_distance_anim(ax, self.target_anim, "target", CMAP_TARGET_KEY, CMAP_TARGET_NORM)

	def render_interface(self):
		self.fig = matplotlib.pyplot.figure()
		self.ax_source_graph  = self.fig.add_subplot(4, 2, 1, projection='3d')
		self.ax_target_graph  = self.fig.add_subplot(4, 2, 2, projection='3d')
		self.ax_source_dists  = self.fig.add_subplot(4, 2, 3)
		self.ax_target_dists  = self.fig.add_subplot(4, 2, 4)
		self.ax_source_matrix = self.fig.add_subplot(4, 2, 5)
		self.ax_target_matrix = self.fig.add_subplot(4, 2, 6)
		self.ax_source_dist_anim = self.fig.add_subplot(4, 2, 7)
		self.ax_target_dist_anim = self.fig.add_subplot(4, 2, 8)
		self.redraw()
		self.plot_snapshot_distance_matrix(self.ax_source_matrix, self.snapshot_keys, self.source_dist_matrix, CMAP_SOURCE_KEY, CMAP_SOURCE_NORM)
		self.plot_snapshot_distance_matrix(self.ax_target_matrix, self.snapshot_keys, self.target_dist_matrix, CMAP_TARGET_KEY, CMAP_TARGET_NORM)
		self.setup_frame_slider()
		self.setup_sigma_slider(self.redraw)

	def plot_snapshot_distance_anim(self, ax, anim, snapshot_key, cmap, norm):
		frames = list(range(1, len(anim) + 1))
		names = list(self.cm.snapshots.keys())

		dists = []
		for f in frames:
			row = []
			ix = f - 1
			c = numpy.array(anim[ix])
			for name in names:
				s = numpy.array(self.cm.snapshots[name][snapshot_key])
				d = numpy.linalg.norm(c - s)
				row.append(d)
			row.append(min(row))
			dists.append(row)

		dists = numpy.array(dists)
		ax.set_title(snapshot_key)
		ax.matshow(dists.T, aspect='auto', cmap=cmap, norm=norm)
		ax.set_yticks(numpy.arange(len(names) + 1))
		ax.set_xticks([f for f in frames if f % 5 == 0])
		ax.set_yticklabels(names + ["min"])
		ax.set_xticklabels([str(f) for f in frames if f % 5 == 0])
	
	def show(self):
		matplotlib.pyplot.show()

if __name__ == "__main__":
	v = Vis("sphere-cube-5-to-1-square.json")
	# v = Vis("sphere-cube-5-to-1-square-missing.json")
	v.render_interface()
	v.show()