import os
import glob
import matplotlib
matplotlib.use('TkAgg')
import pandas as pd
from nptdms import TdmsFile
from openpyxl import Workbook
import tkinter as tk
from tkinter import filedialog
import matplotlib.pyplot as plt
import mplcursors
import numpy as np
import warnings

warnings.filterwarnings("ignore", category=UserWarning, module="mplcursors._pick_info")

def export_tdms_to_excel(tdms_file_path, excel_file_path):
    tdms_file = TdmsFile.read(tdms_file_path)

    # Create an empty DataFrame for the metadata
    metadata_df = pd.DataFrame(columns=["Type", "Name", "Property", "Value"])

    # Extract file-level properties and add them to the metadata DataFrame
    for property_name, property_value in tdms_file.properties.items():
        metadata_df = pd.concat([metadata_df, pd.DataFrame({"Type": ["File"], "Name": [""], "Property": [property_name], "Value": [property_value]})], ignore_index=True)

    # Extract group-level and channel-level properties and add them to the metadata DataFrame
    for group in tdms_file.groups():
        group_name = group.name
        for property_name, property_value in group.properties.items():
            metadata_df = pd.concat([metadata_df, pd.DataFrame({"Type": ["Group"], "Name": [group_name], "Property": [property_name], "Value": [property_value]})], ignore_index=True)

        for channel in group.channels():
            channel_name = channel.name.split("/")[-1].strip("'")
            for property_name, property_value in channel.properties.items():
                metadata_df = pd.concat([metadata_df, pd.DataFrame({"Type": ["Channel"], "Name": [channel_name], "Property": [property_name], "Value": [property_value]})], ignore_index=True)

    # Create an empty DataFrame for the main data channels
    data_channels_df = pd.DataFrame()

    # Extract the main data channels and add them to the data_channels DataFrame
    for group in tdms_file.groups():
        for channel in group.channels():
            channel_name = channel.name.split("/")[-1].strip("'")
            data = channel[:]
            data_channels_df[channel_name] = data

    # Write the DataFrames to an Excel file with two worksheets
    with pd.ExcelWriter(excel_file_path, engine="openpyxl") as writer:
        metadata_df.to_excel(writer, sheet_name="Metadata", index=False)
        data_channels_df.to_excel(writer, sheet_name="Data Channels", index=False)

    print(f"TDMS data has been exported to '{excel_file_path}'.")
	
def convert_excel_to_csv(file_path, output_directory):
    # Load the second sheet (index 1) in the Excel file
    sheet = pd.read_excel(file_path, sheet_name=1, engine='openpyxl')

    # Create the output CSV file path
    csv_file_name = f"{os.path.splitext(os.path.basename(file_path))[0]}_sheet2.csv"
    csv_file_path = os.path.join(output_directory, csv_file_name)

    # Save the second sheet as a CSV file
    sheet.to_csv(csv_file_path, index=False)
    print(f"Successfully saved {csv_file_path}")
      
def pick_points(csv_file_path, results):
    current_sel = None

    def on_click(event):
        nonlocal current_sel
        if current_sel:
            index = int(current_sel.target.index)
            point = (data.iloc[index]['Time (s)'], data.iloc[index]['Load (kN)'])
            picked_point = round(point[1], 2)
            background_load = calculate_background_load(data)
            difference = round(picked_point - background_load, 2)
            print(f"{sample_name}: {picked_point} kN, Background: {background_load} kN, Difference: {difference} kN")
            results.loc[sample_name] = [picked_point, background_load, difference, None, None]
            # After calculating picked_point, background_load, difference
            #results = results.append({'Sample Name': sample_name,
                                      #'Picked Load (kN)': picked_point, 
                                      #'Background Load (kN)': background_load, 
                                      #'Difference (kN)': difference, 
                                      #'Young\'s Modulus (MPa)': None, 
                                      #'Poisson\'s Ratio': None}, 
                                     #ignore_index=True)

            current_sel.annotation.set_visible(False)
            current_sel = None

    def on_hover(sel):
        nonlocal current_sel
        if current_sel:
            current_sel.annotation.set_visible(False)
        
        current_sel = sel
        index = int(sel.target.index)
        point = (data.iloc[index]['Time (s)'], data.iloc[index]['Load (kN)'])
        sel.annotation.set_text(f'{sample_name}\nLoad: {point[1]:.2f} kN')
        sel.annotation.set_visible(True)
        fig.canvas.draw_idle()
    
    def calculate_background_load(data):
        n_values = 10
        initial_values = data['Load (kN)'].head(n_values).mean()
        return round(initial_values, 2)

    sample_name = os.path.basename(csv_file_path)[:-11]
    data = pd.read_csv(csv_file_path, skiprows=1, usecols=[0, 1], names=['Time (s)', 'Load (kN)'])
    fig, ax = plt.subplots()
    line, = ax.plot(data['Time (s)'], data['Load (kN)'])
    ax.set_title(sample_name)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Load (kN)')

    ax.set_xlim(data['Time (s)'].min(), data['Time (s)'].max())
    ax.set_ylim(data['Load (kN)'].min(), data['Load (kN)'].max() * 1.1)

    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    cursor = mplcursors.cursor(hover=True, highlight=True)
    cursor.connect("add", on_hover)
    fig.canvas.mpl_connect("button_press_event", on_click)

    plt.show()

def analyze_stress_strain(csv_file_path, input_directory, results, cf=0.0023):

    current_sel = None
    points = []
    
    # Inner function for handling click events on the graph
    def on_click(event):
        if event.artist == line1:
            nonlocal current_sel
            if current_sel:
                ind = event.ind[0]
                point = (calc_data['Axial Strain'][ind], calc_data['Stress'][ind])
                points.append(point)
                print(f"Point selected: Axial Strain = {point[0]:.4f}, Stress = {point[1]:.3f}")
                if len(points) >= 2:
                    # Identify the range of data points between the two selected points
                    start_strain = min(points[0][0], points[1][0])
                    end_strain = max(points[0][0], points[1][0])
                    selected_range = calc_data[(calc_data['Axial Strain'] >= start_strain) & (calc_data['Axial Strain'] <= end_strain)]

                    # Calculating Young's modulus using a trendline through all data in the selected range
                    youngs_modulus, _ = np.polyfit(selected_range['Axial Strain'], selected_range['Stress'], 1)

                    # Calculating Poisson's ratio
                    poissons_ratio, _ = np.polyfit(selected_range['Axial Strain'], selected_range['Circum Strain'], 1)
                    poissons_ratio = -poissons_ratio  # Adjust sign as needed

                    # Append the point to the results DataFrame
                    #last_index = results.index[-1]
                    #results.at[last_index, 'Young\'s Modulus (MPa)'] = youngs_modulus
                    #results.at[last_index, 'Poisson\'s Ratio'] = poissons_ratio
                    results.loc[sample_name, 'Young\'s Modulus (MPa)'] = youngs_modulus
                    results.loc[sample_name, 'Poisson\'s Ratio'] = poissons_ratio

                current_sel.annotation.set_visible(False)
                current_sel = None

    # Inner function for handling hover events on the graph
    def on_hover(sel):
        if sel.artist == line1:
            nonlocal current_sel
            if current_sel:
                current_sel.annotation.set_visible(False)
            
            current_sel = sel
            index = int(sel.target.index)
            point = (calc_data.iloc[index]['Axial Strain'], calc_data.iloc[index]['Stress'])
            sel.annotation.set_text(f'Strain: {point[0]:.3f}\nStress: {point[1]:.3f}')
            sel.annotation.set_visible(True)
            fig.canvas.draw_idle()

    # Function to preprocess data
    def preprocess_data(data):
        
        def calculate_background_load(data):
            n_values = 10
            initial_values = data['Load (kN)'].head(n_values).mean()
            return round(initial_values, 2)
        
        background_load = calculate_background_load(data)

        data['Time (s)'] = data['Time (s)'] - data['Time (s)'].iloc[0]
        data['Displacement (mm)'] = -(data['Displacement (mm)'] - data['Displacement (mm)'].iloc[0])  # Correct for axial
        data['Load (kN)'] = data['Load (kN)'] - background_load
        data['Extentionometer'] = data['Extentionometer'] - data['Extentionometer'].max()

        return data

    # Function to calculate strains and stresses
    def calculate_strains_stresses(data, Ri, L, cf):
        Load = data['Load (kN)']
        LVDT = data['Displacement (mm)']
        Ext = data['Extentionometer']

        # Define other parameters
        lc = 74       # Chain length in mm
        a = 4.5       # Rod radius in mm
        m_15 = 2.0304 # LVDT slope from calibration

        stress = 1e3 * Load / (np.pi * Ri**2)
        axial_strain = (LVDT - cf * Load) / L
        dl = Ext * m_15
        theta = 2 * np.pi - (lc / (Ri + a))
        dC = (dl * np.pi) / (np.sin(theta / 2) + (np.pi - theta / 2) * np.cos(theta / 2))
        circum_strain = dC / (2 * np.pi * Ri)
        vol_strain = axial_strain + 2 * circum_strain

        return stress, axial_strain, circum_strain, vol_strain


    sample_name = os.path.basename(csv_file_path)[:-11]  
    data = pd.read_csv(csv_file_path, usecols=['TimeStamp', 'Load', 'LVDT', 'Extentionometer'])
    data.columns = ['Time (s)', 'Load (kN)', 'Displacement (mm)', 'Extentionometer']
    # Read additional data (thickness and diameter) from another CSV file
    additional_csv_path = os.path.join(input_directory, "sample_info.csv")
    additional_data = pd.read_csv(additional_csv_path)
    sample_additional_data = additional_data[additional_data['Sample Name'] == sample_name]
    av_thickness = sample_additional_data['Av Thickness'].iloc[0]
    av_diameter = sample_additional_data['Av Diameter'].iloc[0]

    # Processing data
    Ri = av_diameter / 2  # Radius
    L = av_thickness      # Thickness
    preprocessed_data = preprocess_data(data)
    # Finding the index of maximum load
    max_load_index = preprocessed_data['Load (kN)'].idxmax()
    # Cropping data till the maximum load
    cropped_data = preprocessed_data.iloc[:max_load_index + 1]
    # Continue with the calculation using cropped_data
    stress, axial_strain, circum_strain, vol_strain = calculate_strains_stresses(cropped_data, Ri, L, cf)

    # DataFrame for calculation
    calc_data = pd.DataFrame({'Axial Strain': axial_strain, 'Circum Strain': circum_strain, 'Vol Strain': vol_strain, 'Stress': stress})

    # Plotting the stress-strain curve
    fig, ax = plt.subplots()
    line1, = ax.plot(calc_data['Axial Strain'], calc_data['Stress'], label='Axial strain', picker=True)
    line2, = ax.plot(calc_data['Circum Strain'], calc_data['Stress'], label='Circumferential strain')
    line3, = ax.plot(calc_data['Vol Strain'], calc_data['Stress'], label='Volumetric strain')
    ax.set_xlabel('Strain')
    ax.set_ylabel('Stress [MPa]')
    ax.legend()
    ax.grid(True)

    # Optional: Set axes limits and major locator
    ax.set_xlim(calc_data['Circum Strain'].min() * 1.1, calc_data['Axial Strain'].max() * 1.1)
    ax.set_ylim(calc_data['Stress'].min(), calc_data['Stress'].max() * 1.1)
    ax.yaxis.set_major_locator(plt.MaxNLocator(integer=True))

    cursor = mplcursors.cursor(hover=True, highlight=True)
    cursor.connect("add", on_hover)
    fig.canvas.mpl_connect("pick_event", on_click)
    
    plt.show()

def browse_input_directory():
    global input_directory_label
    input_directory = filedialog.askdirectory()
    input_directory_label.config(text=input_directory)

def browse_output_directory():
    global output_directory_label
    output_directory = filedialog.askdirectory()
    output_directory_label.config(text=output_directory)

def process_files():
    tdms_files_directory = input_directory_label.cget("text")
    output_directory = output_directory_label.cget("text")
    for tdms_file_path in glob.glob(os.path.join(tdms_files_directory, "*.tdms")):
        file_name = os.path.basename(tdms_file_path)
        file_name_without_extension = os.path.splitext(file_name)[0]
        excel_file_name = file_name_without_extension + ".xlsx"
        excel_file_path = os.path.join(output_directory, excel_file_name)
        
        print(f"Processing file: {tdms_file_path}")
        export_tdms_to_excel(tdms_file_path, excel_file_path)

    print("All TDMS files have been processed.")

    for excel_file_path in glob.glob(os.path.join(output_directory, "*.xls*")):
            if excel_file_path.endswith(".xlsx") or excel_file_path.endswith(".xls"):
                convert_excel_to_csv(excel_file_path, output_directory)

    cf_value = float(cf_entry.get())            
    results = pd.DataFrame(columns=['Sample Name', 'Picked Load (kN)', 'Background Load (kN)', 'Difference (kN)', 'Young\'s Modulus (MPa)', 'Poisson\'s Ratio'])
    results.set_index('Sample Name', inplace=True)
    for csv_file_path in glob.glob(os.path.join(output_directory, "*.csv")):
        if "picked_points" not in csv_file_path:
            pick_points(csv_file_path, results)
            if analyze_stress_strain_var.get():
                analyze_stress_strain(csv_file_path, input_directory_label.cget("text"), results, cf=cf_value)
    final_output_csv_path = os.path.join(output_directory, "picked_points.csv")
    results.to_csv(final_output_csv_path)
    print(f"Final results saved to: {final_output_csv_path}")

root = tk.Tk()
root.title("Data Processor")

input_directory_label = tk.Label(root, text="")
output_directory_label = tk.Label(root, text="")

input_directory_button = tk.Button(root, text="Browse Input Directory", command=browse_input_directory)
output_directory_button = tk.Button(root, text="Browse Output Directory", command=browse_output_directory)

# Checkbox for optional stress-strain analysis
analyze_stress_strain_var = tk.BooleanVar()
analyze_stress_strain_checkbutton = tk.Checkbutton(root, text="Analyze Stress-Strain", variable=analyze_stress_strain_var)
analyze_stress_strain_checkbutton.pack()

process_files_button = tk.Button(root, text="Process Files", command=process_files)

cf_label = tk.Label(root, text="Enter Machine Stiffness Correction (mm/kN):")
cf_entry = tk.Entry(root)
cf_entry.insert(0, "0.0023")  # Default value

#Packing the GUI elements
input_directory_button.pack(pady=5)
input_directory_label.pack(pady=5)
output_directory_button.pack(pady=5)
output_directory_label.pack(pady=5)

analyze_stress_strain_checkbutton.pack(pady=5)

cf_label.pack(pady=5)
cf_entry.pack(pady=5)

process_files_button.pack(pady=10)

root.mainloop()

