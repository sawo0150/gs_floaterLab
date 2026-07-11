#!/usr/bin/env python3
"""
box_crop_viewer.py
A lightweight 3D GUI tool based on PyVista with Fly/Joystick camera style,
and an easy-to-use, keyboard-controlled wireframe 3D Box (no annoying sphere handles)
for precise filtering and pruning of floaters from a 3DGS PLY file.
"""
import numpy as np
from pathlib import Path
from plyfile import PlyData, PlyElement
import argparse
import pyvista as pv

class SplatBoxEditor:
    def __init__(self, ply_path, out_path, opacity_filter=0.05):
        self.ply_path = Path(ply_path)
        self.out_path = Path(out_path)
        self.opacity_filter = opacity_filter
        
        print(f"[Load] Loading PLY file: {self.ply_path}...")
        self.ply_data = PlyData.read(str(self.ply_path))
        self.vertices = self.ply_data["vertex"]
        
        # Original coordinates & attributes
        self.xyz = np.stack([self.vertices["x"], self.vertices["y"], self.vertices["z"]], axis=1).astype(np.float32)
        # Convert sigmoid opacity to raw opacity for rendering
        self.raw_opacity = 1.0 / (1.0 + np.exp(-np.array(self.vertices["opacity"], dtype=np.float64)))
        
        # Keep track of active indices (not deleted)
        self.active_mask = np.ones(len(self.xyz), dtype=bool)
        
        # Initialize UI Plotter
        self.plotter = pv.Plotter(title="3DGS Custom Box Pruning Editor")
        self.plotter.set_background("black")
        
        # Enable Joystick Style (Fly Camera mode: drag to look around, FPS-like camera control)
        self.plotter.enable_joystick_style()
        
        # Build pyvista mesh for rendering
        self.render_mask = self.raw_opacity > self.opacity_filter
        self.update_mesh()
        
        # Setup custom Keyboard-Controlled Box parameters
        init_bounds = self.poly_mesh.bounds
        self.box_center = np.array([
            (init_bounds[0] + init_bounds[1]) / 2.0,
            (init_bounds[2] + init_bounds[3]) / 2.0,
            (init_bounds[4] + init_bounds[5]) / 2.0
        ], dtype=np.float32)
        
        self.box_size = np.array([
            max((init_bounds[1] - init_bounds[0]) * 0.15, 0.8),
            max((init_bounds[3] - init_bounds[2]) * 0.15, 0.8),
            max((init_bounds[5] - init_bounds[4]) * 0.15, 0.8)
        ], dtype=np.float32)
        
        # Grid snap parameters
        self.snap_step = 0.1 # meter
        self.fly_speed = 0.2
        
        # Draw the initial Box
        self.update_box_mesh()
        
        # Setup keyboard controls
        self.setup_controls()
        self.update_info_text()
        
    def update_mesh(self):
        visible_mask = self.active_mask & self.render_mask
        if visible_mask.sum() == 0:
            visible_mask = self.active_mask
            
        pts = self.xyz[visible_mask]
        op = self.raw_opacity[visible_mask]
        
        self.poly_mesh = pv.PolyData(pts)
        self.poly_mesh["opacity"] = op
        
        if hasattr(self, "mesh_actor"):
            self.plotter.remove_actor(self.mesh_actor)
            
        self.mesh_actor = self.plotter.add_points(
            self.poly_mesh, 
            scalars="opacity", 
            cmap="inferno", 
            render_points_as_spheres=True, 
            point_size=4.0
        )
        
    def update_box_mesh(self):
        # Calculate bounds from center and size
        xmin = self.box_center[0] - self.box_size[0]/2.0
        xmax = self.box_center[0] + self.box_size[0]/2.0
        ymin = self.box_center[1] - self.box_size[1]/2.0
        ymax = self.box_center[1] + self.box_size[1]/2.0
        zmin = self.box_center[2] - self.box_size[2]/2.0
        zmax = self.box_center[2] + self.box_size[2]/2.0
        self.box_bounds = [xmin, xmax, ymin, ymax, zmin, zmax]
        
        # Draw a clean wireframe Box mesh (without annoying sphere handles!)
        box_mesh = pv.Box(bounds=self.box_bounds)
        self.plotter.add_mesh(
            box_mesh, 
            color="red", 
            style="wireframe", 
            line_width=2.5, 
            name="box_gizmo", # name parameter ensures it replaces the old one
            render=True
        )
        
    def update_info_text(self):
        # Instructions and metrics
        instructions = (
            "=== View Controls ===\n"
            "Mouse Drag: LOOK AROUND (Joystick Fly-camera)\n"
            "Mouse Wheel / Right Drag: ZOOM\n"
            "WASD : Fly Camera Forward/Left/Backward/Right\n"
            "Q / E: Fly Camera Up / Down\n"
            "[ / ]: Decrease / Increase Camera Fly Speed\n\n"
            "=== Box Controls (RED Wireframe) ===\n"
            "Arrow Keys : Move Box on X / Y axis\n"
            "I / K      : Move Box on Z axis (Up / Down)\n"
            "- / +      : Decrease / Increase Box Move Step\n"
            "1 / 2      : Resize Box Width (X-axis)\n"
            "3 / 4      : Resize Box Depth (Y-axis)\n"
            "5 / 6      : Resize Box Height (Z-axis)\n\n"
            "=== Edit Actions ===\n"
            "Delete / X : PRUNE Gaussians inside the RED box\n"
            "S          : SAVE current cleaned PLY file"
        )
        if hasattr(self, "instruction_text"):
            self.plotter.remove_actor(self.instruction_text)
        self.instruction_text = self.plotter.add_text(instructions, position="upper_left", font_size=9, color="white")
        
        status_info = (
            f"Active Gaussians: {self.active_mask.sum():,}\n"
            f"Box Center: [{self.box_center[0]:.2f}, {self.box_center[1]:.2f}, {self.box_center[2]:.2f}] m\n"
            f"Box Dimensions: [{self.box_size[0]:.2f} x {self.box_size[1]:.2f} x {self.box_size[2]:.2f}] m\n"
            f"Box Snap Step: {self.snap_step:.3f} m | Fly Speed: {self.fly_speed:.2f}"
        )
        if hasattr(self, "status_text"):
            self.plotter.remove_actor(self.status_text)
        self.status_text = self.plotter.add_text(status_info, position="lower_left", font_size=11, color="green")

    def prune_inside_box(self):
        xmin, xmax, ymin, ymax, zmin, zmax = self.box_bounds
        pts = self.xyz
        inside = (
            (pts[:, 0] >= xmin) & (pts[:, 0] <= xmax) &
            (pts[:, 1] >= ymin) & (pts[:, 1] <= ymax) &
            (pts[:, 2] >= zmin) & (pts[:, 2] <= zmax)
        )
        to_delete = self.active_mask & inside
        num_to_delete = int(to_delete.sum())
        
        if num_to_delete == 0:
            print("No active Gaussians inside the box.")
            return
            
        self.active_mask[inside] = False
        self.update_mesh()
        self.update_info_text()
        print(f"[Pruned] Removed {num_to_delete:,} Gaussians. Active remaining: {self.active_mask.sum():,}")

    def save_ply(self):
        print(f"[Save] Exporting cleaned PLY to {self.out_path}...")
        clean_vertices_data = self.vertices.data[self.active_mask]
        new_el = PlyElement.describe(clean_vertices_data, 'vertex')
        new_ply = PlyData([new_el], text=self.ply_data.text, byte_order=self.ply_data.byte_order)
        self.out_path.parent.mkdir(parents=True, exist_ok=True)
        new_ply.write(str(self.out_path))
        print(f"[Success] Saved {len(clean_vertices_data):,} Gaussians to {self.out_path}")
        self.update_info_text()

    def setup_controls(self):
        # 1. Camera Fly Controls
        def move_w():
            dir_vec = np.array(self.plotter.camera.direction)
            self.plotter.camera.position = np.array(self.plotter.camera.position) + dir_vec * self.fly_speed
            self.plotter.camera.focal_point = np.array(self.plotter.camera.focal_point) + dir_vec * self.fly_speed
            
        def move_s():
            dir_vec = np.array(self.plotter.camera.direction)
            self.plotter.camera.position = np.array(self.plotter.camera.position) - dir_vec * self.fly_speed
            self.plotter.camera.focal_point = np.array(self.plotter.camera.focal_point) - dir_vec * self.fly_speed

        def move_d():
            dir_vec = np.array(self.plotter.camera.direction)
            up_vec = np.array(self.plotter.camera.up)
            right_vec = np.cross(dir_vec, up_vec)
            right_vec /= np.linalg.norm(right_vec)
            self.plotter.camera.position = np.array(self.plotter.camera.position) + right_vec * self.fly_speed
            self.plotter.camera.focal_point = np.array(self.plotter.camera.focal_point) + right_vec * self.fly_speed

        def move_a():
            dir_vec = np.array(self.plotter.camera.direction)
            up_vec = np.array(self.plotter.camera.up)
            right_vec = np.cross(dir_vec, up_vec)
            right_vec /= np.linalg.norm(right_vec)
            self.plotter.camera.position = np.array(self.plotter.camera.position) - right_vec * self.fly_speed
            self.plotter.camera.focal_point = np.array(self.plotter.camera.focal_point) - right_vec * self.fly_speed

        def move_q():
            up_vec = np.array(self.plotter.camera.up)
            up_vec /= np.linalg.norm(up_vec)
            self.plotter.camera.position = np.array(self.plotter.camera.position) + up_vec * self.fly_speed
            self.plotter.camera.focal_point = np.array(self.plotter.camera.focal_point) + up_vec * self.fly_speed

        def move_e():
            up_vec = np.array(self.plotter.camera.up)
            up_vec /= np.linalg.norm(up_vec)
            self.plotter.camera.position = np.array(self.plotter.camera.position) - up_vec * self.fly_speed
            self.plotter.camera.focal_point = np.array(self.plotter.camera.focal_point) - up_vec * self.fly_speed

        def speed_up():
            self.fly_speed = min(self.fly_speed * 1.5, 5.0)
            self.update_info_text()
            
        def speed_down():
            self.fly_speed = max(self.fly_speed / 1.5, 0.02)
            self.update_info_text()

        # Bind Camera
        self.plotter.add_key_event("w", move_w)
        self.plotter.add_key_event("s", move_s)
        self.plotter.add_key_event("a", move_a)
        self.plotter.add_key_event("d", move_d)
        self.plotter.add_key_event("q", move_q)
        self.plotter.add_key_event("e", move_e)
        self.plotter.add_key_event("bracketright", speed_up) # ]
        self.plotter.add_key_event("bracketleft", speed_down) # [

        # 2. Box Movement Controls (Grid snap)
        def box_left():
            self.box_center[0] -= self.snap_step
            self.update_box_mesh()
            self.update_info_text()
        def box_right():
            self.box_center[0] += self.snap_step
            self.update_box_mesh()
            self.update_info_text()
        def box_up():
            self.box_center[1] += self.snap_step
            self.update_box_mesh()
            self.update_info_text()
        def box_down():
            self.box_center[1] -= self.snap_step
            self.update_box_mesh()
            self.update_info_text()
        def box_z_up():
            self.box_center[2] += self.snap_step
            self.update_box_mesh()
            self.update_info_text()
        def box_z_down():
            self.box_center[2] -= self.snap_step
            self.update_box_mesh()
            self.update_info_text()
            
        def step_up():
            self.snap_step = min(self.snap_step * 2.0, 2.0)
            self.update_info_text()
        def step_down():
            self.snap_step = max(self.snap_step / 2.0, 0.005)
            self.update_info_text()

        self.plotter.add_key_event("Left", box_left)
        self.plotter.add_key_event("Right", box_right)
        self.plotter.add_key_event("Up", box_up)
        self.plotter.add_key_event("Down", box_down)
        self.plotter.add_key_event("i", box_z_up)
        self.plotter.add_key_event("k", box_z_down)
        self.plotter.add_key_event("plus", step_up)
        self.plotter.add_key_event("equal", step_up)
        self.plotter.add_key_event("minus", step_down)

        # 3. Box Resizing Controls
        def size_x_up():
            self.box_size[0] += 0.1
            self.update_box_mesh()
            self.update_info_text()
        def size_x_down():
            self.box_size[0] = max(self.box_size[0] - 0.1, 0.1)
            self.update_box_mesh()
            self.update_info_text()
        def size_y_up():
            self.box_size[1] += 0.1
            self.update_box_mesh()
            self.update_info_text()
        def size_y_down():
            self.box_size[1] = max(self.box_size[1] - 0.1, 0.1)
            self.update_box_mesh()
            self.update_info_text()
        def size_z_up():
            self.box_size[2] += 0.1
            self.update_box_mesh()
            self.update_info_text()
        def size_z_down():
            self.box_size[2] = max(self.box_size[2] - 0.1, 0.1)
            self.update_box_mesh()
            self.update_info_text()

        self.plotter.add_key_event("1", size_x_up)
        self.plotter.add_key_event("2", size_x_down)
        self.plotter.add_key_event("3", size_y_up)
        self.plotter.add_key_event("4", size_y_down)
        self.plotter.add_key_event("5", size_z_up)
        self.plotter.add_key_event("6", size_z_down)

        # 4. Actions
        self.plotter.add_key_event("Delete", self.prune_inside_box)
        self.plotter.add_key_event("x", self.prune_inside_box)
        self.plotter.add_key_event("s", self.save_ply)

    def run(self):
        print("\n[Start] Custom Editor window opened. Controls mapped to keyboard.")
        self.plotter.show()

def main():
    parser = argparse.ArgumentParser(description="Precision Keyboard-Controlled Box Pruning Editor for 3DGS PLY")
    parser.add_argument("--orig", type=str, required=True, 
                        help="Path to original point_cloud.ply")
    parser.add_argument("--out", type=str, required=True, 
                        help="Path to save the cleaned point_cloud.ply")
    parser.add_argument("--opacity_filter", type=float, default=0.05, 
                        help="Opacity threshold for rendering speedup (default: 0.05)")
    args = parser.parse_args()
    
    editor = SplatBoxEditor(args.orig, args.out, args.opacity_filter)
    editor.run()

if __name__ == "__main__":
    main()
