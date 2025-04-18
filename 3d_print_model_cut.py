bl_info = {
    "name": "3D Print Model Cut",
    "author": "The Anomaly",
    "version": (1, 23),
    "blender": (4, 2, 0),
    "location": "View3D > Sidebar > 3D Print Model Cut",
    "description": "Cuts models into 8 manifold parts for 3D printing",
    "category": "Object",
}

import bpy
import mathutils
import bmesh
from bpy.types import Operator, Panel
from bpy.props import FloatProperty

def find_boundary_loops(bm):
    """Find closed loops of selected edges in the bmesh to cap open boundaries."""
    boundary_loops = []
    visited = set()
    for edge in bm.edges:
        if edge.select and edge not in visited:
            loop = []
            current_edge = edge
            start_vert = current_edge.verts[0]
            current_vert = start_vert
            while True:
                loop.append(current_vert)
                visited.add(current_edge)
                next_edges = [e for e in current_vert.link_edges if e.select and e not in visited]
                if not next_edges:
                    break
                if len(next_edges) > 1:
                    print("Warning: non-manifold boundary detected with multiple paths")
                    break
                current_edge = next_edges[0]
                current_vert = current_edge.other_vert(current_vert)
                if current_vert == start_vert and len(loop) >= 3:
                    boundary_loops.append(loop)
                    break
    return boundary_loops

class OBJECT_OT_CreateCuttingCubes(Operator):
    """Cuts models into 8 manifold parts with connectors for 3D printing"""
    bl_idname = "object.create_cutting_cubes"
    bl_label = "3D Print Model Cut"
    bl_options = {'REGISTER', 'UNDO'}

    scale_factor: FloatProperty(
        name="Scale Factor",
        description="Scale factor for cube size (relative to model)",
        default=1.1,
        min=1.0,
        max=2.0,
    )

    @classmethod
    def poll(cls, context):
        return (context.active_object is not None and 
                context.active_object.type == 'MESH' and
                context.mode == 'OBJECT')

    def execute(self, context):
        obj = context.active_object
        if not obj or obj.type != 'MESH':
            self.report({'ERROR'}, "Please select a mesh object")
            return {'CANCELLED'}

        # Store original model name
        original_name = obj.name

        # Apply transformations to the model
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(True)
        context.view_layer.objects.active = obj
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)

        # Get bounding box in world coordinates
        world_matrix = obj.matrix_world
        bbox_corners = [world_matrix @ mathutils.Vector(corner) for corner in obj.bound_box]
        min_coords = mathutils.Vector((min(c[i] for c in bbox_corners) for i in range(3)))
        max_coords = mathutils.Vector((max(c[i] for c in bbox_corners) for i in range(3)))

        # Calculate center and size
        center = (min_coords + max_coords) / 2
        size = max_coords - min_coords
        half_size = size / 2 * self.scale_factor

        # Define octant offsets and names
        octant_offsets = [
            (1, 1, 1), (1, 1, -1), (1, -1, 1), (1, -1, -1),
            (-1, 1, 1), (-1, 1, -1), (-1, -1, 1), (-1, -1, -1)
        ]
        position_names = []
        for offset in octant_offsets:
            x_pos = 'left' if offset[0] < 0 else 'right'
            y_pos = 'back' if offset[1] < 0 else 'front'
            z_pos = 'bottom' if offset[2] < 0 else 'top'
            position_names.append(f"{x_pos}_{y_pos}_{z_pos}")

        # Connector dimensions
        base_xy_scale = 1/3
        connector_xy_scale = 1/6
        connector_z_depth = 1/20
        connector_taper_scale = 0.9
        void_clearance_scale = 1.05

        # Deselect all
        bpy.ops.object.select_all(action='DESELECT')

        cutting_cubes = []
        for i, offset in enumerate(octant_offsets):
            is_top_cube = offset[2] > 0
            is_left_cube = offset[0] < 0
            is_right_cube = offset[0] > 0
            is_front_cube = offset[1] > 0
            is_back_cube = offset[1] < 0
            cube_center = mathutils.Vector((
                center.x + offset[0] * half_size.x / 2,
                center.y + offset[1] * half_size.y / 2,
                center.z + offset[2] * half_size.z / 2
            ))

            # Create cube
            bpy.ops.mesh.primitive_cube_add(size=1, location=cube_center)
            cube = context.active_object
            cube.name = f"CuttingCube_{i}"
            cube.scale = (half_size.x, half_size.y, half_size.z)
            cube.display_type = 'WIRE'
            bpy.ops.object.select_all(action='DESELECT')
            cube.select_set(True)
            context.view_layer.objects.active = cube
            bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)

            # Connector sizes
            connector_size = mathutils.Vector((
                half_size.x * connector_xy_scale,
                half_size.y * connector_xy_scale,
                half_size.z * connector_z_depth
            ))
            base_size = mathutils.Vector((
                half_size.x * base_xy_scale,
                half_size.y * base_xy_scale,
                half_size.z * connector_z_depth
            ))
            void_base_size_top_bottom = mathutils.Vector((
                base_size.x * void_clearance_scale,
                base_size.y * void_clearance_scale,
                base_size.z * void_clearance_scale
            ))
            void_base_size_left_right = mathutils.Vector((
                connector_size.x * void_clearance_scale,
                base_size.y * void_clearance_scale,
                base_size.z * void_clearance_scale
            ))
            void_base_size_front_back = mathutils.Vector((
                base_size.x * void_clearance_scale,
                connector_size.y * void_clearance_scale,
                base_size.z * void_clearance_scale
            ))

            # Top/Bottom Connectors
            if is_top_cube:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh = cube.data
                for poly in mesh.polygons:
                    if abs(poly.normal.z + 1.0) < 0.0001:
                        poly.select = True
                bpy.ops.object.mode_set(mode='EDIT')
                inset_thickness = (half_size.x - base_size.x) / 2 / half_size.x
                bpy.ops.mesh.inset(thickness=inset_thickness, depth=0)
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, 0, -connector_size.z),
                        "orient_type": 'NORMAL'
                    }
                )
                bpy.ops.transform.resize(
                    value=(connector_taper_scale, connector_taper_scale, 1.0),
                    orient_type='LOCAL',
                    constraint_axis=(True, True, False)
                )
                bpy.ops.object.mode_set(mode='OBJECT')
            else:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh = cube.data
                for poly in mesh.polygons:
                    if abs(poly.normal.z - 1.0) < 0.0001:
                        poly.select = True
                bpy.ops.object.mode_set(mode='EDIT')
                inset_thickness = (half_size.x - void_base_size_top_bottom.x) / 2 / half_size.x
                bpy.ops.mesh.inset(thickness=inset_thickness, depth=0)
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, 0, -void_base_size_top_bottom.z),
                        "orient_type": 'GLOBAL'
                    }
                )
                bpy.ops.transform.resize(
                    value=(connector_taper_scale, connector_taper_scale, 1.0),
                    orient_type='LOCAL',
                    constraint_axis=(True, True, False)
                )
                bpy.ops.mesh.delete(type='FACE')
                bpy.ops.object.mode_set(mode='OBJECT')

            # Left/Right Connectors
            if is_left_cube:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh = cube.data
                for poly in mesh.polygons:
                    if abs(poly.normal.x - 1.0) < 0.0001:
                        poly.select = True
                bpy.ops.object.mode_set(mode='EDIT')
                inset_thickness = min(
                    (half_size.y - base_size.y) / 2 / half_size.y,
                    (half_size.z - base_size.z) / 2 / half_size.z
                )
                bpy.ops.mesh.inset(thickness=inset_thickness, depth=0)
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (connector_size.x, 0, 0),
                        "orient_type": 'GLOBAL'
                    }
                )
                bpy.ops.transform.resize(
                    value=(1.0, connector_taper_scale, connector_taper_scale),
                    orient_type='LOCAL',
                    constraint_axis=(False, True, True)
                )
                bpy.ops.object.mode_set(mode='OBJECT')
            elif is_right_cube:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh = cube.data
                for poly in mesh.polygons:
                    if abs(poly.normal.x + 1.0) < 0.0001:
                        poly.select = True
                bpy.ops.object.mode_set(mode='EDIT')
                inset_thickness = min(
                    (half_size.y - void_base_size_left_right.y) / 2 / half_size.y,
                    (half_size.z - void_base_size_left_right.z) / 2 / half_size.z
                )
                bpy.ops.mesh.inset(thickness=inset_thickness, depth=0)
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (-void_base_size_left_right.x, 0, 0),
                        "orient_type": 'GLOBAL'
                    }
                )
                bpy.ops.transform.resize(
                    value=(1.0, connector_taper_scale, connector_taper_scale),
                    orient_type='LOCAL',
                    constraint_axis=(False, True, True)
                )
                bpy.ops.mesh.delete(type='FACE')
                bpy.ops.object.mode_set(mode='OBJECT')

            # Front/Back Connectors
            if is_back_cube:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh = cube.data
                for poly in mesh.polygons:
                    if abs(poly.normal.y - 1.0) < 0.0001:
                        poly.select = True
                bpy.ops.object.mode_set(mode='EDIT')
                inset_thickness = min(
                    (half_size.x - base_size.x) / 2 / half_size.x,
                    (half_size.z - base_size.z) / 2 / half_size.z
                )
                bpy.ops.mesh.inset(thickness=inset_thickness, depth=0)
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, connector_size.y, 0),
                        "orient_type": 'GLOBAL'
                    }
                )
                bpy.ops.transform.resize(
                    value=(connector_taper_scale, 1.0, connector_taper_scale),
                    orient_type='LOCAL',
                    constraint_axis=(True, False, True)
                )
                bpy.ops.object.mode_set(mode='OBJECT')
            elif is_front_cube:
                bpy.ops.object.mode_set(mode='EDIT')
                bpy.ops.mesh.select_all(action='DESELECT')
                bpy.ops.object.mode_set(mode='OBJECT')
                mesh = cube.data
                for poly in mesh.polygons:
                    if abs(poly.normal.y + 1.0) < 0.0001:
                        poly.select = True
                bpy.ops.object.mode_set(mode='EDIT')
                inset_thickness = min(
                    (half_size.x - void_base_size_front_back.x) / 2 / half_size.x,
                    (half_size.z - void_base_size_front_back.z) / 2 / half_size.z
                )
                bpy.ops.mesh.inset(thickness=inset_thickness, depth=0)
                bpy.ops.mesh.extrude_region_move(
                    TRANSFORM_OT_translate={
                        "value": (0, -void_base_size_front_back.y, 0),
                        "orient_type": 'GLOBAL'
                    }
                )
                bpy.ops.transform.resize(
                    value=(connector_taper_scale, 1.0, connector_taper_scale),
                    orient_type='LOCAL',
                    constraint_axis=(True, False, True)
                )
                bpy.ops.mesh.delete(type='FACE')
                bpy.ops.object.mode_set(mode='OBJECT')

            cutting_cubes.append(cube)

        # Cut the model into 8 parts
        cut_parts = []
        for i, cube in enumerate(cutting_cubes):
            bpy.ops.object.select_all(action='DESELECT')
            obj.select_set(True)
            context.view_layer.objects.active = obj
            bpy.ops.object.duplicate()
            model_part = context.active_object
            model_part.name = f"{original_name}_{position_names[i]}"

            bpy.ops.object.select_all(action='DESELECT')
            model_part.select_set(True)
            bpy.context.view_layer.objects.active = model_part

            mod = model_part.modifiers.new(name=f"BooleanCut_{i}", type='BOOLEAN')
            mod.operation = 'INTERSECT'
            mod.object = cube
            mod.solver = 'EXACT'
            mod.use_self = True
            mod.use_hole_tolerant = True

            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception as e:
                self.report({'ERROR'}, f"Failed to apply Boolean modifier for part {i}: {str(e)}")
                continue

            vertex_count = len(model_part.data.vertices)
            if vertex_count == 0:
                self.report({'WARNING'}, f"Part {i} ({position_names[i]}) has no geometry")
                continue

            # Enhanced manifold fixing
            bpy.ops.object.mode_set(mode='EDIT')
            bpy.ops.mesh.select_mode(type='EDGE')
            bpy.ops.mesh.select_all(action='DESELECT')
            bpy.ops.mesh.delete_loose()
            bpy.ops.mesh.select_non_manifold()

            mesh = context.object.data
            selected_edges = sum(1 for edge in mesh.edges if edge.select)
            if selected_edges > 0:
                try:
                    bpy.ops.mesh.fill()
                    # Check if fill resolved all open edges
                    bpy.ops.mesh.select_all(action='DESELECT')
                    bpy.ops.mesh.select_non_manifold()
                    selected_edges_after = sum(1 for edge in mesh.edges if edge.select)
                    if selected_edges_after > 0:
                        print(f"Part {i} ({position_names[i]}) still has {selected_edges_after} open edges, attempting manual capping")
                        bm = bmesh.from_edit_mesh(mesh)
                        boundary_loops = find_boundary_loops(bm)
                        for loop in boundary_loops:
                            try:
                                face = bm.faces.new(loop)
                                print(f"Created face with {len(loop)} vertices for part {i}")
                            except ValueError as e:
                                print(f"Failed to create face for part {i}: {e}")
                        bmesh.update_edit_mesh(mesh)
                        # Final verification
                        bpy.ops.mesh.select_all(action='DESELECT')
                        bpy.ops.mesh.select_non_manifold()
                        final_selected = sum(1 for edge in mesh.edges if edge.select)
                        if final_selected > 0:
                            self.report({'WARNING'}, f"Part {i} ({position_names[i]}) still has {final_selected} open edges after manual capping")
                    else:
                        print(f"Fill successful for part {i} ({position_names[i]})")
                except Exception as e:
                    self.report({'WARNING'}, f"Error fixing manifold for part {i} ({position_names[i]}): {str(e)}")
            else:
                print(f"No open edges initially in part {i} ({position_names[i]})")

            # Final cleanup
            bpy.ops.mesh.select_all(action='SELECT')
            bpy.ops.mesh.normals_make_consistent(inside=False)
            bpy.ops.object.mode_set(mode='OBJECT')

            # Center origin
            bpy.ops.object.origin_set(type='ORIGIN_GEOMETRY', center='BOUNDS')

            cut_parts.append(model_part)

        # Clean up cutting cubes
        bpy.ops.object.select_all(action='DESELECT')
        for cube in cutting_cubes:
            cube.select_set(True)
        bpy.ops.object.delete()

        # Select all parts
        bpy.ops.object.select_all(action='DESELECT')
        obj.select_set(False)
        for part in cut_parts:
            part.select_set(True)
        if cut_parts:
            context.view_layer.objects.active = cut_parts[0]

        self.report({'INFO'}, "Model cut into 8 manifold parts with connectors")
        return {'FINISHED'}

class VIEW3D_PT_CutModel(Panel):
    bl_label = "3D Print Model Cut"
    bl_idname = "VIEW_3D_PT_cut_model"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = '3D Print Model Cut'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.create_cutting_cubes", text="3D Print Model Cut")

classes = (
    OBJECT_OT_CreateCuttingCubes,
    VIEW3D_PT_CutModel,
)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

if __name__ == "__main__":
    register()
