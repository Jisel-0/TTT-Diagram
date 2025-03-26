#!/usr/bin/env python3
#! -*- coding: utf-8 -*-

"""
Plot TTT and CCT diagrams
"""
import argparse
import matplotlib.pyplot as plt
from transformation_models_modified import Alloy, TransformationDiagrams

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Script for plotting TTT and CCT diagrams',
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)

    parser.add_argument('-g', '--gs', type=float, default=7, help='ASTM grain size number')
    parser.add_argument('-C', '--C', type=float, default=0., help='Carbon wt.%%')
    parser.add_argument('-Si', '--Si', type=float, default=0., help='Silicon wt.%%')
    parser.add_argument('-Mn', '--Mn', type=float, default=0., help='Manganese wt.%%')
    parser.add_argument('-Ni', '--Ni', type=float, default=0., help='Nickel wt.%%')
    parser.add_argument('-Mo', '--Mo', type=float, default=0., help='Molybdenum wt.%%')
    parser.add_argument('-Cr', '--Cr', type=float, default=0., help='Chromium wt.%%')
    parser.add_argument('-V', '--V', type=float, default=0., help='Vanadium wt.%%')
    parser.add_argument('-Co', '--Co', type=float, default=0., help='Cobalt wt.%%')
    parser.add_argument('-Cu', '--Cu', type=float, default=0., help='Copper wt.%%')
    parser.add_argument('-Al', '--Al', type=float, default=0., help='Aluminium wt.%%')
    parser.add_argument('-W', '--W', type=float, default=0., help='Tungsten wt.%%')
    parser.add_argument('-Tini', '--Tini', type=float, default=900.,
                        help='Initial continuous cooling temperature (oC)')
    parser.add_argument('-e', '--exp', action='store_true', help='Export to .xlsx format')
    parser.add_argument('-N', '--N', type=float, default=0., help='Nitrogen wt.%%')
    parser.add_argument('-Nb', '--Nb', type=float, default=0., help='Niobium wt.%%')
    parser.add_argument('-Ti', '--Ti', type=float, default=0., help='Titanium wt.%%')
    parser.add_argument('-Ru', '--Ru', type=float, default=0., help='Ruthenium wt.%%')
    parser.add_argument('-B', '--B', type=float, default=0., help='Boron wt.%%')
    parser.add_argument('-Fe', '--Fe', type=float, default=0., help='Iron wt.%%')

    args = parser.parse_args()
    comp = vars(args)
    gs = comp.pop('gs')
    Tini = comp.pop('Tini')
    export = comp.pop('exp')
    # Los demás argumentos se pasan tal cual al constructor de Alloy (incluso si no se usan)

    # Defines alloy (grain size gs and composition)
    alloy = Alloy(gs=gs, **comp)

    # Initializes diagrams object
    diagrams = TransformationDiagrams(alloy)

    fig, ax1 = plt.subplots(figsize=(8, 6))

    # Plot TTT
    diagrams.TTT(ax=ax1)

    title = 'TTT'

    if export:
        try:
            fout = '{}_TTT.xlsx'.format(title.strip(' (wt.%)'))
            print('Exporting data to {}'.format(fout))
            diagrams.df_TTT.to_excel(fout)
        except Exception as ex:
            print(ex)

    fig.suptitle(title)
    plt.show()