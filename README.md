<img width="997" height="249" alt="immeshexporter" src="https://github.com/user-attachments/assets/f879bf4e-9f62-4bc6-8762-accbf54034e9" />
A WIP, modern, pre-2.8 indexed mesh exporter for Trainz and the Auran JET engine.

This exporter is designed to be a replacement for the well-used legacy exporter written by USCHI0815 (Torsten), due to how inefficiant the model's exported can be (blender->xml->TrainzMeshImporter.exe->.im).
Rather than relying on the old and frustratingly slow importer executable the 2.4 exporter used (TrainzMeshImporter.exe, created by N3V Games), this exporter writes to the indexed mesh file directly instead of using XML as a middleman. This results in a much tidier and easily maintained codebase, faster exports for content creators, and fine-tuned control over what versions of the JET/E2 game engines the file will work in and what data the file will contain (tangents, skinning, texture slots, etc).
While rileyzzzz has expressed 0 interest in backporting this to Blender 2.7x, it is a necessity due to the above, alongside sharp-normal support (no more edgesplit!).
This is (probably) a very stupid move, but given that pre-2.8 users are stuck with the nonsense, it makes sense to port over the 2.8 one.

The exporter currently supports the serialization of vertex and index data of triangle meshes (meshes will be automatically triangulated on export), texture coordinates, both per-vertex and per-face normals, vertex tangents (optional), bounding box export (optional), material data from the Principled BSDF node (see below, both solid RGB colors and texture slots supported), animated scenes (for either armature or dummy object hierarchies) through the generation of separate .kin files, and automatic texture.txt metadata generation for any of the mesh's dependent texture files.

An export option is provided to force the usage of wide strings within the exported .im file. As this type of string data is rarely used within exported .im/.kin files (the only notable example being the PB15 fireman), tools dealing with the .im format often fail to parse (or crash) when encountering wide strings. Although the intended purpose of the wide string data is to allow for an extended character set when naming materials or textures, it can also serve as a means of protection against software that isn't fully conformant with the .im spec. If you want to protect your model against ripping software or attachment edits, this option may be beneficial.

Once again, this exporter is a work in progress, so if you find any bugs, make sure to create a GitHub issue or bring it to my attention so I can investigate it.

Each of the material data from the principled BSDF node is mapped to the file according to the table below, with target slot types referenced from the Auran JET specification.
If a texture slot is denoted as "Unused by Trainz", while some existing Trainz material types that utilize these texture slots have been documented, they broke upon Trainz 2009's release. They are maintained to ensure maximum compatibility with the Auran JET specification. Note however that the unused texture's solid color counterpart is separate from the texture data, and if a Solid Color slot is not marked as N/A and has a value that isn't a texture during export, it WILL be written to the .im material data, which is ALL used by Trainz.

Material Slot | Target .IM Data (Solid Color)   | Target .IM Data (Texture)
------------- | ------------------------------- | -------------------------
Base Color    | Material Diffuse & Ambient      | Diffuse Texture
Specular      | Material Specular {0-1 to RGB}  | Specular Texture (unused by Trainz)
Roughness     | Shininess {(1.0 - rough) * 128} | Shine Texture (unused by Trainz)
Metallic      | N/A                             | Reflection Texture (spheremap used by m.reflect, etc)
Normal        | N/A                             | Normal Map Texture (must have a Normal Map node between the texture and Principled BSDF)
Alpha         | Material Opacity                | Opacity Texture (should support using the same diffuse texture node for both diffuse and alpha slots)
Emission      | Emissive Color                  | Selfillum Texture (unused by Trainz)
IOR           | N/A                             | Refraction Texture (unused by Trainz)

There were several additional texture slots in the JET spec that are unsupported by Trainz (TEX_Ambient, TEX_Filtercolor, and TEX_Displacement). They are not currently supported by the exporter, nor should be due to versioning differences since Trainz 2009 (see here - https://trainz.shaneturner.co.uk/3rdparty/PM2IM%20Tutorial.pdf ).

On the materials tab, you will find a new interface called "Trainz IM Mesh Exporter", and it will (eventually) contain some handy features for exporting.
A new feature found in this release is a dropdown selection for Material Types (m.)

*Material Types per Trainz Versions for PM/IM Meshs*
Introduced in Trainz     | Introduced in Ultimate Trainz Collection | Introduced in Trainz 2004 | Introduced in Trainz 2006 / Classics 1 & 2 / 3 | Introduced in Trainz 2009   | Introduced in Trainz 2010/2012 | Introduced in Trainz: A New Era
--------------------     | ---------------------------------------- | ------------------------- | ---------------------------------------------- | --------------------------- | ------------------------------ | -------------------------------
m.tribillboard (unused)  | -> carried over                          | -> carried over           | -> carried over                            	 | -> carried over             | -> carried over                | Removed
m.billboard (unused)     | -> carried over                          | -> carried over           | -> carried over                            	 | -> carried over             | -> carried over                | Removed
m.reflect                | -> carried over                          | -> carried over           | -> carried over                            	 | -> carried over             | -> carried over                | -> carried over 
m.gloss                  | -> carried over                          | -> carried over           | -> carried over                            	 | -> carried over             | -> carried over                | -> carried over 
m.onetex                 | -> carried over                          | -> carried over           | -> carried over                     			 | -> carried over             | -> carried over                | -> carried over 
m.notex                  | -> carried over                          | -> carried over           | -> carried over                           	 | -> carried over             | -> carried over                | -> carried over 
None                     | None                                     | m.tbumptex                | -> carried over                          	  	 | -> carried over             | -> carried over                | -> carried over 
None                     | None                                     | m.tbumpgloss              | -> carried over                             	 | -> carried over             | -> carried over                | -> carried over 
None                     | None                                     | m.tglossrust (unused)     | -> carried over                          	     | -> carried over             | -> carried over                | Removed
None                     | None                                     | None                      | None                                           | m.tbumpenv                  | -> carried over                | -> carried over 
None                     | None                                     | None                      | None                                           | m.tbumpglosscol (unused)    | -> carried over                | -> carried over 
None                     | None                                     | None                      | None                                           | m.tbumpcoltex (unused)      | -> carried over                | -> carried over 
None                     | None                                     | None                      | None                                           | m.nofogtex (unused)         | -> carried over                | Removed
None                     | None                                     | None                      | None                                           | m.tonetexnoalpha (unused)   | -> carried over                | Removed
None                     | None                                     | None                      | None                                           | m.tgroundonetex (unused)    | -> carried over                | -> carried over
None                     | None                                     | None                      | None                                           | m.groundbase (unused)       | -> carried over                | Removed

There is alot of unused ones, which are not included with the dropdown list.

## Installation
1. Select `Code -> Download ZIP` at the top of this page.
2. In Blender, go to `File -> User Preferences -> Add-ons`, select `Install from File...`, and navigate to the downloaded zip file.
3. Search for `Indexed Mesh` in the addons list and click the checkbox to enable the addon.
4. `Save User Settings` in the menu at the bottom left of the window.
