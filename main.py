import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QWidget
import vtk
import argparse
import os
import glob
import preprocess
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkRenderingCore import (
    vtkActor,
    vtkActor2D,
    vtkCoordinate,
    vtkPolyDataMapper,
    vtkPolyDataMapper2D,
    vtkRenderWindow,
    vtkRenderWindowInteractor,
    vtkRenderer,
    vtkTextMapper,
    vtkTextProperty,
    vtkViewport
)

class MSApp(QMainWindow):
    def __init__(self, args, parent=None):
        super(MSApp, self).__init__(parent)

        # Process command line arguments
        parser = argparse.ArgumentParser(description="MS - Progression Analysis")
        parser.add_argument("--subjectfolder", type=str, help="Subject folder")
        args = parser.parse_args(args)

        self.subject_folder = args.subjectfolder
        self.subject_name = os.path.basename(os.path.normpath(self.subject_folder))
        followup_prefix = self.subject_name + "_"
        self.followup_folder_names = [f for f in glob.glob(os.path.join(self.subject_folder, followup_prefix + '*')) if os.path.isdir(f)]

        self.followup_count = len(self.followup_folder_names)
        self.baseline = self.followup_folder_names[0] + "/Baseline_IDs.nii.gz"
        self.followup = self.followup_folder_names[0] + "/Followup_IDs.nii.gz"
        print("Number of followup data found: ", self.followup_count - 1)
        self.currentFollowup = 0
        self.actor = None
        self.is_followup = False
        self.is_comparison = False
        self.view_choice = 0
        self.current_view = 0
        self.comparison_actor = None
        self.last_actor_choice = 0

        # Set up the main window
        self.setWindowTitle("MS - Progression Analysis")
        self.frame = QWidget()
        self.vl = QVBoxLayout()
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        self.vl.addWidget(self.vtkWidget)

        # Create a renderer and add it to the window
        self.renderer = vtk.vtkRenderer()
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtkWidget.GetRenderWindow().GetInteractor()
        self.interactor.AddObserver("KeyPressEvent", self.keypress_callback)
        self.renderer.SetBackground(0.1, 0.2, 0.4)  # Background color


        #self.renderSlider()

        modes = [
            vtkViewport.GradientModes.VTK_GRADIENT_VERTICAL,
            vtkViewport.GradientModes.VTK_GRADIENT_HORIZONTAL,
            vtkViewport.GradientModes.VTK_GRADIENT_RADIAL_VIEWPORT_FARTHEST_SIDE,
            vtkViewport.GradientModes.VTK_GRADIENT_RADIAL_VIEWPORT_FARTHEST_CORNER,
        ]
        colors = vtk.vtkNamedColors()
        self.renderer.GradientBackgroundOn()
        self.renderer.SetGradientMode(modes[2])
        self.renderer.SetBackground([15/255, 32/255, 39/255])
        self.renderer.SetBackground2([44/255, 83/255, 100/255])
        # Start the interaction
        self.frame.setLayout(self.vl)
        self.setCentralWidget(self.frame)

        self.interactor.Initialize()
        self.openglRendererInUse = self.vtkWidget.GetRenderWindow().ReportCapabilities().splitlines()[1].split(":")[1].strip()
        self.read_subject_data()
        #self.show()

        #self.interactor.Start()
        self.resize(1500, 1500)

        #print(self.vtkWidget.GetRenderWindow().ReportCapabilities())
        # Add OpenGL context information as text overlay
        self.text_overlay()
        self.renderer.ResetCamera()

    def text_overlay(self):
        self.textActor = vtk.vtkTextActor()
        current_view = ""
        if(self.view_choice == 0):
            current_view = "BASELINE"
        elif(self.view_choice == 1):
            current_view = "FOLLOWUP"
        else:
            current_view = "COMPARISON"

        self.textActor.SetInput(f"Shortcut keys:\n--------------------\n<  > : Previous, Next\nT : Toggle Baseline/Followup\nC : Compare View\n--------------------\nData: {os.path.basename(self.followup_folder_names[self.currentFollowup])}\nCurrently Viewing: {current_view}\nOpenGL Context: {self.openglRendererInUse}")
        self.textActor.GetTextProperty().SetColor(1.0, 1.0, 1.0)  # White text
        self.textActor.SetPosition(20, 20)  # Position in pixels from bottom left
        # Access the text property to modify font attributes
        textProperty = self.textActor.GetTextProperty()
        # Set the font family to Courier (or a monospaced font)
        textProperty.SetFontFamilyToCourier()
        textProperty.SetFontSize(30)
        textProperty.SetBold(1)
        self.renderer.AddActor(self.textActor)

    def keypress_callback(self, obj, event):
        key = obj.GetKeySym()
        if key == "Left": # PREVIOUS SCAN
            if(self.currentFollowup==0):
                self.currentFollowup = 0
            else:
                self.currentFollowup = self.currentFollowup - 1
                self.read_subject_data(self.currentFollowup)

        if key == "Right": # NEXT SCAN
            if (self.currentFollowup == self.followup_count-1):
                self.currentFollowup = self.followup_count-1
            else:
                self.currentFollowup = self.currentFollowup + 1
                self.read_subject_data(self.currentFollowup)

        if key == "T" or key == "t":  # FOLLOWUP TOGGLE DISPLAY
            if(self.is_followup == False):
                self.view_choice = 1
                self.read_subject_data(self.currentFollowup)
                self.is_followup = True
            else:
                self.view_choice = 0
                self.read_subject_data(self.currentFollowup)
                self.is_followup = False
        if key == "C" or key == "c": # SHOW COMPARISON DISPLAY
            if (self.is_comparison == False):
                self.view_choice = 2
                self.read_subject_data(self.currentFollowup)
                self.is_comparison = True
            else:
                self.view_choice = self.last_actor_choice
                self.read_subject_data(self.currentFollowup)
                self.is_comparison = False

    def renderSlider(self):
        # Create a slider representation
        slider_rep = vtk.vtkSliderRepresentation2D()
        slider_rep.SetMinimumValue(0.0)
        slider_rep.SetMaximumValue(self.followup_count-1)
        slider_rep.SetValue(0.0)
        slider_rep.SetTitleText("followup")
        slider_rep.GetSliderProperty().SetColor(1, 0, 0)  # Slider color
        slider_rep.GetTitleProperty().SetColor(1, 1, 1)  # Title color
        slider_rep.GetLabelProperty().SetColor(1, 1, 0)  # Label color
        slider_rep.SetSliderLength(0.01)
        slider_rep.SetSliderWidth(0.02)
        slider_rep.SetEndCapLength(0.01)
        slider_rep.SetEndCapWidth(0.01)
        slider_rep.SetTubeWidth(0.005)
        #slider_rep.SetMinimumValueText("Min")  # Optional
        #slider_rep.SetMaximumValueText("Max")  # Optional
        #slider_rep.SetPlaceFactor(1)  # This defines where the slider should be placed in the window

        # Position the slider
        slider_rep.GetPoint1Coordinate().SetCoordinateSystemToNormalizedViewport()
        slider_rep.GetPoint1Coordinate().SetValue(0.65, 0.1)
        slider_rep.GetPoint2Coordinate().SetCoordinateSystemToNormalizedViewport()
        slider_rep.GetPoint2Coordinate().SetValue(0.98, 0.1)

        # Create the slider widget
        self.slider_widget = vtk.vtkSliderWidget()
        self.slider_widget.SetInteractor(self.interactor)
        self.slider_widget.SetRepresentation(slider_rep)
        self.slider_widget.KeyPressActivationOff()  # Prevents the widget from being activated/deactivated with the keyboard
        self.slider_widget.SetAnimationModeToAnimate()  # Optional animation
        self.slider_widget.SetEnabled(True)
        self.slider_widget.AddObserver("InteractionEvent", self.slider_callback)


    def read_subject_data(self, followupindex = 0):
        self.renderer.RemoveAllViewProps()

        if(self.view_choice == 0):
            data_file_name = self.followup_folder_names[followupindex] + "/lesions_baseline.vtm"
        if(self.view_choice == 1):
            data_file_name = self.followup_folder_names[followupindex] + "/lesions_followup.vtm"
        if(self.view_choice == 2):
            data_file_name = self.followup_folder_names[followupindex] + "/lesion_diff_on_union.vtm"
            self.actor.SetVisibility(False)

        # reader
        reader = vtk.vtkXMLMultiBlockDataReader()
        reader.SetFileName(data_file_name)
        reader.Update()

        # get the multiblock dataset
        mb = reader.GetOutput()

        # loop over all blocks and add each to the renderer
        num_blocks = mb.GetNumberOfBlocks()
        for i in range(num_blocks):
            nc = vtk.vtkNamedColors()
            lut = vtk.vtkLookupTable()
            lut.SetNumberOfTableValues(3)
            lut.SetTableValue(0, nc.GetColor4d("LightCoral"))
            lut.SetTableValue(1, nc.GetColor4d("LightSlateGray"))
            lut.SetTableValue(2, nc.GetColor4d("PaleGreen"))
            lut.Build()

            polydata = mb.GetBlock(i)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            mapper.SetLookupTable(lut)
            mapper.SetScalarRange(polydata.GetScalarRange())
            if (self.view_choice == 2):
                self.comparison_actor = vtk.vtkActor()
                self.comparison_actor.SetMapper(mapper)
                self.renderer.AddActor(self.comparison_actor)
            else:
                self.actor = vtk.vtkActor()
                self.actor.SetMapper(mapper)
                self.renderer.AddActor(self.actor)
                self.actor.SetVisibility(True)
                self.last_actor_choice = self.view_choice
        self.text_overlay()
        self.interactor.Render()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MSApp(sys.argv[1:])
    window.showMaximized()
    sys.exit(app.exec_())