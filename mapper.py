import json

import numpy


class Kernels:
    
    @staticmethod
    def gaussian(a, b, sigma): 
        dist = numpy.linalg.norm(b - a)
        numer = -(dist) ** 2
        denom = 2 * (sigma ** 2)
        return numpy.exp(numer / denom)


class ScatteredDataInterpolation:

    def __init__(self, source, target, kernel, sigma):
        self.source = [numpy.array(v) for v in source]
        self.target = [numpy.array(v) for v in target]
        self.kernel = kernel
        self.sigma = sigma

        # Build matrix containing kernel applied to combinations of values
        n = len(self.source)
        A = numpy.matrix(numpy.zeros((n, n)))
        for (i, pose_i) in enumerate(self.source):
            for (j, pose_j) in enumerate(self.source):
                A[i, j] = kernel(pose_i, pose_j, sigma)
        
        # Build matrix containing target values
        b = numpy.vstack(self.target)

        # Solve for weights
        self.weights = (A.T * A).I * A.T * b

    def interpolate(self, current_source_pose):
        values = [
            self.kernel(current_source_pose, s, self.sigma)
            for s in self.source
        ]
        result = numpy.matrix(values) * self.weights
        return result.tolist()[0]


class PoseTracker:

    def __init__(self, attribute_indices):
        self.attribute_indices = attribute_indices
    
    def pose_at_frame(self, frame):
        return [ai.read_at_time(frame) for ai in self.attribute_indices]
        
    def current_pose(self):
        return [ai.read() for ai in self.attribute_indices]
    
    def set_pose_at_frame(self, frame, values):
        for (index, value) in zip(self.attribute_indices, values):
            index.set_at_time(frame, value)
    
    def set_current_pose(self, values):
        for (index, value) in zip(self.attribute_indices, values):
            index.set(value)
            
    def go_to_zero(self):
        for index in self.attribute_indices:
            index.set(0)
            

class CrossMapping:

    def __init__(self):
        self.source = None
        self.target = None
        self.sigma = 1.0
        self.interpolator = None
        self.snapshots = {}

    def configure_from_json(self, filepath, index):
        with open(filepath, "r") as f:
            data = json.loads(f.read())[index]
        
        # Params
        self.sigma = data["sigma"]

        # Load in snapshots
        self.snapshots = {}
        for key in data["snapshots"].keys():
            self.snapshots[key] = data["snapshots"][key]
        
    def init_source(self, attrs):
        self.source = PoseTracker(attrs)
        self.snapshots = {}
        
    def init_target(self, attrs):
        self.target = PoseTracker(attrs)
        self.snapshots = {}
        
    def is_initialized(self):
        return self.source is not None and self.target is not None
        
    def is_ready_to_run(self):
        return self.is_initialized() and len(self.snapshots.keys()) >= 1 and self.interpolator is not None
        
    def new_snapshot(self, name):
        self.snapshots[name] = {
            "source": self.source.current_pose(),
            "target": self.target.current_pose()
        }
        
    def go_to_snapshot(self, name):
        self.source.set_current_pose(self.snapshots[name]["source"])
        self.target.set_current_pose(self.snapshots[name]["target"])
        
    def delete_snapshot(self, name):
        del self.snapshots[name]
    
    def names_of_snapshots(self):
        return list(self.snapshots.keys())
        
    def number_of_snapshots(self):
        return len(self.snapshots.keys())

    def get_snapshot_distance_matrices(self):
        keys = self.snapshots.keys()
        source = []
        target = []
        for key_a in keys:
            a_s = numpy.array(self.snapshots[key_a]["source"])
            a_t = numpy.array(self.snapshots[key_a]["target"])
            s_row = []
            t_row = []
            for key_b in keys:
                b_s = numpy.array(self.snapshots[key_b]["source"])
                b_t = numpy.array(self.snapshots[key_b]["target"])
                d_s = numpy.linalg.norm(b_s - a_s)
                d_t = numpy.linalg.norm(b_t - a_t)
                s_row.append(d_s)
                t_row.append(d_t)
            source.append(s_row)
            target.append(t_row)
        return keys, source, target


    def solve(self, check_initialized=True):
        if check_initialized and not self.is_initialized():
            raise ValueError("Source and target pose trackers not yet initialized")
        
        # Stack poses for each snapshot, ensuring to put them in the same order
        source_data = []
        target_data = []
        for key in self.snapshots.keys():
            source_data.append(self.snapshots[key]["source"])
            target_data.append(self.snapshots[key]["target"])
        
        self.interpolator = ScatteredDataInterpolation(
            source_data,
            target_data,
            Kernels.gaussian,
            self.sigma
        )

    def apply(self, pose):     
        if self.interpolator is None:
            raise ValueError("Interpolator has not been setup")
        else:
            return self.interpolator.interpolate(pose)
        
    def apply_current(self):
        if self.interpolator is None:
            raise ValueError("Interpolator has not been setup")
        else:
            values = self.apply(self.source.current_pose())
            print("THE VALUES ARE ", str(["%2.2f" % v for v in values]))
            self.target.set_current_pose(values)

    def try_apply_current(self):
        if self.interpolator is not None:
            values = self.apply(self.source.current_pose())
            self.target.set_current_pose(values)
