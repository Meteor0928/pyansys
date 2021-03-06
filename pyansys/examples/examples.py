"""
pyansys examples

"""

from __future__ import print_function
import os, inspect, sys

import pyansys


# get location of this folder and the example files
dir_path = os.path.dirname(os.path.realpath(__file__))
rstfile = os.path.join(dir_path, 'file.rst')
hexarchivefile = os.path.join(dir_path, 'HexBeam.cdb')
tetarchivefile = os.path.join(dir_path, 'TetBeam.cdb')
hexbeamfile = os.path.join(dir_path, 'hexbeam.vtk')
fullfile = os.path.join(dir_path, 'file.full')

    
def RunAll():
    """ Runs all the functions within this module """
    testfunctions = []
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isfunction(obj) and name != 'RunAll':
              testfunctions.append(obj)      

    # run all the functions
    any(f() for f in testfunctions)


def DisplayHexBeam():
    """ Displays a hex beam mesh """
    # Load an archive file
    archive = pyansys.ReadArchive(hexarchivefile)
    archive.ParseFEM()
    archive.uGrid.Plot()
    

def LoadResult():
    """
    Loads a result file and prints out the displacement of all the nodes from
    a modal analysis.
    
    """
    
    # Load result file
    result = pyansys.ResultReader(rstfile)
    print('Loaded result file with {:d} result sets'.format(result.nsets))
    print('Contains {:d} nodes'.format(len(result.nnum)))

    # display result
    disp = result.GetNodalResult(0)

    print('Nodal displacement for nodes 30 to 40 is:')
   
    for i in range(29, 40):
        node = result.nnum[i]
        x = disp[i, 0]
        y = disp[i, 1]
        z = disp[i, 2]
        print('{:2d}  {:10.6f}   {:10.6f}   {:10.6f}'.format(node, x, y, z))


def DisplayDisplacement():
    """ Load and plot 1st bend of a hexahedral beam """
    
    # get location of this file
    fobj = pyansys.ResultReader(rstfile)
    
    print('Displaying ANSYS Mode 1')
    fobj.PlotNodalResult(0, label='Displacement')
    
    
def DisplayStress():
    """ Load and plot 1st bend of a hexahedral beam """
    
    # get location of this file
    result = pyansys.ResultReader(rstfile)
    
    print('Displaying node averaged stress in x direction for Mode 6')
    result.PlotNodalStress(5, 'Sx')


def LoadKM():
    """ Loads m and k matrices from a full file """
    import numpy as np
    
    # Create file reader object
    fobj = pyansys.FullReader(fullfile)
    dofref, k, m = fobj.LoadKM(utri=False)

    # print results
    ndim = k.shape[0]
    print('Loaded {:d} x {:d} mass and stiffness matrices'.format(ndim, ndim))
    print('\t k has {:d} entries'.format(k.indices.size))
    print('\t m has {:d} entries'.format(m.indices.size))

    # compute natural frequencies if installed
    try:
        from scipy.sparse import linalg
    except:
        return

    # removing constrained nodes (this is not efficient)
    free = np.logical_not(fobj.const).nonzero()[0]
    k = k[free][:, free]
    m = m[free][:, free]
    
    import numpy as np
    # Solve
    w, v = linalg.eigsh(k, k=20, M=m, sigma=10000)

    # System natural frequencies
    f = np.real(w)**0.5/(2*np.pi)
    
    print('First four natural frequencies:')
    for i in range(4):
        print('{:.3f} Hz'.format(f[i]))
        
        
def SolveKM():
    """ 
    Loads and solves a mass and stiffness matrix from an ansys full file
    """
    import numpy as np
    from scipy.sparse import linalg
    import pyansys
    
    
    # load the mass and stiffness matrices
    full = pyansys.FullReader(pyansys.examples.fullfile)
    dofref, k, m = full.LoadKM(utri=False)
    
    # removing constrained nodes (this is not efficient)
    free = np.logical_not(full.const).nonzero()[0]
    k = k[free][:, free]
    m = m[free][:, free]
    
    # Solve
    w, v = linalg.eigsh(k, k=20, M=m, sigma=10000)
    
    # System natural frequencies
    f = (np.real(w))**0.5/(2*np.pi)
    
    
    #%% Plot result
    import vtkInterface

    # Get the 4th mode shape
    mode_shape = v[:, 3] # x, y, z displacement for each node
    
    # create the full mode shape including the constrained nodes
    full_mode_shape = np.zeros(dofref.shape[0])
    full_mode_shape[np.logical_not(full.const)] = mode_shape
    
    # reshape and compute the normalized displacement
    disp = full_mode_shape.reshape((-1, 3))
    n = (disp*disp).sum(1)**0.5
    n /= n.max() # normalize
    
    # load an archive file and create a vtk unstructured grid
    archive = pyansys.ReadArchive(pyansys.examples.hexarchivefile)
    grid = archive.ParseVTK()
    
    # plot the normalized displacement
#    grid.Plot(scalars=n)
    
    # Fancy plot the displacement
    plobj = vtkInterface.PlotClass()
    
    # add two meshes to the plotting class.  Meshes are copied on load
    plobj.AddMesh(grid, style='wireframe')
    plobj.AddMesh(grid, scalars=n, stitle='Normalized\nDisplacement',
                  flipscalars=True)
    
    # Update the coordinates by adding the mode shape to the grid
    plobj.UpdateCoordinates(grid.GetNumpyPoints() + disp/80, render=False)
    plobj.AddText('Cantliver Beam 4th Mode Shape at {:.4f}'.format(f[3]),
                  fontsize=30)
    plobj.Plot(); del plobj


def DisplayCellQual(meshtype='tet'):
    """ 
    Displays minimum scaled jacobian of a sample mesh
    
    For an ANSYS analysis to run properly, the minimum scaled jacobian of each
    cell must be greater than 0.
    
    Parameters
    ----------
    meshtype string, optional 
        Set to 'hex' to display cell quality of a hexahedral meshed beam.
        
    Returns
    -------
    None
    
    """
    
    # load archive file and parse for subsequent FEM queries
    if meshtype == 'hex':
        archive = pyansys.ReadArchive(hexarchivefile)
    else:
        archive = pyansys.ReadArchive(tetarchivefile)
            
    # create vtk object
    archive.ParseFEM()

    # get cell quality
    qual = pyansys.CellQuality(archive.uGrid)
    
    # plot cell quality
    archive.uGrid.Plot(scalars=qual, stitle='Cell Minimum Scaled\nJacobian',
                       rng=[0, 1])
    
