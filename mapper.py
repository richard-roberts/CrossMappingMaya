import numpy

class Kernels:
    
    @staticmethod
    def gaussian(a, b, sigma): 
        dist = numpy.linalg.norm(b - a)
        numer = -dist ** 2
        denom = 2 * (sigma ** 2)
        return numpy.exp(numer / denom)


class ScatteredDataInterpolation:

    def __init__(self, source_poses, target_poses, kernel, sigma):
        self.source_poses = source_poses
        self.kernel = kernel
        self.sigma = sigma

        # Build matrix containing kernel applied to combinations of values
        n = len(source_poses)
        A = numpy.matrix(numpy.zeros((n, n)))
        for (i, pose_i) in enumerate(source_poses):
            for (j, pose_j) in enumerate(source_poses):
                A[i, j] = kernel(pose_i, pose_j, sigma)
        
        # Build matrix containing target values
        b = numpy.vstack([t.tolist() for t in target_poses])

        # Solve for weights
        self.weights = (A.T * A).I * A.T * b

    def interpolate(self, current_source_pose):
        values = [
            self.kernel(current_source_pose, source_pose, self.sigma)
            for source_pose in self.source_poses
        ]
        result = numpy.array(values) * self.weights
        return result.tolist()[0]


class PoseTracker:

    def __init__(self, attribute_indices):
        self.attribute_indices = attribute_indices
        self.poses = {}

    def read_attribute(self, index):
        raise NotImplementedError("read_attribute not implemented")

    def set_attribute(self, index, value):
        raise NotImplementedError("set_attribute not implemented")

    def current_pose(self):
        p = numpy.array([
            self.read_attribute(attr_index)
            for attr_index in self.attribute_indices
        ])
        return p

    def set_current_pose(self, values):
        print("Setting current pose to ", values) #TODO: remove print
        for (index, value) in zip(self.attribute_indices, values):
            self.set_attribute(index, value)

    def save_pose(self, name, pose, verbose=False):
        if verbose: print("Adding pose", name, pose)
        self.poses[name] = pose

    def save_current_pose(self, name):
        self.save_pose(name, self.current_pose())

    def as_matrix(self):
        return numpy.matrix(list(self.poses.values()))


class CrossMapping:

    def __init__(self, source_attribute_indices, target_attribute_indices, sigma):
        self.source = PoseTracker(source_attribute_indices)
        self.target = PoseTracker(target_attribute_indices)
        self.sigma = sigma
        self.interpolator = None

    def save_current_poses(self, name):
        self.source.save_current_pose(name)
        self.target.save_current_pose(name)

    def save_predefined_pose(self, name, source, target):
        self.source.save_pose(name, source)
        self.target.save_pose(name, target)

    def solve(self):
        self.interpolator = ScatteredDataInterpolation(
            self.source.as_matrix(),
            self.target.as_matrix(),
            Kernels.gaussian,
            self.sigma
        )

    def apply(self, pose):        
        return self.interpolator.interpolate(pose)
        
        
    def apply_current(self):
        values = self.apply(self.source.current_pose().values)
        self.target.set_current_pose(values)

if __name__ == "__main__":
    cm = CrossMapping(["x"], ["x", "y"], 1.0)
    cm.save_predefined_pose("P1", numpy.array([0.0]), numpy.array([0.0, 0.0]))
    cm.save_predefined_pose("P2", numpy.array([1.0]), numpy.array([1.0, -0.5]))
    cm.solve()
    values = cm.apply(numpy.array([0.5]))
    print(values)
