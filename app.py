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
        self.top_number = None
        self.current_filter_choice = None
        self.exclude_list = []
        self.legend = vtk.vtkLegendBoxActor()

        self.renderer.ResetCamera()
        # Set the interactor style to trackball camera
        self.trackballStyle = vtkInteractorStyleTrackballCamera()
        self.iren.SetInteractorStyle(self.trackballStyle)
        self.iren.AddObserver("KeyPressEvent", self.iren_keyPressEvent)
        # Start the VTK event loop
        self.vtkWidget.Initialize()
        self.vtkWidget.Start()

    def setupUI(self):
        print("Starting application...")
        self.comboBox_filter_type.addItems(["Shrinking", "Growing", "Unchanged"])
        self.pushButton_SetInputData.clicked.connect(self.selectFolder)
        self.radioButton_default.toggled.connect(self.handleRadioButtonClicked)
        self.radioButton_followup.toggled.connect(self.handleRadioButtonClicked)
        self.radioButton_comparison.toggled.connect(self.handleRadioButtonClicked)
        self.radioButton_wireframe.toggled.connect(self.handleRadioButtonClicked)
        self.slider_data.valueChanged.connect(self.sliderValueChanged)

    def spinBoxValueChanged(self):
        value = self.spinBox_top_lesion.value()
        followupIndex = self.slider_data.value()
        self.current_filter_choice = self.comboBox_filter_type.currentText()
        if (self.current_filter_choice == "Shrinking"):
            current_query_item = "one"
        if (self.current_filter_choice == "Growing"):
            current_query_item = "minus_one"
        if (self.current_filter_choice == "Unchanged"):
            current_query_item = "zero"

        # Reading JSON data
        self.exclude_list.clear()
        for item in self.activity_data:
            self.exclude_list.append(item[current_query_item])
        dict_from_list = {index: value for index, value in enumerate(self.exclude_list)}
        sorted_dict = dict(sorted(dict_from_list.items(), key=lambda item: item[1]))
        # print(sorted_dict)
        sorted_indices = list(sorted_dict.keys())
        shortlist_count = value
        # print(sorted_indices)
        selected_indices = sorted_indices[-shortlist_count:]

        if self.radioButton_default.isChecked(): # BASELINE
            self.top_number = value
            self.displayDefaultGeometry(followupIndex, True, selected_indices)
        if self.radioButton_followup.isChecked(): # FOLLOWUP
            self.top_number = value
            self.displayFollowupGeometry(followupIndex, True, selected_indices)
        if self.radioButton_comparison.isChecked(): # COMPARISON
            self.top_number = value
            self.displayComparisonGeometry(followupIndex, True, selected_indices)

    def handleRadioButtonClicked(self):
        if self.radioButton_default.isChecked(): # BASELINE
            self.displayDefaultGeometry()
        if self.radioButton_followup.isChecked(): # FOLLOWUP
            self.displayFollowupGeometry()
        if self.radioButton_comparison.isChecked(): # COMPARISON
            self.displayComparisonGeometry()
        if self.radioButton_wireframe.isChecked(): # WIREFRAME
            self.displayWireframeGeometry()

    def currentFilterSelectionChanged(self, index):
        # index is the new index of the combo box
        selected_text = self.comboBox_filter_type.currentText()
        #print(f"Selected: {selected_text} at index {index}")
        self.spinBoxValueChanged()

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

            ##### Run preprocessing
            preprocess.run_preprocess(self.followup_folder_names)

            self.radioButton_default.setEnabled(True)
            self.radioButton_followup.setEnabled(True)
            self.radioButton_comparison.setEnabled(True)
            self.slider_data.setEnabled(True)
            #self.radioButton_wireframe.setEnabled(True)  # Enable this adter implementing logic.
            self.spinBox_top_lesion.setEnabled(True)
            self.comboBox_filter_type.setEnabled(True)
            self.spinBox_top_lesion.setMinimum(1)  # Minimum value

            print("Finished preprocessing.")
            self.label_FolderName.setText("Root Folder Loaded: " + folder_name)
            self.text_overlay_initialize()
            self.text_shortcut_overlay_initialize()
            self.display_legend()
            self.displayDefaultGeometry()
            self.renderer.ResetCamera()
            self.spinBox_top_lesion.valueChanged.connect(self.spinBoxValueChanged)
            self.comboBox_filter_type.currentIndexChanged.connect(self.currentFilterSelectionChanged)

    def closeEvent(self, QCloseEvent):
        super().closeEvent(QCloseEvent)
        self.vtkWidget.Finalize()

    def displayDefaultGeometry(self, followupindex = 0, count_update = False, indices = None):
        for actor in self.lesion_actors:
            self.renderer.RemoveActor(actor)
        self.lesion_actors.clear()

        activity_data_filename = self.followup_folder_names[followupindex] + "/lesion_activity_data.json"
        data_file_name = self.followup_folder_names[followupindex] + "/lesions_baseline.vtm"
        self.renderer.RemoveActor(self.legend)

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
            # nc = vtk.vtkNamedColors()
            # lut = vtk.vtkLookupTable()
            # lut.SetNumberOfTableValues(3)
            # lut.SetTableValue(0, nc.GetColor4d("LightCoral"))
            # lut.SetTableValue(1, nc.GetColor4d("LightSlateGray"))
            # lut.SetTableValue(2, nc.GetColor4d("PaleGreen"))
            # lut.Build()
            polydata = mb.GetBlock(i)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            #mapper.SetLookupTable(lut)
            #mapper.SetScalarRange(polydata.GetScalarRange())
            mapper.SetScalarVisibility(0)
            self.actor = vtk.vtkActor()
            self.actor.SetMapper(mapper)
            self.actor.GetProperty().SetColor(1.0, 1.0, 1.0)
            self.renderer.AddActor(self.actor)
            self.lesion_actors.append(self.actor)
            if indices != None:
                if i in indices:
                    self.actor.SetVisibility(True)
                else:
                    self.actor.SetVisibility(False)
            else:
                self.actor.SetVisibility(True)
        self.text_overlay_update(os.path.basename(self.followup_folder_names[self.studyIndex]))
        self.vtkWidget.Render()

        self.slider_data.setMinimum(0)
        self.slider_data.setMaximum(len(self.followup_folder_names)-1)
        #self.slider_data.setValue(self.studyIndex)  # Initial slider position

        self.label_study.setText(os.path.basename(self.followup_folder_names[self.studyIndex]))
        self.spinBox_top_lesion.setMaximum(self.num_blocks)  # Maximum value
        if(count_update == False):
            self.spinBox_top_lesion.setValue(self.num_blocks)  # Initial value


    def displayFollowupGeometry(self, followupindex = 0, count_update = False, indices = None):
        for actor in self.lesion_actors:
            self.renderer.RemoveActor(actor)
        self.lesion_actors.clear()
        activity_data_filename = self.followup_folder_names[followupindex] + "/lesion_activity_data.json"
        data_file_name = self.followup_folder_names[followupindex] + "/lesions_followup.vtm"
        self.renderer.RemoveActor(self.legend)

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
            # nc = vtk.vtkNamedColors()
            # lut = vtk.vtkLookupTable()
            # lut.SetNumberOfTableValues(3)
            # lut.SetTableValue(0, nc.GetColor4d("LightCoral"))
            # lut.SetTableValue(1, nc.GetColor4d("LightSlateGray"))
            # lut.SetTableValue(2, nc.GetColor4d("PaleGreen"))
            # lut.Build()
            polydata = mb.GetBlock(i)
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputData(polydata)
            #mapper.SetLookupTable(lut)
            #mapper.SetScalarRange(polydata.GetScalarRange())
            mapper.SetScalarVisibility(0)
            self.actor = vtk.vtkActor()
            self.actor.SetMapper(mapper)
            self.actor.GetProperty().SetColor(1.0, 1.0, 1.0)
            self.renderer.AddActor(self.actor)
            self.lesion_actors.append(self.actor)
            if indices != None:
                if i in indices:
                    self.actor.SetVisibility(True)
                else:
                    self.actor.SetVisibility(False)
            else:
                self.actor.SetVisibility(True)

        self.vtkWidget.Render()
        self.spinBox_top_lesion.setMaximum(self.num_blocks)  # Maximum value
        if (count_update == False):
            self.spinBox_top_lesion.setValue(self.num_blocks)  # Initial value
        self.text_overlay_update(os.path.basename(self.followup_folder_names[self.studyIndex]))

    def displayComparisonGeometry(self, followupindex = 0, count_update = False, indices = None):
        # Code to display comparison geometry
        for actor in self.lesion_actors:
            self.renderer.RemoveActor(actor)
        self.lesion_actors.clear()

        activity_data_filename = self.followup_folder_names[followupindex] + "/lesion_activity_data.json"
        data_file_name = self.followup_folder_names[followupindex] + "/lesion_diff_on_union.vtm"
        self.renderer.AddActor(self.legend)

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
            if indices != None:
                if i in indices:
                    self.actor.SetVisibility(True)
                else:
                    self.actor.SetVisibility(False)
            else:
                self.actor.SetVisibility(True)

        self.vtkWidget.Render()
        self.spinBox_top_lesion.setMaximum(self.num_blocks)  # Maximum value
        if(count_update == False):
            self.spinBox_top_lesion.setValue(self.num_blocks)  # Initial value
        self.text_overlay_update(os.path.basename(self.followup_folder_names[self.studyIndex]))

    def displayWireframeGeometry(self):
        print('Displaying wireframe geometry')

    def text_overlay_initialize(self):
        self.textActor = vtk.vtkTextActor()
        self.textActor.GetTextProperty().SetColor(1.0, 1.0, 1.0)  # White text
        self.textActor.SetPosition(20, 20)  # Position in pixels from bottom left
        textProperty = self.textActor.GetTextProperty()
        textProperty.SetFontFamilyToCourier()
        textProperty.SetFontSize(18)
        self.renderer.AddActor(self.textActor)

    def display_legend(self):
        nc = vtk.vtkNamedColors()
        sphereSource = vtk.vtkSphereSource()
        sphereSource.SetCenter(0.0, 0.0, 0.0)
        sphereSource.SetRadius(50.0)
        sphereSource.Update()
        self.legend.SetNumberOfEntries(3)
        self.legend.GetEntryTextProperty().SetFontFamilyToCourier()
        self.legend.SetEntry(0, sphereSource.GetOutput(), "Growing",  nc.GetColor3d("LightCoral"))
        self.legend.SetEntry(1, sphereSource.GetOutput(), "Unchanged", nc.GetColor3d("LightSlateGray"))
        self.legend.SetEntry(2, sphereSource.GetOutput(), "Shrinking", nc.GetColor3d("PaleGreen"))
        self.legend.SetBorder(0)
        self.legend.SetBox(0)
        self.legend.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.legend.SetPosition(0.9, 0.5)  # Position at lower left
        self.legend.SetPosition2(0.08, 0.08)  # Size of the legend box
        self.legend.SetBackgroundColor(0.1, 0.1, 0.1)  # Dark background for visibility

    def text_shortcut_overlay_initialize(self):
        self.shortcutsActor = vtk.vtkTextActor()
        self.shortcutsActor.SetInput(f"< : Previous\n> : Next\nB : Baseline\nF : Followup\nC : Comparison")
        self.shortcutsActor.GetTextProperty().SetColor(1.0, 1.0, 1.0)  # White text
        self.shortcutsActor.GetPositionCoordinate().SetCoordinateSystemToNormalizedViewport()
        self.shortcutsActor.SetPosition(0.01, 0.85)  # Position in pixels from bottom left
        textProperty = self.shortcutsActor.GetTextProperty()
        textProperty.SetFontFamilyToCourier()
        textProperty.SetFontSize(16)
        self.renderer.AddActor(self.shortcutsActor)

    def iren_keyPressEvent(self, obj, event):
        key = obj.GetKeySym()  # Get the key symbol for the pressed key
        if key == "Left":
            currentValue = self.slider_data.value()
            minValue = self.slider_data.minimum()
            if currentValue > minValue:
                self.slider_data.setValue(currentValue - 1)
        elif key == "Right":
            currentValue = self.slider_data.value()
            maxValue = self.slider_data.maximum()
            if currentValue < maxValue:
                self.slider_data.setValue(currentValue + 1)
        elif key == "B" or key == "b":
            self.radioButton_default.setChecked(True)
        elif key == "F" or key == "f":
            self.radioButton_followup.setChecked(True)
        elif key == "C" or key == "c":
            self.radioButton_comparison.setChecked(True)

    def text_overlay_update(self, str):
        self.textActor.SetInput(f"Data: " + str)
        self.renderer.AddActor(self.textActor)
    # Slider value changed handler
    def sliderValueChanged(self, value):
        self.label_study.setText(os.path.basename(self.followup_folder_names[value]))
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