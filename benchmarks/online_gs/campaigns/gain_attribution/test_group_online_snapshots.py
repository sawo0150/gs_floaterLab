import json
import tempfile
import unittest
from pathlib import Path
import numpy as np
import torch
from plyfile import PlyData
from export_group_online_snapshots import export_group


class GroupExportTests(unittest.TestCase):
    def prepare(self, folder):
        roots = []
        centers = np.array([[0,0,0],[1,0,0],[0,1,0],[1,1,1]], dtype=float)
        ref = np.column_stack([np.arange(4), centers, np.tile([0,0,0,1], (4,1))])
        for index in range(3):
            root = Path(folder)/str(index); (root/'stream_snapshots').mkdir(parents=True)
            roots.append(root)
            np.savetxt(root/'traj_full_beforeBA.txt', ref)
            poses = {}
            for uid, center in enumerate(centers):
                pose=torch.eye(4, dtype=torch.float64); pose[:3,3]=-torch.tensor(center)*2
                poses[uid]=pose
            state={'parameters': {'xyz':torch.full((2,3),float(index)),
                'features_dc':torch.zeros(2,1,3),'features_rest':torch.zeros(2,15,3),
                'opacity':torch.ones(2,1),'scaling':torch.zeros(2,3),'rotation':torch.ones(2,4)},
                'keyframe_w2c':poses,'active_sh_degree':1,'training_uids':[0,2],
                'metadata':{'state_seconds':10.+index}}
            torch.save(state, root/'stream_snapshots/state.pt')
            (root/'stream_snapshots/manifest.json').write_text(json.dumps({'snapshots':[
                {'file':'state.pt','copy_finished_seconds':10.+index}]}))
        return roots

    def test_shared_coordinates_preserve_each_map_and_timing(self):
        with tempfile.TemporaryDirectory() as folder:
            roots=self.prepare(folder); reports=export_group(roots)
            self.assertEqual(reports[0]['actual_times_seconds'],[10.,11.,12.])
            self.assertFalse(reports[0]['alignment_quality_accepted'])
            for index,root in enumerate(roots):
                out=root/'stream_evaluation_shared/state'
                vertices=PlyData.read(out/'3dgs_before_final.ply')['vertex']
                np.testing.assert_array_equal(vertices['x'],[index,index])
                provenance=json.loads((out/'paired_coordinate_provenance.json').read_text())
                self.assertEqual(len(provenance['sources']),3)
            with self.assertRaises(FileExistsError): export_group(roots)

    def test_different_common_pose_rejected_before_export(self):
        with tempfile.TemporaryDirectory() as folder:
            roots=self.prepare(folder); path=roots[2]/'stream_snapshots/state.pt'
            state=torch.load(path,weights_only=True); state['keyframe_w2c'][1][0,3]+=.01
            torch.save(state,path)
            with self.assertRaises(ValueError): export_group(roots)
            self.assertFalse(any((r/'stream_evaluation_shared').exists() for r in roots))

    def test_explicit_subset_uses_all_and_only_identical_anchors(self):
        with tempfile.TemporaryDirectory() as folder:
            roots=self.prepare(folder);path=roots[2]/'stream_snapshots/state.pt'
            state=torch.load(path,weights_only=True);state['keyframe_w2c'][3][0,3]+=.01
            torch.save(state,path)
            reports=export_group(roots,identical_anchor_subset=True)
            self.assertEqual(reports[0]['common_keyframes'],3)
            self.assertEqual(set(reports[0]['excluded_pose_differences']),{3})
            prov=json.loads((roots[0]/'stream_evaluation_shared/state/paired_coordinate_provenance.json').read_text())
            self.assertEqual(prov['common_keyframe_uids'],[0,1,2])


if __name__ == '__main__': unittest.main()
