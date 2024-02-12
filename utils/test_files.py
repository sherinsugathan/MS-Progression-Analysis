import os
import vtk

path = "C:/Sherin/Workspace/1_ProjectSource/27_Samuel_MS_Feature/Subjects_Matched_new/Subjects_Matched/1001BC/1001BC_m00_m12_snacai/Lesion_7_baseline.nii.gz"

reader_baseline = vtk.vtkNIFTIImageReader()
reader_baseline.SetFileName(path)
reader_baseline.Update()

surface_baseline = vtk.vtkDiscreteMarchingCubes()
surface_baseline.SetInputConnection(reader_baseline.GetOutputPort())
surface_baseline.Update()

mapper = vtk.vtkPolyDataMapper()
mapper.SetInputData(surface_baseline.GetOutput())
mapper.Update()
lesionActor = vtk.vtkActor()
lesionActor.SetMapper(mapper)

# Create a renderer and add the cone actor to it
renderer = vtk.vtkRenderer()
renderer.AddActor(lesionActor)
renderer.SetBackground(0.1, 0.2, 0.4)

# Create a render window
renderWindow = vtk.vtkRenderWindow()
renderWindow.AddRenderer(renderer)

# Create a render window interactor
renderWindowInteractor = vtk.vtkRenderWindowInteractor()
renderWindowInteractor.SetRenderWindow(renderWindow)

# Initialize the interactor and start the rendering loop
renderWindow.Render()
renderWindowInteractor.Initialize()
renderWindowInteractor.Start()