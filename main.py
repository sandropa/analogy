import xml.etree.ElementTree as ET
import zipfile
import uuid

class GeoGebra:
    """
    A class to programmatically create modern, compliant GeoGebra (.ggb) files.
    """
    def __init__(self, app='suite', sub_app='graphing'):
        # --- 1. Replicate the full XML structure ---
        
        # Define namespaces and other root attributes
        self.root_attribs = {
            "format": "5.0",
            "version": "5.2.892.0",
            "app": app,
            "subApp": sub_app,
            "platform": "w", # w for web
            "id": str(uuid.uuid4()),
            "xsi:noNamespaceSchemaLocation": "http://www.geogebra.org/apps/xsd/ggb.xsd",
            "xmlns": "",
            "xmlns:xsi": "http://www.w3.org/2001/XMLSchema-instance",
        }
        self.root = ET.Element('geogebra', self.root_attribs)

        # Add the main structural tags with default values
        self._add_gui()
        self._add_euclidian_view()
        self._add_kernel()
        
        # The construction is where we'll add objects
        self.construction = ET.SubElement(self.root, 'construction')

    def _add_gui(self):
        """Adds a default <gui> structure."""
        gui = ET.SubElement(self.root, 'gui')
        ET.SubElement(gui, 'window', width="1280", height="800")
        # A minimal perspective is sufficient for the file to open
        perspectives = ET.SubElement(gui, 'perspectives')
        perspective = ET.SubElement(perspectives, 'perspective', id="graphing")
        panes = ET.SubElement(perspective, 'panes')
        ET.SubElement(panes, 'pane', location="", divider="0.25", orientation="1")
        views = ET.SubElement(perspective, 'views')
        ET.SubElement(views, 'view', id="1", visible="true", inframe="false", stylebar="false", location="1", size="950", window="100,100,600,400")
        ET.SubElement(views, 'view', id="2", visible="true", inframe="false", stylebar="false", location="3", size="300", tab="ALGEBRA", window="100,100,600,400")
        ET.SubElement(gui, 'labelingStyle', val="1")
        ET.SubElement(gui, 'font', size="16")

    def _add_euclidian_view(self):
        """Adds a default <euclidianView>."""
        ev = ET.SubElement(self.root, 'euclidianView')
        ET.SubElement(ev, 'viewNumber', viewNo="1")
        ET.SubElement(ev, 'size', width="880", height="606")
        ET.SubElement(ev, 'coordSystem', xZero="440", yZero="303", scale="50", yscale="50")
        ET.SubElement(ev, 'evSettings', axes="true", grid="true", gridIsBold="false", pointCapturing="3", rightAngleStyle="1", checkboxSize="26", gridType="3")
        ET.SubElement(ev, 'bgColor', r="255", g="255", b="255")
        ET.SubElement(ev, 'axesColor', r="0", g="0", b="0")
        ET.SubElement(ev, 'gridColor', r="192", g="192", b="192")

    def _add_kernel(self):
        """Adds a default <kernel>."""
        kernel = ET.SubElement(self.root, 'kernel')
        ET.SubElement(kernel, 'continuous', val="false")
        ET.SubElement(kernel, 'usePathAndRegionParameters', val="true")
        ET.SubElement(kernel, 'decimals', val="2")
        ET.SubElement(kernel, 'angleUnit', val="degree")
        ET.SubElement(kernel, 'algebraStyle', val="3")
        ET.SubElement(kernel, 'coordStyle', val="0")

    def _create_element_base(self, el_type, label, color, layer=0, visible=True, label_visible=True):
        """Helper to create a basic element with common properties."""
        element = ET.Element('element', type=el_type, label=label)
        ET.SubElement(element, 'show', object=str(visible).lower(), label=str(label_visible).lower())
        ET.SubElement(element, 'objColor', r=str(color[0]), g=str(color[1]), b=str(color[2]), alpha="0")
        ET.SubElement(element, 'layer', val=str(layer))
        ET.SubElement(element, 'labelMode', val="0")
        return element

    def add_point(self, label, x, y, size=5, color=(21, 101, 192)):
        """Adds a free point to the construction."""
        element = self._create_element_base('point', label, color)
        ET.SubElement(element, 'pointSize', val=str(size))
        ET.SubElement(element, 'pointStyle', val="0")
        ET.SubElement(element, 'coords', x=str(x), y=str(y), z="1.0")
        self.construction.append(element)

    def add_line_by_coeffs(self, label, a, b, c, color=(0, 103, 88)):
        """Adds a line defined by Ax + By + C = 0."""
        # Add the human-readable expression first
        exp = f"{a}x + {b}y + {c} = 0" # This is a simplification, but works
        ET.SubElement(self.construction, 'expression', label=label, exp=exp, type="line")
        
        element = self._create_element_base('line', label, color)
        ET.SubElement(element, 'fixed', val="false")
        ET.SubElement(element, 'lineStyle', thickness="5", type="0")
        # The coordinates for a line are its coefficients A, B, C
        ET.SubElement(element, 'coords', x=str(a), y=str(b), z=str(c))
        self.construction.append(element)

    def add_segment(self, label, point1_label, point2_label, color=(200, 0, 200)):
        """Adds a line segment between two existing points."""
        # --- 2. Fix the command/element order and structure ---
        
        # The <command> must come BEFORE the <element>
        command = ET.SubElement(self.construction, 'command', name="Segment")
        ET.SubElement(command, 'input', a0=point1_label, a1=point2_label)
        ET.SubElement(command, 'output', a0=label)
        
        # The dependent <element> does NOT have an <input> tag
        element = self._create_element_base('segment', label, color)
        ET.SubElement(element, 'lineStyle', thickness="5")
        self.construction.append(element)
        
    def add_orthogonal_line(self, label, point_label, line_label, color=(0,0,0)):
        """Adds a line orthogonal to a given line through a given point."""
        command = ET.SubElement(self.construction, 'command', name="OrthogonalLine")
        ET.SubElement(command, 'input', a0=point_label, a1=line_label)
        ET.SubElement(command, 'output', a0=label)
        
        element = self._create_element_base('line', label, color)
        ET.SubElement(element, 'lineStyle', thickness="5")
        self.construction.append(element)

    def save(self, filename):
        """Saves the construction to a .ggb file."""
        if not filename.endswith('.ggb'):
            filename += '.ggb'
        
        # Register the 'xsi' namespace prefix to avoid it being written as 'ns0'
        ET.register_namespace('xsi', "http://www.w3.org/2001/XMLSchema-instance")
        
        # Convert the XML tree to a string with the XML declaration
        xml_string = ET.tostring(self.root, encoding='utf-8', method='xml', xml_declaration=True)

        with zipfile.ZipFile(filename, 'w', zipfile.ZIP_DEFLATED) as zf:
            zf.writestr('geogebra.xml', xml_string)
            
        print(f"Successfully created compliant GeoGebra file: {filename}")

# --- Main execution ---
if __name__ == "__main__":
    ggb = GeoGebra()

    # --- Example 1: Recreate the file from your XML analysis ---
    print("Creating example with orthogonal line...")
    # Line f: y = 2  -->  0x + 1y - 2 = 0
    ggb.add_line_by_coeffs("f", a=0, b=1, c=-2, color=(0, 103, 88))
    ggb.add_point("A", x=-3, y=4, color=(21, 101, 192))
    ggb.add_orthogonal_line("g", point_label="A", line_label="f", color=(0,0,0))

    # --- Example 2: The original goal of a segment between two points ---
    print("Creating example with a segment...")
    ggb.add_point("P", x=5, y=5)
    ggb.add_point("Q", x=8, y=1)
    ggb.add_segment("seg1", "P", "Q", color=(255, 87, 34))

    ggb.save("python_geogebra_v2.ggb")