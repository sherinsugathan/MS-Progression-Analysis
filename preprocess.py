import vtk
import re
import os
import json
from collections import defaultdict

def compute_difference(followup_folder_names):
    # Check if already processed.
    for followup_folder in followup_folder_names:
        if os.path.isfile(followup_folder + "/lesion_diff_on_union.vtm"):
          print("Lesion comparison data already computed. Skipping...")
          continue
        print("The input data folder is currently undergoing preprocessing for visualization, which requires a one-time execution. Please wait for this process to complete...")
        print(f"Processing followup folder {followup_folder}.")

        lesion_files = defaultdict(lambda: {'baseline': None, 'followup': None})

        baseline_shifted_folder = followup_folder + "/Shifted_lesions"
        if os.path.isdir(baseline_shifted_folder): # Shifted lesions folder exists
            file_pattern = re.compile(r'Lesion_(\d+)_baseline_flirt\.nii\.gz')
            for filename in os.listdir(baseline_shifted_folder):
                match = file_pattern.match(filename)
                if match:
                    lesion_number = match.group(1)
                    lesion_files[lesion_number]['baseline'] = os.path.join(baseline_shifted_folder, filename)
            file_pattern = re.compile(r'Lesion_(\d+)_followup\.nii\.gz')
            for filename in os.listdir(followup_folder):
                match = file_pattern.match(filename)
                if match:
                    lesion_number = match.group(1)
                    lesion_files[lesion_number]['followup'] = os.path.join(followup_folder, filename)
        else: # There is no "ShiftedLesions" folder
            file_pattern = re.compile(r'Lesion_(\d+)_(baseline|followup)\.nii\.gz')
            for filename in os.listdir(followup_folder):
                match = file_pattern.match(filename)
                if match:
                    lesion_number, file_type = match.groups()
                    lesion_files[lesion_number][file_type] = filename
        num_items = len(lesion_files)
        mb = vtk.vtkMultiBlockDataSet()
        mb.SetNumberOfBlocks(num_items)
        block_number = 0
        iterations_data = []
        for lesion_number, files in lesion_files.items():
            baseline_file = files['baseline']
            followup_file = files['followup']
            if baseline_file and followup_file:
                #full_path_baseline = os.path.join(followup_folder, baseline_file)
                new_filename = baseline_file.replace("baseline.nii.gz", "baseline_flirt.nii.gz")
                shifted_lesions_file_path = os.path.join(followup_folder + "/Shifted_lesions/", new_filename)
                #print("The path is", shifted_lesions_file_path)
                if os.path.exists(shifted_lesions_file_path):
                    full_path_baseline = shifted_lesions_file_path
                    print("Reading shifted lesion baseline data.")
                else:
                    full_path_baseline = os.path.join(followup_folder, baseline_file)

                confluent_preprocessed_filepath = followup_folder + "/confluent_preprocessed/" + followup_file
                if os.path.exists(confluent_preprocessed_filepath):
                    full_path_followup = confluent_preprocessed_filepath
                    print("Reading confluent lesion filtered data.")
                else:
                    full_path_followup = os.path.join(followup_folder, followup_file)

                #print(full_path_baseline, full_path_followup)
                print(f"Iteration {block_number}: Processing baseline and followup.")
                probe_result_poly = volume_probe(full_path_baseline, full_path_followup)
                mb.SetBlock(block_number, probe_result_poly)
                # count data
                count_zero = 0
                count_minus_one = 0
                count_one = 0
                scalars = probe_result_poly.GetPointData().GetScalars()
                for i in range(scalars.GetNumberOfTuples()):
                    value = scalars.GetTuple1(i)
                    if value == 0:
                        count_zero += 1
                    elif value <  0:
                        count_minus_one += 1
                    elif value > 0:
                        count_one += 1
                iteration_dict = {
                    "iteration": block_number,
                    "minus_one": count_minus_one,
                    "zero": count_zero,
                    "one": count_one
                }
                iterations_data.append(iteration_dict)
                block_number = block_number + 1

        # Write the list of dictionaries to a JSON file
        with open(followup_folder + '/lesion_activity_data.json', 'w') as json_file:
            json.dump(iterations_data, json_file, indent=4)

        writer = vtk.vtkXMLMultiBlockDataWriter()
        writer.SetFileName(followup_folder + "/" +'lesion_diff_on_union.vtm')
        writer.SetInputData(mb)
        writer.SetDataModeToBinary()  # enable binary mode
        writer.Write()
    return

# generate binary data from already existing lesion data for faster loading and easy processing.
def generate_fast_files(followup_folder_names):
    for followup_folder in followup_folder_names:
        if os.path.isfile(followup_folder + "/lesions_baseline.vtm") and os.path.isfile(followup_folder + "/lesions_followup.vtm"):
          print("Fast access files already created. Skipping...")
          continue
        print(f"gen fastProcessing followup folder {followup_folder}.")
        file_pattern = re.compile(r'Lesion_(\d+)_(baseline|followup)\.nii\.gz')
        lesion_files = defaultdict(lambda: {'baseline': None, 'followup': None})
        for filename in os.listdir(followup_folder):
            match = file_pattern.match(filename)
            if match:
                lesion_number, file_type = match.groups()
                lesion_files[lesion_number][file_type] = filename
        num_items = len(lesion_files)
        mb_baseline = vtk.vtkMultiBlockDataSet()
        mb_baseline.SetNumberOfBlocks(num_items)
        mb_followup = vtk.vtkMultiBlockDataSet()
        mb_followup.SetNumberOfBlocks(num_items)
        block_number = 0
        for lesion_number, files in lesion_files.items():
            baseline_file = files['baseline']
            followup_file = files['followup']
            if baseline_file and followup_file:
                #full_path_baseline = os.path.join(followup_folder, baseline_file)

                new_filename = baseline_file.replace("baseline.nii.gz", "baseline_flirt.nii.gz")
                shifted_lesions_file_path = os.path.join(followup_folder + "/Shifted_lesions/", new_filename)
                print("The path is", shifted_lesions_file_path)
                if os.path.exists(shifted_lesions_file_path):
                    full_path_baseline = shifted_lesions_file_path
                    print("Reading shifted lesion baseline data.")
                else:
                    full_path_baseline = os.path.join(followup_folder, baseline_file)

                confluent_preprocessed_filepath = followup_folder + "/confluent_preprocessed/" + followup_file
                if os.path.exists(confluent_preprocessed_filepath):
                    full_path_followup = confluent_preprocessed_filepath
                    print("Reading confluent lesion filtered data.")
                else:
                    full_path_followup = os.path.join(followup_folder, followup_file)
                print(f"Iteration {block_number}: Processing baseline and followup.")
                reader_baseline = vtk.vtkNIFTIImageReader()
                reader_baseline.SetFileName(full_path_baseline)
                reader_baseline.Update()
                reader_followup = vtk.vtkNIFTIImageReader()
                reader_followup.SetFileName(full_path_followup)
                reader_followup.Update()
                surface_baseline = vtk.vtkDiscreteMarchingCubes()
                surface_baseline.SetInputConnection(reader_baseline.GetOutputPort())
                surface_baseline.Update()
                mb_baseline.SetBlock(block_number, surface_baseline.GetOutput())
                surface_followup = vtk.vtkDiscreteMarchingCubes()
                surface_followup.SetInputConnection(reader_followup.GetOutputPort())
                surface_followup.Update()
                mb_followup.SetBlock(block_number, surface_followup.GetOutput())
                block_number = block_number + 1

        writer_baseline = vtk.vtkXMLMultiBlockDataWriter()
        writer_baseline.SetFileName(followup_folder + "/" + 'lesions_baseline.vtm')
        writer_baseline.SetInputData(mb_baseline)
        writer_baseline.SetDataModeToBinary()  # enable binary mode
        writer_baseline.Write()

        writer_followup = vtk.vtkXMLMultiBlockDataWriter()
        writer_followup.SetFileName(followup_folder + "/" + 'lesions_followup.vtm')
        writer_followup.SetInputData(mb_followup)
        writer_followup.SetDataModeToBinary()  # enable binary mode
        writer_followup.Write()



def volume_probe(baseline, followup):
    # Creating union image
    niftiReaderLesionMask1 = vtk.vtkNIFTIImageReader()
    niftiReaderLesionMask1.SetFileName(baseline)
    niftiReaderLesionMask1.Update()
    niftiReaderLesionMask2 = vtk.vtkNIFTIImageReader()
    niftiReaderLesionMask2.SetFileName(followup)
    niftiReaderLesionMask2.Update()

    # Create vtkImageCast filters to convert both images to the same scalar type
    caster1 = vtk.vtkImageCast()
    caster1.SetInputData(niftiReaderLesionMask1.GetOutput())
    caster1.SetOutputScalarTypeToFloat()  # Convert the first image to float
    caster1.Update()

    caster2 = vtk.vtkImageCast()
    caster2.SetInputData(niftiReaderLesionMask2.GetOutput())
    caster2.SetOutputScalarTypeToFloat()  # Convert the second image to float
    caster2.Update()

    orImageFilter = vtk.vtkImageLogic()
    orImageFilter.SetInput1Data(caster1.GetOutput())
    orImageFilter.SetInput2Data(caster2.GetOutput())
    orImageFilter.SetOperationToOr()
    orImageFilter.Update()

    marchingCubesOr = vtk.vtkMarchingCubes()
    marchingCubesOr.SetInputData(orImageFilter.GetOutput())
    marchingCubesOr.SetValue(0, 1)  # Set the isovalue; adjust based on your data
    marchingCubesOr.Update()

    #writer = vtk.vtkNIFTIImageWriter()
    #writer.SetFileName("union.nii")
    #writer.SetInputData(orImageFilter.GetOutput())
    #writer.Write()

    subtractImageFilter = vtk.vtkImageMathematics()
    subtractImageFilter.SetInput1Data(caster1.GetOutput())
    subtractImageFilter.SetInput2Data(caster2.GetOutput())
    subtractImageFilter.SetOperationToSubtract()
    subtractImageFilter.Update()
    #writer.SetFileName("diff.nii")
    #writer.SetInputData(subtractImageFilter.GetOutput())
    #writer.Write()

    probeFilter = vtk.vtkProbeFilter()
    probeFilter.SetSourceData(subtractImageFilter.GetOutput())
    #probeFilter.SetInputData(orImageFilter.GetOutput())
    probeFilter.SetInputData(marchingCubesOr.GetOutput())
    probeFilter.CategoricalDataOff()
    probeFilter.Update()

    return probeFilter.GetOutput()

    print("preprocessing complete")

    #writer.SetFileName("probe.nii")
    #writer.SetInputData(probeFilter.GetOutput())
    #writer.Write()

    nc = vtk.vtkNamedColors()
    lut = vtk.vtkLookupTable()
    lut.SetNumberOfTableValues(3)
    lut.SetTableValue(0,nc.GetColor4d("PaleGreen"))
    lut.SetTableValue(1,nc.GetColor4d("LightSlateGray"))
    lut.SetTableValue(2,nc.GetColor4d("LightCoral"))
    lut.Build()

    mapper = vtk.vtkPolyDataMapper()
    mapper.SetInputData(probeFilter.GetOutput())
    mapper.SetLookupTable(lut)
    mapper.SetScalarRange(probeFilter.GetOutput().GetScalarRange())
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

def generate_followup_no_confluent(followup_folder_names):
    for followup_folder in followup_folder_names:
        if os.path.isdir(followup_folder + "/confluent_preprocessed"):
          print("Confluent lesions already processed. Skipping...")
          continue
        print(f"Processing followup folder {followup_folder}.")
        file_pattern = re.compile(r'Lesion_(\d+)_followup\.nii\.gz')
        lesion_files = defaultdict(lambda: {'baseline': None, 'followup': None})
        for filename in os.listdir(followup_folder):
            match = file_pattern.match(filename)
            if match:
                lesion_number = match.group(1)
                lesion_files[lesion_number]['followup'] = os.path.join(followup_folder, filename)
        #print(lesion_files)
        for lesion_number, files in lesion_files.items():
            followup_file = files['followup']

            confluent_lesion_annotation_filepath = followup_folder + "/Shifted_lesions/misc/All_lumps_followup.nii.gz"
            if os.path.exists(confluent_lesion_annotation_filepath):
                print("Found confluent lesion annotation.")
                confluent_preprocess_path = followup_folder + "/confluent_preprocessed"
                if not os.path.exists(confluent_preprocess_path):
                    os.makedirs(confluent_preprocess_path)
                # print(followup_file)
                # print(confluent_lesion_annotation_filepath)

                confluent_removed_image_data = remove_confluent_lesion(followup_file, confluent_lesion_annotation_filepath)
                confluent_removed_image_data_filename = confluent_preprocess_path + "/" + os.path.basename(followup_file)

                writer = vtk.vtkNIFTIImageWriter()
                writer.SetFileName(confluent_removed_image_data_filename)
                writer.SetInputData(confluent_removed_image_data)
                writer.Write()
                print("Wrote followup data with confluent lesion removed: ", os.path.basename(followup_file))
            else:
                print("No confluent lesion annotations found.")

def cast_image(image, target_scalar_type):
    cast = vtk.vtkImageCast()
    cast.SetInputData(image)
    cast.SetOutputScalarType(target_scalar_type)
    cast.Update()
    return cast.GetOutput()

def remove_confluent_lesion(followup_file, confluent_lesion_annotation_filepath):
    reader1 = vtk.vtkNIFTIImageReader()
    reader1.SetFileName(followup_file)
    reader1.Update()

    reader2 = vtk.vtkNIFTIImageReader()
    reader2.SetFileName(confluent_lesion_annotation_filepath)
    reader2.Update()

    image1_cast = cast_image(reader1.GetOutput(), vtk.VTK_UNSIGNED_CHAR)
    image2_cast = cast_image(reader2.GetOutput(), vtk.VTK_UNSIGNED_CHAR)

    math1 = vtk.vtkImageLogic()
    math1.SetInput1Data(image1_cast)
    math1.SetInput2Data(image2_cast)
    math1.SetOperationToAnd()  # Subtract volumes
    math1.Update()

    image3_cast = cast_image(reader1.GetOutput(), vtk.VTK_UNSIGNED_CHAR)
    image4_cast = cast_image(math1.GetOutput(), vtk.VTK_UNSIGNED_CHAR)

    math2 = vtk.vtkImageLogic()
    math2.SetInput1Data(image3_cast)
    math2.SetInput2Data(image4_cast)
    math2.SetOperationToXor()  # Subtract volumes
    math2.Update()

    return math2.GetOutput()

def run_preprocess(followup_folder_names):
    generate_followup_no_confluent(followup_folder_names)
    compute_difference(followup_folder_names)
    generate_fast_files(followup_folder_names)

#folders = ['C:/Sherin/Workspace/1_ProjectSource/27_Samuel_MS_Feature/Subjects_Matched_new/Subjects_Matched/1001BC/1001BC_m00_m12_snacai', 'C:/Sherin/Workspace/1_ProjectSource/27_Samuel_MS_Feature/Subjects_Matched_new/Subjects_Matched/1001BC/1001BC_m12_m24_snacai', 'C:/Sherin/Workspace/1_ProjectSource/27_Samuel_MS_Feature/Subjects_Matched_new/Subjects_Matched/1001BC/1001BC_m24_m36_snacai', 'C:/Sherin/Workspace/1_ProjectSource/27_Samuel_MS_Feature/Subjects_Matched_new/Subjects_Matched/1001BC/1001BC_m36_m48_snacai', 'C:/Sherin/Workspace/1_ProjectSource/27_Samuel_MS_Feature/Subjects_Matched_new/Subjects_Matched/1001BC/1001BC_m48_m60_snacai', 'C:/Sherin/Workspace/1_ProjectSource/27_Samuel_MS_Feature/Subjects_Matched_new/Subjects_Matched/1001BC/1001BC_m60_m96_snacai']
#compute_difference(folders)
#generate_fast_files(folders)

#generate_followup_no_confluent(folders)
