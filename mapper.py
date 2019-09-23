import numpy as np

class Kernels:
    
    @staticmethod
    def gaussian(a, b, sigma): 
        dist = np.linalg.norm(b - a)
        numer = -dist ** 2
        denom = 2 * (sigma ** 2)
        return np.exp(numer / denom)


class ScatteredDataInterpolation:

    def __init__(self, source_poses, target_poses, kernel, sigma):
        self.source_poses = source_poses
        self.kernel = kernel
        self.sigma = sigma

        # Build matrix containing kernel applied to combinations of values
        n = len(source_poses)
        A = np.matrix(np.zeros((n, n)))
        for (i, pose_i) in enumerate(source_poses):
            for (j, pose_j) in enumerate(source_poses):
                A[i, j] = kernel(pose_i, pose_j, sigma)
        
        # Build matrix containing target values
        b = np.vstack([t.tolist() for t in target_poses])

        # Solve for weights
        self.weights = (A.T * A).I * A.T * b

    def interpolate(self, current_source_pose):
        values = [
            self.kernel(current_source_pose, source_pose, self.sigma)
            for source_pose in self.source_poses
        ]
        result = np.array(values) * self.weights
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
        p = np.array([
            self.read_attribute(attr_index)
            for attr_index in self.attribute_indices
        ])
        return p

    def set_current_pose(self, values):
        print("Setting current pose to ", values) #TODO: remove print
        for (index, value) in zip(self.attribute_indices, values):
            self.set_attribute(index, value)

    def save_pose(self, name, pose):
        print("Adding pose", name, pose)
        self.poses[name] = pose

    def save_current_pose(self, name):
        self.save_pose(name, self.current_pose())

    def as_matrix(self):
        return [self.poses.values()]


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
        self.source.save_pose(name, target)

    def solve(self):
        self.interpolator = ScatteredDataInterpolation(
            self.source.as_matrix(),
            self.target.as_matrix(),
            Kernels.gaussian,
            self.sigma
        )

    def apply(self):
        values = self.interpolator.interpolate(
            self.source.current_pose().values
        )
        self.target.set_current_pose(values)

if __name__ == "__main__":
    cm = CrossMapping(["x"], ["x", "y"], 1.0)
    cm.save_predefined_pose("P1", np.array([0.0]), np.array([0.0, 0.0]))
    cm.save_predefined_pose("P2", np.array([1.0]), np.array([1.0, -0.5]))
    cm.solve()
    cm.apply()
