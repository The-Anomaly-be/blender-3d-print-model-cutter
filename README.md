# 3D Print Model Cutter Blender Add-on

**3D Print Model Cut** is a Blender add-on I made initially for my own use, it splits a 3D mesh model into 8 manifold parts, each with male and female connectors, to facilitate 3D printing and assembly. The script ensures that all resulting parts are watertight and suitable for printing, with centered origins and intuitive naming based on the original model.

Print bigger pieces in any printer. Take a look at the youtube video here to see how it works:
https://youtu.be/ZIDgdPFDEcg

## Features
- **Model Splitting**: Divides a selected mesh into 8 parts (left/right, front/back, top/bottom).
- **Connectors**: Adds male and female connectors for easy assembly of printed parts, some extra space is available in the holes for glue or to deal with 3D print inconsistencies.
- **Manifold Output**: Ensures all parts are closed, watertight meshes suitable for 3D printing.
- **Practical Naming**: Names parts using the original model name (e.g., `ModelName_right_front_top`).
- **Centered Origins**: Sets each part’s origin to its geometric center for easier handling.

## Requirements
- Blender 4.2.0 or later (not tested in lower versions but it should work)
- A manifold (watertight) mesh model is needed for best results

## Installation
1. **Download the Script**:
   - Clone this repository or download the `3d_print_model_cut.py` file.

2. **Install in Blender**:
   - Open Blender and go to `Edit > Preferences > Add-ons`.
   - Click `Install...` and select the `3d_print_model_cut.py` file.
   - Enable the add-on by checking the box next to "Object: 3D Print Model Cut".

3. **Verify Installation**:
   - In the 3D Viewport, look for the `3D Print Model Cut` tab in the Sidebar (`N` key to toggle).

## How to Use
Follow these steps to split your 3D model into 8 printable parts:

1. **Prepare Your Model**:
   - Import or create a 3D mesh model in Blender.
   - Ensure the model is manifold (watertight) for best results. You can check this using Blender’s 3D Print Toolbox add-on or by selecting the model and running `Select > Select All by Trait > Non Manifold` in Edit Mode.
   - Apply all transformations (`Ctrl+A > All Transforms`) to reset scale, rotation, and location.

2. **Select the Model**:
   - In Object Mode, select the mesh you want to split.
   - Ensure only one mesh is selected and it’s active (highlighted in orange).

3. **Access the Add-on**:
   - Open the Sidebar in the 3D Viewport by pressing `N` or clicking the right arrow.
   - Navigate to the `3D Print Model Cut` tab.

4. **Run the Script**:
   - Click the `3D Print Model Cut` button in the panel.
   - The script will:
     - Split the model into 8 parts.
     - Add male and female connectors for assembly.
     - Name each part with the original model name and position (e.g., `ModelName_right_front_top`).
     - Center the origin of each part.
     - Ensure all parts are manifold.

5. **Be Patient**:
   - The more complex your model is, the more time it will take. Sometimes I had to wait for more than 10 minutes on a high-end PC before seeing the result.
   - Blender will look like it's stuck but it's simply processing. Just wait, go grab a coffee :)

7. **Check the Results**:
   - The original model remains unchanged, and 8 new mesh objects appear in the scene.
   - Inspect the parts in the Outliner or 3D Viewport. Each part is named clearly (e.g., `ModelName_left_back_bottom`).
   - Check the Blender Console (`Window > Toggle System Console`) for warnings about non-manifold issues, especially if your model has complex geometry.

8. **Export for 3D Printing**:
   - Select each part and export it as an STL file (`File > Export > STL`).
   - Ensure the export settings match your 3D printer’s requirements (e.g., units in millimeters).
   - Print the parts and assemble them using the connectors.

## Troubleshooting
- **Non-Manifold Parts**: If warnings appear about open edges, your model may have non-manifold geometry. Use Blender’s 3D Print Toolbox to identify and fix issues (e.g., `Mesh > Clean Up > Fill Holes` in Edit Mode).
- **Parts Missing Geometry**: Increase the `Scale Factor` (e.g., to 1.2) to ensure cutting cubes fully intersect the model.
- **Boolean Errors**: Simplify complex models or check for overlapping geometry before running the script.
- **Console Warnings**: Check the Blender Console for detailed messages about specific parts (e.g., `right_front_top`) that may need manual inspection.

## Contributing
Contributions are welcome! To contribute:
1. Fork the repository.
2. Create a new branch (`git checkout -b feature/your-feature`).
3. Make changes and test thoroughly in Blender.
4. Submit a pull request with a clear description of your changes.

Please ensure your code follows Blender’s Python API conventions, includes comments for clarity, and adheres to the terms of the GPL-3.0 license.

## License
This project is licensed under the **GNU General Public License v3.0** (GPL-3.0). See the [LICENSE](LICENSE) file for details.

The GPL-3.0 ensures that this software remains free and open-source. Any derivative works or distributions must also be licensed under GPL-3.0, and the source code must be made available.

## Acknowledgments
- Built with the Blender Python API.
- Inspired by the need for easy-to-assemble big sized 3D-printed models :)
- Thanks to the Blender community for resources and feedback.
