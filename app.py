from PyQt5 import QtWidgets as qWidget
from PyQt5 import QtGui as qGui
from PyQt5 import QtCore as qCore
from PyQt5.QtCore import pyqtSlot
from PyQt5.QtWidgets import QFileDialog, QCheckBox, QButtonGroup, QAbstractButton, QVBoxLayout, QListWidgetItem, \
    QAbstractItemView
qWidget.QApplication.setAttribute(qCore.Qt.AA_EnableHighDpiScaling, True) #enable highdpi scaling
qWidget.QApplication.setAttribute(qCore.Qt.AA_UseHighDpiPixmaps, True) #use highdpi icons
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
from PyQt5 import uic, Qt
from vtk.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
from vtkmodules.vtkInteractionStyle import vtkInteractorStyleTrackballCamera
import sys
import vtk
vtk.vtkObject.GlobalWarningDisplayOff()
import os
import glob
import json
import preprocess

class mainWindow(qWidget.QMainWindow):
    """Main window class."""

    def __init__(self, *args):
        """Init."""
        super(mainWindow, self).__init__(*args)
        ui = os.path.join(os.path.dirname(__file__), 'ui/gui.ui')
        uic.loadUi(ui, self)
        # Initialize VTK stuff for the QFrame
        self.vtkWidget = QVTKRenderWindowInteractor(self.frame)
        vbox = qWidget.QVBoxLayout()
        vbox.addWidget(self.vtkWidget)
        self.frame.setLayout(vbox)
        modes = [
            vtkViewport.GradientModes.VTK_GRADIENT_VERTICAL,
            vtkViewport.GradientModes.VTK_GRADIENT_HORIZONTAL,
            vtkViewport.GradientModes.VTK_GRADIENT_RADIAL_VIEWPORT_FARTHEST_SIDE,
            vtkViewport.GradientModes.VTK_GRADIENT_RADIAL_VIEWPORT_FARTHEST_CORNER,
        ]

        # Create a renderer and add it to the QVTKRenderWindowInteractor
        self.renderer = vtk.vtkRenderer()
        self.renderer.GradientBackgroundOn()
        self.renderer.SetGradientMode(modes[2])
        self.renderer.SetBackground([15 / 255, 32 / 255, 39 / 255])
        self.renderer.SetBackground2([44 / 255, 83 / 255, 100 / 255])
        self.vtkWidget.GetRenderWindow().AddRenderer(self.renderer)
        self.iren = self.vtkWidget.GetRenderWindow().GetInteractor()

        self.lesion_actors = []
        self.studyIndex = 0

        self.renderer.ResetCamera()
        # Set the interactor style to trackball camera
        self.trackballStyle = vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.trackballStyle)
        # Start the VTK event loop
        self.vtkWidget.Initialize()
        self.vtkWidget.Start()

    def setupUI(self):
        print("Starting application...")
        self.comboBox_filter_type.addItems(["Shrinking", "Growing", "Unchanged"])
        self.pushButton_SetInputData.clicked.connect(self.selectFolder)
        self.radioButton_default.clicked.connect(self.handleRadioButtonClicked)
        self.radioButton_followup.clicked.connect(self.handleRadioButtonClicked)
        self.radioButton_comparison.clicked.connect(self.handleRadioButtonClicked)
        self.radioButton_wireframe.clicked.connect(self.handleRadioButtonClicked)
        self.slider_data.valueChanged.connect(self.sliderValueChanged)

    def handleRadioButtonClicked(self):
        if self.radioButton_default.isChecked(): # BASELINE
            self.displayDefaultGeometry()
        if self.radioButton_followup.isChecked(): # FOLLOWUP
            self.displayFollowupGeometry()
        if self.radioButton_comparison.isChecked(): # COMPARISON
            self.displayComparisonGeometry()
        if self.radioButton_wireframe.isChecked(): # WIREFRAME
            self.displayWireframeGeometry()


    def selectFolder(self):
        folderPath = QFileDialog.getExistingDirectory(self, "Select Folder")
        if folderPath:
            folder_name = os.path.basename(folderPath)
            self.subject_folder = folderPath
            self.subject_name = os.path.basename(os.path.normpath(self.subject_folder))
            followup_prefix = self.subject_name + "_"
            self.followup_folder_names = [f for f in glob.glob(os.path.join(self.subject_folder, followup_prefix + '*')) if os.path.isdir(f)]
            # finish preprocessing
            if(len(self.followup_folder_names) ==0):
                print("No relevant data files found in source folder. Exiting...")
                return
            self.followup_folder_names.sort()
            preprocess.compute_difference(self.followup_folder_names)
            preprocess.generate_fast_files(self.followup_folder_names)
            self.radioButton_default.setEnabled(True)
            self.radioButton_followup.setEnabled(True)
            self.radioButton_comparison.setEnabled(True)
            #self.radioButton_wireframe.setEnabled(True)  # Enable this adter implementing logic.
            self.spinBox_top_lesion.setEnabled(True)
            self.spinBox_top_lesion.setMinimum(1)  # Minimum value

            print("Finished preprocessing.")
            self.label_FolderName.setText("Loaded: " + folder_name)
            self.displayDefaultGeometry()
            self.text_overlay_initialize()
            self.renderer.ResetCamera()

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.vtkWidget.Finalize()

    def displayDefaultGeometry(self, followupindex = 0):
        for actor in self.lesion_actors:
            self.renderer.RemoveActor(actor)
        self.lesion_actors.clear()

        activity_data_filename = self.followup_folder_names[followupindex] + "/lesion_activity_data.json"
        data_file_name = self.followup_folder_names[followupindex] + "/lesions_baseline.vtm"

        # reader
        reader = vtk.vtkXMLMultiBlockDataReader()
        reader.SetFileName(data_file_name)
        reader.Update()

        # Reading JSON data
        with open(activity_data_filename, 'r') as json_file:
            self.activity_data = json.load(json_file)

        mb = reader.GetOutput()
        self.num_blocks = mb.GetNumberOfBlocks()
        for i in range(self.num_blocks):
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
            self.actor = vtk.vtkActor()
            self.actor.SetMapper(mapper)
            self.renderer.AddActor(self.actor)
            self.lesion_actors.append(self.actor)
            self.actor.SetVisibility(True)

        self.vtkWidget.Render()

        self.slider_data.setMinimum(0)
        self.slider_data.setMaximum(len(self.followup_folder_names)-1)
        self.slider_data.setValue(self.studyIndex)  # Initial slider position

        self.label_study.setText(os.path.basename(self.followup_folder_names[self.studyIndex]))
        self.spinBox_top_lesion.setMaximum(self.num_blocks)  # Maximum value
        self.spinBox_top_lesion.setValue(self.num_blocks)  # Initial value

    def displayFollowupGeometry(self, followupindex = 0):
        for actor in self.lesion_actors:
            self.renderer.RemoveActor(actor)
        self.lesion_actors.clear()
        activity_data_filename = self.followup_folder_names[followupindex] + "/lesion_activity_data.json"
        data_file_name = self.followup_folder_names[followupindex] + "/lesions_followup.vtm"

        # reader
        reader = vtk.vtkXMLMultiBlockDataReader()
        reader.SetFileName(data_file_name)
        reader.Update()

        # Reading JSON data
        with open(activity_data_filename, 'r') as json_file:
            self.activity_data = json.load(json_file)

        mb = reader.GetOutput()
        self.num_blocks = mb.GetNumberOfBlocks()
        for i in range(self.num_blocks):
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
            self.actor = vtk.vtkActor()
            self.actor.SetMapper(mapper)
            self.renderer.AddActor(self.actor)
            self.lesion_actors.append(self.actor)
            self.actor.SetVisibility(True)

        self.vtkWidget.Render()
        self.spinBox_top_lesion.setMaximum(self.num_blocks)  # Maximum value
        self.spinBox_top_lesion.setValue(self.num_blocks)  # Initial value

    def displayComparisonGeometry(self, followupindex = 0):
        # Code to display comparison geometry
        for actor in self.lesion_actors:
            self.renderer.RemoveActor(actor)
        self.lesion_actors.clear()

        activity_data_filename = self.followup_folder_names[followupindex] + "/lesion_activity_data.json"
        data_file_name = self.followup_folder_names[followupindex] + "/lesion_diff_on_union.vtm"

        # reader
        reader = vtk.vtkXMLMultiBlockDataReader()
        reader.SetFileName(data_file_name)
        reader.Update()

        # Reading JSON data
        with open(activity_data_filename, 'r') as json_file:
            self.activity_data = json.load(json_file)

        mb = reader.GetOutput()
        self.num_blocks = mb.GetNumberOfBlocks()
        for i in range(self.num_blocks):
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
            self.actor = vtk.vtkActor()
            self.actor.SetMapper(mapper)
            self.renderer.AddActor(self.actor)
            self.lesion_actors.append(self.actor)
            self.actor.SetVisibility(True)

        self.vtkWidget.Render()
        self.spinBox_top_lesion.setMaximum(self.num_blocks)  # Maximum value
        self.spinBox_top_lesion.setValue(self.num_blocks)  # Initial value

    def displayWireframeGeometry(self):
        print('Displaying wireframe geometry')

    def text_overlay_initialize(self):
        self.textActor = vtk.vtkTextActor()
        #self.textActor.SetInput(f"Data:")
        self.textActor.GetTextProperty().SetColor(1.0, 1.0, 1.0)  # White text
        self.textActor.SetPosition(20, 20)  # Position in pixels from bottom left
        textProperty = self.textActor.GetTextProperty()
        textProperty.SetFontFamilyToCourier()
        textProperty.SetFontSize(20)
        self.renderer.AddActor(self.textActor)

    def text_overlay_update(self, str):
        self.textActor.SetInput(f"Data: " + str)
        self.renderer.AddActor(self.textActor)
    # Slider value changed handler
    def sliderValueChanged(self, value):
        self.label_study.setText(os.path.basename(self.followup_folder_names[value]))
        self.text_overlay_update(os.path.basename(self.followup_folder_names[value]))
        if self.radioButton_default.isChecked(): # BASELINE
            self.displayDefaultGeometry(value)
        if self.radioButton_followup.isChecked(): # FOLLOWUP
            self.displayFollowupGeometry(value)
        if self.radioButton_comparison.isChecked(): # COMPARISON
            self.displayComparisonGeometry(value)
        #if self.radioButton_wireframe.isChecked(): # WIREFRAME TODO: not implemented yet.
        #    self.displayWireframeGeometry(value)
        self.studyIndex = value

app = qWidget.QApplication(sys.argv)
window = mainWindow()
window.setupUI()
window.show()

window.showMaximized()
sys.exit(app.exec_())