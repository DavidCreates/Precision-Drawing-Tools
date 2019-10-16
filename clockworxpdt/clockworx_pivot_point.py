# ***** BEGIN GPL LICENSE BLOCK *****
#
#
# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.	See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software Foundation,
# Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301, USA.
#
# ***** END GPL LICENCE BLOCK *****

# ----------------------------------------------------------
# Author: Alan Odom (Clockmender)
# ----------------------------------------------------------
#
import bpy
import bmesh
from bpy.types import Operator, Panel, PropertyGroup, SpaceView3D
from mathutils import Vector, Matrix
from math import pi
from .pdt_functions import viewCoords, draw3D, drawCallback3D
from .pdt_msg_strings import *


class PDT_OT_ModalDrawOperator(bpy.types.Operator):
    """Show/Hide Pivot Point"""

    bl_idname = "pdt.modaldraw"
    bl_label = "PDT Modal Draw"

    _handle = None  # keep function handler

    @staticmethod
    def handle_add(self, context):
        """Draw Pivot Point Graphic if not displayed.

        Draws 7 element Pivot Point Graphic

        Args:
            context: Current Blender bpy.context

        Returns:
            Nothing.
        """

        if PDT_OT_ModalDrawOperator._handle is None:
            PDT_OT_ModalDrawOperator._handle = SpaceView3D.draw_handler_add(
                drawCallback3D, (self, context), "WINDOW", "POST_VIEW"
            )
            context.window_manager.pdt_run_opengl = True

    @staticmethod
    def handle_remove(self, context):
        """Remove Pivot Point Graphic if displayed.

        Removes 7 element Pivot Point Graphic

        Args:
            context: Current Blender bpy.context

        Returns:
            Nothing.
        """

        if PDT_OT_ModalDrawOperator._handle is not None:
            SpaceView3D.draw_handler_remove(PDT_OT_ModalDrawOperator._handle, "WINDOW")
        PDT_OT_ModalDrawOperator._handle = None
        context.window_manager.pdt_run_opengl = False

    def execute(self, context):
        """Pivot Point Show/Hide Button Function.

        Operational execute function for Show/Hide Pivot Point function

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        if context.area.type == "VIEW_3D":
            if context.window_manager.pdt_run_opengl is False:
                self.handle_add(self, context)
                context.area.tag_redraw()
            else:
                self.handle_remove(self, context)
                context.area.tag_redraw()

            return {"FINISHED"}
        else:
            self.report({"ERROR"}, PDT_ERR_NO3DVIEW)

        return {"CANCELLED"}


class PDT_OT_ViewPlaneRotate(Operator):
    """Rotate Selected Vertices about Pivot Point in View Plane"""

    bl_idname = "pdt.viewplanerot"
    bl_label = "PDT View Rotate"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])


    def execute(self, context):
        """Rotate Selected Vertices about Pivot Point.

        Rotates any selected vertices about the Pivot Point
        in View Oriented coordinates, works in any view orientation.

        Args:
            context: Current Blender bpy.context

        Notes:
            Uses pdt_pivotloc, pdt_pivotang scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        if obj.mode != "EDIT":
            errmsg = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            self.report({"ERROR"}, errmsg)
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        v1 = Vector((0, 0, 0))
        v2 = viewCoords(0, 0, 1)
        axis = (v2 - v1).normalized()
        rot = Matrix.Rotation((scene.pdt_pivotang * pi / 180), 4, axis)
        verts = verts = [v for v in bm.verts if v.select]
        bmesh.ops.rotate(
            bm, cent=scene.pdt_pivotloc - obj.matrix_world.decompose()[0], matrix=rot, verts=verts
        )
        bmesh.update_edit_mesh(obj.data)
        return {"FINISHED"}


class PDT_OT_ViewPlaneScale(Operator):
    """Scale Selected Vertices about Pivot Point"""

    bl_idname = "pdt.viewscale"
    bl_label = "PDT View Scale"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])


    def execute(self, context):
        """Scales Selected Vertices about Pivot Point.

        Scales any selected vertices about the Pivot Point
        in View Oriented coordinates, works in any view orientation

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_pivotloc, pdt_pivotscale scene variables

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        if obj.mode != "EDIT":
            errmsg = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            self.report({"ERROR"}, errmsg)
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        verts = verts = [v for v in bm.verts if v.select]
        for v in verts:
            dx = (scene.pdt_pivotloc.x - obj.matrix_world.decompose()[0].x - v.co.x) * (
                1 - scene.pdt_pivotscale.x
            )
            dy = (scene.pdt_pivotloc.y - obj.matrix_world.decompose()[0].y - v.co.y) * (
                1 - scene.pdt_pivotscale.y
            )
            dz = (scene.pdt_pivotloc.z - obj.matrix_world.decompose()[0].z - v.co.z) * (
                1 - scene.pdt_pivotscale.z
            )
            dv = Vector((dx, dy, dz))
            v.co = v.co + dv
        bmesh.update_edit_mesh(obj.data)
        return {"FINISHED"}


class PDT_OT_PivotToCursor(Operator):
    """Set The Pivot Point to Cursor Location"""

    bl_idname = "pdt.pivotcursor"
    bl_label = "PDT Pivot To Cursor"

    def execute(self, context):
        """Moves Pivot Point to Cursor Location.

        Moves Pivot Point to Cursor Location in active scene

        Args:
            context: Current Blender bpy.context

        Returns:
             Status Set.
        """

        scene = context.scene
        scene.pdt_pivotloc = scene.cursor.location
        return {"FINISHED"}


class PDT_OT_CursorToPivot(Operator):
    """Set The Cursor Location to Pivot Point"""

    bl_idname = "pdt.cursorpivot"
    bl_label = "PDT Cursor To Pivot"

    def execute(self, context):
        """Moves Cursor to Pivot Point Location.

        Moves Cursor to Pivot Point Location in active scene

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        scene.cursor.location = scene.pdt_pivotloc
        return {"FINISHED"}


class PDT_OT_PivotSelected(Operator):
    """Set Pivot Point to Selected Geometry"""

    bl_idname = "pdt.pivotselected"
    bl_label = "PDT Pivot to Selected"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])


    def execute(self, context):
        """Moves Pivot Point centroid of Selected Geometry.

        Moves Pivot Point centroid of Selected Geometry in active scene
        using Snap_Cursor_To_Selected, then puts cursor back to original location.

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        obj_loc = obj.matrix_world.decompose()[0]
        if obj.mode != "EDIT":
            errmsg = f"{PDT_ERR_EDIT_MODE} {obj.mode})"
            self.report({"ERROR"}, errmsg)
            return {"FINISHED"}
        bm = bmesh.from_edit_mesh(obj.data)
        verts = verts = [v for v in bm.verts if v.select]
        if len(verts) > 0:
            old_cursor_loc = scene.cursor.location.copy()
            bpy.ops.view3d.snap_cursor_to_selected()
            scene.pdt_pivotloc = scene.cursor.location
            scene.cursor.location = old_cursor_loc
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, PDT_ERR_NO_SEL_GEOM)
            return {"FINISHED"}


class PDT_OT_PivotOrigin(Operator):
    """Set Pivot Point at Object Origin"""

    bl_idname = "pdt.pivotorigin"
    bl_label = "PDT Pivot to Object Origin"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return all([bool(ob), ob.type == "MESH", ob.mode == "EDIT"])

    def execute(self, context):
        """Moves Pivot Point to Object Origin.

        Moves Pivot Point to Object Origin in active scene

        Args:
            context: Current Blender bpy.context

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        obj_loc = obj.matrix_world.decompose()[0]
        scene.pdt_pivotloc = obj_loc
        return {"FINISHED"}


class PDT_OT_PivotWrite(Operator):
    """Write Pivot Point Location to Object"""

    bl_idname = "pdt.pivotwrite"
    bl_label = "PDT Write PP to Object?"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return all([bool(ob), ob.type == "MESH"])

    def execute(self, context):
        """Writes Pivot Point Location to Object's Custom Properties.

        Writes Pivot Point Location to Object's Custom Properties
        as Vector to 'PDT_PP_LOC' - Requires Confirmation through dialogue

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_pivotloc scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        obj["PDT_PP_LOC"] = scene.pdt_pivotloc
        return {"FINISHED"}

    def invoke(self, context, event):
        return context.window_manager.invoke_props_dialog(self)

    def draw(self, context):
        row = self.layout
        row.label(text="Are You Sure About This?")


class PDT_OT_PivotRead(Operator):
    """Read Pivot Point Location from Object"""

    bl_idname = "pdt.pivotread"
    bl_label = "PDT Read PP"

    @classmethod
    def poll(cls, context):
        ob = context.object
        return all([bool(ob), ob.type == "MESH"])

    def execute(self, context):
        """Reads Pivot Point Location from Object's Custom Properties.

        Sets Pivot Point Location from Object's Custom Properties
        using 'PDT_PP_LOC'

        Args:
            context: Current Blender bpy.context

        Note:
            Uses pdt_pivotloc scene variable

        Returns:
            Status Set.
        """

        scene = context.scene
        obj = bpy.context.view_layer.objects.active
        if obj is None:
            self.report({"ERROR"}, PDT_ERR_NO_ACT_OBJ)
            return {"FINISHED"}
        if "PDT_PP_LOC" in obj:
            scene.pdt_pivotloc = obj["PDT_PP_LOC"]
            return {"FINISHED"}
        else:
            self.report({"ERROR"}, PDT_ERR_NOPPLOC)
            return {"FINISHED"}
