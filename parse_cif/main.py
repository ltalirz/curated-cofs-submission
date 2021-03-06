#!/usr/bin/env python
"""Add new entries to the CURATED-COFs files: cof-papers.csv and cof-frameworks.csv."""

import os
import numpy as np
import panel as pn
import pandas
import datetime
import re

pn.extension()

class CifParse():
    """Input form for CIF file"""

    def __init__(self):
        self.name_input = pn.widgets.TextInput(name='COF name', placeholder='Insert...')
        self.cell_input = pn.widgets.TextInput(name='Cell info', placeholder='a = b = 37.2145 37.2145 Å , c = 4.0878 Å, α = β = 90° 90 and γ = 120°')
        self.symm_input = pn.widgets.TextInput(name='Symm info', placeholder='P6')
        self.coord_input = pn.widgets.input.TextAreaInput(
            name='Atomic coord. info', 
            placeholder='Enter a string here...', 
            max_length=100000,
            height=800,
            )

        self.textbox = pn.widgets.input.TextAreaInput(
            name='Output CIF', 
            placeholder='Output CIF will be shown here...', 
            height=800
            )

        self.btn_parse = pn.widgets.Button(name='Parse CIF', button_type='primary')
        self.btn_parse.on_click(self.on_click_parse)

        from structure import structure_jsmol
        import bokeh.models as bmd
        self.jsmol_script_source = bmd.ColumnDataSource()
        self.applet = structure_jsmol(self.jsmol_script_source)
        
    def servable(self):
        """Layout of the CIF section of the page."""
        self.column = pn.Column(
            pn.pane.HTML("""<h2>Copy and Paste CIF's info</h2>"""),
            self.name_input,
            self.cell_input,
            self.symm_input,
            self.coord_input,
            self.btn_parse,
            pn.pane.Bokeh(self.applet),
            self.textbox,

            width=1000
        )
        return self.column.servable()

    def display(self, cif_str):
        """Update applet to show CIF."""
        from structure import structure_jsmol

        self.jsmol_script_source.data['script'] = [
"""load data "cifstring"
{}
end "cifstring"
""".format(str(cif_str))]
        
    def parse_cell_input(self):
        """Try first to understand a string like:
        'a = b = 37.2145Å, c = 4.0878 Å, α = β = 90° and γ = 120°'.
        If it fails, simply extract six floats.
        """
        fail_parsing = False

        data = self.cell_input.value
        data = re.sub("and", " ", data)  # remove "and" that makes conflicts with "a"
        data = re.sub("Ɣ", "γ", data)    # replace weird gamma
        data = re.sub("[^0-9.abcαβγ]", " ", data).split()
        if "." in data: data.remove(".") # remove isolate dots

        for i, val in enumerate(data):
            if val in 'abcαβγ':
                for j in data[i:]:
                    if j not in 'abcαβγ':
                        try:
                            self.cif_dict[val] = float(j)
                        except:
                            fail_parsing = True
                        break

        if fail_parsing or not all(celldim in self.cif_dict for celldim in 'abcαβγ'):
            data = self.cell_input.value
            data = re.sub("[^0-9.]", " ", data).split()
            if "." in data: data.remove(".")
            for i, celldim in enumerate('abcαβγ'):
                self.cif_dict[celldim] = float(data[i])

    def on_click_parse(self, event):
        self.cif_dict = {} # Reset to avoid problems
        self.parse_cell_input() 

        self.cif_dict['symm'] = self.symm_input.value

        self.cif_dict['coord'] = []

        for line in self.coord_input.value.splitlines():
            cols = len(line.split())
            # skip len==0, and len==1 (pagenumbers)
            if cols==4:
                self.cif_dict['coord'].append(line)
            if cols==5:
                d = line.split()
                newline = f'{d[0]} {d[2]} {d[3]} {d[4]}'
                self.cif_dict['coord'].append(newline)
            if cols==8:
                d = line.split()
                newline1 = f'{d[0]} {d[1]} {d[2]} {d[3]}'
                newline2 = f'{d[4]} {d[5]} {d[6]} {d[7]}'
                self.cif_dict['coord'].append(newline1)
                self.cif_dict['coord'].append(newline2)

        filename = self.name_input.value.strip() + ".cif"
        with open(filename, 'w') as ofile:
            print()

            print("data_crystal", file=ofile)
            print(" ", file=ofile)
            print("_cell_length_a    %.5f" % self.cif_dict['a'], file=ofile)
            print("_cell_length_b    %.5f" % self.cif_dict['b'], file=ofile)
            print("_cell_length_c    %.5f" % self.cif_dict['c'], file=ofile)
            print("_cell_angle_alpha %.5f" % self.cif_dict['α'], file=ofile)
            print("_cell_angle_beta  %.5f" % self.cif_dict['β'], file=ofile)
            print("_cell_angle_gamma %.5f" % self.cif_dict['γ'], file=ofile)
            print(" ", file=ofile)
            print(f"_symmetry_space_group_name_H-M  '{self.cif_dict['symm']}'", file=ofile)
            print(" ", file=ofile)
            print("loop_", file=ofile)
            print("_atom_site_label", file=ofile)
            #print("_atom_site_type_symbol", file=ofile)
            print("_atom_site_fract_x", file=ofile)
            print("_atom_site_fract_y", file=ofile)
            print("_atom_site_fract_z", file=ofile)
            for line in self.cif_dict['coord']:
                print(line, file=ofile)

        self.textbox.value = open(filename, 'r').read()

        print ('Printed CIF file:', filename)

        from ase.io import read, write
        from ase.io.cif import write_cif
        from ase.geometry.dimensionality import analyze_dimensionality
        from ase.build import make_supercell

        atoms = read(filename, format='cif') # need to load to unwrap?

        import tempfile
        with tempfile.TemporaryFile() as handle:
            write(handle, atoms, format='cif')
            handle.seek(0)
            self.cif_str = handle.read()

        self.display(self.cif_str.decode())

        

cif = CifParse()
cif.servable()
